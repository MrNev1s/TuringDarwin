# First device-memory write gate — still blocked

The 0.6.0 host-memory test writes only ordinary CPU-addressable kernel RAM.
It does not authorize any write to VRAM, BAR1/BAR2, MMU registers, page-table
memory visible to the GPU, or an instance block.

A future first device-memory write requires all of the following evidence:

1. exact ownership of the destination allocation;
2. exact physical-address provenance;
3. confirmation that the range is not firmware, framebuffer, GOP or existing
   driver state;
4. a fixed byte count no larger than one 4 KiB page;
5. prefix and suffix canaries outside the payload;
6. independent readback through a separately audited path;
7. cache-policy and flush semantics;
8. timeout and failure telemetry;
9. zeroization and release;
10. a recovery route that does not require retrying the failed operation.

Until every item is proven, `device_memory_write_whitelist=EMPTY` remains
mandatory.
