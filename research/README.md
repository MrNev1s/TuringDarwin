# Offline MMU research

Everything in this directory is CPU-only research code. It must not import or
invoke IOKit, map a device, open `/dev`, use subprocesses, access the network,
or perform MMIO.

## Modules

- `tu102_mmu_model.py` — address geometry and entry encoders/decoders.
- `tu102_page_table_image.py` — minimal single-mapping byte images.
- `tu102_address_space.py` — deterministic multi-page/mixed-page builder.
- `mmu_transaction_plan.py` — ordering, evidence, timeout and rollback model.
- `mmu-golden-vectors.json` — fixed non-random conformance vectors.
- `mmu-register-exclusion-matrix.csv` — MMU registers excluded from passive use.

## Primary references

- Linux Nouveau/NVKM `tu102.c`, `vmmgp100.c`, `vmmtu102.c` and TU102 BAR code.
- NVIDIA Open GPU Kernel Modules `uvm_turing_mmu.c`.

No third-party source code is vendored. Only derived constants, test vectors,
and source references are stored here.
