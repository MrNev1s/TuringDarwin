# TU102/TU116 page-table format notes

This document is a concise engineering reference for the offline model. The
full evidence discussion and safety boundary are in `MMU-RESEARCH-0.5.0.md`.

## Supported leaf sizes

- small page: shift 12, 4096 bytes;
- large page: shift 16, 65536 bytes;
- huge/direct PD0 page: shift 21, 2097152 bytes.

## Common 49-bit VA split

The 4 KiB and 64 KiB leaf tables each cover 2 MiB. A 2 MiB mapping terminates
directly in the low half of PD0. All paths resolve a 49-bit virtual address.

## Descriptor arrays reconstructed from Nouveau

```text
gp100_vmm_desc_12:
  SPT bits=9 size=8  align=0x1000
  PD0 bits=8 size=16 align=0x1000
  PD1 bits=9 size=8  align=0x1000
  PD2 bits=9 size=8  align=0x1000
  ROOT bits=2 size=8 align=0x1000

gp100_vmm_desc_16:
  LPT bits=5 size=8  align=0x0100
  PD0 bits=8 size=16 align=0x1000
  PD1 bits=9 size=8  align=0x1000
  PD2 bits=9 size=8  align=0x1000
  ROOT bits=2 size=8 align=0x1000
```

## Direct 2 MiB leaf

For page shift 21, PD0 is no longer a pointer to an LPT/SPT. Its low 64-bit
half contains the PTE itself and the high half is zero. This path is modelled
offline but is not selected for a first hardware experiment.

## First conservative mapping profile for future work

This is a design target, not an authorised hardware operation:

- page size: 4 KiB first;
- physical target: VRAM only;
- kind: uncompressed; exact logical/hardware kind choice still unresolved;
- valid: true;
- privileged: false;
- read-only initially true;
- atomic operations disabled;
- one page only;
- no sparse PTE;
- no fault replay;
- no compression/comptags;
- no system-memory aperture;
- no large-page path until small-page image tests pass.

This intentionally minimizes the number of independent mechanisms exercised
by a future hardware experiment.

## PD0 half ordering

The 128-bit PD0 entry follows Nouveau's `pt[0]` / `pt[1]` ordering:

- bytes 0..7: LPT / 64 KiB table PDE;
- bytes 8..15: SPT / 4 KiB table PDE.

This ordering matters even when only one leaf size is populated.
