# TuringDarwin — Canonical Project State

**State version:** 11  
**Updated:** 2026-07-29  
**Repository:** `MrNev1s/TuringDarwin`  
**Current real-hardware-verified component:** `TuringProbe.kext 0.3.0`  
**Current source candidate:** `TuringProbe.kext 0.4.0`

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

## 10. TuringProbe 0.3.0 artifact status

**[OFFLINE VERIFIED; PCI-ONLY HARDWARE BOOT AUTHORISED]**

Build provenance:

- source commit `ce0a12459e31f3d4b8b2e948207ab7a142de0207`;
- Xcode 16.2, macOS SDK 15.2, x86_64;
- MacKernelSDK `05094e5e88cec7caedbfb35e8449ed0db94bf95b`;
- `BUILD SUCCEEDED`;
- Mach-O UUID `34E1451B-891E-36BB-BA88-5D5B60A37431`;
- outer artifact SHA-256 `36f9d3f598ccf75c50e019e5a69224156ec9bec3e943414dbe9859f131080418`;
- inner kext ZIP SHA-256 `2272673c66d11560893a6da65ae0e03058d6b9b0b4a2733f653b69f997867694`;
- executable SHA-256 `3ec68a887f8655d91e5f1490ce8b40adb4244b76c6907d9602948645d7829745`;
- built `Info.plist` SHA-256 `f40cdf7fb7a2b6574669ad0c25890dd6effe84fd2d6c625bb079a73fa49d7acb`.

Binary audit result: **PASS**.

Confirmed in the compiled artifact:

- exact PCI/subsystem matching remains unchanged;
- `-tdtop-read` requires `-tdmmio-read`;
- three identity reads remain fixed;
- the optional TOP path uses one bounded 64-iteration loop;
- each TOP offset is `0x022700 + index * 4`, ending at `0x0227FC`;
- the mapping release path remains present;
- no direct PCI/MMIO write, DMA, interrupt, power, user-client, or bus-master
  enable call site was found.

Nouveau's `gk104_top_parse` source uses the same fixed 64-dword table and
bitfields. Unknown engine types remain raw/UNKNOWN rather than guessed.

Non-blocking artifact metadata defect:

- `build-Debug.manifest.txt` incorrectly reports `turingprobe_version=0.2.1`;
- it also reports only the old three-register whitelist;
- the compiled `Info.plist`, strings, symbols, and disassembly confirm actual
  version 0.3.0 and the PTOP path;
- `tools/build.sh` must be corrected before the next release.

The artifact is authorised only for a PCI-only compatibility boot with
`-tdprobe`. Neither `-tdmmio-read` nor `-tdtop-read` is authorised until the
PCI-only result is reviewed.

## 11. TuringProbe 0.3.0 PCI-only hardware acceptance

**[REAL-HARDWARE VERIFIED — PASS]**

- macOS 15.7.7 / build 24G720;
- kext `0.3.0`, UUID `34E1451B-891E-36BB-BA88-5D5B60A37431`;
- service registered, matched, active, busy 0;
- boot mode `-tdprobe`;
- `TuringProbeMMIOAccess = No`;
- `TuringProbeTopInventoryAccess = No`;
- PCI Command remained `0x0003`;
- Bus Master remained disabled;
- probe completed successfully;
- GOP remained 1920x1080 ARGB8888;
- runtime log ZIP SHA-256 `e89bcf73c342667d683fcf74b9b8ca8a7382fb8487f559c8b0badd542a629124`.

This closes the v0.3.0 PCI-only compatibility gate.

The next authorised experiment is one identity-only BAR0 boot with
`-tdprobe -tdmmio-read`. `-tdtop-read` remains prohibited until the identity
result is reviewed. No new offsets and no write path are authorised.



## 12. TuringProbe 0.3.0 identity-only hardware gate

**[REAL-HW VERIFIED — PASS]**

- macOS 15.7.7 / build 24G720;
- version 0.3.0, UUID `34E1451B-891E-36BB-BA88-5D5B60A37431`;
- boot mode `-tdprobe -tdmmio-read`;
- BAR0 read-only mapping created and explicitly released;
- mapping not retained after probe;
- exactly three identity reads completed;
- no PTOP access: requested No, completed No, TOP read count 0;
- `NV_PMC_BOOT_0 = 0x168000A1`;
- chipset TU116 `0x168`, revision `0xA1`;
- strap `0x00400080`, crystal 27 MHz;
- PCI Command remained `0x0003`;
- Bus Master remained disabled;
- GOP remained 1920×1080 ARGB8888;
- runtime log ZIP SHA-256 `e5a6476a06c9d30981c1377763c1b578a6562388f1ac86859de97540d3f27317`.

