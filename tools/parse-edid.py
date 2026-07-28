#!/usr/bin/env python3
from pathlib import Path
import argparse

def manufacturer(raw):
    value = (raw[8] << 8) | raw[9]
    return "".join(chr(((value >> shift) & 0x1F) + 64) for shift in (10, 5, 0))

def main():
    p = argparse.ArgumentParser()
    p.add_argument("edid", type=Path)
    args = p.parse_args()
    data = args.edid.read_bytes()
    if len(data) < 128 or data[:8] != b"\x00\xff\xff\xff\xff\xff\xff\x00":
        raise SystemExit("not a valid EDID base block")
    print(f"manufacturer={manufacturer(data)}")
    print(f"product=0x{int.from_bytes(data[10:12], 'little'):04x}")
    print(f"serial_numeric={int.from_bytes(data[12:16], 'little')}")
    print(f"week={data[16]}")
    print(f"year={1990 + data[17]}")
    print(f"version={data[18]}.{data[19]}")
    print(f"extensions={data[126]}")
    blocks = len(data) // 128
    for i in range(blocks):
        block = data[i*128:(i+1)*128]
        print(f"block_{i}_checksum={sum(block) & 0xff}")

if __name__ == "__main__":
    main()
