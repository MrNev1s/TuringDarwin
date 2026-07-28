# VBIOS notes

Inspected file: `TU116(3).rom`

- Size: 1,047,040 bytes (`0xFFA00`)
- SHA-256: `4ea82dadeda06b347c0eca76d4bf41f0dc56e7a402452b00cb8c72b38b2e40b4`
- Container prefix: `NVGI`
- The file does not begin with a raw `55 AA` option-ROM header.
- Two byte-identical embedded PCI option-ROM chains begin at `0x28600` and
  `0xA0600`.
- Each chain contains:
  - legacy image: `10DE:2182`, code type 0, length `0xF000`, checksum valid;
  - UEFI image: `10DE:2182`, code type 3, length `0x11000`, last-image flag set,
    checksum valid.
- Identifying strings include `TUF-GTX1660TI`, VBIOS
  `90.16.48.40.1E`, and the EVO gaming board name.

This is only structural validation of the vendor container and PCI images.
BIT tables, memory timing tables, display scripts and embedded Falcon firmware
have not yet been semantically validated. Version 0.1 never reads or maps the
live expansion ROM and does not modify this file.