One controlled PTOP read-only hardware boot is now authorised with exactly
`-tdprobe -tdmmio-read -tdtop-read`. No additional offsets and no write path
are authorised. A failed TOP boot must not be retried.


## 13. TuringProbe 0.3.0 PTOP hardware inventory

**[REAL-HARDWARE VERIFIED — PASS]**

- boot mode `-tdprobe -tdmmio-read -tdtop-read`;
- read-only BAR0 mapping created and explicitly released;
- mapping not retained after probe;
- 3 identity reads plus exactly 64 PTOP reads;
- PTOP range `0x022700..0x0227FC`;
- total MMIO read count 67;
- 34 invalid/empty words, 10 DATA words, 10 ENUM words and 10 ENGINE_TYPE words;
- 10 devices decoded;
- 10 known types, 0 unknown types, 0 malformed records;
- `TPTopDecodeValid = Yes`;
- PCI Command remained `0x0003`;
- Bus Master remained disabled;
- GOP remained 1920×1080 ARGB8888;
- runtime log ZIP SHA-256 `1f91f1c51b0659a55ab0190c242d5210ed8823d2c7876dfaf96cc376c783629a`.

Confirmed PTOP inventory:

| Block | Instance | Address | Engine | Runlist | IRQ | Reset | Fault |
|---|---:|---:|---:|---:|---:|---:|---:|
| GR | 0 | `0x400000` | 0 | 0 | 12 | 12 | 64 |
| CE | 0 | `0x104000` | 11 | 0 | 5 | 6 | 15 |
| CE | 1 | `0x104000` | 12 | 0 | 6 | 7 | 16 |
| CE | 2 | `0x104000` | 8 | 8 | 7 | 21 | 17 |
| CE | 3 | `0x104000` | 9 | 9 | 10 | 22 | 18 |
| CE | 4 | `0x104000` | 10 | 10 | 11 | 23 | 19 |
| NVDEC | 0 | `0x830000` | 1 | 1 | 17 | 15 | 10 |
| SEC2 | 0 | `0x087000` | 3 | 3 | 15 | 14 | 14 |
| NVENC | 0 | `0x1C8000` | 2 | 2 | 16 | 18 | 11 |
| GSP | 0 | `0x110000` | — | — | 27 | — | 2 |

This closes the initial PTOP topology milestone. The entries prove that the
blocks are advertised by hardware; they do not prove initialisation, firmware,
scheduling, or command-submission readiness.

### Next gate

**[DESIGN/RESEARCH ONLY — NO NEW HARDWARE ACCESS AUTHORISED]**

The next candidate milestone is a new minimal read-only FB/MMU capability
inventory. Every proposed offset must first be justified from primary Nouveau,
NVIDIA open-kernel or envytools sources and excluded if it can acknowledge,
clear, pop, trigger, select an indexed window or otherwise have read side
effects.

Until that review is complete, return the test EFI to `-tdprobe` only.
No new MMIO offsets and no write path are authorised.


## 14. TuringProbe 0.4.0 FB/MMU source candidate

**[SOURCE IMPLEMENTED, NOT BUILT, NOT AUTHORISED FOR HARDWARE]**

Version 0.4.0 preserves every verified 0.3.0 mode and adds one isolated mode:

```text
-tdprobe -tdmmio-read -tdfb-read
```

The mode performs the three verified identity reads and exactly one new 32-bit
read at BAR0 offset `0x100CE0`. TU102/TU116 uses Nouveau's
`gp102_fb_vidmem_size()` decoder for this register:

- magnitude mask `0x000003F0`, shift 4;
- scale mask `0x0000000F`;
- nominal bytes `magnitude << (scale + 20)`;
- bit `0x40000000` applies a 15/16 reduction.

The exact target gate accepts only a valid result of 6 GiB. Any other value
causes the mapping to be released and attachment to fail.

The candidate also publishes a clearly source-labelled TU102 MMU profile with
no additional MMIO reads: 47-bit DMA addressing, GF100 MMU/memory classes,
GP100 VMM class, a 16-entry kind map with invalid kind `0x07`, system-memory
kinds, and page shift 16 (historically misreported here as 16 KiB; corrected to 64 KiB in section 19).

