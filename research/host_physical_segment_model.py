#!/usr/bin/env python3
"""Pure software model for the one-page host physical-segment gate."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

PAGE_SIZE = 4096
ALIGNMENT = PAGE_SIZE
PREFIX_GUARD_SIZE = 64
SUFFIX_GUARD_SIZE = 64
PAYLOAD_SIZE = PAGE_SIZE - PREFIX_GUARD_SIZE - SUFFIX_GUARD_SIZE
PREFIX_CANARY = 0xC3
SUFFIX_CANARY = 0x3C
FNV_OFFSET_BASIS = 0xCBF29CE484222325
FNV_PRIME = 0x100000001B3
EXPECTED_CHECKSUM = 0xBB8BA5B0A94B2525
PHYSICAL_ADDRESS_BITS = 47
PHYSICAL_ADDRESS_LIMIT = 1 << PHYSICAL_ADDRESS_BITS


class PhysicalModelError(ValueError):
    pass


class State(str, Enum):
    NEW = "new"
    DESCRIPTOR_CREATED = "descriptor-created"
    WRITTEN = "written"
    VERIFIED = "verified"
    SEGMENT_VALIDATED = "segment-validated"
    ZEROIZED = "zeroized"
    RELEASED = "released"


def payload_byte(index: int) -> int:
    if not 0 <= index < PAYLOAD_SIZE:
        raise PhysicalModelError("payload index out of range")
    return (index * 131 + 0x5D) & 0xFF


def fnv1a64(data: bytes | bytearray | memoryview) -> int:
    value = FNV_OFFSET_BASIS
    for byte in data:
        value ^= int(byte)
        value = (value * FNV_PRIME) & 0xFFFFFFFFFFFFFFFF
    return value


@dataclass(frozen=True)
class SegmentValidation:
    address_nonzero: bool
    address_page_aligned: bool
    length_exact: bool
    within_47_bits: bool

    @property
    def valid(self) -> bool:
        return (
            self.address_nonzero
            and self.address_page_aligned
            and self.length_exact
            and self.within_47_bits
        )


def validate_segment(address: int, length: int) -> SegmentValidation:
    nonzero = address != 0
    aligned = nonzero and (address & (ALIGNMENT - 1)) == 0
    length_exact = length == PAGE_SIZE
    within = (
        nonzero
        and length > 0
        and address < PHYSICAL_ADDRESS_LIMIT
        and length <= PHYSICAL_ADDRESS_LIMIT
        and address <= PHYSICAL_ADDRESS_LIMIT - length
    )
    return SegmentValidation(nonzero, aligned, length_exact, within)


class HostPhysicalSegmentModel:
    def __init__(self) -> None:
        self.state = State.NEW
        self._page: bytearray | None = None

    @property
    def page(self) -> bytearray:
        if self._page is None:
            raise PhysicalModelError("descriptor is not active")
        return self._page

    @property
    def prefix(self) -> memoryview:
        return memoryview(self.page)[:PREFIX_GUARD_SIZE]

    @property
    def payload(self) -> memoryview:
        return memoryview(self.page)[PREFIX_GUARD_SIZE:PREFIX_GUARD_SIZE + PAYLOAD_SIZE]

    @property
    def suffix(self) -> memoryview:
        return memoryview(self.page)[PREFIX_GUARD_SIZE + PAYLOAD_SIZE:]

    def create_descriptor(self) -> None:
        if self.state != State.NEW:
            raise PhysicalModelError("descriptor may be created only once")
        self._page = bytearray(PAGE_SIZE)
        self.state = State.DESCRIPTOR_CREATED

    def write(self) -> None:
        if self.state != State.DESCRIPTOR_CREATED:
            raise PhysicalModelError("write requires descriptor-created state")
        self.prefix[:] = bytes([PREFIX_CANARY]) * PREFIX_GUARD_SIZE
        self.suffix[:] = bytes([SUFFIX_CANARY]) * SUFFIX_GUARD_SIZE
        self.payload[:] = bytes(payload_byte(i) for i in range(PAYLOAD_SIZE))
        self.state = State.WRITTEN

    def verify(self) -> int:
        if self.state != State.WRITTEN:
            raise PhysicalModelError("verify requires written state")
        expected = bytes(payload_byte(i) for i in range(PAYLOAD_SIZE))
        checksum = fnv1a64(self.payload)
        if bytes(self.payload) != expected:
            raise PhysicalModelError("payload mismatch")
        if checksum != EXPECTED_CHECKSUM:
            raise PhysicalModelError("checksum mismatch")
        if any(value != PREFIX_CANARY for value in self.prefix):
            raise PhysicalModelError("prefix guard mismatch")
        if any(value != SUFFIX_CANARY for value in self.suffix):
            raise PhysicalModelError("suffix guard mismatch")
        self.state = State.VERIFIED
        return checksum

    def validate_physical_segment(self, address: int, length: int) -> SegmentValidation:
        if self.state != State.VERIFIED:
            raise PhysicalModelError("segment validation requires verified state")
        result = validate_segment(address, length)
        if not result.valid:
            raise PhysicalModelError("physical segment rejected")
        self.state = State.SEGMENT_VALIDATED
        return result

    def zeroize(self) -> None:
        if self.state not in {State.DESCRIPTOR_CREATED, State.WRITTEN, State.VERIFIED, State.SEGMENT_VALIDATED}:
            raise PhysicalModelError("zeroization is not allowed")
        self.page[:] = bytes(PAGE_SIZE)
        if any(self.page):
            raise PhysicalModelError("descriptor zeroization failed")
        self.state = State.ZEROIZED

    def release(self) -> None:
        if self.state != State.ZEROIZED:
            raise PhysicalModelError("release requires zeroized state")
        self._page = None
        self.state = State.RELEASED
