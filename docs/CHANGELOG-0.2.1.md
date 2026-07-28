# TuringProbe 0.2.1

## Added

- compile-time `TURINGPROBE_ENABLE_MMIO_READ=1` gate;
- runtime `-tdmmio-read` gate in addition to `-tdprobe`;
- exact BAR0 type/base/size/descriptor validation;
- short-lived `kIOMapReadOnly` BAR0 mapping;
- three-register source-backed whitelist;
- TU116 BOOT0 validation, BOOT1 endian/vGPU rejection, strap crystal decode;
- PCI Command snapshots before mapping, after mapping, and after reads;
- mapping-lifetime and MMIO telemetry in IORegistry;
- source audit and contract test specific to the MMIO boundary.

## Preserved safety boundaries

- no PCI writes;
- no MMIO writes;
- no DMA or DMA-capable buffer allocation;
- no interrupts, firmware, power state, reset, display control, or user client;
- no retained BAR mapping;
- no hardware-driven loops and no full aperture dump.

## Verification status

Source checks can run off-target. Compilation and hardware testing are not yet
claimed until the GitHub artifact and target logs are reviewed.

## Critical ownership correction

- rejected the compiled 0.2.0 artifact before hardware use;
- replaced implicit `OSPtr<IOMemoryMap>` scope assumptions with explicit raw-pointer ownership;
- added one mandatory `mapping->release()` and pointer clearing;
- release telemetry now reflects the actual release state;
- safety and contract tests fail if explicit release is removed.
