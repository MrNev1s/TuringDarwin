#!/usr/bin/env python3
from __future__ import annotations

import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "research"))

from tu102_address_space import (  # noqa: E402
    AddressSpaceError,
    MappingAttributes,
    SyntheticAddressSpace,
)
from tu102_mmu_model import (  # noqa: E402
    BIG_PAGE_SHIFT,
    HUGE_PAGE_SHIFT,
    SMALL_PAGE_SHIFT,
)


def must_fail(fn, *args, **kwargs):
    try:
        fn(*args, **kwargs)
    except AddressSpaceError:
        return
    raise AssertionError(f"expected AddressSpaceError from {fn.__name__}")


rng = random.Random(0x54553131365F4D4D)
translated = 0

# 4 KiB: 4 MiB crosses a 2 MiB leaf boundary.
small = SyntheticAddressSpace(table_base=0x01000000)
small.map_range(0x0000000040000000, 0x0000000100000000, 4 * 1024 * 1024,
                page_shift=SMALL_PAGE_SHIFT)
small_image = small.compile()
for _ in range(4000):
    offset = rng.randrange(4 * 1024 * 1024)
    result = small_image.translate(0x40000000 + offset)
    assert result.physical_address == 0x100000000 + offset
    assert result.page_shift == SMALL_PAGE_SHIFT
    translated += 1
assert len(small_image.mappings) == 1024

# 64 KiB: 4 MiB crosses a 2 MiB large-page leaf boundary.
big = SyntheticAddressSpace(table_base=0x02000000)
big.map_range(0x0000000080000000, 0x0000000200000000, 4 * 1024 * 1024,
              page_shift=BIG_PAGE_SHIFT)
big_image = big.compile()
for _ in range(4000):
    offset = rng.randrange(4 * 1024 * 1024)
    result = big_image.translate(0x80000000 + offset)
    assert result.physical_address == 0x200000000 + offset
    assert result.page_shift == BIG_PAGE_SHIFT
    translated += 1
assert len(big_image.mappings) == 64

# 2 MiB: 600 MiB crosses the 512 MiB PD0 table coverage boundary.
huge = SyntheticAddressSpace(table_base=0x03000000)
huge.map_range(0x0000000100000000, 0x0000000300000000, 600 * 1024 * 1024,
               page_shift=HUGE_PAGE_SHIFT)
huge_image = huge.compile()
for _ in range(4000):
    offset = rng.randrange(600 * 1024 * 1024)
    result = huge_image.translate(0x100000000 + offset)
    assert result.physical_address == 0x300000000 + offset
    assert result.page_shift == HUGE_PAGE_SHIFT
    translated += 1
assert len(huge_image.mappings) == 300

# Mixed small/large tables can coexist in different parts of one 2 MiB PD0 region.
mixed = SyntheticAddressSpace(table_base=0x04000000)
mixed.map_range(0x0000000200000000, 0x0000000400000000, 1 * 1024 * 1024,
                page_shift=SMALL_PAGE_SHIFT)
mixed.map_range(0x0000000200100000, 0x0000000500000000, 1 * 1024 * 1024,
                page_shift=BIG_PAGE_SHIFT)
mixed_image = mixed.compile()
for offset in (0, 0x1234, 0xFFFFF):
    assert mixed_image.translate(0x200000000 + offset).physical_address == 0x400000000 + offset
for offset in (0, 0x1234, 0xFFFFF):
    assert mixed_image.translate(0x200100000 + offset).physical_address == 0x500000000 + offset
translated += 6

# Root-index boundary: cross 128 TiB without losing hierarchy correctness.
root_boundary = SyntheticAddressSpace(table_base=0x05000000)
root_va = (1 << 47) - 0x1000
root_boundary.map_range(root_va, 0x0000000600000000, 0x2000,
                        page_shift=SMALL_PAGE_SHIFT)
root_image = root_boundary.compile()
assert root_image.translate(root_va).physical_address == 0x600000000
assert root_image.translate(root_va + 0x1000).physical_address == 0x600001000
translated += 2

# Alias policy is explicit and fail-closed by default.
alias = SyntheticAddressSpace()
alias.map_range(0x100000, 0x80000000, 0x1000, page_shift=SMALL_PAGE_SHIFT)
must_fail(alias.map_range, 0x200000, 0x80000000, 0x1000,
          page_shift=SMALL_PAGE_SHIFT)
