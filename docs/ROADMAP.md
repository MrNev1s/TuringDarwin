# Roadmap and feasibility

| Stage | Scope | Current status |
|---|---|---|
| 0.1.0 | Exact PCI match, config/capabilities/BAR descriptors | **Built and real-hardware verified** |
| 0.1.1 | Named capabilities, full ReBAR decode, before/after Command invariant | **Source implemented; build/live test pending** |
| 0.2 | BAR0 read-only MMIO with reviewed whitelist | Design gate only; no code yet |
| 0.3 | Offline full VBIOS/BIT parser and test vectors | Structural verifier exists; full parser pending |
| 1.x | GPU VM, channels, FIFO and Copy Engine proof | Research only; substantial risk |
| 2.x | User-space compute/Vulkan interface | Architectural research only |
| 3.x | Display/modeset/framebuffer | Architectural research only |
| 4.x | NVK port | Long-term, low single-developer feasibility |
| 5.x | WindowServer/Metal integration | Private interfaces; practically very difficult |

A successful diagnostic or MMIO-read stage does not imply framebuffer, Vulkan,
Metal, WindowServer acceleration, video decode, or power management.
