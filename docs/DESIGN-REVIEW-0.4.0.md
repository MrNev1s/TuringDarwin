# TuringProbe 0.4.0 design review — FB capacity / MMU source profile

## Status

**SOURCE IMPLEMENTED, NOT BUILT, NOT AUTHORISED FOR HARDWARE.**

Version 0.4.0 preserves every verified 0.3.0 mode and adds one separately gated
read-only framebuffer-memory inventory mode:

```text
-tdprobe -tdmmio-read -tdfb-read
```

`-tdfb-read` requires `-tdmmio-read`. Version 0.4.0 rejects simultaneous
`-tdtop-read` and `-tdfb-read`, so each expanded inventory remains isolated.

## New hardware read

Exactly one new 32-bit read is permitted:

| Offset | Source path | Purpose |
|---:|---|---|
| `0x100CE0` | Nouveau `gp102_fb_vidmem_size()` used by TU102/TU116 | encoded physical VRAM capacity |

The decoder follows Nouveau exactly:

- magnitude: bits `9:4`;
- scale: bits `3:0`;
- nominal bytes: `magnitude << (scale + 20)`;
- when bit `30` is set, usable size is reduced to `15/16`.

For this exact board the gate accepts only a valid decode equal to 6 GiB. An
unexpected value causes the kext to release the mapping and refuse attachment.

## MMU profile is source metadata, not MMIO

The following properties are published from Nouveau's static `tu102_mmu`
architecture definition. They do not cause hardware reads:

- DMA address width: 47 bits;
- MMU class: GF100;
- memory class: GF100;
- VMM class: GP100;
- 16-entry kind map;
- invalid kind: `0x07`;
- system-memory kinds supported;
- TU102/TU116 default big page: 16 KiB.

No MMU control, fault, invalidate, page-table, replay, or interrupt register is
read by this version.

## Preserved safety properties

- exact `10DE:2182 / 1043:8854` matching;
- `-tdprobe` required;
- `-tdunsafe` rejected;
- BAR0 must remain the verified 16 MiB non-prefetchable aperture;
- Bus Master must be disabled;
- dedicated compile-time gate `TURINGPROBE_ENABLE_FB_READ=1`;
- mapping requested with `kIOMapReadOnly`;
- one read of `0x100CE0`, no loop and no polling;
- mapping explicitly released and pointer cleared;
- PCI Command checked before mapping, after mapping, after reads, and after the
  complete probe;
- no PCI/MMIO writes, DMA, interrupts, firmware, reset, power, clocks, fans,
  voltage, FIFO, channels, engine commands, display programming or user client.

## Proof boundary

This stage can establish the hardware-reported VRAM capacity encoding and record
a source-backed MMU architecture profile. It does not initialise the MMU,
inspect page tables, allocate VRAM, map GPU virtual addresses, submit commands,
or prove that any memory engine is usable.

## Required gates

1. GitHub Actions Xcode build.
2. Mach-O audit: exactly three identity-read calls and one FB-read call in FB
   mode, no additional MMIO accessor or write call sites.
3. PCI-only hardware boot with `-tdprobe`.
4. Identity-only hardware boot with `-tdprobe -tdmmio-read`.
5. One controlled FB test with `-tdprobe -tdmmio-read -tdfb-read`.

No 0.4.0 boot is authorised before the compiled artifact audit.
