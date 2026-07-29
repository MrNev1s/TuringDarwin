# TuringDarwin / TuringProbe 0.7.0 host physical-segment staging

TuringProbe is a staged research kext for the exact ASUS TU116 target
`10DE:2182 / 1043:8854` on macOS Sequoia.

## Real-hardware milestones already passed

- exact PCI discovery and BAR inventory;
- TU116 identity and bounded PTOP topology;
- 6 GiB physical VRAM capacity discovery;
- isolated 12 KiB host-kernel allocation;
- 4096-byte CPU write/readback, canaries, zeroization and free.

## New 0.7.0 source candidate

`-tdprobe -tdhostphys-test` creates exactly one 4096-byte
`IOBufferMemoryDescriptor` with:

- kernel virtual mapping;
- 4096-byte alignment;
- system mapper disabled with `kIOMemoryMapperNone`;
- no I/O transfer direction;
- 64-byte prefix and suffix guards;
- 3968-byte deterministic CPU payload;
- one raw `getPhysicalSegment(0, ..., kIOMemoryMapperNone)` query;
- exact 4096-byte segment-length validation;
- page-alignment and TU116 47-bit range validation;
- full zeroization and explicit descriptor release.

It does not prepare a DMA transfer, create an `IODMACommand`, map the memory to
the GPU, program page tables/PDB/BARs, invalidate the TLB or submit commands.

Run the complete suite:

```bash
bash tools/run-offline-validation.sh
```

## Current gate

Build the complete 0.7.0 artifact and audit its Mach-O. Do not install or boot
`-tdhostphys-test` before the binary audit. Keep the real machine on
`-tdprobe` only.
