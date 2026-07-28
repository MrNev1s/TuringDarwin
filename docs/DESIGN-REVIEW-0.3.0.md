# TuringProbe 0.3.0 design review — bounded PTOP inventory

Date: 2026-07-29
Status: source implemented and locally audited; not Xcode-built; not hardware-authorised

## Purpose

Version 0.3.0 preserves every v0.2.1 safety invariant and adds one optional,
source-backed read-only inventory of the GPU PTOP device table.

TU116 is wired to Nouveau's `gk104_top_new` implementation. That parser reads
exactly 64 32-bit words beginning at BAR0 offset `0x022700` and decodes DATA,
ENUM and ENGINE_TYPE records. The TuringProbe implementation mirrors the same
finite table extent and bitfields.

Primary implementation references:

- Linux Nouveau `engine/device/base.c`, TU116 `nv168_chipset`: uses
  `gk104_top_new` and `gm107_fuse_new`.
- Linux Nouveau `subdev/top/gk104.c`, `gk104_top_parse`: fixed 64-word walk at
  `0x022700 + i*4` and record bitfields.

## Boot modes

- `-tdprobe`: PCI-only compatibility mode.
- `-tdprobe -tdmmio-read`: three-register identity mode, unchanged from 0.2.1.
- `-tdprobe -tdmmio-read -tdtop-read`: identity gate plus the fixed 64-word
  PTOP inventory.

`-tdtop-read` without `-tdmmio-read` fails closed. `-tdunsafe` remains rejected.

## MMIO contract

The expanded mode performs exactly 67 32-bit reads:

1. three real-hardware-verified identity reads;
2. 64 consecutive PTOP words at `0x022700..0x0227fc`.

There is no polling, retry loop, delay, indexed window, interrupt read,
read-to-clear register, or arbitrary offset input. BAR0 is mapped once with
`kIOMapReadOnly` and the `IOMemoryMap` is explicitly released before return.

## Output

The kext publishes the raw 256-byte TOP table plus structured device records:
raw type, translated name, instance, PRI address, fault, engine, runlist,
interrupt and reset identifiers, together with validity/count telemetry.

## Prohibited

No PCI/MMIO writes, DMA, bus-master enable, interrupts, firmware, reset,
power/clock/fan/voltage control, FIFO/channels/Copy Engine commands, display
programming, IOUserClient, user-selected offsets, or persistent mapping.

## Hardware gate

No hardware boot is authorised until GitHub Actions produces the 0.3.0 Mach-O
and a binary call-site audit confirms one read-only mapping, explicit release,
three identity reads, one fixed 64-iteration TOP loop, and zero write paths.
The first real-hardware boot must again be PCI-only.
