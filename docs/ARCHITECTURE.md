# Architecture: milestone 0.1

## Kernel component

`TuringProbe` matches the exact primary and secondary PCI IDs in Info.plist and
re-verifies all four IDs in `start()` before calling `super::start()` or
publishing any data.

Modules:

- `TuringProbe.cpp`: boot-argument gates and service lifecycle.
- `PCIConfig.cpp`: identity, fixed PCI header fields, and 256-byte snapshot.
- `CapabilityParser.cpp`: bounded conventional and extended capability walks.
- `BARInspector.cpp`: raw BAR decoding and already-published IODeviceMemory
  descriptors, without mapping them.
- `Logging.hpp`: one bounded kernel-log prefix.

There is no user client in v0.1. All output is read from IORegistry and the
unified log. There is no workloop, command gate, interrupt source, DMA object,
BAR map, firmware handler or display interface because none is required for a
read-only PCI probe.

## Future module boundaries

MMIO, firmware, memory management, channel/FIFO, interrupts, command submission,
display and user-client code must be implemented as separate later modules.
No future stage is authorised by this repository.
