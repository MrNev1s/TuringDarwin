# TuringDarwin — Canonical Project State

**State version:** 2  
**Updated:** 2026-07-29  
**Repository:** `MrNev1s/TuringDarwin`  
**Current verified runtime component:** `TuringProbe.kext 0.1.0`  
**Current development component:** `TuringProbe.kext 0.1.1`  

This is the canonical hand-off file for the project. Update it after every
successful build, boot experiment, hardware-state change, or scope decision.
Claims are tagged as follows:

- **[REAL-HW VERIFIED]** observed on the target computer;
- **[OFFLINE VERIFIED]** proven from supplied files or static binary analysis;
- **[IMPLEMENTED, NOT BUILT]** present in source but not yet compiled by Xcode;
- **[PLANNED]** approved design, not implemented;
- **[BLOCKED]** deliberately forbidden until an earlier gate passes.

## 1. Non-negotiable safety contract

The active 0.1.x branch is PCI configuration **read-only**.

Forbidden in 0.1.x:

- PCI configuration writes;
- changing the PCI Command Register;
- enabling bus mastering, memory decoding, or I/O decoding;
- creating BAR mappings or dereferencing MMIO;
- DMA allocation/mapping/submission;
- interrupts, MSI/MSI-X enablement, workloops, command gates, or user clients;
- firmware loading;
- GPU power, clock, voltage, fan, or reset operations;
- display/modeset or framebuffer modification.

Boot controls:

- `-tdprobe`: required for 0.1.x attachment;
- `-tdoff`: force-disable;
- `-tdmmio-read`: rejected by 0.1.x;
- `-tdunsafe`: rejected by 0.1.x.

No MMIO write is authorised. No PCI write is authorised.

## 2. Target machine

### CPU / platform

- Intel Core i5-12400F, Alder Lake H0, 6C/12T, no iGPU.
- MSI PRO B760M-P DDR4 (MS-7E02 rev 1.0).
- BIOS E7E02IMS.160 dated 2023-09-09.
- SMBIOS `iMacPro1,1`.
- OpenCore boots macOS without an Intel iGPU.

### GPU target

**[REAL-HW VERIFIED]**

| Field | Value |
|---|---|
| Board | ASUS TUF Gaming GeForce GTX 1660 Ti EVO TOP |
| GPU | NVIDIA TU116-400-A1 |
| BDF | `01:00.0` |
| Vendor / Device | `10DE:2182` |
| Subsystem | `1043:8854` |
| Revision | `A1` |
| Class | `030000` |
| Header | `0x80` (multifunction) |
| ACPI path | `_SB_.PC00.PEG1.PEGP` |
| IOService path | `/AppleACPIPlatformExpert/PC00@0/AppleACPIPCI/PEG1@1/IOPP/PEGP@0` |
| IODeviceTree path | `/PC00@0/PEG1@1/PEGP@0` |

Sibling NVIDIA functions found offline:

- `01:00.1` — `10DE:1AEB` HDA;
- `01:00.2` — `10DE:1AEC` USB xHCI;
- `01:00.3` — `10DE:1AED` Type-C policy controller.

`TuringProbe` matches only `01:00.0` and repeats the exact four-ID check in
`start()`.

## 3. macOS runtime baseline

**[REAL-HW VERIFIED]** on 2026-07-29:

- macOS `15.7.7`, build `24G720`;
- `TuringProbe 0.1.0` loaded through OpenCore;
- `kmutil showloaded` reported `com.mrnev1s.driver.TuringProbe (0.1.0)`;
- IORegistry service was `registered, matched, active, busy 0`;
- GOP/IONDRV framebuffer remained active;
- desktop output remained `1920×1080`, ARGB8888;
- `system_profiler` continued to report 8 MB framebuffer VRAM and no graphics
  accelerator kext, which is expected;
- no panic or boot hang was reported.

The unified log notification from `kernelmanager_helper` saying the bundle was
not found is not evidence of a failed load: `kmutil` and IORegistry independently
proved the OpenCore-injected kext was active.

