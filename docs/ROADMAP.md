# Roadmap and feasibility

| Stage | Scope | Status |
|---|---|---|
| 0.1.x | Exact PCI match, capability and BAR inventory | Real-hardware verified |
| 0.2.1 | Three fixed BAR0 identity reads | Real-hardware verified |
| 0.3.0 | Bounded PTOP topology inventory | Real-hardware verified |
| 0.4.0 | One-register physical VRAM capacity decode | Real-hardware verified: 6 GiB |
| 0.5.0 | TU102/TU116 page-table format model | Offline verified and built |
| 0.5.1 | Golden vectors, multi-page builder, rollback design, complete CI | Source implemented; local PASS; GitHub build pending |
| 0.6.x candidate | Isolated memory allocation/write/readback design | Research only; no hardware implementation |
| 1.x | GPU VM activation, channels/FIFO, Copy Engine | Not authorised |
| 2.x | Compute/Vulkan userspace interface | Architectural research |
| 3.x | Display/modeset/framebuffer | Architectural research |
| 4.x | NVK Darwin winsys/port | Long-term, low single-developer feasibility |
| 5.x | WindowServer/Metal integration | Private stack; potentially impractical |

## Current next gate

Build 0.5.1 with GitHub Actions and audit the Mach-O only. The purpose is to
confirm that all offline suites ran and that the kext hardware access surface
remains unchanged. Do not install or boot 0.5.1.

After that audit, continue offline design of the first missing primitive:
bounded isolated memory allocation and CPU write/readback with a proven inverse.

No MMU register, VRAM write, PDB programming, BAR1/BAR2 programming, TLB
invalidation, DMA, interrupt or command submission is authorised.
