# BAR0 register whitelist — TuringProbe v0.2.1

Status: **implemented in source; not yet compiled or tested on the target**.

No register not listed here may be read. Every access is 32-bit, occurs once,
and is performed through the single checked accessor in `MMIOReadOnly.cpp`.
The mapping requests `kIOMapReadOnly`; no write primitive exists in the module.

| Symbol | Offset | Width | Purpose | Read-safety basis |
|---|---:|---:|---|---|
| `NV_PMC_BOOT_1` | `0x000004` | 32 bit | Endianness sanity and Turing vGPU flags | Nouveau reads it during device construction before engine initialisation. Turing vGPU mode is detected from bits `0x00030000`. This probe never executes Nouveau's endian-switch write. |
| `NV_PMC_BOOT_0` | `0x000000` | 32 bit | Chipset and revision identification | Nouveau reads it to derive chipset `(value & 0x1ff00000) >> 20` and revision `value & 0xff`; chipset `0x168` selects TU116. |
| `NV_PEXTDEV_BOOT_0_STRAP` | `0x101000` | 32 bit | Board strap and crystal selection | Nouveau reads it during device construction and decodes `0x00400040` to 13.5, 14.318, 27, or 25 MHz. |

Primary hardware reference:

- Linux Nouveau `drivers/gpu/drm/nouveau/nvkm/engine/device/base.c`, revision
  `v6.19-rc8-185-g2687c848e578`, device-construction path around lines
  3119–3137 and 3169–3405.

Apple mapping reference:

- XNU `iokit/IOKit/IOMemoryDescriptor.h`, revision `10063.121.3`:
  `kIOMapReadOnly` creates a read-only mapping and writes fault; releasing the
  returned `IOMemoryMap` destroys the mapping.

## Explicit exclusions

The whitelist excludes interrupt/status registers, doorbells, reset controls,
PRAMIN, VRAM windows, FIFO/runlist/channel registers, display registers,
firmware/Falcon mailboxes, clock/power/thermal controls, and any register whose
read may acknowledge or clear state.

## Runtime rejection rules

The probe refuses MMIO when any of the following is true:

- exact PCI/subsystem identity does not match;
- `-tdprobe` or `-tdmmio-read` is absent for the MMIO path;
- `-tdunsafe` is present;
- PCI memory decoding is disabled;
- Bus Master Enable is set;
- BAR0 is absent, I/O-space, 64-bit, prefetchable, misaligned, or not exactly
  the real-hardware-verified 16 MiB aperture;
- the IOPCIFamily descriptor disagrees with PCI configuration;
- read-only mapping creation fails;
- PCI Command Register changes;
- BOOT1 reports big-endian mode, all ones, or vGPU mode;
- BOOT0 does not identify chipset `0x168`;
- strap decoding is invalid.
