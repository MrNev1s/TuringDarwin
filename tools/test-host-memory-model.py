#!/usr/bin/env python3
from __future__ import annotations

import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "research"))

from host_memory_model import (  # noqa: E402
    ALIGNMENT,
    ALLOCATION_SIZE,
    EXPECTED_CHECKSUM,
    GUARD_SIZE,
    HostMemoryModel,
    MemoryModelError,
    PAGE_SIZE,
    PAYLOAD_SIZE,
    PREFIX_CANARY,
    State,
    SUFFIX_CANARY,
    fnv1a64,
    payload_byte,
)

assert PAGE_SIZE == 4096
assert ALIGNMENT == 4096
assert GUARD_SIZE == 4096
assert PAYLOAD_SIZE == 4096
assert ALLOCATION_SIZE == 12288
assert fnv1a64(bytes(payload_byte(i) for i in range(PAYLOAD_SIZE))) == EXPECTED_CHECKSUM

model = HostMemoryModel()
result = model.run()
assert result.valid
assert result.checksum == 0xACAC786CC2682325
assert model.state == State.RELEASED

# Bounded randomized CPU writes never reach either canary page.
rng = random.Random(0x1660A1)
model = HostMemoryModel()
model.allocate()
model.initialise_guards()
for iteration in range(50000):
    length = rng.randrange(0, 257)
    offset = rng.randrange(0, PAYLOAD_SIZE - length + 1)
    data = rng.randbytes(length)
    model.write_payload_slice(offset, data)
    if iteration % 250 == 0:
        assert all(v == PREFIX_CANARY for v in model.prefix)
        assert all(v == SUFFIX_CANARY for v in model.suffix)
assert all(v == PREFIX_CANARY for v in model.prefix)
assert all(v == SUFFIX_CANARY for v in model.suffix)
model.zeroize()
model.release()
assert model.state == State.RELEASED

# Every one-byte overrun/underrun is rejected before mutation.
for offset, data in [(-1, b"x"), (PAYLOAD_SIZE, b"x"), (PAYLOAD_SIZE - 1, b"xx")]:
    model = HostMemoryModel()
    model.allocate()
    model.initialise_guards()
    before = bytes(model.backing)
    try:
        model.write_payload_slice(offset, data)
    except MemoryModelError:
        pass
    else:
        raise AssertionError("out-of-bounds write was accepted")
    assert bytes(model.backing) == before
    model.zeroize()
    model.release()

# Deliberate canary corruption is detected by verification.
for corrupt_prefix in (True, False):
    model = HostMemoryModel()
    model.allocate()
    model.write_pattern()
    if corrupt_prefix:
        model.prefix[0] ^= 0xFF
    else:
        model.suffix[-1] ^= 0xFF
    result = model.verify()
    assert not result.valid
    model.zeroize()
    model.release()

# Release before zeroization is forbidden.
model = HostMemoryModel()
model.allocate()
try:
    model.release()
except MemoryModelError:
    pass
else:
    raise AssertionError("release before zeroization was accepted")
model.zeroize()
model.release()

print("HOST MEMORY MODEL CONTRACT PASSED")
print("- exact 3-page / 12288-byte layout")
print("- 4096-byte payload and 4096-byte canaries")
print("- 50000 randomized bounded writes")
print("- one-byte underflow/overflow rejection")
print("- deterministic FNV-1a readback checksum")
print("- verified payload and full-allocation zeroization")
print("- zero device access")
