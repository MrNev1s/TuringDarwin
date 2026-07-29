# TuringProbe 0.6.0 — isolated host-memory self-test

## Status

**SOURCE IMPLEMENTED; NOT BUILT; NOT BOOTED.**

This is the first new runtime primitive after the MMU model. It intentionally
uses ordinary wired kernel memory only. It does not allocate VRAM, obtain a
physical address, create a memory descriptor, enable DMA, or touch any GPU
register.

## Exact runtime mode

```text
-tdprobe -tdhostmem-test
```

The mode is rejected when `-tdmmio-read` is present. Therefore identity, PTOP,
FB and host-memory experiments cannot run in the same boot.

## Exact allocation

```text
alignment:       4096 bytes
prefix canary:   4096 bytes, value 0xA5
payload:         4096 bytes
suffix canary:   4096 bytes, value 0x5A
total:          12288 bytes
```

The source uses one `IOMallocAligned(12288, 4096)` call and one matching
`IOFreeAligned(..., 12288)` call. Apple XNU documents `IOMallocAligned` as a
wired kernel allocation with a byte-alignment restriction and requires the
same allocation size when freeing it with `IOFreeAligned`.

Primary source:
`apple-oss-distributions/xnu/iokit/IOKit/IOLib.h`.

## Sequence

1. Allocate one page-aligned 12 KiB host buffer.
2. Explicitly clear and verify all bytes.
3. Fill prefix/suffix canaries.
4. Write a deterministic 4096-byte payload with the CPU.
5. Read every byte back and compare it.
6. Compute FNV-1a-64; expected value `0xACAC786CC2682325`.
7. Verify both guard pages are unchanged.
8. Zero and verify the payload.
9. Recheck both guards.
10. Zero and verify the entire 12 KiB allocation.
11. Free it and clear every local pointer.

Any mismatch causes attachment failure, but cleanup still runs.

## Deliberate exclusions

- no `IOBufferMemoryDescriptor`;
- no `IOMemoryDescriptor`;
- no `IODMACommand`;
- no physical-address query;
- no contiguous allocation;
- no `prepare()` / `complete()`;
- no GPU-visible mapping;
- no MMIO or PCI write;
- no device-memory write.

## Proof boundary

A successful runtime test will prove that the kext can own, bound, verify,
zeroize and release one aligned kernel buffer. It will not prove that the
buffer is visible to the GPU or suitable for page tables. That requires a
separate physical-address and mapping gate later.
