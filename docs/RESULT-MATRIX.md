# Verification and experiment matrix

| Item | Status | Evidence / next proof |
|---|---|---|
| Sequoia desktop through GTX 1660 Ti GOP | **Real hardware verified** | macOS 15.7.7 runtime logs |
| GPU exact match `10DE:2182 / 1043:8854` | **Real hardware verified** | active TuringProbe IORegistry service |
| VBIOS hash and embedded ROM checksums | **Offline verified** | supplied ROM and parser |
| TuringProbe 0.1.0 Xcode build | **Verified** | GitHub Actions build #9 |
| TuringProbe 0.1.0 attachment | **Verified** | `kmutil` and IORegistry |
| Bus mastering remains disabled | **Verified during 0.1.0 probe** | Command Register `0x0003` |
| Exact live BAR bases and lengths | **Verified** | IODeviceMemory and TPBAR descriptors |
| Conventional and extended capability chain | **Verified** | live extended config reads |
| TuringProbe 0.1.1 source safety audit | **Locally passed; rerun in Actions** | `tools/safety-audit.py` |
| TuringProbe 0.1.1 Xcode build | **Not yet run** | GitHub Actions required |
| 0.1.1 command before/after invariant | **Not yet hardware tested** | both values must remain `3` |
| 0.1.1 complete ReBAR decode | **Not yet hardware tested** | expected three entries |
| BAR0 read-only MMIO | **Planned, not implemented** | separate 0.2 branch and whitelist review |
| PCI/MMIO writes | **Forbidden** | no approval |
| Copy Engine / DMA / channels | **Research only** | no implementation |
| Vulkan/NVK | **Long-term research** | no implementation |
| WindowServer/Metal | **Very low feasibility** | private stack reverse engineering |
