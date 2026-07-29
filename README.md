# TuringDarwin / TuringProbe 0.5.1 MMU research

TuringProbe is a staged research kext for the exact ASUS TU116 target
`10DE:2182 / 1043:8854` on macOS Sequoia.

## Verified real-hardware milestones

- exact PCI discovery and BAR inventory;
- three-register TU116 identity;
- bounded 64-dword PTOP topology inventory;
- one-register physical VRAM capacity decode: 6 GiB.

## Current 0.5.1 work

Version 0.5.1 is an **offline MMU correctness and CI release**. It adds no new
MMIO offset, boot argument, write path, DMA path, interrupt path, firmware path,
or user client.

New offline coverage:

- fixed source-derived golden vectors;
- deterministic multi-page address-space builder;
- 4 KiB, 64 KiB and 2 MiB mappings;
- leaf, PD0 and root-index boundary crossings;
- mixed 4 KiB/64 KiB PD0 halves;
- overlap and alias policy;
- 4 KiB ↔ 2 MiB promotion/demotion;
- transaction and rollback state machine;
- complete validation suite wired into GitHub Actions and `tools/build.sh`.

Run everything with:

```bash
bash tools/run-offline-validation.sh
```

Read:

- `docs/MMU-RESEARCH-0.5.1.md`
- `docs/MMU-PAGE-TABLE-FORMAT.md`
- `docs/MMU-HARDWARE-TRANSACTION-0.5.1.md`
- `docs/MMU-ROLLBACK-MATRIX-0.5.1.md`
- `docs/MMU-REGISTER-EXCLUSION.md`

## Hardware policy

Keep the verified test EFI on `-tdprobe` only. Do not install 0.5.1 merely
because it compiles: the kext hardware interface is unchanged from 0.4.0 and a
boot would produce no new MMU evidence.

No MMU register read, VRAM allocation, page-table write, PDB programming,
BAR1/BAR2 programming, TLB invalidation, DMA, channel, FIFO, Copy Engine, or
command submission is authorised.