alias.map_range(0x200000, 0x80000000, 0x1000,
                page_shift=SMALL_PAGE_SHIFT, allow_alias=True)
alias_image = alias.compile()
assert alias_image.translate(0x100000).physical_address == 0x80000000
assert alias_image.translate(0x200000).physical_address == 0x80000000
translated += 2

# Virtual overlaps are rejected even when page sizes differ.
overlap = SyntheticAddressSpace()
overlap.map_range(0x400000, 0x90000000, 0x200000, page_shift=HUGE_PAGE_SHIFT)
must_fail(overlap.map_range, 0x400000, 0xA0000000, 0x1000,
          page_shift=SMALL_PAGE_SHIFT)
must_fail(overlap.map_range, 0x500000, 0xA1000000, 0x10000,
          page_shift=BIG_PAGE_SHIFT)

# Promotion 512x4 KiB -> 1x2 MiB and demotion round-trip.
promote = SyntheticAddressSpace(table_base=0x06000000)
promote.map_range(0x800000, 0xA0000000, 0x200000,
                  page_shift=SMALL_PAGE_SHIFT,
                  attributes=MappingAttributes(read_only=True, atomic_disable=True))
original = promote.compile()
original_digest = original.digest()
samples = [0, 1, 0xFFF, 0x1000, 0x1FFFFF]
expected = [original.translate(0x800000 + offset).physical_address for offset in samples]
promote.promote_4k_to_2m(0x800000)
promoted = promote.compile()
assert len(promoted.mappings) == 1
assert promoted.mappings[0].page_shift == HUGE_PAGE_SHIFT
for offset, pa in zip(samples, expected):
    assert promoted.translate(0x800000 + offset).physical_address == pa
promote.demote_2m_to_4k(0x800000)
demoted = promote.compile()
assert len(demoted.mappings) == 512
assert demoted.digest() == original_digest
for offset, pa in zip(samples, expected):
    assert demoted.translate(0x800000 + offset).physical_address == pa
translated += len(samples) * 3

# Promotion fails if contiguity or attributes differ.
bad_promote = SyntheticAddressSpace()
bad_promote.map_range(0xC00000, 0xC0000000, 0x200000,
                      page_shift=SMALL_PAGE_SHIFT)
page = bad_promote._pages[0xC01000]  # test-only fault injection into CPU model
bad_promote._pages[0xC01000] = type(page)(
    virtual_address=page.virtual_address,
    physical_address=page.physical_address + 0x1000,
    page_shift=page.page_shift,
    attributes=page.attributes,
)
must_fail(bad_promote.promote_4k_to_2m, 0xC00000)

# Exact unmap and gap detection.
unmap = SyntheticAddressSpace()
unmap.map_range(0x1000000, 0xD0000000, 0x4000, page_shift=SMALL_PAGE_SHIFT)
unmap.unmap_range(0x1000000, 0x4000)
assert not unmap.mappings
must_fail(unmap.unmap_range, 0x1000000, 0x1000)

# Corrupted/absent table paths fail closed.
corrupt_space = SyntheticAddressSpace()
corrupt_space.map_range(0x2000000, 0xE0000000, 0x1000, page_shift=SMALL_PAGE_SHIFT)
corrupt_image = corrupt_space.compile()
leaf_address = next(address for address, label in corrupt_image.labels.items() if label.startswith("leaf:"))
broken_tables = dict(corrupt_image.tables)
del broken_tables[leaf_address]
broken = type(corrupt_image)(
    root_address=corrupt_image.root_address,
    tables=broken_tables,
    labels=corrupt_image.labels,
    logical_sizes=corrupt_image.logical_sizes,
    mappings=corrupt_image.mappings,
)
must_fail(broken.translate, 0x2000000)

print("MMU ADDRESS-SPACE CONTRACT PASSED")
print(f"- {translated} sampled translations")
print("- multi-page 4 KiB, 64 KiB and 2 MiB mappings")
print("- leaf, PD0 and root-index boundary crossings")
print("- mixed 4 KiB/64 KiB PD0 halves")
print("- explicit alias policy and overlap rejection")
print("- 4 KiB <-> 2 MiB promotion/demotion round-trip")
print("- corruption and incomplete unmap paths fail closed")
print("- zero MMIO and zero device access")
