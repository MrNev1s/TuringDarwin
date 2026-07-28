# Roadmap and feasibility

| Stage | Scope | Current status |
|---|---|---|
| 0.1 | Exact PCI match, read-only config/capabilities/BAR descriptors | Source implemented; build/live test pending |
| 0.2 | Offline VBIOS parser with test vectors | Structural ROM verifier exists; full parser pending |
| 0.3 | Read-only MMIO from a reviewed whitelist | Not authorised |
| 1.x | GPU VM, channels, FIFO and Copy Engine proof | Research only; medium difficulty and high risk |
| 2.x | User-space compute/Vulkan interface | Architectural research only |
| 3.x | Display/modeset/framebuffer | Architectural research only |
| 4.x | NVK port | Long-term, low single-developer feasibility |
| 5.x | WindowServer/Metal integration | Private interfaces; practically very difficult |

A successful 0.1 does not imply framebuffer, Vulkan, Metal, WindowServer
acceleration, video decode or power management.
