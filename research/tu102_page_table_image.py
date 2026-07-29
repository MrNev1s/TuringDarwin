#!/usr/bin/env python3
"""Build and walk synthetic TU102 page-table images entirely in RAM."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Mapping

from tu102_mmu_model import (
    BIG_PAGE_SHIFT,
    HUGE_PAGE_SHIFT,
    ModelError,
    PdeAperture,
    PteAperture,
    SMALL_PAGE_SHIFT,
    decode_pde,
    decode_pte,
    encode_pd0_pair,
    encode_pde,
    encode_pte,
    geometry,
    split_virtual_address,
)

TABLE_ALLOCATION_BYTES = 0x1000


@dataclass(frozen=True)
class SyntheticPageTableImage:
    page_shift: int
    virtual_address: int
    physical_address: int
    table_addresses: Mapping[str, int]
    tables: Mapping[int, bytes]

    def table(self, name: str) -> bytes:
        return self.tables[self.table_addresses[name]]


class PageWalkError(ModelError):
    pass


def _write_u64(table: bytearray, offset: int, value: int) -> None:
    if offset < 0 or offset + 8 > len(table):
        raise ModelError("64-bit table write outside allocation")
    table[offset:offset + 8] = value.to_bytes(8, "little")


def _read_u64(table: bytes, offset: int) -> int:
    if offset < 0 or offset + 8 > len(table):
        raise PageWalkError("64-bit table read outside allocation")
    return int.from_bytes(table[offset:offset + 8], "little")


def build_single_mapping(
    virtual_address: int,
    physical_address: int,
    *,
    page_shift: int,
    table_base: int = 0x01000000,
    read_only: bool = True,
    kind: int = 0,
) -> SyntheticPageTableImage:
    if table_base & 0xFFF:
        raise ModelError("synthetic table base must be 4 KiB aligned")
    geometry(page_shift)
    parts = split_virtual_address(virtual_address, page_shift)

    names = ("root", "pd2", "pd1", "pd0")
    if page_shift != HUGE_PAGE_SHIFT:
        names += ("leaf",)
    addresses = {name: table_base + index * TABLE_ALLOCATION_BYTES
                 for index, name in enumerate(names)}
    tables: Dict[int, bytearray] = {
        address: bytearray(TABLE_ALLOCATION_BYTES)
        for address in addresses.values()
    }

    _write_u64(tables[addresses["root"]], parts["root"] * 8,
               encode_pde(addresses["pd2"], PdeAperture.VIDEO_MEMORY))
    _write_u64(tables[addresses["pd2"]], parts["pd2"] * 8,
               encode_pde(addresses["pd1"], PdeAperture.VIDEO_MEMORY))
    _write_u64(tables[addresses["pd1"]], parts["pd1"] * 8,
               encode_pde(addresses["pd0"], PdeAperture.VIDEO_MEMORY))

    pte = encode_pte(
        physical_address,
        page_shift=page_shift,
        aperture=PteAperture.VIDEO_MEMORY,
        kind=kind,
        valid=True,
        read_only=read_only,
        atomic_disable=True,
    )
    pd0_offset = parts["pd0"] * 16

    if page_shift == HUGE_PAGE_SHIFT:
        # A 2 MiB leaf is stored directly in the low 64-bit half of PD0.
        pair = encode_pd0_pair(pte, 0)
    else:
        leaf_pde = encode_pde(addresses["leaf"], PdeAperture.VIDEO_MEMORY)
        if page_shift == BIG_PAGE_SHIFT:
            pair = encode_pd0_pair(leaf_pde, 0)
        elif page_shift == SMALL_PAGE_SHIFT:
            pair = encode_pd0_pair(0, leaf_pde)
        else:
            raise ModelError("unsupported page shift")
        _write_u64(tables[addresses["leaf"]], parts["leaf"] * 8, pte)

    tables[addresses["pd0"]][pd0_offset:pd0_offset + 16] = pair
    frozen = {address: bytes(data) for address, data in tables.items()}
    return SyntheticPageTableImage(
        page_shift=page_shift,
        virtual_address=virtual_address,
        physical_address=physical_address,
        table_addresses=addresses,
        tables=frozen,
    )


def _follow_pde(tables: Mapping[int, bytes], entry: int, label: str) -> int:
    decoded = decode_pde(entry)
    if not decoded["present"]:
        raise PageWalkError(f"{label} PDE is not present")
    target = int(decoded["table_address"])
    if target not in tables:
        raise PageWalkError(f"{label} target table is absent from image")
    return target


def walk_mapping(
    tables: Mapping[int, bytes],
    root_address: int,
    virtual_address: int,
    *,
    page_shift: int,
) -> int:
    geometry(page_shift)
    parts = split_virtual_address(virtual_address, page_shift)
    if root_address not in tables:
        raise PageWalkError("root table is absent")

    root = tables[root_address]
    pd2_addr = _follow_pde(tables, _read_u64(root, parts["root"] * 8), "root")
    pd2 = tables[pd2_addr]
    pd1_addr = _follow_pde(tables, _read_u64(pd2, parts["pd2"] * 8), "pd2")
    pd1 = tables[pd1_addr]
    pd0_addr = _follow_pde(tables, _read_u64(pd1, parts["pd1"] * 8), "pd1")
    pd0 = tables[pd0_addr]

    pair_offset = parts["pd0"] * 16
    if page_shift == HUGE_PAGE_SHIFT:
        pte = _read_u64(pd0, pair_offset)
    else:
        half_offset = 0 if page_shift == BIG_PAGE_SHIFT else 8
        leaf_entry = _read_u64(pd0, pair_offset + half_offset)
        leaf_addr = _follow_pde(tables, leaf_entry, "pd0 leaf")
        leaf = tables[leaf_addr]
        pte = _read_u64(leaf, parts["leaf"] * 8)

    decoded = decode_pte(pte)
    if not decoded["valid"]:
        raise PageWalkError("leaf PTE is invalid")
    page_base = int(decoded["physical_address"])
    return page_base + parts["offset"]


def table_digest_material(image: SyntheticPageTableImage) -> bytes:
    out = bytearray()
    for name in ("root", "pd2", "pd1", "pd0", "leaf"):
        if name not in image.table_addresses:
            continue
        addr = image.table_addresses[name]
        out += addr.to_bytes(8, "little")
        out += image.tables[addr]
    return bytes(out)
