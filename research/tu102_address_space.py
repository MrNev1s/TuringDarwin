#!/usr/bin/env python3
"""Deterministic CPU-only TU102/TU116 address-space builder.

This module never opens a device, maps BARs, allocates DMA memory, or performs
MMIO. It builds byte-exact synthetic VER2 page-table images in ordinary Python
bytearrays and walks them with an independent decoder.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
import hashlib
import json
from typing import Dict, Iterable, Mapping, MutableMapping, Sequence

from tu102_mmu_model import (
    BIG_PAGE_SHIFT,
    DMA_ADDRESS_BITS,
    HUGE_PAGE_SHIFT,
    ModelError,
    PdeAperture,
    PteAperture,
    SMALL_PAGE_SHIFT,
    VIRTUAL_ADDRESS_BITS,
    decode_pde,
    decode_pte,
    encode_pde,
    encode_pte,
    geometry,
    split_virtual_address,
    validate_physical_address,
    validate_virtual_address,
)

TABLE_ALLOCATION_BYTES = 0x1000
SUPPORTED_PAGE_SHIFTS = (SMALL_PAGE_SHIFT, BIG_PAGE_SHIFT, HUGE_PAGE_SHIFT)


class AddressSpaceError(ModelError):
    """Fail-closed address-space construction or walk error."""


@dataclass(frozen=True)
class MappingAttributes:
    aperture: PteAperture = PteAperture.VIDEO_MEMORY
    kind: int = 0
    valid: bool = True
    volatile: bool = False
    privileged: bool = False
    read_only: bool = True
    atomic_disable: bool = True


@dataclass(frozen=True)
class PageMapping:
    virtual_address: int
    physical_address: int
    page_shift: int
    attributes: MappingAttributes

    @property
    def page_size(self) -> int:
        return 1 << self.page_shift

    @property
    def virtual_end(self) -> int:
        return self.virtual_address + self.page_size

    @property
    def physical_end(self) -> int:
        return self.physical_address + self.page_size


@dataclass(frozen=True)
class TranslationResult:
    virtual_address: int
    physical_address: int
    page_shift: int
    page_base: int
    attributes: Mapping[str, int | bool]


@dataclass(frozen=True)
class CompiledAddressSpace:
    root_address: int
    tables: Mapping[int, bytes]
    labels: Mapping[int, str]
    logical_sizes: Mapping[int, int]
    mappings: tuple[PageMapping, ...]

    def mapping_for_address(self, virtual_address: int) -> PageMapping:
        validate_virtual_address(virtual_address)
        found = [
            mapping
            for mapping in self.mappings
            if mapping.virtual_address <= virtual_address < mapping.virtual_end
        ]
        if len(found) != 1:
            if not found:
                raise AddressSpaceError("virtual address is not mapped")
            raise AddressSpaceError("virtual address resolves to overlapping mappings")
        return found[0]

    def translate(self, virtual_address: int, *, page_shift: int | None = None) -> TranslationResult:
        validate_virtual_address(virtual_address)
        if page_shift is None:
            mapping = self.mapping_for_address(virtual_address)
            page_shift = mapping.page_shift
        geometry(page_shift)
        parts = split_virtual_address(virtual_address, page_shift)

        root = _table(self.tables, self.root_address, "root")
        pd2_addr = _follow_pde(self.tables, _read_u64(root, parts["root"] * 8), "root")
        pd2 = _table(self.tables, pd2_addr, "pd2")
        pd1_addr = _follow_pde(self.tables, _read_u64(pd2, parts["pd2"] * 8), "pd2")
        pd1 = _table(self.tables, pd1_addr, "pd1")
        pd0_addr = _follow_pde(self.tables, _read_u64(pd1, parts["pd1"] * 8), "pd1")
        pd0 = _table(self.tables, pd0_addr, "pd0")

        pair_offset = parts["pd0"] * 16
        if page_shift == HUGE_PAGE_SHIFT:
            pte = _read_u64(pd0, pair_offset)
        else:
            half_offset = 0 if page_shift == BIG_PAGE_SHIFT else 8
            leaf_pde = _read_u64(pd0, pair_offset + half_offset)
            leaf_addr = _follow_pde(self.tables, leaf_pde, "pd0 leaf")
            leaf = _table(self.tables, leaf_addr, "leaf")
            pte = _read_u64(leaf, parts["leaf"] * 8)

        decoded = decode_pte(pte)
        if not bool(decoded["valid"]):
            raise AddressSpaceError("leaf PTE is invalid")
        page_base = int(decoded["physical_address"])
        physical_address = page_base + parts["offset"]
        return TranslationResult(
            virtual_address=virtual_address,
            physical_address=physical_address,
            page_shift=page_shift,
            page_base=page_base,
            attributes=decoded,
        )

    def digest(self) -> str:
        digest = hashlib.sha256()
        digest.update(self.root_address.to_bytes(8, "little"))
        for address in sorted(self.tables):
            digest.update(address.to_bytes(8, "little"))
            digest.update(self.logical_sizes[address].to_bytes(4, "little"))
            digest.update(self.tables[address])
        return digest.hexdigest()

    @property
    def allocated_bytes(self) -> int:
        return sum(len(table) for table in self.tables.values())


class SyntheticAllocator:
    """Deterministic 4 KiB allocator used only for synthetic table addresses."""

    def __init__(self, base: int = 0x01000000, limit: int = 1 << DMA_ADDRESS_BITS):
        if base < 0 or base & (TABLE_ALLOCATION_BYTES - 1):
            raise AddressSpaceError("synthetic allocator base must be 4 KiB aligned")
        if limit <= base or limit > (1 << DMA_ADDRESS_BITS):
            raise AddressSpaceError("synthetic allocator limit is invalid")
        self._next = base
        self._limit = limit

    def allocate(self) -> int:
        address = self._next
        end = address + TABLE_ALLOCATION_BYTES
        if end > self._limit:
            raise AddressSpaceError("synthetic page-table allocator exhausted")
        self._next = end
        return address


class SyntheticAddressSpace:
    """Mutable mapping registry compiled into deterministic page-table bytes."""

    def __init__(self, *, table_base: int = 0x01000000):
        self.table_base = table_base
        self._pages: Dict[int, PageMapping] = {}

    @property
    def mappings(self) -> tuple[PageMapping, ...]:
        return tuple(self._pages[address] for address in sorted(self._pages))

    def clone(self) -> "SyntheticAddressSpace":
        cloned = SyntheticAddressSpace(table_base=self.table_base)
        cloned._pages = dict(self._pages)
        return cloned

    def map_range(
        self,
        virtual_address: int,
        physical_address: int,
        length: int,
        *,
        page_shift: int,
        attributes: MappingAttributes | None = None,
        allow_alias: bool = False,
    ) -> None:
        geo = geometry(page_shift)
        attrs = attributes or MappingAttributes()
        if not isinstance(length, int) or length <= 0:
            raise AddressSpaceError("mapping length must be a positive integer")
        if length & (geo.page_size - 1):
            raise AddressSpaceError("mapping length must be page aligned")
        validate_virtual_address(virtual_address)
        validate_physical_address(physical_address, page_shift)
        if virtual_address & (geo.page_size - 1):
            raise AddressSpaceError("virtual address must be page aligned")
        if virtual_address + length > (1 << VIRTUAL_ADDRESS_BITS):
            raise AddressSpaceError("mapping exceeds 49-bit virtual address space")
        if physical_address + length > (1 << DMA_ADDRESS_BITS):
            raise AddressSpaceError("mapping exceeds 47-bit physical address space")

        candidates = [
            PageMapping(
                virtual_address=virtual_address + offset,
                physical_address=physical_address + offset,
                page_shift=page_shift,
                attributes=attrs,
            )
            for offset in range(0, length, geo.page_size)
        ]

        existing = list(self._pages.values())
        for candidate in candidates:
            for other in existing:
                if _overlaps(candidate.virtual_address, candidate.virtual_end,
                             other.virtual_address, other.virtual_end):
                    raise AddressSpaceError("virtual mapping overlaps an existing mapping")
                if not allow_alias and _overlaps(
                    candidate.physical_address,
                    candidate.physical_end,
                    other.physical_address,
                    other.physical_end,
                ):
                    raise AddressSpaceError("physical alias requires allow_alias=True")
            for other in candidates:
                if other is candidate:
                    continue
                if _overlaps(candidate.virtual_address, candidate.virtual_end,
                             other.virtual_address, other.virtual_end):
                    raise AssertionError("candidate pages overlap")

        self._pages.update({mapping.virtual_address: mapping for mapping in candidates})

    def unmap_range(self, virtual_address: int, length: int) -> None:
        if not isinstance(length, int) or length <= 0:
            raise AddressSpaceError("unmap length must be positive")
        end = virtual_address + length
        selected = [
            mapping
            for mapping in self._pages.values()
            if virtual_address <= mapping.virtual_address and mapping.virtual_end <= end
        ]
        if not selected:
            raise AddressSpaceError("unmap range contains no complete mappings")
        covered = sum(mapping.page_size for mapping in selected)
        if covered != length:
            raise AddressSpaceError("unmap range must exactly cover complete mappings")
        cursor = virtual_address
        for mapping in sorted(selected, key=lambda item: item.virtual_address):
            if mapping.virtual_address != cursor:
                raise AddressSpaceError("unmap range contains a gap")
            cursor = mapping.virtual_end
        if cursor != end:
            raise AddressSpaceError("unmap range is incomplete")
        for mapping in selected:
            del self._pages[mapping.virtual_address]

    def promote_4k_to_2m(self, virtual_address: int) -> None:
        huge_size = 1 << HUGE_PAGE_SHIFT
        small_size = 1 << SMALL_PAGE_SHIFT
        if virtual_address & (huge_size - 1):
            raise AddressSpaceError("promotion base must be 2 MiB aligned")
        pages = []
        for index in range(huge_size // small_size):
            va = virtual_address + index * small_size
            mapping = self._pages.get(va)
            if mapping is None or mapping.page_shift != SMALL_PAGE_SHIFT:
                raise AddressSpaceError("promotion requires 512 present 4 KiB mappings")
            pages.append(mapping)
        first = pages[0]
        if first.physical_address & (huge_size - 1):
            raise AddressSpaceError("promotion physical base must be 2 MiB aligned")
        for index, mapping in enumerate(pages):
            if mapping.physical_address != first.physical_address + index * small_size:
                raise AddressSpaceError("promotion requires physically contiguous pages")
            if mapping.attributes != first.attributes:
                raise AddressSpaceError("promotion requires identical attributes")
        for mapping in pages:
            del self._pages[mapping.virtual_address]
        self._pages[virtual_address] = PageMapping(
            virtual_address=virtual_address,
            physical_address=first.physical_address,
            page_shift=HUGE_PAGE_SHIFT,
            attributes=first.attributes,
        )

    def demote_2m_to_4k(self, virtual_address: int) -> None:
        huge_size = 1 << HUGE_PAGE_SHIFT
        small_size = 1 << SMALL_PAGE_SHIFT
        mapping = self._pages.get(virtual_address)
        if mapping is None or mapping.page_shift != HUGE_PAGE_SHIFT:
            raise AddressSpaceError("demotion requires one 2 MiB mapping")
        del self._pages[virtual_address]
        for index in range(huge_size // small_size):
            va = virtual_address + index * small_size
            pa = mapping.physical_address + index * small_size
            self._pages[va] = replace(
                mapping,
                virtual_address=va,
                physical_address=pa,
                page_shift=SMALL_PAGE_SHIFT,
            )

    def compile(self) -> CompiledAddressSpace:
        allocator = SyntheticAllocator(self.table_base)
        tables: Dict[int, bytearray] = {}
        labels: Dict[int, str] = {}
        logical_sizes: Dict[int, int] = {}
        table_keys: Dict[tuple[object, ...], int] = {}
        pd0_modes: Dict[tuple[int, int], set[int]] = {}

        def allocate(key: tuple[object, ...], label: str, logical_size: int = TABLE_ALLOCATION_BYTES) -> int:
            if key in table_keys:
                return table_keys[key]
            address = allocator.allocate()
            table_keys[key] = address
            tables[address] = bytearray(TABLE_ALLOCATION_BYTES)
            labels[address] = label
            logical_sizes[address] = logical_size
            return address

        root_address = allocate(("root",), "root", 32)

        for mapping in self.mappings:
            parts = split_virtual_address(mapping.virtual_address, mapping.page_shift)
            pd2_address = allocate(("pd2", parts["root"]), f"pd2:r{parts['root']}")
            _write_expected_pde(
                tables[root_address], parts["root"] * 8, pd2_address, "root"
            )

            pd1_key = ("pd1", parts["root"], parts["pd2"])
            pd1_address = allocate(pd1_key, f"pd1:r{parts['root']}:p2{parts['pd2']}")
            _write_expected_pde(
                tables[pd2_address], parts["pd2"] * 8, pd1_address, "pd2"
            )

            pd0_key = ("pd0", parts["root"], parts["pd2"], parts["pd1"])
            pd0_address = allocate(
                pd0_key,
                f"pd0:r{parts['root']}:p2{parts['pd2']}:p1{parts['pd1']}",
            )
            _write_expected_pde(
                tables[pd1_address], parts["pd1"] * 8, pd0_address, "pd1"
            )

            pte = encode_pte(
                mapping.physical_address,
                page_shift=mapping.page_shift,
                aperture=mapping.attributes.aperture,
                kind=mapping.attributes.kind,
                valid=mapping.attributes.valid,
                volatile=mapping.attributes.volatile,
                privileged=mapping.attributes.privileged,
                read_only=mapping.attributes.read_only,
                atomic_disable=mapping.attributes.atomic_disable,
            )
            pair_offset = parts["pd0"] * 16
            mode_key = (pd0_address, parts["pd0"])
            modes = pd0_modes.setdefault(mode_key, set())

            if mapping.page_shift == HUGE_PAGE_SHIFT:
                if modes:
                    raise AddressSpaceError("2 MiB PTE conflicts with PD0 leaf tables")
                modes.add(HUGE_PAGE_SHIFT)
                _write_zero_expected_u64(tables[pd0_address], pair_offset, pte, "2 MiB PTE")
                _write_zero_expected_u64(tables[pd0_address], pair_offset + 8, 0, "2 MiB upper half")
                continue

            if HUGE_PAGE_SHIFT in modes:
                raise AddressSpaceError("leaf table conflicts with a 2 MiB PTE")
            modes.add(mapping.page_shift)
            logical_leaf_size = 0x100 if mapping.page_shift == BIG_PAGE_SHIFT else 0x1000
            leaf_key = (
                "leaf",
                parts["root"],
                parts["pd2"],
                parts["pd1"],
                parts["pd0"],
                mapping.page_shift,
            )
            leaf_address = allocate(
                leaf_key,
                f"leaf:{mapping.page_shift}:r{parts['root']}:p2{parts['pd2']}:p1{parts['pd1']}:p0{parts['pd0']}",
                logical_leaf_size,
            )
            half_offset = 0 if mapping.page_shift == BIG_PAGE_SHIFT else 8
            _write_expected_pde(
                tables[pd0_address], pair_offset + half_offset, leaf_address, "pd0 leaf"
            )
            _write_zero_expected_u64(
                tables[leaf_address], parts["leaf"] * 8, pte, "leaf PTE"
            )

        frozen = {address: bytes(table) for address, table in tables.items()}
        return CompiledAddressSpace(
            root_address=root_address,
            tables=frozen,
            labels=labels,
            logical_sizes=logical_sizes,
            mappings=self.mappings,
        )


def _table(tables: Mapping[int, bytes], address: int, label: str) -> bytes:
    if address not in tables:
        raise AddressSpaceError(f"{label} table is absent")
    table = tables[address]
    if len(table) != TABLE_ALLOCATION_BYTES:
        raise AddressSpaceError(f"{label} allocation is not 4 KiB")
    return table


def _read_u64(table: bytes | bytearray, offset: int) -> int:
    if offset < 0 or offset + 8 > len(table):
        raise AddressSpaceError("64-bit table access outside allocation")
    return int.from_bytes(table[offset:offset + 8], "little")


def _write_u64(table: bytearray, offset: int, value: int) -> None:
    if value < 0 or value >= (1 << 64):
        raise AddressSpaceError("table entry does not fit 64 bits")
    if offset < 0 or offset + 8 > len(table):
        raise AddressSpaceError("64-bit table write outside allocation")
    table[offset:offset + 8] = value.to_bytes(8, "little")


def _write_zero_expected_u64(
    table: bytearray,
    offset: int,
    value: int,
    label: str,
) -> None:
    current = _read_u64(table, offset)
    if current not in (0, value):
        raise AddressSpaceError(f"conflicting {label} entry")
    _write_u64(table, offset, value)


def _write_expected_pde(
    table: bytearray,
    offset: int,
    target_address: int,
    label: str,
) -> None:
    value = encode_pde(target_address, PdeAperture.VIDEO_MEMORY)
    current = _read_u64(table, offset)
    if current not in (0, value):
        raise AddressSpaceError(f"conflicting {label} PDE target")
    _write_u64(table, offset, value)


def _follow_pde(tables: Mapping[int, bytes], entry: int, label: str) -> int:
    decoded = decode_pde(entry)
    if not bool(decoded["present"]):
        raise AddressSpaceError(f"{label} PDE is not present")
    address = int(decoded["table_address"])
    if address not in tables:
        raise AddressSpaceError(f"{label} target table is absent")
    return address


def _overlaps(start_a: int, end_a: int, start_b: int, end_b: int) -> bool:
    return start_a < end_b and start_b < end_a


if __name__ == "__main__":
    space = SyntheticAddressSpace()
    space.map_range(0x400000, 0x80000000, 0x400000, page_shift=SMALL_PAGE_SHIFT)
    image = space.compile()
    print(json.dumps({
        "mappings": len(image.mappings),
        "tables": len(image.tables),
        "digest": image.digest(),
    }, indent=2))
