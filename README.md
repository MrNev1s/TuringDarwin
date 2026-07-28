# TuringDarwin / TuringProbe 0.2.1

`TuringProbe.kext` is the deliberately constrained diagnostic component for the
exact ASUS TU116 board `10DE:2182 / 1043:8854`. It is not a framebuffer,
accelerator, Vulkan, Metal, compute, power-management, or display driver.

Read [`PROJECT_STATE.md`](PROJECT_STATE.md) first. It is the canonical project
hand-off and separates real-hardware facts from source-only work.

## Verified baseline

`TuringProbe 0.1.1` is real-hardware verified on macOS 15.7.7 / Darwin 24G720:

- exact PCI match and active IORegistry service;
- PCI Command Register remained `0x0003` before and after the probe;
- Bus Master Enable remained clear;
- BAR0 is a 16 MiB, 32-bit, non-prefetchable MMIO aperture;
- GOP/IONDRV output remained stable at 1920×1080;
- no MMIO, DMA, interrupt, firmware, power, or user-client path was used.

## 0.2.1 scope

Version 0.2.1 adds the first **read-only BAR0 experiment**. It has two modes:

- `-tdprobe`: PCI-only compatibility mode; no BAR is mapped;
- `-tdprobe -tdmmio-read`: maps only BAR0 with `kIOMapReadOnly`, reads exactly
  three fixed 32-bit registers once each, then explicitly releases the mapping before
  `start()` completes.

The three authorised offsets are:

| Offset | Register | Purpose |
|---:|---|---|
| `0x000004` | `NV_PMC_BOOT_1` | endian/vGPU sanity gate |
| `0x000000` | `NV_PMC_BOOT_0` | TU116 chipset and revision |
| `0x101000` | `NV_PEXTDEV_BOOT_0_STRAP` | crystal strap decode |

No PCI or MMIO write primitive exists in the new module. There is no full BAR
dump, loop, DMA allocation, bus-master change, interrupt registration, firmware
loading, reset, power control, display control, or IOUserClient.

Fail-closed controls:

- `-tdoff` always disables attachment;
- `-tdprobe` is always required;
- `-tdmmio-read` is required only for the BAR0 path;
- `-tdunsafe` is rejected;
- exact device/subsystem IDs, BAR type/base/size, memory decoding, and disabled
  bus mastering are all checked before mapping.

## Build status

The source passes local structural audits and contract tests. It has **not yet
been compiled by Xcode or run on the target GPU**. Do not place
`-tdmmio-read` in an EFI until the GitHub-built artifact has been uploaded and
statically audited.

The workflow pins:

- Xcode 16.2;
- macOS SDK 15.2;
- `x86_64`;
- MacKernelSDK commit
  `05094e5e88cec7caedbfb35e8449ed0db94bf95b`.

Run **Build TuringProbe kext** with `Debug`. Expected artifact:

```text
TuringProbe-v0.2.1-Debug-x86_64
```