Safety constraints:

- dedicated compile-time gate `TURINGPROBE_ENABLE_FB_READ=1`;
- `-tdfb-read` requires `-tdmmio-read`;
- simultaneous `-tdtop-read` and `-tdfb-read` is rejected;
- one new read, no loops or polling;
- `kIOMapReadOnly`, explicit release and pointer clear remain mandatory;
- PCI Command and Bus Master invariants remain mandatory;
- no new write, DMA, interrupt, firmware, reset, power, FIFO, channel, engine,
  display or user-client path exists.

Local source gates passed:

- safety audit;
- ReBAR decoder contract;
- MMIO ownership/boot-policy contract;
- bounded PTOP contract;
- FB/MMU one-register decoder contract.

The stale 0.3.0 build-manifest version/whitelist defect has been corrected in
`tools/build.sh`.

### Next gate

Build 0.4.0 with GitHub Actions, upload the complete artifact, and audit the
compiled Mach-O. Until that audit passes, keep the verified 0.3.0 kext and
`-tdprobe` only. No 0.4.0 hardware boot or `-tdfb-read` use is authorised.

## 15. TuringProbe 0.4.0 compiled artifact

**[OFFLINE VERIFIED; PCI-ONLY HARDWARE BOOT AUTHORISED]**

Build provenance:

- source commit `e8c729e06ffe381f56abad98f8896ea294adfb44`;
- Xcode 16.2, macOS SDK 15.2, x86_64;
- MacKernelSDK `05094e5e88cec7caedbfb35e8449ed0db94bf95b`;
- `BUILD SUCCEEDED`;
- Mach-O UUID `5830AA6F-E4D0-34F0-A49E-00C53461D535`;
- outer artifact SHA-256 `2f3e53a0709c0e259b4eb3a77c47c688986d80e8d30146259da45afcc2337e85`;
- inner kext ZIP SHA-256 `1c53817a7565da75dcd0a90dddf5ca7034f3390a70b83ecbb51f4775eddc9b33`;
- executable SHA-256 `f286d15537bcbe8a5f921d6c39831fc2902468bb0fa2d7be0bf6558319f74659`;
- built `Info.plist` SHA-256 `2b1d2ec4cece285aa81121f0bf6258122850ff353df370a202b4b22327a7a21b`.

Binary audit result: **PASS**.

Confirmed in the compiled artifact:

- exact PCI/subsystem matching remains unchanged;
- both MMIO and FB compile-time gates are enabled;
- `-tdfb-read` requires `-tdmmio-read`;
- simultaneous TOP and FB modes are rejected;
- the three identity reads remain fixed;
- the optional FB path contains exactly one read at `0x100CE0`;
- the compiled FB decoder requires exactly 6 GiB;
- the FB path has no loop or polling;
- MMU information is source metadata and causes no extra MMIO reads;
- explicit BAR0 mapping release and pointer clear remain present;
- no direct PCI/MMIO write, DMA, interrupt, power, user-client or bus-master
  enable call site was found.

The build manifest metadata defect from 0.3.0 is fixed and now correctly reports
version 0.4.0, both compile gates and the FB whitelist.

The workflow's kextutil check remains inconclusive because the command is
routed to an unsupported kmutil mode. It is not counted as a successful check.

The artifact is authorised only for a PCI-only compatibility boot with
`-tdprobe`. `-tdmmio-read`, `-tdtop-read` and `-tdfb-read` remain prohibited
until the PCI-only result is reviewed.



## 16. TuringProbe 0.4.0 PCI-only hardware gate

**[REAL-HARDWARE VERIFIED — PASS]**

- macOS 15.7.7 / build 24G720;
- version 0.4.0, UUID `5830AA6F-E4D0-34F0-A49E-00C53461D535`;
- service registered, matched and active;
- boot mode `-tdprobe`;
- MMIO access No;
- TOP inventory access No;
- FB/MMU inventory access No;
- PCI Command remained `0x0003`;
- Bus Master remained disabled;
- no PCI/MMIO writes, DMA, interrupts, firmware, power changes or user client;
- GOP remained 1920×1080 ARGB8888;
- runtime log ZIP SHA-256 `1dbd35178de70bdaf081d3280bd0e5daa1b10190392b1e6a2ad6a01d652abca5`.

