#!/usr/bin/env python3
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
cpp = (ROOT / "kext/TuringProbe/HostMemorySelfTest.cpp").read_text()
hpp = (ROOT / "kext/TuringProbe/HostMemorySelfTest.hpp").read_text()
main = (ROOT / "kext/TuringProbe/TuringProbe.cpp").read_text()
pbx = (ROOT / "TuringProbe.xcodeproj/project.pbxproj").read_text()
build = (ROOT / "tools/build.sh").read_text()

assert cpp.count("IOMallocAligned(") == 1
assert cpp.count("IOFreeAligned(") == 1
assert "kHostMemoryAllocationSize" in cpp
assert "kHostMemoryGuardSize = kHostMemoryPageSize" in cpp
assert "kHostMemoryPayloadSize = kHostMemoryPageSize" in cpp
assert "kHostMemoryAlignment = kHostMemoryPageSize" in cpp
assert "kExpectedPayloadChecksum = 0xACAC786CC2682325ULL" in cpp
assert "TPHostMemoryPrefixCanaryValidAfterWrite" in cpp
assert "TPHostMemorySuffixCanaryValidAfterWrite" in cpp
assert "TPHostMemoryPayloadZeroized" in cpp
assert "TPHostMemoryEntireAllocationZeroBeforeFree" in cpp
assert "TPHostMemoryAllocationFreed" in cpp
assert "TURINGPROBE_ENABLE_HOST_MEMORY_TEST" in cpp
assert "IOPCIDevice" not in cpp + hpp
for forbidden in (
    "IOBufferMemoryDescriptor", "IOMemoryDescriptor", "IODMACommand",
    "IOMallocContiguous", "getPhysicalSegment", "getPhysicalAddress",
    "prepare(", "complete(", "IOMappedWrite", "OSWriteLittleInt",
    "configWrite", "setBusMasterEnable",
):
    assert forbidden not in cpp + hpp, forbidden

assert 'bootArgumentPresent("-tdhostmem-test")' in main
assert "hostMemoryRequested && mmioRequested" in main
assert '"-tdprobe -tdhostmem-test"' in main
assert "performHostMemorySelfTest(this)" in main
assert "TuringProbeDeviceMemoryWrites" in main
assert pbx.count("TURINGPROBE_ENABLE_HOST_MEMORY_TEST=1") == 2
assert "HostMemorySelfTest.cpp" in pbx
assert "HostMemorySelfTest.hpp" in pbx
assert pbx.count("MODULE_VERSION = 0.7.0") == 2
assert "host_memory_compile_gate=TURINGPROBE_ENABLE_HOST_MEMORY_TEST=1" in build
assert "host_memory_test=3x4096" in build
assert "device_memory_write_whitelist=EMPTY" in build

# Host mode must remain isolated from every MMIO expansion argument.
mode_block = re.search(
    r"const bool hostMemoryRequested.*?if \(hostMemoryRequested && mmioRequested\).*?return false;",
    main,
    re.S,
)
assert mode_block is not None

print("HOST MEMORY KEXT CONTRACT PASSED")
print("- one aligned wired host allocation and one matching free")
print("- 4096-byte prefix/payload/suffix layout")
print("- deterministic CPU write/readback, canaries and zeroization")
print("- no physical-address query, descriptor, DMA or device-memory path")
print("- isolated -tdhostmem-test boot mode")
