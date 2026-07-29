#!/usr/bin/env python3
from __future__ import annotations

import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "research"))

from tu102_mmu_model import (  # noqa: E402
    BIG_GEOMETRY,
    BIG_PAGE_SHIFT,
    DMA_ADDRESS_BITS,
    HUGE_GEOMETRY,
    HUGE_PAGE_SHIFT,
    INVALID_KIND,
    KIND_MAP,
    ModelError,
    PdeAperture,
    PteAperture,
    SMALL_GEOMETRY,
    SMALL_PAGE_SHIFT,
    VIRTUAL_ADDRESS_BITS,
    compose_virtual_address,
    decode_pde,
    decode_pte,
    encode_instance_pdb,
    encode_pd0_pair,
    encode_pde,
    encode_pte,
    hierarchy_summary,
    split_virtual_address,
)

assert SMALL_GEOMETRY.page_size == 4096
assert BIG_GEOMETRY.page_size == 65536
assert HUGE_GEOMETRY.page_size == 2097152
for geo in (SMALL_GEOMETRY, BIG_GEOMETRY, HUGE_GEOMETRY):
    assert geo.virtual_address_bits == 49
assert SMALL_GEOMETRY.leaf_entries == 512
assert BIG_GEOMETRY.leaf_entries == 32
assert HUGE_GEOMETRY.leaf_entries == 256
assert SMALL_GEOMETRY.leaf_table_bytes == 4096
assert BIG_GEOMETRY.leaf_table_bytes == 256
assert SMALL_GEOMETRY.leaf_coverage == 2 * 1024 * 1024
assert BIG_GEOMETRY.leaf_coverage == 2 * 1024 * 1024

# Fixed VA vector proving every field boundary.
va = 0x1A5_1234_5678
for shift in (SMALL_PAGE_SHIFT, BIG_PAGE_SHIFT, HUGE_PAGE_SHIFT):
    parts = split_virtual_address(va, shift)
    assert compose_virtual_address(parts, shift) == va

rng = random.Random(0x5444313136)
va_vectors = 0
for shift in (SMALL_PAGE_SHIFT, BIG_PAGE_SHIFT, HUGE_PAGE_SHIFT):
    for _ in range(20000):
        va = rng.randrange(1 << VIRTUAL_ADDRESS_BITS)
        assert compose_virtual_address(split_virtual_address(va, shift), shift) == va
        va_vectors += 1

# Uncompressed PTE round-trips across apertures and attributes.
pte_vectors = 0
valid_kinds = [i for i, mapped in enumerate(KIND_MAP) if mapped != INVALID_KIND]
for shift in (SMALL_PAGE_SHIFT, BIG_PAGE_SHIFT, HUGE_PAGE_SHIFT):
    for aperture in PteAperture:
        for _ in range(5000):
            pa = rng.randrange(0, 1 << DMA_ADDRESS_BITS)
            pa &= ~((1 << shift) - 1)
            logical_kind = rng.choice(valid_kinds)
            attrs = dict(
                valid=bool(rng.getrandbits(1)),
                volatile=bool(rng.getrandbits(1)),
                privileged=bool(rng.getrandbits(1)),
                read_only=bool(rng.getrandbits(1)),
                atomic_disable=bool(rng.getrandbits(1)),
            )
            entry = encode_pte(pa, page_shift=shift, aperture=aperture,
                               kind=logical_kind, **attrs)
            decoded = decode_pte(entry)
            assert decoded["physical_address"] == pa
            assert decoded["aperture"] == int(aperture)
            assert decoded["hardware_kind"] == KIND_MAP[logical_kind]
            for key, value in attrs.items():
                assert decoded[key] == value
            pte_vectors += 1

# PDE targets and the 128-bit PD0 small/big pair.
pde_vectors = 0
for aperture in (PdeAperture.VIDEO_MEMORY,
                 PdeAperture.SYSTEM_COHERENT,
                 PdeAperture.SYSTEM_NONCOHERENT):
    for _ in range(5000):
        addr = rng.randrange(0, 1 << DMA_ADDRESS_BITS) & ~0xFFF
        entry = encode_pde(addr, aperture)
        decoded = decode_pde(entry)
        assert decoded["table_address"] == addr
        assert decoded["aperture"] == int(aperture)
        pde_vectors += 1

small = encode_pde(0x200000, PdeAperture.VIDEO_MEMORY)
big = encode_pde(0x300000, PdeAperture.VIDEO_MEMORY)
pair = encode_pd0_pair(big, small)
assert len(pair) == 16
assert int.from_bytes(pair[:8], "little") == big
assert int.from_bytes(pair[8:], "little") == small

# Instance/PDB word uses VER2 and 64 KiB mode bits, with no hardware access.
pdb = encode_instance_pdb(0x400000, aperture=PteAperture.VIDEO_MEMORY)
assert pdb & (1 << 10)
assert pdb & (1 << 11)
assert pdb & ~0xFFF == 0x400000

# Fail-closed validation vectors.
def must_fail(fn, *args, **kwargs):
    try:
        fn(*args, **kwargs)
    except ModelError:
        return
    raise AssertionError(f"expected ModelError from {fn.__name__}")

must_fail(split_virtual_address, 1 << VIRTUAL_ADDRESS_BITS, SMALL_PAGE_SHIFT)
must_fail(encode_pte, 0x123, page_shift=SMALL_PAGE_SHIFT)
must_fail(encode_pte, 0, page_shift=SMALL_PAGE_SHIFT, kind=7)
must_fail(encode_pte, 1 << DMA_ADDRESS_BITS, page_shift=SMALL_PAGE_SHIFT)
must_fail(encode_pde, 0x123, PdeAperture.VIDEO_MEMORY)
must_fail(encode_instance_pdb, 0x123)

small_summary = hierarchy_summary(SMALL_PAGE_SHIFT)
big_summary = hierarchy_summary(BIG_PAGE_SHIFT)
huge_summary = hierarchy_summary(HUGE_PAGE_SHIFT)
assert small_summary["pd0_table_bytes"] == 4096
assert big_summary["pd0_table_bytes"] == 4096
assert huge_summary["pd0_table_bytes"] == 4096
assert huge_summary["terminates_at_pd0"] is True
assert small_summary["root_entries"] == 4

# Logical compressed kinds fall back to source-defined uncompressed kinds when
# no GSP/PMU compression path is authorised.
fallback = encode_pte(0x200000, page_shift=HUGE_PAGE_SHIFT, kind=8)
assert decode_pte(fallback)["hardware_kind"] == 0x06
for invalid_kind in (7, 15):
    must_fail(encode_pte, 0x200000, page_shift=HUGE_PAGE_SHIFT,
              kind=invalid_kind)
must_fail(encode_pte, 0x200000, page_shift=HUGE_PAGE_SHIFT,
          kind=0, comptagline=1)

print("MMU MODEL CONTRACT PASSED")
print("- 4 KiB, 64 KiB and 2 MiB hierarchies: 49-bit VA")
print(f"- {va_vectors} VA round-trip vectors")
print(f"- {pte_vectors + pde_vectors} PTE/PDE randomized vectors")
print("- logical-kind fallback and compression rejection")
print("- fail-closed alignment/range/kind checks")
print("- zero MMIO and zero device access")
