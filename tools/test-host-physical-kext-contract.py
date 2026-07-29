#!/usr/bin/env python3
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
cpp = (ROOT / "kext/TuringProbe/HostPhysicalSegmentTest.cpp").read_text()
hpp = (ROOT / "kext/TuringProbe/HostPhysicalSegmentTest.hpp").read_text()
main = (ROOT / "kext/TuringProbe/TuringProbe.cpp").read_text()
pbx = (ROOT / "TuringProbe.xcodeproj/project.pbxproj").read_text()
build = (ROOT / "tools/build.sh").read_text()

assert cpp.count("IOBufferMemoryDescriptor::withOptions(") == 1
assert cpp.count("getBytesNoCopy(") == 1
assert cpp.count("getPhysicalSegment(") == 1
assert cpp.count("descriptor->release();") == 1
assert "descriptor = nullptr;" in cpp
assert "IOBufferMemoryDescriptor *descriptor" in cpp
assert "auto descriptor" not in cpp
assert "OSPtr<IOBufferMemoryDescriptor>" not in cpp
assert "kIODirectionNone | kIOMemoryMapperNone" in cpp
assert "kDescriptorCapacity = 4096U" in cpp
assert "kDescriptorAlignment = 4096U" in cpp
assert "kPrefixGuardSize = 64U" in cpp
assert "kSuffixGuardSize = 64U" in cpp
assert "kExpectedPayloadChecksum = 0xBB8BA5B0A94B2525ULL" in cpp
assert "kHostPhysicalAddressBits = 47U" in cpp
assert "physicalSegmentLength == kDescriptorCapacity" in cpp
assert "TPHostPhysicalAddressWithin47Bits" in cpp
assert "TPHostPhysicalEntireDescriptorZeroBeforeRelease" in cpp
assert "TPHostPhysicalDescriptorReleased" in cpp
assert "TURINGPROBE_ENABLE_HOST_PHYSICAL_TEST" in cpp
assert "IOPCIDevice" not in cpp + hpp

for forbidden in (
    "IODMACommand", "IOMemoryMap *", "#include <IOKit/IOMemoryMap.h>", "IOMapper::", "prepare(", "complete(",
    "createMappingInTask", "map(", "IOMappedWrite", "OSWriteLittleInt",
    "configWrite", "setBusMasterEnable", "kIOMemoryPhysicallyContiguous",
    "inTaskWithPhysicalMask", "dmaCommandOperation",
):
    assert forbidden not in cpp + hpp, forbidden

assert 'bootArgumentPresent("-tdhostphys-test")' in main
assert "hostPhysicalRequested && mmioRequested" in main
assert "hostMemoryRequested && hostPhysicalRequested" in main
assert '"-tdprobe -tdhostphys-test"' in main
assert "performHostPhysicalSegmentTest(this)" in main
assert "TuringProbeHostPhysicalSegmentAccess" in main
assert "TuringProbeDeviceMemoryWrites" in main
assert pbx.count("TURINGPROBE_ENABLE_HOST_PHYSICAL_TEST=1") == 2
assert "HostPhysicalSegmentTest.cpp" in pbx
assert "HostPhysicalSegmentTest.hpp" in pbx
assert pbx.count("MODULE_VERSION = 0.7.0") == 2
assert "host_physical_compile_gate=TURINGPROBE_ENABLE_HOST_PHYSICAL_TEST=1" in build
assert "host_physical_mode=-tdprobe+-tdhostphys-test" in build
assert "device_memory_write_whitelist=EMPTY" in build
assert "host_physical_raw_segment_queries=1" in build

mode_block = re.search(
    r"const bool hostPhysicalRequested.*?if \(hostPhysicalRequested && mmioRequested\).*?return false;",
    main,
    re.S,
)
assert mode_block is not None

print("HOST PHYSICAL SEGMENT KEXT CONTRACT PASSED")
print("- one descriptor, one raw segment query and one explicit release")
print("- one 4096-byte wired kernel page with mapper disabled")
print("- bounded CPU write/readback, canaries and zeroization")
print("- exact 4096-byte segment, page alignment and 47-bit checks")
print("- no prepare/complete, DMA, mapper, GPU or device-memory path")
print("- isolated -tdhostphys-test boot mode")