One identity-only compatibility boot is now authorised with exactly
`-tdprobe -tdmmio-read`. `-tdtop-read` and `-tdfb-read` remain prohibited.


## 17. TuringProbe 0.4.0 identity-only hardware gate

**[REAL-HARDWARE VERIFIED — PASS]**

- macOS 15.7.7 / build 24G720;
- version 0.4.0, UUID `5830AA6F-E4D0-34F0-A49E-00C53461D535`;
- boot mode `-tdprobe -tdmmio-read`;
- BAR0 read-only mapping created and explicitly released;
- mapping not retained after probe;
- exactly three identity reads completed;
- PTOP read count 0;
- FB/MMU read count 0;
- `NV_PMC_BOOT_0 = 0x168000A1`;
- chipset TU116 `0x168`, revision `0xA1`;
- strap `0x00400080`, crystal 27 MHz;
- PCI Command remained `0x0003`;
- Bus Master remained disabled;
- GOP remained 1920×1080 ARGB8888;
- runtime log ZIP SHA-256 `a03e924fbdb1a4ed0d57f4a4dedc8dec1f06ebb3c87285e5e6529a588bbe6f4f`.

One controlled FB-capacity hardware boot is now authorised using exactly
`-tdprobe -tdmmio-read -tdfb-read`.

The authorised new hardware access is one 32-bit read at `BAR0+0x100CE0`.
`-tdtop-read` must remain absent. No MMU register, additional offset, polling
or write path is authorised. A failed FB boot must not be retried.


## 18. TuringProbe 0.4.0 FB-capacity hardware milestone

**[REAL-HARDWARE VERIFIED — PASS]**

- boot mode `-tdprobe -tdmmio-read -tdfb-read`;
- BAR0 read-only mapping created and explicitly released;
- mapping not retained after probe;
- exactly 3 identity reads and 1 FB read;
- total MMIO read count 4;
- PTOP read count 0;
- no MMU register was read;
- `BAR0+0x100CE0 = 0x00000307`;
- magnitude 48, scale 7, shift 27;
- decoded capacity `6442450944` bytes / `6144` MiB / 6 GiB;
- one-sixteenth reduction not active;
- decoded capacity matches the target board;
- PCI Command remained `0x0003`;
- Bus Master remained disabled;
- no PCI/MMIO writes, DMA, interrupts, firmware, power changes or user client;
- GOP remained 1920×1080 ARGB8888;
- runtime log ZIP SHA-256 `860d78a10bf50fe4e3da3a67d1c3ec936c6772aa25197000392b492e15e5599d`.

`system_profiler` still reports 8 MB because macOS is using the generic
GOP/IONDRV framebuffer rather than a functional NVIDIA graphics driver. That
display aperture is separate from the 6 GiB physical VRAM value decoded
directly from the TU116 FB register.

This closes the initial FB-capacity milestone. It does not prove that VRAM can
yet be allocated, mapped or accessed.

### Next gate

**[DESIGN/RESEARCH ONLY — NO NEW HARDWARE ACCESS AUTHORISED]**

The next candidate milestone is the first actual read-only MMU capability
inventory. Every proposed MMU offset must be justified from primary sources
and rejected if it can clear, acknowledge, invalidate, select an indexed
window, pop a queue, trigger work or otherwise have a read side effect.

Until that review, use `-tdprobe` only. Do not repeat `-tdfb-read`.


## 19. TuringProbe 0.5.0 offline MMU research

**[OFFLINE MODEL IMPLEMENTED — NO NEW HARDWARE ACCESS]**

A detailed source audit found no necessary static MMU capability register that
is clearly side-effect-free. The new MMU hardware whitelist is therefore
empty. The test EFI remains `-tdprobe` only.

Important correction: v0.4.0 source telemetry called page shift 16 a 16 KiB
page. That was incorrect; `1 << 16` bytes is 64 KiB. The 6 GiB FB-capacity
hardware result is unaffected because no MMU register or page table was used.

Version 0.5.0 adds:

- a pure software 4 KiB / 64 KiB TU102 page-table model;
- a derived 49-bit virtual-address hierarchy distinct from 47-bit DMA width;
- PTE/PDE/PD0/PDB encoding and decoding helpers;
- deterministic randomized round-trip and fail-closed tests;
- a register exclusion matrix for invalidate, fault-buffer and BAR window
  registers;
- corrected future MMU metadata properties.

