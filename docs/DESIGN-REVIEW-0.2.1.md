# TuringProbe 0.2.1 — source design review

**Date:** 2026-07-29  
**Status:** source implemented and locally audited; not compiled; not booted.

## Entry condition

TuringProbe 0.1.1 passed its real-hardware PCI-only gate on the target TU116.
PCI Command remained `0x0003`, Bus Master Enable remained clear, the 16 MiB
BAR0 descriptor was confirmed, and GOP output remained stable.

## Implemented boundary

0.2.1 introduces one short-lived BAR0 mapping only when both `-tdprobe` and
`-tdmmio-read` are present. PCI-only mode with only `-tdprobe` remains
available in the same binary.

Before mapping, the code verifies:

- exact `10DE:2182 / 1043:8854` identity;
- `-tdoff` and `-tdunsafe` are absent;
- PCI memory decoding is already enabled;
- Bus Master Enable is clear;
- BAR0 is implemented, memory-space, 32-bit, non-prefetchable;
- the raw BAR0 base matches the existing IOPCIFamily descriptor;
- the descriptor is exactly 16 MiB and correctly aligned.

The mapping requests `kIOMapReadOnly`, is local to one lexical scope, and is
not retained. The code reads exactly three 32-bit offsets once each:

1. `0x000004` — `NV_PMC_BOOT_1`;
2. `0x000000` — `NV_PMC_BOOT_0`;
3. `0x101000` — `NV_PEXTDEV_BOOT_0_STRAP`.

The implementation rejects all-ones reads, unsupported big-endian mode, vGPU
bits, a non-TU116 BOOT0 chipset value, unknown crystal straps, any PCI Command
change, or any appearance of Bus Master Enable.

## Explicitly absent

- PCI writes;
- MMIO writes or writable mapping requests;
- loops or full BAR dumps;
- DMA buffers/commands;
- interrupts/MSI changes;
- firmware, reset, power, clock, fan, voltage, thermal, or display control;
- channels, FIFO, runlists, fences, Copy Engine, or command submission;
- IOUserClient, workloop, or command gate.

## Local verification completed

- `tools/safety-audit.py`: PASS;
- `tools/test-decoder-contract.py`: PASS;
- `tools/test-mmio-contract.py`: PASS;
- Python tool syntax: PASS;
- Info.plist parse/version: PASS;
- Xcode project structural references/version/compile gate: PASS;
- shell syntax for build/bootstrap/collector: PASS.

## Proof boundary

No Xcode compilation or live MMIO claim is made. The next gate is a GitHub
Actions build followed by static binary/import/disassembly review. Only after
that review may a separate test EFI be prepared, and the first 0.2.1 boot must
remain PCI-only before the BAR0 mode is attempted.
