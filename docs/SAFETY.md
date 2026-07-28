# Safety contract for TuringProbe 0.1

## Required gates

- The driver attaches only when `-tdprobe` is present.
- `-tdoff` always prevents attachment.
- `-tdmmio-read` and `-tdunsafe` are rejected by this source version.
- Identity must be exactly `10DE:2182`, subsystem `1043:8854`.

## Guaranteed absent from the source tree

- PCI configuration writes
- changes to PCI command bits
- BAR mappings or dereferences
- I/O-space writes
- DMA allocation or mapping
- bus mastering changes
- firmware or VBIOS execution/loading
- interrupt registration
- GPU command submission
- power-state, clocks, voltage, fan or power-limit changes
- display mode changes

`tools/safety-audit.py` fails when prohibited primitives appear in `kext/` or
`include/`. This is a static guard, not proof of runtime correctness.

## Test topology

Keep the known-good EFI untouched. Test only from a copied EFI on a separate
USB device. Retain physical access to the power button and BIOS boot menu.
Never place the experimental kext in `/Library/Extensions` or the system volume.
