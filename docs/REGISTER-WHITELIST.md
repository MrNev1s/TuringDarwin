# BAR0 read-only whitelist

## Version 0.3.0

Identity mode (`-tdprobe -tdmmio-read`) performs exactly three reads:

| Offset | Width | Name |
|---:|---:|---|
| `0x000004` | 32 | `NV_PMC_BOOT_1` |
| `0x000000` | 32 | `NV_PMC_BOOT_0` |
| `0x101000` | 32 | `NV_PEXTDEV_BOOT_0_STRAP` |

Expanded TOP mode adds exactly 64 reads:

| Range | Count | Width | Purpose |
|---|---:|---:|---|
| `0x022700..0x0227fc` | 64 | 32 | Nouveau `gk104_top_parse` device-info table |

Total expanded read count: 67. No other BAR0 offset is authorised.

The TOP table parser is finite and contains no polling. Unknown engine types are
reported without being treated as a write or control path. Malformed or
unterminated records fail the TOP gate after the mapping is released.

## Version 0.4.0 candidate FB inventory

New mode: `-tdprobe -tdmmio-read -tdfb-read`.

| Offset | Width | Count | Status | Purpose |
|---:|---:|---:|---|---|
| `0x100CE0` | 32 | 1 | source implemented, not built | TU102/TU116 physical VRAM capacity encoding |

The mode also performs the three already-verified identity reads. Total reads:
4. No MMU control or status register is read. The published 47-bit DMA width,
kind map and class information are source metadata from Nouveau `tu102_mmu`.

`-tdfb-read` and `-tdtop-read` are mutually exclusive in 0.4.0.
