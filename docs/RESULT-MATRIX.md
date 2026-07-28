# Verification and experiment matrix

This matrix deliberately separates offline evidence, source verification and
future hardware experiments.

| Item | Status | Evidence / next proof |
|---|---|---|
| macOS Sequoia reaches desktop on GTX 1660 Ti GOP | Reported as verified on the real PC by the user | Existing working installation; not re-tested by this package |
| GPU primary ID `10DE:2182` | Confirmed offline | PC-DATA device inventory and VBIOS PCIR headers |
| ASUS subsystem `1043:8854` | Confirmed offline | PC-DATA device inventory |
| PCI BDF `01:00.0` and multifunction siblings | Confirmed offline | PC-DATA Windows PnP properties |
| VBIOS file hash and embedded ROM checksums | Confirmed offline | `tools/verify-rom.py` against supplied ROM |
| Stable EFI configuration inventory | Confirmed offline | Parsed supplied `EFI_STABLE.zip` |
| v0.1 source contains no authorised write/MMIO/DMA primitives | Static audit passed | `tools/safety-audit.py`; this is not runtime proof |
| `Info.plist` and OpenCore entry parse | Offline validation passed | Python plist parser; repeat with `plutil` on macOS |
| Xcode 16.2 compilation | Not yet verified | Run `tools/build.sh Debug` on Sequoia with SDK 15.2 |
| Kext attachment and IORegistry publication | Requires first experiment | Separate test EFI with `-tdprobe` |
| Exact live BAR bases and lengths | Requires first experiment | `TPBARDescriptors` and `TPMemoryRanges` |
| Exact capability offsets and live link state | Requires first experiment | `TPConventionalCapabilities` and `TPExtendedCapabilities` |
| Read-only MMIO | Not authorised | Separate reviewed milestone and explicit user approval required |
| Copy Engine / DMA / channels | Research only | No implementation in v0.1 |
| Vulkan/NVK | Theoretically possible but major project | No implementation in v0.1 |
| WindowServer/Metal acceleration | Practically very difficult | Private interfaces and extensive reverse engineering required |