No new boot argument, MMIO offset, MMIO write, DMA, interrupt, firmware,
reset, power, FIFO, channel, engine or user-client path is introduced.

### Completed in this research package

- independent cross-check against NVIDIA's open Turing UVM implementation;
- 4 KiB, 64 KiB and 2 MiB hierarchy support;
- byte-exact synthetic page-table images;
- 30,000 complete image build/walk round trips;
- logical-kind fallback correction and fail-closed compression policy.

### Next gate

Add fixed NVIDIA-derived golden vectors, multi-page/mixed-page conflict tests
and a CPU-only allocator/state-machine design. No hardware build or boot is
required. No MMIO write or new hardware offset is authorised.


## 20. TuringProbe 0.5.0 compiled research artifact

**[OFFLINE BUILD/BINARY AUDIT — PASS; NO HARDWARE BOOT]**

- source commit reported by artifact: `053519a6b32589c7828cf22679ad06265eb97edf`;
- Xcode 16.2, SDK 15.2, x86_64;
- Mach-O UUID `49C45C8E-33E4-3A74-931E-34F87072F0BF`;
- outer artifact SHA-256 `b97d725524513800d40c6dbcf3b9a15b1f61b7bee6534ff66ea92702820da2ba`;
- inner kext ZIP SHA-256 `25bb2bb49ed527e466b3e5d7f010d507ecef23b8d438cea4421abdbb7af63b27`;
- executable SHA-256 `013823b58797411048edc0fa99528036ca233a9126fb23efa66b67a842815b96`;
- compiled project symbol set is unchanged from v0.4.0;
- identity, PTOP and FB read helpers are unchanged from v0.4.0;
- no new MMU hardware accessor, PDB/BAR/TLB path or write path exists;
- corrected MMU values are static source metadata only: 49-bit VA, 4 KiB
  small pages and 64 KiB big pages;
- independent MMU-model and page-table-image suites passed again with zero
  device access.

The GitHub source-validation step omitted the two offline MMU model suites;
this is a CI coverage gap, not a binary defect. Add both suites to the next
workflow revision.

This release must not be installed merely because it compiled. A real-hardware
boot would produce no new evidence. Keep the verified test EFI on `-tdprobe`
only. No new MMIO offset or write is authorised.

## 21. TuringProbe 0.5.1 complete offline MMU validation

**[SOURCE IMPLEMENTED AND LOCALLY VALIDATED — NO HARDWARE BOOT]**

0.5.1 closes the CI and modelling gaps identified during the 0.5.0 artifact
audit.

Added:

- fixed source-derived golden vectors for VA, PTE, PDE and instance/PDB words;
- a deterministic multi-page address-space builder;
- 4 KiB, 64 KiB and 2 MiB range mappings;
- leaf, PD0 and 128 TiB root-index boundary tests;
- mixed 4 KiB/64 KiB PD0 halves;
- explicit physical-alias opt-in and virtual-overlap rejection;
- 512×4 KiB to 2 MiB promotion and exact demotion round-trip;
- transaction/evidence/timeout/rollback state machine;
- a single complete validation script used by GitHub Actions and tools/build.sh.

Validation results:

- 60,000 VA split/compose vectors;
- 60,000 randomized PTE/PDE vectors;
- 30,000 complete single-image build/walk vectors;
- 4 fixed PTE vectors including the maximum aligned 47-bit address;
- 12,025 sampled multi-page translations;
- all offline failure injection points roll back to the safe baseline;
- the first device-memory write remains explicitly blocked;
- zero MMIO and zero device access.

CI fixes:

- research/** and docs/** changes trigger the workflow;
- all MMU suites are mandatory before Xcode compilation;
- local and CI builds use the same validation entry point;
- unsupported kextutil -n invocation removed;
- manifest states mmu_hardware_whitelist=EMPTY.

The kext version is advanced for provenance, but no new hardware accessor,
boot argument, MMIO offset or write path is added. A 0.5.1 hardware boot is not
required or authorised.

### Next gate

Build 0.5.1 in GitHub Actions and audit the resulting Mach-O only to confirm
that the hardware symbol/read surface remains unchanged from 0.5.0/0.4.0 and
that the complete validation log is packaged. Do not install the kext in EFI.

After artifact audit, continue research on the first missing primitive: a
bounded, isolated memory-allocation and CPU write/readback design. No actual
VRAM allocation or write is authorised.

