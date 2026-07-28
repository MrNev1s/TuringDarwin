# TuringProbe 0.3.0 — Read-only BAR0 MMIO gate

Status: **source implemented; build and real-hardware gates remain pending**.

## Entry evidence

TuringProbe 0.1.1 passed on macOS 15.7.7 / Darwin 24G720. PCI Command
remained `0x0003`, Bus Master Enable remained clear, BAR0 was 16 MiB, and GOP
output remained stable.

## Gates

BAR0 mapping occurs only when all of these are true:

1. build-time `TURINGPROBE_ENABLE_MMIO_READ=1`;
2. boot argument `-tdprobe`;
3. boot argument `-tdmmio-read`;
4. exact `10DE:2182 / 1043:8854` identity;
5. `-tdoff` and `-tdunsafe` are absent;
6. PCI memory decoding is enabled and bus mastering is disabled;
7. BAR0 and its IOPCIFamily descriptor pass exact type/base/length checks.

With only `-tdprobe`, v0.3.0 remains in PCI-only compatibility mode and maps no
BAR. This permits a safe diagnostic fallback without changing the kext.

## Mapping lifetime

- BAR0 descriptor is obtained only by PCI register `0x10`.
- `IOMemoryDescriptor::map(kIOMapReadOnly)` is used.
- No cache policy override is requested.
- The mapping exists only in a local scope.
- Exactly three fixed reads occur.
- The `IOMemoryMap *` is explicitly released and cleared before the service registers.
- No mapping or virtual address is stored in the service object.

## Whitelist

- `0x000004` — `NV_PMC_BOOT_1`;
- `0x000000` — `NV_PMC_BOOT_0`;
- `0x101000` — `NV_PEXTDEV_BOOT_0_STRAP`.

See `REGISTER-WHITELIST.md` for source rationale and rejection policy.

## Non-goals

No PCI/MMIO writes, full BAR dump, PRAMIN, VRAM, ROM toggles, DMA, buffers,
interrupts, firmware, FIFO, channels, runlists, fences, reset, display control,
power management, clocks, fans, voltage, or user client.

## Acceptance criteria

- GitHub build succeeds with pinned Xcode 16.2 / SDK 15.2 / MacKernelSDK;
- binary audit finds exactly the intended mapping/read call sites and no writes;
- macOS boots from the test EFI with `-tdprobe -tdmmio-read`;
- BOOT0 identifies TU116 (`0x168`);
- BOOT1 and strap values are plausible;
- PCI Command is unchanged and bus mastering remains disabled;
- mapping is released before `start()` completes;
- GOP image, resolution, fans, and system stability are unchanged.

## 0.4.0 FB/MMU profile gate

The next candidate adds one static read at `0x100CE0`, using the decoder from
Nouveau `gp102_fb_vidmem_size()`. The result must decode to exactly 6 GiB on the
exact target board. TU102 MMU constants are published as source-only metadata;
no MMU control, fault, invalidate or page-table register is accessed.
