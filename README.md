# TuringDarwin / TuringProbe 0.5.0 MMU research

TuringProbe is a staged research kext for the exact ASUS TU116 target
`10DE:2182 / 1043:8854` on macOS Sequoia.

## Verified hardware milestones

- PCI discovery and BAR inventory;
- three-register TU116 identity;
- bounded PTOP topology inventory;
- one-register physical VRAM capacity decode: 6 GiB.

## Current 0.5.0 work

Version 0.5.0 adds an **offline** TU102/TU116 page-table model and corrects a
source-metadata error from 0.4.0: page shift 16 means 64 KiB, not 16 KiB.

No new MMIO offset, boot argument or hardware operation is added.

Read:

- `docs/MMU-RESEARCH-0.5.0.md`
- `docs/MMU-PAGE-TABLE-FORMAT.md`
- `docs/MMU-REGISTER-EXCLUSION.md`

Run:

```bash
python3 tools/test-mmu-model.py
python3 tools/test-page-table-image.py
python3 tools/test-fb-mmu-contract.py
python3 tools/test-mmio-contract.py
python3 tools/safety-audit.py
```

## Hardware policy

Use the verified test EFI with `-tdprobe` only. Do not enable the old MMIO,
PTOP or FB one-shot modes again. No MMU write or new MMU read is authorised.
