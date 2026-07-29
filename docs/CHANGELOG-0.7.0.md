# Changelog 0.7.0

- Added isolated `-tdhostphys-test` mode.
- Added exactly one 4096-byte `IOBufferMemoryDescriptor` allocation.
- Added `kIOMemoryMapperNone` to suppress the system mapper.
- Added no-direction, no-prepare, no-complete descriptor policy.
- Added 64-byte prefix/suffix guards and 3968-byte CPU payload.
- Added deterministic CPU write/readback and checksum verification.
- Added exactly one raw `getPhysicalSegment` query at offset zero.
- Added exact one-page length, page alignment and 47-bit range checks.
- Added full descriptor zeroization and explicit raw-pointer release.
- Added 50,000 randomized physical-segment validation vectors.
- Added source contracts excluding DMA, mapper, GPU and device-memory paths.
- Kept all device-memory, PDB, BAR and TLB write whitelists empty.
