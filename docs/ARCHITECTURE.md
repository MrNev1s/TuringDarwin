# Architecture: TuringProbe 0.5.1

## Kernel boundary

The compiled kext still has the same hardware-facing modules as 0.4.0:

- exact PCI match and bounded capability parsing;
- BAR metadata inspection;
- short-lived `kIOMapReadOnly` BAR0 mapping;
- three fixed identity reads;
- optional historical bounded PTOP table read;
- optional historical one-register VRAM capacity read.

0.5.1 adds no MMU accessor, no new boot argument and no write path.

## Offline boundary

The MMU work is outside the Xcode project and runs as ordinary Python:

- format model;
- single-image builder/walker;
- multi-page address-space builder/walker;
- fixed golden vectors;
- transaction/rollback plan.

The safety audit rejects IOKit, MMIO, device, process and network access tokens
inside the offline research modules and rejects their inclusion in the Xcode
project.

## Validation architecture

`tools/run-offline-validation.sh` is the only complete validation entry point.
GitHub Actions and `tools/build.sh` both invoke it, preventing local/CI drift.

The pipeline order is:

```text
safety audit
→ legacy PCI/MMIO/PTOP/FB contracts
→ randomized MMU model
→ byte-exact image model
→ fixed golden vectors
→ multi-page address space
→ transaction/rollback model
→ syntax/plist checks
→ Xcode build
```

## Failure behavior

All kernel paths remain fail-closed and release the BAR0 mapping. All offline
builders reject misalignment, address overflow, invalid kinds, compression,
virtual overlap, accidental physical aliasing, corrupt table chains and
unproven transaction inverses.

## Hardware eligibility

The transaction model stops before `stage-tables-in-device-memory`. No
isolated VRAM allocator or CPU write/readback inverse exists, so all later MMU
phases remain ineligible.
