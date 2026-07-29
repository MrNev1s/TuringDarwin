# Changelog — TuringProbe 0.5.0 MMU research

- Added a pure software TU102/TU116 page-table model.
- Added 4 KiB, 64 KiB and 2 MiB hierarchy split/compose logic.
- Added PTE, PDE, PD0-pair and instance/PDB encoders.
- Added deterministic randomized contract tests.
- Added byte-exact synthetic page-table image generation and independent walks.
- Cross-checked hierarchy, page sizes, PD0 ordering and PTE fields against NVIDIA UVM.
- Corrected logical-kind handling: no-GSP compressed kinds now fall back through the TU102 kind map; compression is blocked.
- Added a machine-readable MMU register exclusion matrix.
- Corrected the v0.4.0 source-metadata mistake: page shift 16 is 64 KiB,
  not 16 KiB.
- Distinguished 47-bit DMA addressing from the derived 49-bit VA hierarchy.
- Added no new MMIO offset, boot argument or write path.
- Hardware authorization remains `-tdprobe` only.
