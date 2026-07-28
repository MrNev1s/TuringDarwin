#!/usr/bin/env python3
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
registers = (ROOT / "include/TuringRegisters.hpp").read_text(encoding="utf-8")
mmio = (ROOT / "kext/TuringProbe/MMIOReadOnly.cpp").read_text(encoding="utf-8")
main = (ROOT / "kext/TuringProbe/TuringProbe.cpp").read_text(encoding="utf-8")
pbx = (ROOT / "TuringProbe.xcodeproj/project.pbxproj").read_text(encoding="utf-8")

expected = {
    "kNvPmcBoot0Offset": 0x000000,
    "kNvPmcBoot1Offset": 0x000004,
    "kNvPextdevBoot0StrapOffset": 0x101000,
}
for name, value in expected.items():
    match = re.search(rf"{name}\s*=\s*(0x[0-9A-Fa-f]+)U", registers)
    assert match and int(match.group(1), 16) == value, name

assert "descriptor->map(kIOMapReadOnly)" in mmio
assert "IOMemoryMap *mapping = descriptor->map(kIOMapReadOnly);" in mmio
assert mmio.count("mapping->release();") == 1
assert "mapping = nullptr;" in mmio
assert 'TPBAR0MappingReleased", mappingReleased' in mmio
assert "auto mapping =" not in mmio
assert "OSPtr<IOMemoryMap>" not in mmio
assert mmio.count("readWhitelisted32(bar0,") == 3
assert "performReadOnlyTopInventory(bar0, owner)" in mmio
assert "configWrite" not in mmio
assert "IOMappedWrite" not in mmio
assert "OSWrite" not in mmio
assert "-tdprobe" in main and "-tdmmio-read" in main and "-tdtop-read" in main
assert "topRequested && !mmioRequested" in main
assert "-tdunsafe" in main
assert pbx.count("TURINGPROBE_ENABLE_MMIO_READ=1") == 2
assert pbx.count("MODULE_VERSION = 0.3.0") == 2

boot0 = 0x168000A1
chipset = (boot0 & 0x1FF00000) >> 20
revision = boot0 & 0xFF
assert chipset == 0x168
assert revision == 0xA1

crystals = {
    0x00000000: 13500,
    0x00000040: 14318,
    0x00400000: 27000,
    0x00400040: 25000,
}
assert crystals[0x00400000] == 27000

print("MMIO CONTRACT PASSED: read-only map, explicit release, identity gate, optional bounded TOP inventory")
