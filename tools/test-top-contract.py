#!/usr/bin/env python3
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
registers = (ROOT / "include/TuringRegisters.hpp").read_text(encoding="utf-8")
top = (ROOT / "kext/TuringProbe/TopInventory.cpp").read_text(encoding="utf-8")

assert re.search(r"kTopTableBaseOffset\s*=\s*0x022700U", registers)
assert re.search(r"kTopTableWordCount\s*=\s*64U", registers)
assert "kExpandedTopMmioReadCount == 67U" in registers
assert top.count("OSReadLittleInt32(") == 1
assert top.count("readTopWord32(bar0, index)") == 1
assert len(re.findall(r"for\s*\(", top)) == 1
assert "index < kTopTableWordCount" in top
assert "while" not in top
assert "IOMappedWrite" not in top
assert "OSWrite" not in top
assert "configWrite" not in top

# Synthetic three-word record using the same bit layout as gk104_top_parse.
CONT = 0x80000000
DATA = 0x1
ENUM = 0x2
TYPE = 0x3

# CE instance 2 at address 0x104000, fault 7, engine 3, runlist 4,
# interrupt 9, reset 5, raw type 0x13.
data_word = CONT | (2 << 26) | 0x00104000 | (7 << 3) | 0x4 | DATA
enum_word = CONT | (3 << 26) | 0x20 | (4 << 21) | 0x10 | (9 << 15) | 0x8 | (5 << 9) | 0x4 | ENUM
type_word = (0x13 << 2) | TYPE

inst = (data_word & 0x3C000000) >> 26
addr = data_word & 0x00FFF000
fault = (data_word & 0x000003F8) >> 3
engine = (enum_word & 0x3C000000) >> 26
runlist = (enum_word & 0x01E00000) >> 21
intr = (enum_word & 0x000F8000) >> 15
reset = (enum_word & 0x00003E00) >> 9
etype = (type_word & 0x7FFFFFFC) >> 2

assert (inst, addr, fault) == (2, 0x104000, 7)
assert (engine, runlist, intr, reset) == (3, 4, 9, 5)
assert etype == 0x13

print("TOP CONTRACT PASSED: fixed 64-dword table, bounded parser, Nouveau bitfields verified")
