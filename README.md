# TuringDarwin / TuringProbe 0.6.0 host-memory staging

TuringProbe is a staged research kext for the exact ASUS TU116 target
`10DE:2182 / 1043:8854` on macOS Sequoia.

## Verified GPU milestones

- exact PCI discovery and BAR inventory;
- TU116 identity;
- bounded PTOP topology;
- 6 GiB physical VRAM capacity.

## New 0.6.0 runtime candidate

`-tdprobe -tdhostmem-test` performs one isolated CPU-only write/readback in
ordinary aligned kernel memory:

- 4 KiB prefix canary;
- 4 KiB payload;
- 4 KiB suffix canary;
- deterministic checksum;
- payload zeroization;
- full-allocation zeroization;
- exact free.

It performs no MMIO, physical-address query, descriptor creation, DMA, GPU
mapping, VRAM access or device-memory write.

Run all source and offline tests:

```bash
bash tools/run-offline-validation.sh
```

## Current gate

Build the complete 0.6.0 artifact and audit its Mach-O. Do not install it before
that audit. The currently verified EFI remains `-tdprobe` only.
