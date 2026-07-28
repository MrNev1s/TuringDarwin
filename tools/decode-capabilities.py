#!/usr/bin/env python3
"""Offline parser for a raw 256-byte PCI configuration snapshot."""
from pathlib import Path
import argparse

def main():
    p = argparse.ArgumentParser()
    p.add_argument("dump", type=Path)
    args = p.parse_args()
    data = args.dump.read_bytes()
    if len(data) != 256:
        raise SystemExit("input must be exactly 256 raw bytes")
    status = int.from_bytes(data[6:8], "little")
    print(f"status=0x{status:04x}")
    if not status & 0x10:
        print("no conventional capability list")
        return
    seen = set()
    off = data[0x34] & 0xfc
    while 0x40 <= off <= 0xfc and off not in seen:
        seen.add(off)
        cap_id = data[off]
        nxt = data[off+1] & 0xfc
        print(f"offset=0x{off:02x} id=0x{cap_id:02x} next=0x{nxt:02x}")
        if not nxt:
            break
        off = nxt

if __name__ == "__main__":
    main()
