#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "research"))

from tu102_mmu_model import (  # noqa: E402
    PdeAperture,
    PteAperture,
    compose_virtual_address,
    decode_pde,
    decode_pte,
    encode_instance_pdb,
    encode_pde,
    encode_pte,
    split_virtual_address,
)

vectors = json.loads((ROOT / "research/mmu-golden-vectors.json").read_text())

for vector in vectors["virtual_address_vectors"]:
    va = int(vector["virtual_address"], 0)
    shift = int(vector["page_shift"])
    actual = split_virtual_address(va, shift)
    assert actual == vector["expected"], (actual, vector)
    assert compose_virtual_address(actual, shift) == va

for vector in vectors["pte_vectors"]:
    entry = encode_pte(
        int(vector["physical_address"], 0),
        page_shift=int(vector["page_shift"]),
        aperture=PteAperture(int(vector["aperture"])),
        kind=int(vector["kind"]),
        valid=bool(vector["valid"]),
        volatile=bool(vector["volatile"]),
        privileged=bool(vector["privileged"]),
        read_only=bool(vector["read_only"]),
        atomic_disable=bool(vector["atomic_disable"]),
    )
    expected = int(vector["expected_entry"], 0)
    assert entry == expected, (hex(entry), vector)
    decoded = decode_pte(entry)
    assert decoded["physical_address"] == int(vector["physical_address"], 0)

for vector in vectors["pde_vectors"]:
    entry = encode_pde(
        int(vector["table_address"], 0),
        PdeAperture(int(vector["aperture"])),
    )
    expected = int(vector["expected_entry"], 0)
    assert entry == expected, (hex(entry), vector)
    decoded = decode_pde(entry)
    assert decoded["table_address"] == int(vector["table_address"], 0)

for vector in vectors["instance_vectors"]:
    entry = encode_instance_pdb(
        int(vector["root_address"], 0),
        aperture=PteAperture(int(vector["aperture"])),
        replay_tex=bool(vector["replay_tex"]),
        replay_gcc=bool(vector["replay_gcc"]),
    )
    assert entry == int(vector["expected_word"], 0), (hex(entry), vector)

print("MMU GOLDEN VECTOR CONTRACT PASSED")
print(f"- {len(vectors['virtual_address_vectors'])} fixed VA vectors")
print(f"- {len(vectors['pte_vectors'])} fixed PTE vectors")
print(f"- {len(vectors['pde_vectors'])} fixed PDE vectors")
print(f"- {len(vectors['instance_vectors'])} fixed instance/PDB vectors")
print("- zero MMIO and zero device access")
