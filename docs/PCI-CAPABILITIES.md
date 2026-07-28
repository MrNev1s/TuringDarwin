# Verified PCI BAR and capability state

The values below were captured on the target GTX 1660 Ti by TuringProbe 0.1.0
on macOS 15.7.7. They are runtime evidence, not inferred defaults.

## BARs and assigned resources

| Resource | Assigned base | Length | Type |
|---|---:|---:|---|
| BAR0 | `0x80000000` | 16 MiB | 32-bit non-prefetchable MMIO |
| BAR1/2 | `0x4000000000` | 256 MiB | 64-bit prefetchable |
| BAR3/4 | `0x4010000000` | 32 MiB | 64-bit prefetchable |
| BAR5 | `0x5000` | 128 B | I/O space |
| Expansion ROM | `0x81000000` | 512 KiB | ROM aperture |

No BAR is mapped or dereferenced by 0.1.x. BAR sizes are taken from existing
`IODeviceMemory` descriptors; the code never probes sizes by writing all ones.

## Conventional capabilities

| Offset | ID | Name | Key state |
|---:|---:|---|---|
| `0x60` | `0x01` | Power Management | PMCSR observed read-only |
| `0x68` | `0x05` | MSI | 64-bit capable, disabled |
| `0x78` | `0x10` | PCI Express | max Gen3 x16, observed idle encoding 1 x16 |

## Extended capabilities

| Offset | ID | Name |
|---:|---:|---|
| `0x100` | `0x0002` | Virtual Channel |
| `0x250` | `0x0018` | Latency Tolerance Reporting |
| `0x258` | `0x001E` | L1 PM Substates |
| `0x128` | `0x0004` | Power Budgeting |
| `0x420` | `0x0001` | Advanced Error Reporting |
| `0x600` | `0x000B` | Vendor-Specific Extended Capability |
| `0x900` | `0x0019` | Secondary PCI Express |
| `0xBB0` | `0x0015` | Resizable BAR |

0.1.1 adds bounded decoding of every ReBAR entry advertised by the count field.
It reads capability and control registers but never writes the selected size.
