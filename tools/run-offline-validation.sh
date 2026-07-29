#!/bin/bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

run() {
  echo
  echo "===== $* ====="
  "$@"
}

run python3 tools/safety-audit.py
run python3 tools/test-decoder-contract.py
run python3 tools/test-mmio-contract.py
run python3 tools/test-top-contract.py
run python3 tools/test-fb-mmu-contract.py
run python3 tools/test-mmu-model.py
run python3 tools/test-page-table-image.py
run python3 tools/test-golden-vectors.py
run python3 tools/test-address-space.py
run python3 tools/test-transaction-plan.py
run python3 tools/test-host-memory-model.py
run python3 tools/test-host-memory-kext-contract.py
run python3 tools/test-host-physical-model.py
run python3 tools/test-host-physical-kext-contract.py

run python3 -m py_compile \
  research/tu102_mmu_model.py \
  research/tu102_page_table_image.py \
  research/tu102_address_space.py \
  research/mmu_transaction_plan.py \
  research/host_memory_model.py \
  research/host_physical_segment_model.py \
  tools/safety-audit.py \
  tools/test-decoder-contract.py \
  tools/test-mmio-contract.py \
  tools/test-top-contract.py \
  tools/test-fb-mmu-contract.py \
  tools/test-mmu-model.py \
  tools/test-page-table-image.py \
  tools/test-golden-vectors.py \
  tools/test-address-space.py \
  tools/test-transaction-plan.py \
  tools/test-host-memory-model.py \
  tools/test-host-memory-kext-contract.py \
  tools/test-host-physical-model.py \
  tools/test-host-physical-kext-contract.py

if command -v plutil >/dev/null 2>&1; then
  run plutil -lint kext/TuringProbe/Info.plist
  run plutil -lint docs/OPENCORE-ENTRY.plist
else
  run python3 - <<'PY'
import plistlib
from pathlib import Path
for name in ("kext/TuringProbe/Info.plist", "docs/OPENCORE-ENTRY.plist"):
    with Path(name).open("rb") as stream:
        plistlib.load(stream)
    print(f"PLIST PARSE PASSED: {name}")
PY
fi

if command -v bash >/dev/null 2>&1; then
  run bash -n tools/build.sh
  run bash -n tools/bootstrap-sdk.sh
  run bash -n tools/collect-macos.sh
  run bash -n tools/run-offline-validation.sh
fi

echo
echo "OFFLINE VALIDATION SUITE PASSED"
echo "- all legacy PCI/MMIO/PTOP/FB contracts"
echo "- MMU golden vectors"
echo "- randomized MMU model and byte-image tests"
echo "- multi-page/mixed-page address-space tests"
echo "- transaction/rollback state-machine tests"
echo "- bounded host-memory allocation/write/readback tests"
echo "- one-page raw host physical-segment model and source contract"
echo "- zero device access"
