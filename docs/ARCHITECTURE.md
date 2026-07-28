# Architecture: TuringProbe 0.2.0

## Service lifecycle

`TuringProbe` matches the exact primary and subsystem PCI IDs in `Info.plist`
and repeats the four-ID verification in `start()`.

Two runtime modes share one binary:

- PCI-only compatibility mode: `-tdprobe`;
- BAR0 read-only mode: `-tdprobe -tdmmio-read`.

`-tdoff` disables the service and `-tdunsafe` is rejected.

## Modules

- `TuringProbe.cpp`: boot gates, exact target verification, service lifecycle,
  PCI Command invariants, mode selection, and final IORegistry status.
- `PCIConfig.cpp`: identity, fixed PCI header fields, conventional config
  snapshot, and registry paths.
- `CapabilityParser.cpp`: bounded conventional/extended capability walks and
  read-only ReBAR decoding.
- `BARInspector.cpp`: raw BAR classification and existing IODeviceMemory
  metadata; it does not map BARs.
- `MMIOReadOnly.cpp`: the only mapping module. It validates BAR0, requests a
  short-lived read-only mapping, executes the three-register whitelist, checks
  PCI Command state, publishes results, and retains no mapping.
- `TuringRegisters.hpp`: immutable whitelist offsets and decode constants.
- `Logging.hpp`: bounded log prefix.

There is no IOUserClient, DMA object, interrupt source, firmware handler,
display interface, workloop, or command gate.

## Failure behavior

Any identity, BAR, descriptor, mapping, register, or PCI Command inconsistency
causes `start()` to fail closed. The PCI device retain is released and the
service does not register. No recovery write or reset is attempted.

## Future boundaries

Firmware, memory management, GPU VM, channels/FIFO, interrupts, command
submission, display, and userspace APIs remain separate future modules. Nothing
in 0.2.0 authorises their implementation or hardware use.
