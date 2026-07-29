# Verification and experiment matrix

| Item | Status | Evidence / boundary |
|---|---|---|
| Sequoia desktop through GTX 1660 Ti GOP | **Real hardware verified** | macOS 15.7.7 logs |
| Exact target `10DE:2182 / 1043:8854` | **Real hardware verified** | active TuringProbe service |
| PCI/BAR/ReBAR inventory | **Real hardware verified** | 0.1.x logs |
| TU116 A1 identity and 27 MHz strap | **Real hardware verified** | 0.2.1 MMIO logs |
| PTOP topology | **Real hardware verified** | GR, 5×CE, NVDEC, NVENC, SEC2, GSP |
| Physical VRAM capacity | **Real hardware verified** | `0x100CE0` decodes to 6 GiB |
| PCI Command unchanged / Bus Master off | **Real hardware verified** | every accepted runtime gate |
| 49-bit VA hierarchy | **Primary-source cross-checked** | Nouveau + NVIDIA UVM |
| 4 KiB / 64 KiB / 2 MiB formats | **Offline verified** | model and byte-image suites |
| Fixed PTE/PDE/PDB golden vectors | **Offline verified** | exact 64-bit values |
| Multi-page mappings | **Offline verified** | 12,025 sampled translations |
| Mixed 4 KiB/64 KiB PD0 halves | **Offline verified** | deterministic builder/walker |
| 4 KiB ↔ 2 MiB promotion/demotion | **Offline verified** | exact digest round-trip |
| Alias/overlap policy | **Offline verified** | fail-closed tests |
| Offline transaction rollback | **Offline verified** | all CPU-only failure points |
| Device-memory staging inverse | **Unproven / blocked** | no VRAM allocator/write/readback |
| PDB/TLB transaction | **Unproven / forbidden** | operational writes required |
| Real GPU translation | **Not proven** | no engine/channel test path |
| PCI/MMIO writes | **Forbidden** | none authorised |
| DMA / channels / Copy Engine | **Forbidden / research only** | no implementation |
| Vulkan/NVK | **Long-term research** | no implementation |
| WindowServer/Metal | **Very low feasibility** | private-stack integration |
