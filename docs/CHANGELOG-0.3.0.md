# TuringProbe 0.3.0 changelog

- Added `-tdtop-read`, requiring both `-tdprobe` and `-tdmmio-read`.
- Added a bounded read-only PTOP device inventory matching Nouveau's
  `gk104_top_parse` layout.
- Reads exactly 64 dwords at `0x022700..0x0227fc` in expanded mode.
- Publishes raw TOP data and structured engine records.
- Preserves read-only BAR0 mapping, explicit release, exact PCI matching,
  unchanged Command Register checks, and disabled Bus Master requirement.
- Added TOP contract tests and expanded source safety audit.
- No write, DMA, interrupt, firmware, reset, power or user-client path added.
