# PCI BAR and capability status before the first macOS probe

## BARs

No trustworthy raw PCI configuration dump with assigned BAR bases and lengths
was present in PC-DATA. Windows exposed only the aggregate `BarTypes` value
`0x00020101`. Therefore no BAR address or length is guessed here.

| Resource | Offline status | v0.1 live property |
|---|---|---|
| BAR0 | Base/length unknown | `TPBAR0Raw`, entry 0 in `TPBARDescriptors` |
| BAR1 | Base/length unknown | `TPBAR1Raw`, entry 1 in `TPBARDescriptors` |
| BAR2 | Base/length unknown | `TPBAR2Raw`, entry 2 in `TPBARDescriptors` |
| BAR3 | Base/length unknown | `TPBAR3Raw`, entry 3 in `TPBARDescriptors` |
| BAR4 | Base/length unknown | `TPBAR4Raw`, entry 4 in `TPBARDescriptors` |
| BAR5 | Base/length unknown | `TPBAR5Raw`, entry 5 in `TPBARDescriptors` |
| Expansion ROM BAR | Raw value unknown | `TPExpansionRomBARRaw` |
| Allocated ranges | Unknown | `TPMemoryRanges` and descriptor lengths |

The implementation does not size a BAR by writing all ones. It reads assigned
config values and asks `IOPCIDevice` for already-published memory descriptors;
it never maps or dereferences them.

## Capabilities

| Capability / property | PC-DATA observation | Exact offset/live state |
|---|---|---|
| PCI Express capability | ExpressSpecVersion raw enum 2 | Pending live probe |
| Current link | speed enum 1, width x16 in captured Windows state | Pending live probe |
| Maximum link | speed enum 3, width x16 | Pending live probe |
| MSI | maximum messages 1 | Offset and enabled state pending |
| MSI-X | Not proven by PC-DATA | Pending live probe |
| Power Management | Expected for PCIe endpoint but not proven from raw dump | Pending live probe |
| AER | Windows reports present | Extended-cap offset pending |
| Resizable BAR | BIOS setting disabled; capability presence not proven | `TPResizableBARPresent` pending |
| ACS | Windows raw support enum 2 | Extended-cap offset pending |
| ARI | Windows reports false | Confirm with extended-cap walk |
| ATS | Windows reports false | Confirm with extended-cap walk |
| Atomic Ops | Windows reports false | Confirm with capability fields |

The first live capture is the acceptance evidence for all values marked pending.
