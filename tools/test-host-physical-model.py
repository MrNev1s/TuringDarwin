#!/usr/bin/env python3
from __future__ import annotations

import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "research"))

from host_physical_segment_model import (  # noqa: E402
    ALIGNMENT,
    EXPECTED_CHECKSUM,
    HostPhysicalSegmentModel,
    PAGE_SIZE,
    PAYLOAD_SIZE,
    PHYSICAL_ADDRESS_LIMIT,
    PhysicalModelError,
    State,
    fnv1a64,
    payload_byte,
    validate_segment,
)

assert PAGE_SIZE == 4096
assert ALIGNMENT == 4096
assert PAYLOAD_SIZE == 3968
assert fnv1a64(bytes(payload_byte(i) for i in range(PAYLOAD_SIZE))) == EXPECTED_CHECKSUM
assert EXPECTED_CHECKSUM == 0xBB8BA5B0A94B2525

model = HostPhysicalSegmentModel()
model.create_descriptor()
assert not any(model.page)
model.write()
assert model.verify() == EXPECTED_CHECKSUM
assert model.validate_physical_segment(0x12345000, PAGE_SIZE).valid
model.zeroize()
model.release()
assert model.state == State.RELEASED

# 50,000 valid page-aligned one-page host physical segments below 47 bits.
rng = random.Random(0x1660_0700)
for _ in range(50000):
    page_number = rng.randrange(1, PHYSICAL_ADDRESS_LIMIT // PAGE_SIZE)
    address = page_number * PAGE_SIZE
    result = validate_segment(address, PAGE_SIZE)
    assert result.valid

# Reject zero, misalignment, wrong length, overflow and 47-bit boundary cases.
invalid = [
    (0, PAGE_SIZE),
    (1, PAGE_SIZE),
    (0x12345001, PAGE_SIZE),
    (0x12345000, 0),
    (0x12345000, PAGE_SIZE - 1),
    (0x12345000, PAGE_SIZE + 1),
    (PHYSICAL_ADDRESS_LIMIT, PAGE_SIZE),
    (PHYSICAL_ADDRESS_LIMIT - PAGE_SIZE + 1, PAGE_SIZE),
]
for address, length in invalid:
    assert not validate_segment(address, length).valid

# State machine refuses physical validation before CPU data verification.
model = HostPhysicalSegmentModel()
model.create_descriptor()
try:
    model.validate_physical_segment(0x12345000, PAGE_SIZE)
except PhysicalModelError:
    pass
else:
    raise AssertionError("unverified descriptor segment was accepted")
model.zeroize()
model.release()

# Release before zeroization is rejected.
model = HostPhysicalSegmentModel()
model.create_descriptor()
try:
    model.release()
except PhysicalModelError:
    pass
else:
    raise AssertionError("descriptor release before zeroization was accepted")
model.zeroize()
model.release()

print("HOST PHYSICAL SEGMENT MODEL CONTRACT PASSED")
print("- exact one-page / 4096-byte descriptor")
print("- 64-byte guards and 3968-byte CPU payload")
print("- deterministic checksum 0xBB8BA5B0A94B2525")
print("- 50000 valid randomized raw physical segments")
print("- zero/misaligned/wrong-length/47-bit overflow rejection")
print("- zeroization required before release")
print("- zero device access")
