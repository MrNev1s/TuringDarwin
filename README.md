# TuringDarwin / TuringProbe 0.4.0

`TuringProbe.kext` is a deliberately constrained research probe for the exact
ASUS GTX 1660 Ti board `10DE:2182 / 1043:8854`. It is not yet a graphics,
framebuffer, Metal, Vulkan, compute, display or power-management driver.

Read `PROJECT_STATE.md` first. It separates real-hardware results from source
work that has not yet been built or booted.

## Real-hardware baseline

TuringProbe 0.3.0 has passed PCI-only, identity-only and bounded PTOP tests on
macOS 15.7.7. It safely identified TU116 A1 and decoded ten advertised hardware
blocks while preserving PCI Command `0x0003`, disabled Bus Master and the GOP
framebuffer.

## 0.4.0 modes

- `-tdprobe`: PCI-only, no BAR mapping.
- `-tdprobe -tdmmio-read`: three verified TU116 identity reads.
- `-tdprobe -tdmmio-read -tdtop-read`: verified fixed 64-dword PTOP inventory.
- `-tdprobe -tdmmio-read -tdfb-read`: new candidate mode; three identity reads
  plus one read of `0x100CE0` to decode physical VRAM capacity.

Version 0.4.0 rejects simultaneous `-tdtop-read` and `-tdfb-read`.

The new FB mode publishes a source-backed TU102 MMU profile—47-bit DMA, 16 MMU
kinds, GP100 VMM class and 16 KiB default big pages—but does not read or modify
MMU control state.

## Safety boundary

There are no PCI/MMIO writes, DMA, interrupts, firmware, reset, power/clock/fan
control, FIFO/channels, engine commands, display programming or IOUserClient.
BAR0 uses `kIOMapReadOnly` and is explicitly released before `start()` returns.

## Build status

The 0.4.0 source passes local structural and contract tests. It has not been
compiled with Xcode and has not been run on hardware. Keep the verified 0.3.0
kext and `-tdprobe` in the test EFI until the 0.4.0 GitHub artifact is audited.

Expected GitHub artifact:

```text
TuringProbe-v0.4.0-Debug-x86_64
```
