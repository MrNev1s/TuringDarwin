#!/usr/bin/env python3
"""Compare two 256-byte PCI configuration dumps.

Accepted inputs:
- exactly 256 raw bytes;
- an ioreg-style OSData value such as <de108221...>;
- whitespace-separated hexadecimal bytes.

This tool performs no device access.
"""
from pathlib import Path
import argparse
import re


def load(path: Path) -> bytes:
    raw = path.read_bytes()
    if len(raw) == 256:
        return raw

    text = raw.decode("utf-8", errors="ignore")
    for candidate in re.findall(r"<([0-9a-fA-F\s]{512,})>", text):
        compact = re.sub(r"\s+", "", candidate)
        if len(compact) >= 512 and len(compact) % 2 == 0:
            data = bytes.fromhex(compact)
            if len(data) >= 256:
                return data[:256]

    compact = re.sub(r"[^0-9a-fA-F]", "", text)
    if len(compact) >= 512 and len(compact) % 2 == 0:
        data = bytes.fromhex(compact)
        if len(data) >= 256:
            return data[:256]

    pairs = re.findall(r"(?i)(?<![0-9a-f])[0-9a-f]{2}(?![0-9a-f])", text)
    data = bytes(int(x, 16) for x in pairs)
    if len(data) < 256:
        raise ValueError(f"{path}: expected at least 256 bytes, got {len(data)}")
    return data[:256]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("before", type=Path)
    parser.add_argument("after", type=Path)
    args = parser.parse_args()

    before = load(args.before)
    after = load(args.after)
    differences = 0
    for offset, (old, new) in enumerate(zip(before, after)):
        if old != new:
            differences += 1
            print(f"0x{offset:02x}: 0x{old:02x} -> 0x{new:02x}")
    print(f"differences={differences}")


if __name__ == "__main__":
    main()
