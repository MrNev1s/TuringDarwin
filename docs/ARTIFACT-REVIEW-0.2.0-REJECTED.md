# TuringProbe 0.2.0 artifact review — REJECTED FOR BOOT

Date: 2026-07-29

## Artifact identity

- outer GitHub artifact SHA-256: `9946e750ff7020ef698cfdc89d721a9467dc151ee3a601557956017623d002d6`;
- inner kext ZIP SHA-256: `4377760f54fb1d2853f47e8c18de90af65f1b078147e3c717d2184fa4636ff5b`;
- Mach-O executable SHA-256: `ca7212ebdf6d004c85687e725102cb72cde373971c4b997faee0e1ba4a8e7654`;
- Info.plist SHA-256: `35a10d0c9862e2dc87bb599a0ab6c4c9a89573007d158e28d1226a7caad8a757`;
- Mach-O UUID: `B944891C-88CB-37E8-8171-842AA1F47D81`;
- source commit: `89b752805cc87032e9b7dc8cb3c990ac4fb66f2b`;
- build result: `BUILD SUCCEEDED`.

## What passed

- exact PCI/subsystem matching;
- x86_64 Mach-O structure;
- `kIOMapReadOnly` requested;
- exactly three fixed MMIO reads at `0x4`, `0x0`, and `0x101000`;
- no MMIO-write primitive or PCI-config write call site;
- no DMA, interrupt, firmware, power, or user-client implementation.

## Blocking defect

The source used `auto mapping = descriptor->map(kIOMapReadOnly)` and assumed that
leaving the local scope would destroy the mapping. In this third-party C++14
build, `OSPtr<T>` is a raw `T*` because the experimental shared-pointer API is
not enabled. Binary disassembly confirms that no release call is emitted for the
returned `IOMemoryMap`. Therefore the BAR0 mapping is retained/leaked and the
property `TPBAR0MappingReleased` would report a false success.

This is not an MMIO write and does not prove GPU corruption, but it violates the
project's short-lived mapping contract. The 0.2.0 artifact must not be placed in
a test EFI or booted.

## Resolution

Version 0.2.1 uses an explicit `IOMemoryMap *`, calls `mapping->release()` on
every path after a successful mapping, clears the pointer, and publishes the
actual release state. It must be rebuilt and audited before any hardware test.
