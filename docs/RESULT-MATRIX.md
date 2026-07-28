# Verification and experiment matrix

| Item | Status | Evidence / next proof |
|---|---|---|
| Sequoia desktop through GTX 1660 Ti GOP | **Real hardware verified** | macOS 15.7.7 runtime logs |
| Exact target `10DE:2182 / 1043:8854` | **Real hardware verified** | active 0.1.1 IORegistry service |
| VBIOS hash and embedded ROM checksums | **Offline verified** | supplied ROM and parser |
| Live BAR bases and lengths | **Real hardware verified** | 0.1.x IODeviceMemory telemetry |
| PCI capability and full ReBAR decode | **Real hardware verified** | 0.1.1 logs |
| Command Register unchanged | **Real hardware verified** | 0.1.1 before/after = `0x0003` |
| Bus mastering remains disabled | **Real hardware verified** | 0.1.1 before/after = No |
| 0.2.1 source safety audit | **Passed locally** | `tools/safety-audit.py` |
| 0.2.1 MMIO contract test | **Passed locally** | exactly three fixed reads/read-only map |
| 0.2.1 Xcode build | **Not yet verified** | GitHub Actions required |
| 0.2.1 binary call-site audit | **Not yet verified** | inspect uploaded artifact |
| 0.2.1 PCI-only compatibility boot | **Not yet tested** | boot with `-tdprobe` |
| 0.2.1 BAR0 read-only boot | **Not yet tested** | later boot with `-tdprobe -tdmmio-read` |
| PCI configuration writes | **Forbidden** | none authorised |
| MMIO writes | **Forbidden** | none authorised |
| DMA / channels / Copy Engine | **Research only** | no implementation |
| Vulkan/NVK | **Long-term research** | no implementation |
| WindowServer/Metal | **Very low feasibility** | private stack reverse engineering |
