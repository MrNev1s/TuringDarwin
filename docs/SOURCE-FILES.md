# Exact source and support file list for v0.1

## Kernel target

- `kext/TuringProbe/Info.plist` — exact PCI personality and bundle metadata.
- `kext/TuringProbe/TuringProbe.hpp` — service declaration.
- `kext/TuringProbe/TuringProbe.cpp` — boot-argument gates, exact target gate,
  lifecycle, bounded publication and service registration.
- `kext/TuringProbe/PCIConfig.hpp` — PCI offsets and read-only API surface.
- `kext/TuringProbe/PCIConfig.cpp` — identity, fixed header fields, 256-byte
  conventional configuration snapshot and IORegistry paths.
- `kext/TuringProbe/CapabilityParser.hpp` — capability parser interface.
- `kext/TuringProbe/CapabilityParser.cpp` — bounded conventional and extended
  capability walks; PM/MSI/MSI-X/PCIe/RBAR decoding.
- `kext/TuringProbe/BARInspector.hpp` — BAR/resource inspector interface.
- `kext/TuringProbe/BARInspector.cpp` — assigned BAR decoding and existing
  `IODeviceMemory` descriptor metadata without mapping.
- `kext/TuringProbe/Logging.hpp` — bounded log prefix.
- `include/TuringDeviceIds.hpp` — exact primary and subsystem IDs.
- `include/TuringTypes.hpp` — fixed-width PCI identity type.
- `include/TuringRegisters.hpp` — intentionally empty; no MMIO whitelist exists
  in v0.1.

## Build and validation

- `TuringProbe.xcodeproj/project.pbxproj`
- `MacKernelSDK.lock.example`
- `tools/bootstrap-sdk.sh`
- `tools/build.sh`
- `tools/safety-audit.py`
- `tools/collect-macos.sh`
- `tools/compare-pci.py`
- `tools/decode-capabilities.py`
- `tools/verify-rom.py`
- `tools/parse-edid.py`

## Documentation and evidence

- `README.md`, `LICENSE`, `EVIDENCE.json`, `SHA256SUMS.txt`
- every file under `docs/`
- parser and ROM test placeholders under `tests/`
- research boundary notes under `research/`
