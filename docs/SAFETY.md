# Safety contract for TuringProbe 0.2.1

## Runtime gates

- exact identity must be `10DE:2182`, subsystem `1043:8854`;
- `-tdoff` always prevents attachment;
- `-tdprobe` is always required;
- BAR0 access additionally requires `-tdmmio-read`;
- `-tdunsafe` is always rejected;
- Bus Master Enable must be clear before mapping and remain clear afterward;
- PCI memory decoding must already be enabled; the kext never changes it;
- BAR0 must exactly match the real-hardware-verified 16 MiB 32-bit,
  non-prefetchable aperture and its IOPCIFamily descriptor.

## Authorised MMIO operation

Only `MMIOReadOnly.cpp` may create a mapping. It requests `kIOMapReadOnly`,
uses one checked 32-bit read primitive, performs exactly three fixed reads, and
releases the local mapping before returning.

## Guaranteed absent from the implemented source path

- PCI configuration writes;
- MMIO writes or a writable mapping request;
- full BAR scanning or hardware polling loops;
- bus-master, memory-enable, or I/O-enable changes;
- DMA allocation, mapping, or submission;
- interrupt registration or MSI/MSI-X changes;
- firmware/VBIOS loading or execution;
- reset, power, clock, voltage, fan, thermal, or power-limit control;
- GPU channels, FIFO, runlists, fences, Copy Engine commands;
- display/modeset/framebuffer changes;
- IOUserClient, workloop, or command gate.

`tools/safety-audit.py` is a static source guard, not proof of runtime safety.
The GitHub artifact still requires disassembly/import audit, and hardware use is
split into PCI-only then BAR0-read gates.

## Recovery topology

Keep the known-good EFI untouched. Test only from a copied EFI, retain physical
access to power/reset and BIOS boot selection, and never store the only copy of
important data on the test volume.
