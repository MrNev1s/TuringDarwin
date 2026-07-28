# Roadmap and feasibility

| Stage | Scope | Status |
|---|---|---|
| 0.1.0 | Exact PCI match, config/capability walk, BAR descriptors | Built and real-hardware verified |
| 0.1.1 | Command invariant, named capabilities, complete ReBAR decode | Built and real-hardware verified |
| 0.3.0 | BAR0 read-only map and three-register whitelist | Source implemented; build/binary/live gates pending |
| 0.2.x | Expand only proven read-only identification telemetry | Blocked on 0.3.0 hardware result |
| 0.3.x | Offline full VBIOS/BIT parser and test vectors | Structural verifier exists; full parser pending |
| 1.x | Memory manager, GPU VM, channels, FIFO, Copy Engine | Research only; no implementation |
| 2.x | Dedicated userspace compute/Vulkan interface | Architectural research only |
| 3.x | Display/modeset/framebuffer | Architectural research only |
| 4.x | NVK Darwin winsys/port | Long-term, low single-developer feasibility |
| 5.x | WindowServer/Metal integration | Private stack; potentially impractical |

The next authorised action is only to build and audit 0.3.0. No MMIO write,
DMA, firmware, interrupt, reset, or command submission stage is authorised.

## Current candidate: 0.4.0

One-register FB capacity inventory plus source-only TU102 MMU architecture
profile. Source implemented; Xcode artifact and hardware gates pending. This is
still discovery only and does not allocate or map GPU memory.
