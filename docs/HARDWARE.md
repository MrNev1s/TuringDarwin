# Confirmed target hardware

Source: supplied `PC-DATA-20260723-121802(1).zip`, stable EFI, and
`TU116(3).rom`. Values below are offline observations, not a live macOS probe.

## PCI functions behind the graphics card

| BDF | PCI ID | Subsystem | Class | Role |
|---|---|---|---|---|
| 01:00.0 | 10DE:2182 rev A1 | 1043:8854 | 030000 | TU116 VGA controller; sole v0.1 match |
| 01:00.1 | 10DE:1AEB | 1043:8854 | 040300 | NVIDIA HDA controller |
| 01:00.2 | 10DE:1AEC | 1043:8854 | 0C0330 | NVIDIA USB xHCI controller |
| 01:00.3 | 10DE:1AED | 1043:8854 | 0C8000 | NVIDIA USB Type-C policy controller |

Windows path for 01:00.0: `PCIROOT(0)#PCI(0100)#PCI(0000)`.
ACPI path: `_SB_.PC00.PEG1.PEGP`.

## Windows-reported PCIe properties for 01:00.0

- Current link width: x16
- Maximum link width: x16
- Maximum reported link-speed encoding: 3 (consistent with Gen3)
- Current link-speed encoding in the captured idle state: 1
- MSI maximum messages: 1
- AER capability reported present
- Raw Windows BAR-type aggregate: `0x00020101`

Actual BAR bases, lengths, conventional capability offsets and extended
capability offsets were not present as a raw PCI dump in PC-DATA. They are
explicit acceptance outputs of the first live TuringProbe run.

## Displays in the report

| Display | Connection observed by Windows | EDID vendor/product | Manufacture |
|---|---|---|---|
| Xiaomi A22FAB-RA | HDMI | XMI:F001 | week 45, 2024 |
| P24H2G | DisplayPort | LHC:FFFF | week 44, 2023 |

Both active 256-byte EDID blobs had valid per-block checksums.
