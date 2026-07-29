# Host physical-segment gate 0.7.0

## Purpose

Establish the first descriptor-backed host-memory primitive that exposes both a
CPU virtual pointer and one raw host physical address without involving the GPU.

## Exact allocation

```text
IOBufferMemoryDescriptor::withOptions(
    kIODirectionNone | kIOMemoryMapperNone,
    4096,
    4096)
```

`IOBufferMemoryDescriptor` is the XNU allocation class intended for memory that
may later participate in I/O or mappings. This gate disables the system mapper,
does not request physically-contiguous multi-page memory, and allocates only one
page.

## Layout

```text
0x000–0x03F  prefix canary, 64 bytes, 0xC3
0x040–0xFBF  payload, 3968 bytes
0xFC0–0xFFF  suffix canary, 64 bytes, 0x3C
```

Payload formula:

```text
byte[i] = (i * 131 + 0x5D) & 0xFF
FNV-1a-64 = 0xBB8BA5B0A94B2525
```

## One permitted physical query

```text
getPhysicalSegment(0, &length, kIOMemoryMapperNone)
```

Acceptance requires:

- address is nonzero;
- address is 4096-byte aligned;
- returned segment length is exactly 4096;
- the entire segment lies below `2^47`;
- CPU readback, checksum and both canaries are valid.

## Cleanup

- zero payload;
- verify canaries remain unchanged;
- zero the complete descriptor page;
- verify complete zeroization;
- call `descriptor->release()` exactly once;
- clear every derived pointer.

## Explicitly absent

- `prepare()` / `complete()`;
- `IODMACommand`;
- `IOMapper` or system IOMMU mapping;
- GPU-visible address;
- VRAM or BAR access;
- live page tables or PDB;
- TLB invalidation;
- interrupts, firmware or commands.

## Status

Source implemented and offline-tested. Hardware boot is prohibited until the
compiled artifact and Mach-O are audited.

## Primary XNU references

- `IOBufferMemoryDescriptor.h` documents `withOptions`, alignment, mapper and
  ownership semantics:
  https://raw.githubusercontent.com/apple-oss-distributions/xnu/main/iokit/IOKit/IOBufferMemoryDescriptor.h
- `IOMemoryDescriptor.h` documents raw physical segments and
  `kIOMemoryMapperNone`:
  https://raw.githubusercontent.com/apple-oss-distributions/xnu/main/iokit/IOKit/IOMemoryDescriptor.h
- `IOBufferMemoryDescriptor.cpp` shows the wired kernel allocation path and
  that `kIOMemoryMapperNone` prevents use of the system mapper:
  https://raw.githubusercontent.com/apple-oss-distributions/xnu/main/iokit/Kernel/IOBufferMemoryDescriptor.cpp
