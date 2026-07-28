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
