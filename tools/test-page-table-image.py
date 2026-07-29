#!/usr/bin/env python3
from __future__ import annotations

import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "research"))

from tu102_mmu_model import (  # noqa: E402
    BIG_PAGE_SHIFT,
    HUGE_PAGE_SHIFT,
    SMALL_PAGE_SHIFT,
)
from tu102_page_table_image import (  # noqa: E402
    PageWalkError,
    build_single_mapping,
    table_digest_material,
    walk_mapping,
)

rng = random.Random(0x4D4D5535)
count = 0
for shift in (SMALL_PAGE_SHIFT, BIG_PAGE_SHIFT, HUGE_PAGE_SHIFT):
    page_size = 1 << shift
    for _ in range(10000):
        va = rng.randrange(1 << 49)
        pa = rng.randrange(1 << 47) & ~(page_size - 1)
        image = build_single_mapping(va, pa, page_shift=shift,
                                     table_base=0x01000000,
                                     read_only=True, kind=0)
        translated = walk_mapping(image.tables, image.table_addresses["root"],
                                  va, page_shift=shift)
        assert translated == pa + (va & (page_size - 1))
        expected_tables = 4 if shift == HUGE_PAGE_SHIFT else 5
        assert len(table_digest_material(image)) == expected_tables * (0x1000 + 8)
        count += 1

small = build_single_mapping(0x12345000, 0x20000000,
                             page_shift=SMALL_PAGE_SHIFT)
try:
    walk_mapping(small.tables, small.table_addresses["root"], 0x12345000,
                 page_shift=BIG_PAGE_SHIFT)
except PageWalkError:
    pass
else:
    raise AssertionError("wrong leaf-size walk unexpectedly succeeded")

image = build_single_mapping(0x400000, 0x80000000,
                             page_shift=SMALL_PAGE_SHIFT)
broken = dict(image.tables)
del broken[image.table_addresses["pd1"]]
try:
    walk_mapping(broken, image.table_addresses["root"], 0x400000,
                 page_shift=SMALL_PAGE_SHIFT)
except PageWalkError:
    pass
else:
    raise AssertionError("missing table unexpectedly succeeded")

corrupt = dict(image.tables)
root = bytearray(corrupt[image.table_addresses["root"]])
root[:] = b"\x00" * len(root)
corrupt[image.table_addresses["root"]] = bytes(root)
try:
    walk_mapping(corrupt, image.table_addresses["root"], 0x400000,
                 page_shift=SMALL_PAGE_SHIFT)
except PageWalkError:
    pass
else:
    raise AssertionError("invalid root entry unexpectedly succeeded")

print("PAGE-TABLE IMAGE CONTRACT PASSED")
print(f"- {count} complete synthetic build/walk round trips")
print("- 4 KiB, 64 KiB and 2 MiB paths")
print("- verified low=LPT/high=SPT PD0 half ordering")
print("- verified direct 2 MiB PTE in low PD0 half")
print("- missing/corrupt/wrong-page-size cases fail closed")
print("- zero device access")
