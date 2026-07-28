#!/usr/bin/env python3
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
registers = (ROOT / "include/TuringRegisters.hpp").read_text(encoding="utf-8")
fb = (ROOT / "kext/TuringProbe/FbMmuInventory.cpp").read_text(encoding="utf-8")
main = (ROOT / "kext/TuringProbe/TuringProbe.cpp").read_text(encoding="utf-8")
build = (ROOT / "tools/build.sh").read_text(encoding="utf-8")

assert re.search(r"kNvPfbVidmemSizeOffset\s*=\s*0x100CE0U", registers)
assert re.search(r"kPfbVidmemMagnitudeMask\s*=\s*0x000003F0U", registers)
assert re.search(r"kPfbVidmemMagnitudeShift\s*=\s*4U", registers)
assert re.search(r"kPfbVidmemScaleMask\s*=\s*0x0000000FU", registers)
assert re.search(r"kPfbVidmemReducedCapacityBit\s*=\s*0x40000000U", registers)
assert "kExpandedFbMmuMmioReadCount == 4U" in registers
assert "kTu102MmuDmaBits = 47U" in registers
assert "kTu102MmuKindCount = 16U" in registers
assert "kTu102MmuInvalidKind = 0x07U" in registers
assert "kTu102DefaultBigPageKiB = 16U" in registers

assert fb.count("OSReadLittleInt32(") == 1
assert fb.count("readFbCapacity32(bar0)") == 1
assert "for (" not in fb and "while (" not in fb and "do {" not in fb
assert "OSWrite" not in fb and "IOMappedWrite" not in fb
assert "TPMMUSourceProfile" in fb
assert "TPFBVidmemMatchesExpected6GiB" in fb
assert "TURINGPROBE_ENABLE_FB_READ" in fb
assert "TPFBInventoryCompileGateEnabled" in fb

assert 'bootArgumentPresent("-tdfb-read")' in main
assert "fbMmuRequested && !mmioRequested" in main
assert "topRequested && fbMmuRequested" in main
assert '"-tdprobe -tdmmio-read -tdfb-read"' in main
assert "mmio_fb_inventory=1x32@0x100ce0" in build
assert "fb_compile_gate=TURINGPROBE_ENABLE_FB_READ=1" in build

# Synthetic register encoding for exactly 6 GiB:
# magnitude 6, scale 10 => 6 << (10 + 20) = 6 GiB.
raw = (6 << 4) | 10
magnitude = (raw & 0x3F0) >> 4
scale = raw & 0xF
size = magnitude << (scale + 20)
assert magnitude == 6
assert scale == 10
assert size == 6 * 1024 * 1024 * 1024

# Validate the optional 15/16 reduction rule used by Nouveau.
raw_reduced = raw | 0x40000000
nominal = ((raw_reduced & 0x3F0) >> 4) << ((raw_reduced & 0xF) + 20)
reduced = nominal // 16 * 15
assert reduced == (6 * 1024 * 1024 * 1024) // 16 * 15

print("FB/MMU CONTRACT PASSED: one 0x100CE0 read, 6 GiB decoder, source-only MMU profile")
