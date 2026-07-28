# Exact source and support file list for v0.2.1

## Canonical state

- `PROJECT_STATE.md` — authoritative human-readable hand-off.
- `PROJECT_STATE.json` — machine-readable project state.
- `EVIDENCE.json` — evidence and input/build provenance.

## Kernel target

- `kext/TuringProbe/Info.plist` — exact PCI personality and bundle metadata.
- `kext/TuringProbe/TuringProbe.hpp/.cpp` — fail-closed boot gates, exact
  target check, lifecycle, mode selection, and Command Register invariant.
- `kext/TuringProbe/PCIConfig.hpp/.cpp` — PCI identity/header snapshots and
  registry paths.
- `kext/TuringProbe/CapabilityParser.hpp/.cpp` — bounded capability walks,
  names, PCIe/MSI telemetry, and full read-only ReBAR decoder.
- `kext/TuringProbe/BARInspector.hpp/.cpp` — BAR and IODeviceMemory metadata.
- `kext/TuringProbe/MMIOReadOnly.hpp/.cpp` — sole read-only BAR0 mapping and
  three-register access module.
- `kext/TuringProbe/Logging.hpp` — bounded kernel log prefix.
- `include/TuringDeviceIds.hpp` — exact target IDs.
- `include/TuringTypes.hpp` — fixed-width identity type.
- `include/TuringRegisters.hpp` — three-entry MMIO whitelist and decode masks.

## Build and validation

- `TuringProbe.xcodeproj/project.pbxproj`
- `.github/workflows/build-kext.yml`
- `MacKernelSDK.lock.example`
- `tools/bootstrap-sdk.sh`
- `tools/build.sh`
- `tools/safety-audit.py`
- `tools/test-decoder-contract.py`
- `tools/test-mmio-contract.py`
- `tools/collect-macos.sh`
- remaining offline PCI/VBIOS/EDID tools under `tools/`.

## Documentation

Key documents are `MMIO-READ-PLAN.md`, `REGISTER-WHITELIST.md`, `SAFETY.md`,
`TESTING.md`, `RESULT-MATRIX.md`, and the root `PROJECT_STATE.md`.
