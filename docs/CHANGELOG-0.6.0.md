# Changelog 0.6.0

- Added isolated `-tdhostmem-test` mode.
- Added one 12 KiB, 4 KiB-aligned wired host-memory allocation.
- Added deterministic 4096-byte CPU write/readback.
- Added 4 KiB prefix and suffix canaries.
- Added FNV-1a-64 checksum verification.
- Added payload and full-allocation zeroization verification.
- Added exact matching free and pointer clearing.
- Added host-memory Python model with 50,000 randomized bounded writes.
- Added source contract preventing descriptors, physical-address queries,
  DMA, device memory and GPU register access.
- Kept `mmu_hardware_whitelist=EMPTY`.
- Added `device_memory_write_whitelist=EMPTY`.
