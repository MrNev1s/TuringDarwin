#!/usr/bin/env python3
"""Offline TU102/TU116 MMU format model.

This module performs no device access. It models the page-table hierarchy and
entry encodings used by Nouveau's GP100/TU102 VMM implementation. It is a
research/test oracle, not production command-submission code.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum
from typing import Dict, Iterable, Mapping

DMA_ADDRESS_BITS = 47
VIRTUAL_ADDRESS_BITS = 49
SMALL_PAGE_SHIFT = 12
BIG_PAGE_SHIFT = 16
HUGE_PAGE_SHIFT = 21
SMALL_PAGE_SIZE = 1 << SMALL_PAGE_SHIFT
BIG_PAGE_SIZE = 1 << BIG_PAGE_SHIFT
HUGE_PAGE_SIZE = 1 << HUGE_PAGE_SHIFT
KIND_COUNT = 16
INVALID_KIND = 0x07
KIND_MAP = (0x00, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07,
            0x06, 0x06, 0x02, 0x01, 0x03, 0x04, 0x05, 0x07)

# Low-to-high index widths from Nouveau gp100_vmm_desc_12/_16.
SMALL_INDEX_BITS = (9, 8, 9, 9, 2)
BIG_INDEX_BITS = (5, 8, 9, 9, 2)
# A 2 MiB mapping terminates in the low 64-bit half of the 16-byte PD0 entry.
HUGE_INDEX_BITS = (8, 9, 9, 2)
HUGE_LEVEL_NAMES = ("pd0", "pd1", "pd2", "root")
LEVEL_NAMES = ("leaf", "pd0", "pd1", "pd2", "root")

PTE_VALID_BIT = 0
PTE_APERTURE_SHIFT = 1
PTE_APERTURE_MASK = 0x3
PTE_VOLATILE_BIT = 3
PTE_PRIVILEGED_BIT = 5
PTE_READ_ONLY_BIT = 6
PTE_ATOMIC_DISABLE_BIT = 7
PTE_KIND_SHIFT = 56
PTE_KIND_MASK = 0xFF
PTE_COMPTAGLINE_SHIFT = 36
PTE_COMPTAGLINE_MASK = (1 << 20) - 1

PDE_APERTURE_SHIFT = 1
PDE_APERTURE_MASK = 0x3
PDE_VOLATILE_BIT = 3

INSTANCE_REPLAY_TEX_BIT = 4
INSTANCE_REPLAY_GCC_BIT = 5
INSTANCE_FORMAT_VER2_BIT = 10
INSTANCE_BIG_PAGE_64K_BIT = 11


class ModelError(ValueError):
    pass


class PteAperture(IntEnum):
    VIDEO_MEMORY = 0
    SYSTEM_COHERENT = 2
    SYSTEM_NONCOHERENT = 3


class PdeAperture(IntEnum):
    INVALID = 0
    VIDEO_MEMORY = 1
    SYSTEM_COHERENT = 2
    SYSTEM_NONCOHERENT = 3


@dataclass(frozen=True)
class PageGeometry:
    page_shift: int
    index_bits: tuple[int, int, int, int, int]

    @property
    def page_size(self) -> int:
        return 1 << self.page_shift

    @property
    def virtual_address_bits(self) -> int:
        return self.page_shift + sum(self.index_bits)

    @property
    def leaf_entries(self) -> int:
        return 1 << self.index_bits[0]

    @property
    def leaf_table_bytes(self) -> int:
        return self.leaf_entries * 8

    @property
    def leaf_coverage(self) -> int:
        return self.leaf_entries * self.page_size


SMALL_GEOMETRY = PageGeometry(SMALL_PAGE_SHIFT, SMALL_INDEX_BITS)
BIG_GEOMETRY = PageGeometry(BIG_PAGE_SHIFT, BIG_INDEX_BITS)
HUGE_GEOMETRY = PageGeometry(HUGE_PAGE_SHIFT, HUGE_INDEX_BITS)


def geometry(page_shift: int) -> PageGeometry:
    if page_shift == SMALL_PAGE_SHIFT:
        return SMALL_GEOMETRY
    if page_shift == BIG_PAGE_SHIFT:
        return BIG_GEOMETRY
    if page_shift == HUGE_PAGE_SHIFT:
        return HUGE_GEOMETRY
    raise ModelError(f"unsupported TU102 page shift: {page_shift}")


def validate_virtual_address(va: int) -> None:
    if not isinstance(va, int) or va < 0:
        raise ModelError("virtual address must be a non-negative integer")
    if va >= (1 << VIRTUAL_ADDRESS_BITS):
        raise ModelError("virtual address exceeds derived 49-bit hierarchy")


def validate_physical_address(pa: int, page_shift: int) -> None:
    if not isinstance(pa, int) or pa < 0:
        raise ModelError("physical address must be a non-negative integer")
    if pa >= (1 << DMA_ADDRESS_BITS):
        raise ModelError("physical address exceeds 47-bit DMA profile")
    if pa & ((1 << page_shift) - 1):
        raise ModelError(f"physical address is not {1 << page_shift}-byte aligned")


def split_virtual_address(va: int, page_shift: int) -> Dict[str, int]:
    validate_virtual_address(va)
    geo = geometry(page_shift)
    value = va >> page_shift
    out: Dict[str, int] = {"offset": va & (geo.page_size - 1)}
    names = HUGE_LEVEL_NAMES if page_shift == HUGE_PAGE_SHIFT else LEVEL_NAMES
    for name, width in zip(names, geo.index_bits):
        out[name] = value & ((1 << width) - 1)
        value >>= width
    if value:
        raise AssertionError("hierarchy did not consume the full address")
    return out


def compose_virtual_address(parts: Mapping[str, int], page_shift: int) -> int:
    geo = geometry(page_shift)
    value = 0
    names = HUGE_LEVEL_NAMES if page_shift == HUGE_PAGE_SHIFT else LEVEL_NAMES
    for name, width in reversed(tuple(zip(names, geo.index_bits))):
        item = int(parts[name])
        if item < 0 or item >= (1 << width):
            raise ModelError(f"{name} index does not fit {width} bits")
        value = (value << width) | item
    offset = int(parts.get("offset", 0))
    if offset < 0 or offset >= geo.page_size:
        raise ModelError("page offset out of range")
    va = (value << page_shift) | offset
    validate_virtual_address(va)
    return va


def encode_pte(
    physical_address: int,
    *,
    page_shift: int,
    aperture: PteAperture = PteAperture.VIDEO_MEMORY,
    kind: int = 0,
    valid: bool = True,
    volatile: bool = False,
    privileged: bool = False,
    read_only: bool = False,
    atomic_disable: bool = False,
    comptagline: int = 0,
) -> int:
    """Encode one uncompressed GP100/TU102 VER2 PTE.

    ``kind`` is the 0..15 logical kind index accepted by Nouveau. On a
    non-GSP path, Nouveau falls back from a compressed logical kind to the
    corresponding uncompressed hardware kind in ``tu102_mmu_kind``. This
    model applies that fallback and rejects compression/comptagline entirely
    because TuringDarwin has no authorised GSP/PMU firmware path.
    """
    validate_physical_address(physical_address, page_shift)
    if kind < 0 or kind >= KIND_COUNT:
        raise ModelError("kind index is outside the 16-entry TU102 map")
    hardware_kind = KIND_MAP[kind]
    if hardware_kind == INVALID_KIND:
        raise ModelError("kind maps to TU102 invalid kind 0x07")
    if comptagline != 0:
        raise ModelError("compression/comptagline is blocked without an authorised firmware path")

    data = physical_address >> 4
    if valid:
        data |= 1 << PTE_VALID_BIT
    data |= (int(aperture) & PTE_APERTURE_MASK) << PTE_APERTURE_SHIFT
    if volatile:
        data |= 1 << PTE_VOLATILE_BIT
    if privileged:
        data |= 1 << PTE_PRIVILEGED_BIT
    if read_only:
        data |= 1 << PTE_READ_ONLY_BIT
    if atomic_disable:
        data |= 1 << PTE_ATOMIC_DISABLE_BIT
    data |= (hardware_kind & PTE_KIND_MASK) << PTE_KIND_SHIFT
    return data & ((1 << 64) - 1)


def decode_pte(entry: int) -> Dict[str, int | bool]:
    if entry < 0 or entry >= (1 << 64):
        raise ModelError("PTE must fit 64 bits")
    low_attr_mask = 0xFF
    hardware_kind = (entry >> PTE_KIND_SHIFT) & PTE_KIND_MASK
    # For the current uncompressed model, bits 8..42 retain physical bits
    # 12..46 after Nouveau's address >> 4 transform.
    address_mask = ((1 << 43) - 1) & ~low_attr_mask
    physical_address = (entry & address_mask) << 4
    return {
        "physical_address": physical_address,
        "valid": bool(entry & (1 << PTE_VALID_BIT)),
        "aperture": (entry >> PTE_APERTURE_SHIFT) & PTE_APERTURE_MASK,
        "volatile": bool(entry & (1 << PTE_VOLATILE_BIT)),
        "privileged": bool(entry & (1 << PTE_PRIVILEGED_BIT)),
        "read_only": bool(entry & (1 << PTE_READ_ONLY_BIT)),
        "atomic_disable": bool(entry & (1 << PTE_ATOMIC_DISABLE_BIT)),
        "hardware_kind": hardware_kind,
        "comptagline": 0,
    }


def encode_pde(table_address: int, aperture: PdeAperture) -> int:
    if table_address < 0 or table_address >= (1 << DMA_ADDRESS_BITS):
        raise ModelError("page-table address exceeds 47-bit DMA profile")
    if table_address & 0xFF:
        raise ModelError("PDE target must satisfy Nouveau's minimum 0x100 alignment")
    if aperture == PdeAperture.INVALID:
        return 0
    data = table_address >> 4
    data |= (int(aperture) & PDE_APERTURE_MASK) << PDE_APERTURE_SHIFT
    if aperture == PdeAperture.SYSTEM_COHERENT:
        data |= 1 << PDE_VOLATILE_BIT
    return data


def decode_pde(entry: int) -> Dict[str, int | bool]:
    if entry < 0 or entry >= (1 << 64):
        raise ModelError("PDE must fit 64 bits")
    aperture = (entry >> PDE_APERTURE_SHIFT) & PDE_APERTURE_MASK
    return {
        "table_address": (entry & ~0xF) << 4,
        "aperture": aperture,
        "volatile": bool(entry & (1 << PDE_VOLATILE_BIT)),
        "present": aperture != PdeAperture.INVALID,
    }


def encode_pd0_pair(big_pde: int, small_pde: int) -> bytes:
    """Encode a 128-bit PD0 entry in Nouveau's pt[0]/pt[1] order.

    pt[0] is the LPT (64 KiB) table and occupies the low 64-bit half.
    pt[1] is the SPT (4 KiB) table and occupies the high 64-bit half.
    """
    if not (0 <= big_pde < (1 << 64) and 0 <= small_pde < (1 << 64)):
        raise ModelError("PD0 halves must be 64-bit values")
    return big_pde.to_bytes(8, "little") + small_pde.to_bytes(8, "little")


def encode_instance_pdb(
    root_address: int,
    *,
    aperture: PteAperture = PteAperture.VIDEO_MEMORY,
    replay_tex: bool = False,
    replay_gcc: bool = False,
) -> int:
    if root_address < 0 or root_address >= (1 << DMA_ADDRESS_BITS):
        raise ModelError("root address exceeds 47-bit DMA profile")
    if root_address & 0xFFF:
        raise ModelError("root page directory must be 4 KiB aligned")
    base = root_address
    base |= int(aperture)
    if aperture == PteAperture.SYSTEM_COHERENT:
        base |= 1 << 2
    if replay_tex:
        base |= 1 << INSTANCE_REPLAY_TEX_BIT
    if replay_gcc:
        base |= 1 << INSTANCE_REPLAY_GCC_BIT
    base |= 1 << INSTANCE_FORMAT_VER2_BIT
    base |= 1 << INSTANCE_BIG_PAGE_64K_BIT
    return base


def hierarchy_summary(page_shift: int) -> Dict[str, int | tuple[int, ...] | bool]:
    geo = geometry(page_shift)
    terminates_at_pd0 = page_shift == HUGE_PAGE_SHIFT
    leaf_entries = 256 if terminates_at_pd0 else geo.leaf_entries
    leaf_table_bytes = 4096 if terminates_at_pd0 else geo.leaf_table_bytes
    leaf_coverage = 512 * 1024 * 1024 if terminates_at_pd0 else geo.leaf_coverage
    return {
        "page_shift": geo.page_shift,
        "page_size": geo.page_size,
        "virtual_address_bits": geo.virtual_address_bits,
        "index_bits_low_to_high": geo.index_bits,
        "leaf_entries": leaf_entries,
        "leaf_table_bytes": leaf_table_bytes,
        "leaf_coverage": leaf_coverage,
        "terminates_at_pd0": terminates_at_pd0,
        "pd0_entries": 1 << 8,
        "pd0_entry_bytes": 16,
        "pd0_table_bytes": (1 << 8) * 16,
        "pd1_entries": 1 << 9,
        "pd1_table_bytes": (1 << 9) * 8,
        "pd2_entries": 1 << 9,
        "pd2_table_bytes": (1 << 9) * 8,
        "root_entries": 1 << 2,
        "root_logical_bytes": (1 << 2) * 8,
        "root_allocation_alignment": 0x1000,
    }


def iter_boundary_addresses(page_shift: int) -> Iterable[int]:
    geo = geometry(page_shift)
    yield 0
    yield geo.page_size - 1
    yield geo.page_size
    yield geo.leaf_coverage - 1
    yield geo.leaf_coverage
    yield (1 << VIRTUAL_ADDRESS_BITS) - 1


if __name__ == "__main__":
    import json
    print(json.dumps({
        "small": hierarchy_summary(SMALL_PAGE_SHIFT),
        "big": hierarchy_summary(BIG_PAGE_SHIFT),
    }, indent=2))
