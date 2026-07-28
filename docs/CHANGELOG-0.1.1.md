# TuringProbe 0.1.1 changes

Status: source complete; Xcode build and target boot still required.

- Preserve PCI-only read scope and fail-closed boot arguments.
- Pin MacKernelSDK to the commit used by the successful 0.1.0 build.
- Publish raw 32-bit PCI values as unsigned 64-bit OSNumbers.
- Add human-readable capability names.
- Decode all bounded Resizable BAR entries and supported sizes.
- Record PCI Command Register and bus-master state before and after probing.
- Add explicit probe-completed, schema, version, and boot-mode properties.
- Add canonical `PROJECT_STATE.md` and `PROJECT_STATE.json`.
- Add a decoder contract test using the real TU116 ReBAR values captured by
  version 0.1.0.
- No MMIO, DMA, interrupts, firmware, power-state or user-client code added.
