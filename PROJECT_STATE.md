# TuringDarwin — Canonical Project State

**State version:** 3  
**Updated:** 2026-07-29  
**Repository:** `MrNev1s/TuringDarwin`  
**Current real-hardware-verified component:** `TuringProbe.kext 0.1.1`  
**Current source candidate:** `TuringProbe.kext 0.2.0`

This file is the authoritative hand-off. Claims use these labels:

- **[REAL-HW VERIFIED]** observed on the target computer;
- **[OFFLINE VERIFIED]** proven from supplied files/static analysis;
- **[SOURCE IMPLEMENTED, NOT BUILT]** present in source but not compiled;
- **[PLANNED]** design only;
- **[BLOCKED]** forbidden until an earlier gate passes.

## 1. Target and runtime baseline

**[REAL-HW VERIFIED]**

| Field | Value |
|---|---|
| GPU | ASUS TUF GTX 1660 Ti, TU116-400-A1 |
| BDF | `01:00.0` |
| PCI ID | `10DE:2182` |
| Subsystem | `1043:8854` |
| Revision / class | `A1` / `030000` |
| ACPI path | `_SB_.PC00.PEG1.PEGP` |
| macOS | 15.7.7, build 24G720 |
| Display baseline | GOP/IONDRV, 1920×1080 ARGB8888 |

Sibling functions are `01:00.1` HDA (`10DE:1AEB`), `01:00.2` xHCI
(`10DE:1AEC`), and `01:00.3` Type-C policy (`10DE:1AED`). TuringProbe matches
only the VGA function and repeats the exact four-ID check in `start()`.

## 2. VBIOS evidence

**[OFFLINE VERIFIED]**

- file `TU116(3).rom`, 1,047,040 bytes;
- SHA-256 `4ea82dadeda06b347c0eca76d4bf41f0dc56e7a402452b00cb8c72b38b2e40b4`;
- `NVGI` container, VBIOS `90.16.48.40.1E`, board string `TUF-GTX1660TI`;
- two valid legacy+UEFI option-ROM chains with valid image checksums.

BIT tables, memory timings, display scripts, and Falcon firmware layout are not
yet promoted to verified facts.

## 3. PCI-only milestone result

**[REAL-HW VERIFIED]** `TuringProbe 0.1.1`:

- loaded and active through OpenCore;
- PCI Command before/after `0x0003`;
- Bus Master Enable before/after `No`;
- no MMIO, DMA, interrupts, firmware, power change, or user client;
- conventional capability walk valid, 3 entries;
- extended capability walk valid, 8 entries;
- ReBAR decode valid, 3 entries;
- GOP output unchanged and no reported panic/hang/corruption.

Runtime log ZIP SHA-256:
`3864fa4ebcb9a48c96f2140e38301d262ffa65fe6126cea5916ad4458135ed41`.

## 4. Assigned resources

**[REAL-HW VERIFIED]**

| Resource | Base | Length | Type |
|---|---:|---:|---|
| BAR0 | `0x80000000` | 16 MiB | 32-bit non-prefetchable MMIO |
| BAR1/2 | `0x4000000000` | 256 MiB | 64-bit prefetchable |
| BAR3/4 | `0x4010000000` | 32 MiB | 64-bit prefetchable |
| BAR5 | `0x5000` | 128 B | I/O space |
| ROM aperture | `0x81000000` | 512 KiB | option ROM window |

ReBAR entries:

| BAR | Current | Supported |
|---:|---:|---|
| 0 | 16 MiB | 16 MiB |
| 1 | 256 MiB | 64, 128, 256 MiB |
| 3 | 32 MiB | 32 MiB |

## 5. PCI capability chain

**[REAL-HW VERIFIED]**

Conventional: PM `0x60`, MSI `0x68`, PCIe `0x78`. MSI is disabled. Link maximum
is PCIe 3.0 ×16; captured idle state was speed encoding 1 ×16.

Extended: Virtual Channel `0x100`, Power Budgeting `0x128`, LTR `0x250`, L1 PM
Substates `0x258`, AER `0x420`, VSEC `0x600`, Secondary PCIe `0x900`, ReBAR
`0xBB0`.

## 6. Verified 0.1.1 build provenance

**[OFFLINE + REAL-HW VERIFIED]**

- Xcode 16.2, macOS SDK 15.2, x86_64;
- MacKernelSDK `05094e5e88cec7caedbfb35e8449ed0db94bf95b`;
- source commit `1168040c73962104da19d22433885e76d21e3405`;
- Mach-O UUID `9942C8A8-8540-3530-8309-C767D6C76FD8`;
- executable SHA-256
  `45d1e6a2a258a7f7699e9f86ee4d30dbfbc6af3e2d04e1d494685c97d5f2d080`.

## 7. TuringProbe 0.2.0 candidate

**[SOURCE IMPLEMENTED, NOT BUILT]**

Two modes:

- `-tdprobe`: PCI-only compatibility mode, no BAR map;
- `-tdprobe -tdmmio-read`: first BAR0 read-only experiment.

Fail-closed requirements before mapping:

- compile gate `TURINGPROBE_ENABLE_MMIO_READ=1`;
- exact target identity;
- `-tdoff` and `-tdunsafe` absent;
- memory decoding enabled and bus mastering disabled;
- BAR0 raw value and IOPCIFamily descriptor agree;
- BAR0 is exactly 16 MiB, 32-bit, non-prefetchable, and aligned.

Mapping contract:

- `IOMemoryDescriptor::map(kIOMapReadOnly)` only;
- mapping held in a local `OSPtr<IOMemoryMap>` scope;
- no cache-policy override;
- no stored virtual address or retained map;
- exactly three 32-bit reads, once each;
- mapping destroyed before `start()` completes.

Whitelist:

| Order | Offset | Register | Validation |
|---:|---:|---|---|
| 1 | `0x000004` | `NV_PMC_BOOT_1` | reject all-ones, big-endian, vGPU bits |
| 2 | `0x000000` | `NV_PMC_BOOT_0` | require chipset `0x168`, publish revision |
| 3 | `0x101000` | `NV_PEXTDEV_BOOT_0_STRAP` | decode known crystal straps |

PCI Command is sampled before map, after map, after reads, and after the full
probe; all values must match and Bus Master Enable must remain clear.

Local source checks passed:

- safety audit;
- PCI/ReBAR decoder contract;
- MMIO whitelist/map contract;
- Python syntax, plist parse, and Xcode-project structural checks.

No claim of Xcode compilation, binary safety, or hardware success is made yet.

## 8. Non-negotiable prohibition list

No PCI write, MMIO write, writable map request, DMA, interrupt, firmware, reset,
power/clock/fan/voltage change, GPU channel/FIFO/Copy Engine command, display
change, full BAR dump, IOUserClient, workloop, or command gate is authorised.

## 9. Next gate

1. Build 0.2.0 in GitHub Actions with the pinned toolchain.
2. Upload the complete artifact for binary/import/disassembly audit.
3. Prepare a separate test-EFI package only after that audit.
4. Boot PCI-only mode first (`-tdprobe`).
5. Only after PCI-only PASS, boot BAR0 mode (`-tdprobe -tdmmio-read`).

A successful BAR0 read does not authorise adding offsets or implementing writes.
