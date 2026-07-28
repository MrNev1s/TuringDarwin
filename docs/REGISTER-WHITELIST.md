# Register whitelist

## v0.1

The GPU MMIO whitelist is empty.

The only permitted reads are PCI configuration-space fields and metadata from
IODeviceMemory descriptors already published by IOPCIFamily. No BAR is mapped.
No register offset in BAR0, BAR1, BAR2 or any other GPU aperture is authorised.

Any future whitelist change requires:

1. a cited hardware-source rationale;
2. an explicit read/write classification;
3. recovery and timeout analysis;
4. a separate source review and user approval.
