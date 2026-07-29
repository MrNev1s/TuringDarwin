# Future MMU hardware transaction — design only

## Status

**NOT IMPLEMENTED. NOT AUTHORISED.**

This document defines the evidence required before the first MMU write. It is
not an instruction to program the GPU.

## Ordered phases

| Phase | Operation | Device write | Timeout | Current status |
|---|---|---:|---:|---|
| 0 | Confirm safe PCI-only baseline | No | — | Real-hardware proven |
| 1 | Allocate bounded CPU model | No | — | Offline proven |
| 2 | Build byte-exact page tables | No | — | Offline proven |
| 3 | Independently walk/verify tables | No | — | Offline proven |
| 4 | Allocate isolated device memory | Yes | 100 ms | Blocked |
| 5 | Write and read back tables | Yes | 100 ms | Blocked |
| 6 | Build/write isolated instance block | Yes | 100 ms | Blocked |
| 7 | Save original state and program PDB | Yes | 50 ms | Blocked |
| 8 | Issue bounded TLB invalidation | Yes | 2000 ms | Blocked |
| 9 | Verify one isolated translation | Yes | 100 ms | Blocked |
| 10 | Restore baseline and release memory | Yes | bounded | Blocked |

## Mandatory invariants

Before any hardware phase can be enabled:

- exact target match remains `10DE:2182 / 1043:8854`;
- stable EFI and physical recovery path exist;
- no production filesystem or display buffer is used;
- all allocations are bounded and recorded;
- original register/state values are captured before mutation;
- every write has an exact whitelist and expected readback mask;
- every poll has a finite timeout;
- every failure path invokes a reviewed inverse;
- Bus Master, DMA and interrupts remain disabled unless separately authorised;
- no engine is allowed to consume the new address space until translation
  verification has its own isolated design.

## First missing primitive

The project currently has no authorised way to allocate isolated VRAM and no
authorised CPU-to-VRAM write/readback path. Therefore the transaction stops at
Phase 3. PDB and invalidation work cannot be responsibly implemented before
that lower-level memory primitive exists.

## Why passive MMU probing is not substituted

The known TU102 MMU registers are operational: PDB selection, BAR windows,
invalidations, fault controls and status/polling. Reading arbitrary status does
not prove page-table format and may depend on active firmware or engine state.
The current empty whitelist is therefore intentional.