## 4. VBIOS evidence

**[OFFLINE VERIFIED]**

| Field | Value |
|---|---|
| File | `TU116(3).rom` |
| Size | `1,047,040` bytes |
| SHA-256 | `4ea82dadeda06b347c0eca76d4bf41f0dc56e7a402452b00cb8c72b38b2e40b4` |
| Container | `NVGI` |
| VBIOS string | `90.16.48.40.1E` |
| Board string | `TUF-GTX1660TI` |
| Option-ROM chains | offsets `0x28600` and `0xA0600` |
| Legacy image | `0xF000` bytes |
| UEFI image | `0x11000` bytes |
| Embedded image checksums | valid |

BIT tables, display scripts, memory timings, and Falcon firmware descriptors
have not yet been promoted to verified facts.

## 5. PCI Command Register safety result

**[REAL-HW VERIFIED]**

`TPCommand = 0x0003` during the 0.1.0 probe:

- I/O Space Enable = 1;
- Memory Space Enable = 1;
- Bus Master Enable = 0.

The first two bits were pre-existing platform state required by the active GOP
resources. Version 0.1.0 contained no write API and did not enable bus mastering.
Version 0.1.1 additionally records the Command Register before and after the
probe and publishes `TPCommandUnchanged`.

## 6. Assigned BARs and device-memory descriptors

**[REAL-HW VERIFIED]**

| BAR/resource | Raw / base | Length | Classification |
|---|---:|---:|---|
| BAR0 | base `0x80000000` | `0x01000000` / 16 MiB | 32-bit non-prefetchable MMIO |
| BAR1/2 | base `0x4000000000` | `0x10000000` / 256 MiB | 64-bit prefetchable |
| BAR3/4 | base `0x4010000000` | `0x02000000` / 32 MiB | 64-bit prefetchable |
| BAR5 | base `0x5000` | `0x80` / 128 B | I/O space |
| Expansion ROM | base `0x81000000` | `0x80000` / 512 KiB | ROM aperture |

No BAR was mapped by `TuringProbe 0.1.0`.

## 7. PCI capabilities observed on the target

### Conventional capabilities

**[REAL-HW VERIFIED]**

| Offset | ID | Name |
|---:|---:|---|
| `0x60` | `0x01` | Power Management |
| `0x68` | `0x05` | MSI |
| `0x78` | `0x10` | PCI Express |

MSI is 64-bit capable and disabled. MSI-X was not present in the observed
conventional chain.

PCIe link:

- capability version 2;
- maximum PCIe speed encoding 3 (PCIe 3.0);
- maximum width x16;
- observed idle speed encoding 1;
- negotiated width x16.

### Extended capabilities

**[REAL-HW VERIFIED]**

| Offset | ID | Name |
|---:|---:|---|
| `0x100` | `0x0002` | Virtual Channel |
| `0x250` | `0x0018` | Latency Tolerance Reporting |
| `0x258` | `0x001E` | L1 PM Substates |
| `0x128` | `0x0004` | Power Budgeting |
| `0x420` | `0x0001` | Advanced Error Reporting |
| `0x600` | `0x000B` | Vendor-Specific Extended Capability |
| `0x900` | `0x0019` | Secondary PCI Express |
| `0xBB0` | `0x0015` | Resizable BAR |

Observed first ReBAR pair:

- capability raw `0x00000100`;
- control raw `0x00000460`;
- encoded entry count field = 3;
- entry 0 identifies BAR0 with current size encoding 4, corresponding to
  16 MiB.

Version 0.1.1 decodes all advertised ReBAR entries without writing controls.

## 8. Build evidence for TuringProbe 0.1.0

**[OFFLINE VERIFIED]**

- GitHub Actions workflow: `Build TuringProbe kext`;
- successful run shown as build `#9`;
- Xcode 16.2;
- macOS SDK 15.2;
- MacKernelSDK commit
  `05094e5e88cec7caedbfb35e8449ed0db94bf95b`;
