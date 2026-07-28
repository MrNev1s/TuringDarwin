# Exact source and support file list for v0.1.1

## Canonical state

- `PROJECT_STATE.md` — authoritative human-readable hand-off.
- `PROJECT_STATE.json` — machine-readable project state.
- `EVIDENCE.json` — evidence and input hashes.

## Kernel target

- `kext/TuringProbe/Info.plist` — exact PCI personality and bundle metadata.
- `kext/TuringProbe/TuringProbe.hpp` — service declaration.
- `kext/TuringProbe/TuringProbe.cpp` — fail-closed boot gates, exact target
  gate, lifecycle, command-register invariant, publication and registration.
- `kext/TuringProbe/PCIConfig.hpp/.cpp` — PCI offsets, identity, fixed header
  fields, 256-byte conventional snapshot and registry paths.
- `kext/TuringProbe/CapabilityParser.hpp/.cpp` — bounded conventional and
  extended capability walks, human-readable names, PM/MSI/MSI-X/PCIe and full
  ReBAR read-only decoding.
- `kext/TuringProbe/BARInspector.hpp/.cpp` — assigned BAR decoding and existing
  `IODeviceMemory` metadata without mapping.
- `kext/TuringProbe/Logging.hpp` — bounded log prefix.
- `include/TuringDeviceIds.hpp` — exact primary and subsystem IDs.
- `include/TuringTypes.hpp` — fixed-width PCI identity type.
- `include/TuringRegisters.hpp` — intentionally empty; no MMIO whitelist exists
  in 0.1.1.

## Build and validation

- `TuringProbe.xcodeproj/project.pbxproj`
- `.github/workflows/build-kext.yml`
- `MacKernelSDK.lock.example`
- `tools/bootstrap-sdk.sh`
- `tools/build.sh`
- `tools/safety-audit.py`
- `tools/collect-macos.sh`
- `tools/compare-pci.py`
- `tools/decode-capabilities.py`
- `tools/verify-rom.py`
- `tools/parse-edid.py`

## Documentation

- all files under `docs/`, especially `PROJECT_STATE.md`,
  `MMIO-READ-PLAN.md`, `SAFETY.md`, `TESTING.md`, and `RESULT-MATRIX.md`.
