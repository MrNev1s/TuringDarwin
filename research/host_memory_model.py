#!/usr/bin/env python3
"""Pure software model for the bounded TuringProbe host-memory self-test."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

PAGE_SIZE = 4096
GUARD_SIZE = PAGE_SIZE
PAYLOAD_SIZE = PAGE_SIZE
ALLOCATION_SIZE = GUARD_SIZE + PAYLOAD_SIZE + GUARD_SIZE
ALIGNMENT = PAGE_SIZE
PREFIX_CANARY = 0xA5
SUFFIX_CANARY = 0x5A
FNV_OFFSET_BASIS = 0xCBF29CE484222325
FNV_PRIME = 0x100000001B3
EXPECTED_CHECKSUM = 0xACAC786CC2682325


class MemoryModelError(ValueError):
    pass


class State(str, Enum):
    NEW = "new"
    ALLOCATED = "allocated"
    PATTERN_WRITTEN = "pattern-written"
    VERIFIED = "verified"
    ZEROIZED = "zeroized"
    RELEASED = "released"


def payload_byte(index: int) -> int:
    if not 0 <= index < PAYLOAD_SIZE:
        raise MemoryModelError("payload index out of range")
    return (index * 131 + 0x5D) & 0xFF


def fnv1a64(data: bytes | bytearray | memoryview) -> int:
    value = FNV_OFFSET_BASIS
    for byte in data:
        value ^= int(byte)
        value = (value * FNV_PRIME) & 0xFFFFFFFFFFFFFFFF
    return value


@dataclass(frozen=True)
class Verification:
    payload_matches: bool
    checksum: int
    checksum_matches: bool
    prefix_canary_valid: bool
    suffix_canary_valid: bool

    @property
    def valid(self) -> bool:
        return (
            self.payload_matches
            and self.checksum_matches
            and self.prefix_canary_valid
            and self.suffix_canary_valid
        )


class HostMemoryModel:
    def __init__(self) -> None:
        self.state = State.NEW
        self._backing: bytearray | None = None

    @property
    def backing(self) -> bytearray:
        if self._backing is None:
            raise MemoryModelError("allocation is not active")
        return self._backing

    @property
    def prefix(self) -> memoryview:
        return memoryview(self.backing)[:GUARD_SIZE]

    @property
    def payload(self) -> memoryview:
        return memoryview(self.backing)[GUARD_SIZE:GUARD_SIZE + PAYLOAD_SIZE]

    @property
    def suffix(self) -> memoryview:
        return memoryview(self.backing)[GUARD_SIZE + PAYLOAD_SIZE:]

    def allocate(self) -> None:
        if self.state != State.NEW:
            raise MemoryModelError("allocation may occur only once")
        self._backing = bytearray(ALLOCATION_SIZE)
        self.state = State.ALLOCATED

    def initialise_guards(self) -> None:
        if self.state != State.ALLOCATED:
            raise MemoryModelError("guards require allocated state")
        self.prefix[:] = bytes([PREFIX_CANARY]) * GUARD_SIZE
        self.suffix[:] = bytes([SUFFIX_CANARY]) * GUARD_SIZE

    def write_pattern(self) -> None:
        if self.state != State.ALLOCATED:
            raise MemoryModelError("pattern write requires allocated state")
        self.initialise_guards()
        self.payload[:] = bytes(payload_byte(i) for i in range(PAYLOAD_SIZE))
        self.state = State.PATTERN_WRITTEN

    def write_payload_slice(self, offset: int, data: bytes) -> None:
        if self.state not in {State.ALLOCATED, State.PATTERN_WRITTEN, State.VERIFIED}:
            raise MemoryModelError("payload write is not allowed in current state")
        if offset < 0 or len(data) < 0 or offset + len(data) > PAYLOAD_SIZE:
            raise MemoryModelError("payload write exceeds exact bounds")
        self.payload[offset:offset + len(data)] = data

    def verify(self) -> Verification:
        if self.state != State.PATTERN_WRITTEN:
            raise MemoryModelError("verification requires pattern-written state")
        expected = bytes(payload_byte(i) for i in range(PAYLOAD_SIZE))
        checksum = fnv1a64(self.payload)
        result = Verification(
            payload_matches=bytes(self.payload) == expected,
            checksum=checksum,
            checksum_matches=checksum == EXPECTED_CHECKSUM,
            prefix_canary_valid=all(v == PREFIX_CANARY for v in self.prefix),
            suffix_canary_valid=all(v == SUFFIX_CANARY for v in self.suffix),
        )
        if result.valid:
            self.state = State.VERIFIED
        return result

    def zeroize(self) -> None:
        if self.state not in {State.ALLOCATED, State.PATTERN_WRITTEN, State.VERIFIED}:
            raise MemoryModelError("zeroization is not allowed in current state")
        self.payload[:] = bytes(PAYLOAD_SIZE)
        if any(self.payload):
            raise MemoryModelError("payload zeroization failed")
        self.state = State.ZEROIZED

    def release(self) -> None:
        if self.state != State.ZEROIZED:
            raise MemoryModelError("release requires verified payload zeroization")
        self.backing[:] = bytes(ALLOCATION_SIZE)
        if any(self.backing):
            raise MemoryModelError("full allocation cleanup failed")
        self._backing = None
        self.state = State.RELEASED

    def run(self) -> Verification:
        self.allocate()
        self.write_pattern()
        result = self.verify()
        if not result.valid:
            raise MemoryModelError("self-test verification failed")
        self.zeroize()
        self.release()
        return result
