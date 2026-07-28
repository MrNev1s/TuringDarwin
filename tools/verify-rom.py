#!/usr/bin/env python3
"""Validate the supplied NVIDIA NVGI container and embedded PCI option ROMs.

This tool is offline-only. It never accesses PCI devices or live expansion ROM.
"""
from pathlib import Path
import argparse
import hashlib
import struct
import sys

DEFAULT_EXPECTED_SHA256 = "4ea82dadeda06b347c0eca76d4bf41f0dc56e7a402452b00cb8c72b38b2e40b4"


def u16(data: bytes, offset: int) -> int:
    if offset < 0 or offset + 2 > len(data):
        raise ValueError(f"u16 out of bounds at 0x{offset:x}")
    return struct.unpack_from("<H", data, offset)[0]


def parse_chain(data: bytes, base: int):
    images = []
    offset = base
    for _ in range(16):
        if offset < 0 or offset + 0x1A > len(data):
            raise ValueError(f"truncated image header at 0x{offset:x}")
        if data[offset:offset + 2] != b"\x55\xaa":
            raise ValueError(f"missing 55AA at 0x{offset:x}")

        pcir_rel = u16(data, offset + 0x18)
        pcir = offset + pcir_rel
        if pcir < offset or pcir + 0x16 > len(data):
            raise ValueError(f"PCIR pointer out of bounds at 0x{offset:x}")
        if data[pcir:pcir + 4] != b"PCIR":
            raise ValueError(f"missing PCIR at 0x{pcir:x}")

        image_length = u16(data, pcir + 0x10) * 512
        if image_length == 0 or offset + image_length > len(data):
            raise ValueError(f"invalid image length at 0x{offset:x}")

        indicator = data[pcir + 0x15]
        image = data[offset:offset + image_length]
        images.append({
            "offset": offset,
            "vendor": u16(data, pcir + 4),
            "device": u16(data, pcir + 6),
            "class": int.from_bytes(data[pcir + 0x0D:pcir + 0x10], "little"),
            "code_type": data[pcir + 0x14],
            "indicator": indicator,
            "length": image_length,
            "checksum_mod_256": sum(image) & 0xFF,
        })
        offset += image_length
        if indicator & 0x80:
            return images, offset

    raise ValueError(f"unterminated option-ROM chain at 0x{base:x}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("rom", type=Path)
    parser.add_argument("--expected-sha256", default=DEFAULT_EXPECTED_SHA256)
    args = parser.parse_args()

    data = args.rom.read_bytes()
    digest = hashlib.sha256(data).hexdigest()
    expected = args.expected_sha256.lower()
    print(f"size={len(data)}")
    print(f"sha256={digest}")
    print(f"expected_sha256_match={digest == expected}")
    print(f"container_magic={data[:4].decode('ascii', errors='replace')}")

    starts = [i for i in range(len(data) - 1) if data[i:i + 2] == b"\x55\xaa"]
    candidates = []
    for start in starts:
        try:
            images, end = parse_chain(data, start)
        except ValueError:
            continue
        if images and all(x["vendor"] == 0x10DE and x["device"] == 0x2182 for x in images):
            candidates.append((start, images, end))

    valid = []
    covered = set()
    for start, images, end in sorted(candidates):
        if start in covered:
            continue
        valid.append((start, images, end))
        covered.update(image["offset"] for image in images[1:])

    all_checksums_valid = True
    for chain, images, end in valid:
        print(f"chain=0x{chain:x} end=0x{end:x}")
        for image in images:
            print("  " + " ".join(
                f"{key}={value if not isinstance(value, int) else hex(value)}"
                for key, value in image.items()
            ))
            all_checksums_valid &= image["checksum_mod_256"] == 0

    chain_shape_valid = (
        len(valid) == 2
        and all(len(images) == 2 for _, images, _ in valid)
        and all(images[0]["code_type"] == 0 and images[1]["code_type"] == 3
                for _, images, _ in valid)
        and all(images[-1]["indicator"] & 0x80 for _, images, _ in valid)
    )
    print(f"all_checksums_valid={all_checksums_valid}")
    print(f"expected_chain_shape_valid={chain_shape_valid}")

    ok = (
        digest == expected
        and data[:4] == b"NVGI"
        and all_checksums_valid
        and chain_shape_valid
    )
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
