# TuringDarwin — Canonical Project State

**State version:** 4  
**Updated:** 2026-07-29  
**Repository:** `MrNev1s/TuringDarwin`  
**Current real-hardware-verified component:** `TuringProbe.kext 0.1.1`  
**Current source candidate:** `TuringProbe.kext 0.2.1`

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

## 7. TuringProbe 0.2 artifact status

### 0.2.0 compiled artifact

**[OFFLINE VERIFIED, REJECTED FOR BOOT]**

The GitHub build succeeded and the binary contained only the intended three
MMIO read call sites, but disassembly proved that the returned `IOMemoryMap` was
not released. The source incorrectly assumed automatic `OSPtr` destruction in a
third-party C++14 build. `TPBAR0MappingReleased` would therefore have reported a
false success. Artifact hashes and details are recorded in
`docs/ARTIFACT-REVIEW-0.2.0-REJECTED.md`. No hardware boot was performed.

### 0.2.1 compiled artifact

**[OFFLINE VERIFIED + REAL-HW VERIFIED IN PCI-ONLY MODE]**

GitHub Actions build provenance:

- source commit `76060d350cc1b58069f6138c5df517857e511059`;
- Xcode 16.2, SDK 15.2, x86_64;
- MacKernelSDK `05094e5e88cec7caedbfb35e8449ed0db94bf95b`;
- `BUILD SUCCEEDED`;
- Mach-O UUID `66D01C7F-5AD6-3EB7-8D98-B839F0733E99`;
- outer artifact SHA-256 `123cc915fa6be6dd002128fbc9fe74197d08e9a5838b436b2987aff9c59e095a`;
- inner kext ZIP SHA-256 `a409b524bc4100e77e4c3ee2cd9bff23e8a5336ef8a990df9755238c89515938`;
- executable SHA-256 `306faf22895d2abc80f11ec1cdc29e22f96185f9a0bb25fb2e9af2ea74938c44`;
- built `Info.plist` SHA-256 `6c5b511b1998425337ddf876e5844db24e7122b6bdda27a917e6a36e822d7270`.

Binary audit result: **PASS**.

The artifact preserves the exact BAR0 whitelist:

| Order | Offset | Register | Validation |
|---:|---:|---|---|
| 1 | `0x000004` | `NV_PMC_BOOT_1` | reject all-ones, big-endian, vGPU bits |
| 2 | `0x000000` | `NV_PMC_BOOT_0` | require chipset `0x168`, publish revision |
| 3 | `0x101000` | `NV_PEXTDEV_BOOT_0_STRAP` | decode known crystal straps |

Disassembly confirms:

- one BAR0 descriptor mapping request with option `0x1000`, correlated with
  `kIOMapReadOnly`;
- exactly three calls to the checked MMIO read accessor;
- one explicit virtual `IOMemoryMap::release()` call after every successful-map
  branch;
- mapping pointer clear immediately after release;
- no direct call sites for PCI/MMIO writes, DMA, interrupt setup, firmware,
  power mutation, or user-client creation.

The mandatory PCI-only compatibility boot has now passed on real hardware:

- version `0.2.1`, UUID `66D01C7F-5AD6-3EB7-8D98-B839F0733E99`;
- service registered, matched, active;
- `TuringProbeBootMode = -tdprobe`;
- PCI Command `0x0003` before and after;
- Bus Master disabled before and after;
- `TuringProbeMMIOAccess = No`;
- GOP output remained 1920×1080 ARGB8888;
- collected runtime ZIP SHA-256
  `b6ad39324a6c75953fb4bff164545c01c1129fdacf2115a8c133fd9135d4d559`.

The first controlled BAR0 read-only hardware boot has now passed:

- boot mode `-tdprobe -tdmmio-read`;
- BAR0 mapping base `0x80000000`, length 16 MiB;
- `kIOMapReadOnly` requested;
- mapping created and explicitly released;
- mapping not retained after probe;
- exactly three whitelisted reads completed;
- `NV_PMC_BOOT_1 = 0x00000000`;
- `NV_PMC_BOOT_0 = 0x168000A1`;
- chipset decoded as TU116 `0x168`, revision `0xA1`;
- `NV_PEXTDEV_BOOT_0_STRAP = 0x00400080`;
- crystal decoded as 27 MHz;
- PCI Command remained `0x0003` before mapping, after mapping, after reads,
  and after the complete probe;
- Bus Master remained disabled throughout;
- GOP output remained 1920x1080 ARGB8888;
- collected MMIO runtime ZIP SHA-256
  `bc72ea4378681f929a25cbe503a1a73443ca091df0f58b43d489090570cfabe4`.

This closes the initial three-register BAR0 identification milestone.
No additional register offsets and no write path are authorised.

## 8. Non-negotiable prohibition list

No PCI write, MMIO write, writable map request, DMA, interrupt, firmware, reset,
power/clock/fan/voltage change, GPU channel/FIFO/Copy Engine command, display
change, full BAR dump, IOUserClient, workloop, or command gate is authorised.

## 9. Next gate

**[DESIGN REVIEW REQUIRED; NOT YET AUTHORISED FOR HARDWARE]**

The initial BAR0 identification milestone is complete. The next stage must be a
new source-backed read-only inventory design with a separately reviewed,
minimal whitelist. Before any new hardware boot it must:

1. justify every additional register from primary Nouveau, NVIDIA open-kernel,
   or envytools documentation;
2. exclude registers with read-to-clear, acknowledge, FIFO-pop, indexed-window,
   or other possible read side effects;
3. retain `kIOMapReadOnly`, one-shot reads, explicit mapping release, exact
   device/subsystem matching, and unchanged PCI Command/Bus Master checks;
4. contain no PCI/MMIO writes, polling, DMA, interrupts, firmware, reset,
   power/clock/fan/voltage control, channels, FIFO, Copy Engine, display
   programming, or IOUserClient;
5. pass source audit, Xcode build, Mach-O call-site audit, and a PCI-only
   compatibility boot before any expanded MMIO run.

Return the test EFI to `-tdprobe` only while this next design is prepared.


## 10. TuringProbe 0.3.0 candidate

**[SOURCE IMPLEMENTED + LOCAL AUDIT PASS; NOT XCODE-BUILT; NOT HARDWARE-AUTHORISED]**

The candidate preserves all 0.2.1 identity reads and adds an optional bounded
PTOP inventory selected by `-tdtop-read`. TU116 uses Nouveau's
`gk104_top_parse`, which reads exactly 64 dwords at `0x022700..0x0227fc`.
Expanded mode therefore contains exactly 67 MMIO reads: 3 identity + 64 TOP.

Safety properties:

- one `kIOMapReadOnly` BAR0 mapping;
- explicit `IOMemoryMap::release()`;
- fixed compile-time table base and count;
- one finite 64-iteration loop, no polling;
- no PCI/MMIO writes, DMA, interrupts, firmware, reset, power/clock/fan/voltage
  control, FIFO/channels/Copy Engine commands, display programming or user
  client;
- `-tdtop-read` fails closed unless `-tdmmio-read` is also present;
- `-tdunsafe` remains rejected.

Next gate: GitHub Actions build and Mach-O call-site audit. The first hardware
boot of the built 0.3.0 artifact must be PCI-only; expanded TOP MMIO remains
blocked until that compatibility boot passes.