- architecture `x86_64`;
- bundle ID `com.mrnev1s.driver.TuringProbe`;
- binary UUID `5E869CB5-83FB-322F-A1F2-F1AE313B4C2B`.

Hashes:

| Artifact | SHA-256 |
|---|---|
| GitHub artifact ZIP | `f2003338edf9600ae48665cea7c6604ed3cc305072c0e74f743e3880275a938b` |
| Verified kext ZIP | `bbb10406dbbb70e0c5fa862150caa6bede6edc532408b2429475abb7091b876f` |
| Mach-O executable | `695d0348cf164827e7e382dc700619b30da78f88d5c0115c219da2ed655d8609` |
| Built Info.plist | `8ccc54cc721d0f4683b48315001e484f40bc7b478809a87377800ac9aa107e12` |
| First runtime log bundle | `25dcb455f4727a331a83ee5bce5c26735b0c6e5c4059fd4c61bc844709c2fa20` |

## 9. Source evidence inputs

| File | SHA-256 |
|---|---|
| `PC-DATA-20260723-121802(1).zip` | `f0cce8af98c55871c9db6b3216e1aa8e83ef3d6a7542ab99b4c09c562416fd6a` |
| `EFI_STABLE.zip` | `3539c4d40009a52df0d08ec15c060e005ca770cd66649180e16e68da529bdfe9` |
| `TU116(3).rom` | `4ea82dadeda06b347c0eca76d4bf41f0dc56e7a402452b00cb8c72b38b2e40b4` |
| Uploaded test `config(1).plist` | `f91486873fea485d2923032f2e8c386f90804b0795b9474fff0c9bcf4300cd74` |

## 10. TuringProbe 0.1.1 milestone

**[IMPLEMENTED, NOT BUILT]**

0.1.1 remains PCI-config read-only and adds:

1. explicit unsigned publication of raw 32-bit PCI values using 64-bit
   `OSNumber` storage, eliminating confusing sign-extension in `ioreg`;
2. human-readable conventional and extended capability names;
3. complete bounded ReBAR entry decoding;
4. supported ReBAR sizes in bytes and the current selected size;
5. before/after PCI Command Register snapshots;
6. `TPCommandUnchanged` and before/after bus-master state;
7. explicit completion, schema, version, and boot-mode properties;
8. exact default MacKernelSDK pin from the successful 0.1.0 build.

Acceptance gate for 0.1.1:

- GitHub build succeeds with the pinned SDK;
- static safety audit succeeds;
- real boot succeeds with `-tdprobe`;
- `TPCommandBeforeProbe == TPCommandAfterProbe == 3`;
- both bus-master properties remain false;
- `TPResizableBARDecodeValid = true`;
- three ReBAR entries are decoded;
- GOP output is unchanged.

## 11. Next hardware stage after 0.1.1

**[PLANNED]** `TuringProbe 0.2 — BAR0 read-only MMIO gate`.

It is not yet implemented in this state package. Required design gates:

- separate source branch and kext version;
- `-tdmmio-read` required in addition to explicit compile-time enablement;
- BAR0 only;
- mapping obtained from the existing BAR0 descriptor;
- fixed small whitelist of identification/status registers derived from
  Nouveau, envytools, and NVIDIA open modules;
- no whole-BAR dump;
- no polling loop without a strict bound;
- no writes of any kind;
- publish pre/post PCI Command Register values;
- abort if bus mastering is enabled unexpectedly;
- one-monitor test path and untouched fallback EFI.

No offsets enter the whitelist until each one has a primary-source provenance
record and a read-safety rationale.

## 12. Long-term feasibility classification

- PCI diagnostics and VBIOS parsing: feasible and underway.
- Read-only MMIO: feasible after whitelist review.
- GPU VM/FIFO/Copy Engine: serious research task; not started.
- Dedicated compute/Vulkan API: architecturally possible, high effort.
- Display/modeset framebuffer: high effort and hardware-risky.
- NVK port: very high effort.
- WindowServer/Metal integration: currently a separate, potentially
  impractical reverse-engineering programme.
