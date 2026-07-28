# TuringProbe 0.2 — Read-only BAR0 MMIO design gate

Status: **design only; no MMIO implementation in 0.1.1**.

## Entry conditions

- 0.1.1 builds with the pinned MacKernelSDK.
- 0.1.1 boots successfully on the target.
- Command Register is unchanged before/after the probe.
- Bus mastering remains disabled.
- Complete ReBAR parsing is valid.
- Untouched fallback EFI remains bootable.

## Proposed fail-closed controls

Both must be true before any BAR mapping is attempted:

1. build-time `TURINGPROBE_ENABLE_MMIO_READ=1`;
2. boot argument `-tdmmio-read`.

`-tdunsafe` remains rejected.

## Mapping rules

- BAR0 descriptor only, exact register offset `0x10`.
- Require non-null descriptor and length at least 16 MiB as observed.
- Create one read-only mapping if the available IOKit API supports explicit
  read-only semantics; otherwise stop and review before implementation.
- Never request cache policy changes without a documented reason.
- No raw dump of the aperture.
- No pointer arithmetic outside a dedicated checked accessor.

## Whitelist record required for each offset

- symbolic register name;
- offset and width;
- GPU generation applicability (TU116/Turing);
- primary source and source revision;
- reason the register is considered safe to read;
- expected stability and all-ones handling;
- whether a read can acknowledge or clear state (such registers are excluded).

## Runtime checks

- record PCI Command Register before mapping, after mapping, and after reads;
- abort if Bus Master Enable is unexpectedly set;
- maximum fixed number of reads;
- no loop driven by a hardware value;
- no interrupt setup;
- release mapping on every failure path and in `stop()`;
- preserve GOP output and monitor state.

## Non-goals

- no MMIO writes;
- no PRAMIN or VRAM access;
- no VBIOS ROM enable toggles;
- no engine reset;
- no firmware upload;
- no DMA, FIFO, channels, runlists, doorbells, or fences;
- no power-management programming.
