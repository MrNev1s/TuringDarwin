#!/usr/bin/env python3
"""Static contract tests for the read-only ReBAR decoder.

This does not replace an Xcode build or hardware test. It prevents accidental
changes to the masks/shifts used for the already-observed TU116 values.
"""

from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "kext" / "TuringProbe" / "CapabilityParser.cpp"
text = SOURCE.read_text(encoding="utf-8")


def constant(name: str) -> int:
    match = re.search(
        rf"constexpr\s+UInt32\s+{re.escape(name)}\s*=\s*(0x[0-9A-Fa-f]+|[0-9]+)U?;",
        text,
    )
    if not match:
        raise AssertionError(f"missing UInt32 constant: {name}")
    return int(match.group(1), 0)


count_mask = constant("kResizableBarCountMask")
count_shift = constant("kResizableBarCountShift")
index_mask = constant("kResizableBarIndexMask")
size_mask = constant("kResizableBarCurrentSizeMask")
size_shift = constant("kResizableBarCurrentSizeShift")
supported_mask_bits = constant("kResizableBarSupportedSizesMask")

# Real TU116 values captured by TuringProbe 0.1.0 at extended capability 0xBB0.
capability0 = 0x00000100
control0 = 0x00000460

entry_count = (control0 & count_mask) >> count_shift
bar_index = control0 & index_mask
size_encoding = (control0 & size_mask) >> size_shift
supported = (capability0 & supported_mask_bits) >> 4
size_bytes = 1 << (size_encoding + 20)

assert entry_count == 3, entry_count
assert bar_index == 0, bar_index
assert size_encoding == 4, size_encoding
assert size_bytes == 16 * 1024 * 1024, size_bytes
assert supported & (1 << size_encoding), hex(supported)

print("decoder contract passed: TU116 ReBAR entry0 = BAR0, 16 MiB, 3 entries")
