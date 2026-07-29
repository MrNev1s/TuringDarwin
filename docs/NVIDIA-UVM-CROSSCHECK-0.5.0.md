# NVIDIA UVM cross-check — Turing MMU model

## Scope

This cross-check compares the offline Nouveau-derived model against NVIDIA's
open `uvm_turing_mmu.c`. It performs no device access.

## Agreements

NVIDIA UVM confirms:

- 49 virtual-address bits;
- levels `48:47`, `46:38`, `37:29`, `28:21`;
- 4 KiB leaf index `20:12`;
- 64 KiB leaf index `20:16`;
- supported page sizes 4 KiB, 64 KiB and 2 MiB;
- 16-byte PD0 dual entries;
- low half = big/64 KiB, high half = small/4 KiB;
- 8-byte entries at other levels;
- PTE fields valid, aperture, volatile, privilege, read-only, atomic-disable,
  address and kind.

## Important model correction found during cross-check

The first draft encoded the caller's logical kind index directly into PTE bits.
That is not generally correct on the no-GSP path. Nouveau first applies the
TU102 16-entry kind map and falls back from compressed logical kinds to an
uncompressed hardware kind. The model now performs that translation and
rejects invalid kind 0x07 and all COMPTAGLINE/compression requests.

## Open questions kept blocked

- Which uncompressed kind should be used for the first experiment: Nouveau's
  default logical kind 0 or NVIDIA UVM's generic-memory hardware kind?
- Exact instance-block/PDB construction and allocation ownership on macOS.
- Safe BAR1/BAR2 window programming.
- TU102 TLB invalidation sequencing and rollback.
- Fault-buffer setup and firmware dependencies.

These are design questions only. No write code or hardware experiment is
included in 0.5.0.
