# Changelog — TuringProbe 0.4.0

- Added fail-closed `-tdfb-read` mode requiring `-tdmmio-read`.
- Added dedicated compile-time gate `TURINGPROBE_ENABLE_FB_READ=1`.
- Added one source-backed read of BAR0 offset `0x100CE0`.
- Added Nouveau-compatible VRAM magnitude/scale and optional 15/16 decoder.
- Added exact 6 GiB target-board validation.
- Added source-labelled TU102 MMU architecture metadata with no extra MMIO.
- Added explicit TOP/FB mutual exclusion.
- Preserved verified PCI-only, identity-only and PTOP modes.
- Fixed stale build-manifest version and whitelist reporting from 0.3.0.
- Added FB/MMU contract test and expanded safety audit.
- No write, DMA, interrupt, firmware, power, command-submission or user-client
  path was added.
