# Source and support files — v0.5.1

## Canonical state

- `PROJECT_STATE.md` — authoritative human-readable hand-off.
- `PROJECT_STATE.json` — machine-readable project state.
- `EVIDENCE.json` — base hardware and VBIOS provenance.
- `EVIDENCE-MMU-0.5.1.json` — current offline MMU evidence.

## Kernel target

- `kext/TuringProbe/Info.plist` — exact PCI personality and bundle metadata.
- `kext/TuringProbe/TuringProbe.hpp/.cpp` — fail-closed boot gates, lifecycle
  and PCI Command invariants.
- `kext/TuringProbe/PCIConfig.hpp/.cpp` — PCI identity/header telemetry.
- `kext/TuringProbe/CapabilityParser.hpp/.cpp` — bounded PCI capabilities and
  ReBAR decoding.
- `kext/TuringProbe/BARInspector.hpp/.cpp` — BAR metadata only.
- `kext/TuringProbe/MMIOReadOnly.hpp/.cpp` — existing short-lived read-only BAR0
  mapping and three identity reads.
- `kext/TuringProbe/TopInventory.hpp/.cpp` — existing bounded PTOP inventory.
- `kext/TuringProbe/FbMmuInventory.hpp/.cpp` — existing one-register VRAM
  capacity read and static MMU metadata.
- `include/TuringRegisters.hpp` — immutable existing read offsets and constants.

No 0.5.1 research Python file is included in the Xcode project.

## Offline MMU research

- `research/tu102_mmu_model.py` — entry and address geometry model.
- `research/tu102_page_table_image.py` — single-mapping byte images.
- `research/tu102_address_space.py` — deterministic multi-page builder/walker.
- `research/mmu_transaction_plan.py` — transaction and rollback model.
- `research/mmu-golden-vectors.json` — fixed conformance vectors.
- `research/mmu-register-exclusion-matrix.csv` — operational register exclusion.

## Complete validation

- `tools/run-offline-validation.sh` — canonical validation entry point.
- `tools/safety-audit.py`
- `tools/test-decoder-contract.py`
- `tools/test-mmio-contract.py`
- `tools/test-top-contract.py`
- `tools/test-fb-mmu-contract.py`
- `tools/test-mmu-model.py`
- `tools/test-page-table-image.py`
- `tools/test-golden-vectors.py`
- `tools/test-address-space.py`
- `tools/test-transaction-plan.py`

## Build

- `TuringProbe.xcodeproj/project.pbxproj`
- `.github/workflows/build-kext.yml`
- `tools/build.sh`
- `tools/bootstrap-sdk.sh`
- `MacKernelSDK.lock.example`

## Current documentation

- `MMU-RESEARCH-0.5.1.md`
- `MMU-PAGE-TABLE-FORMAT.md`
- `MMU-HARDWARE-TRANSACTION-0.5.1.md`
- `MMU-ROLLBACK-MATRIX-0.5.1.md`
- `MMU-REGISTER-EXCLUSION.md`
- `TESTING.md`
- `GITHUB-ACTIONS.md`
