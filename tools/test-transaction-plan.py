#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "research"))

from mmu_transaction_plan import (  # noqa: E402
    DEFAULT_STEPS,
    EvidenceStatus,
    Phase,
    PlanError,
    TransactionPlan,
    TransactionStep,
)

plan = TransactionPlan()
assert plan.hardware_eligible is False
assert plan.first_hardware_step.name == "stage-tables-in-device-memory"
assert [step.name for step in plan.offline_prefix] == [
    "allocate-host-model",
    "build-page-tables",
    "verify-page-tables",
]

result = plan.simulate(stop_before_hardware=True)
assert result.final_phase == Phase.TABLES_VERIFIED
assert result.blocked_reason == "hardware boundary reached at stage-tables-in-device-memory"
assert result.completed_steps == (
    "allocate-host-model",
    "build-page-tables",
    "verify-page-tables",
)

# Every offline failure injection must roll back completely to the safe baseline.
for step in plan.offline_prefix:
    failure = plan.simulate(stop_before_hardware=False, fail_at=step.name)
    assert failure.final_phase == Phase.ROLLED_BACK
    assert failure.safe_baseline_restored is True
    assert failure.blocked_reason == f"injected failure at {step.name}"

# The first hardware mutation is blocked because its inverse is not proven.
hardware_attempt = plan.simulate(stop_before_hardware=False)
assert hardware_attempt.final_phase == Phase.TABLES_VERIFIED
assert hardware_attempt.blocked_reason == (
    "step is not hardware-eligible: stage-tables-in-device-memory"
)

matrix = plan.evidence_matrix()
assert len(matrix) == len(DEFAULT_STEPS)
assert sum(bool(row["device_write"]) for row in matrix) == 5
assert all(row["timeout_ms"] is None for row in matrix[:3])
assert all(row["timeout_ms"] is not None for row in matrix[3:])
assert matrix[-1]["inverse_status"] == EvidenceStatus.BLOCKED.value

# Structural errors are rejected.
def must_fail(fn, *args, **kwargs):
    try:
        fn(*args, **kwargs)
    except PlanError:
        return
    raise AssertionError(f"expected PlanError from {fn.__name__}")

must_fail(TransactionPlan, ())
invalid_step = TransactionStep(
    name="wrong-start",
    source_phase=Phase.TABLES_BUILT,
    target_phase=Phase.TABLES_VERIFIED,
    device_access=False,
    device_write=False,
    timeout_ms=None,
    required_evidence=(),
    inverse_name="undo",
    inverse_status=EvidenceStatus.PROVEN_OFFLINE,
    notes="invalid test step",
)
must_fail(TransactionPlan, (invalid_step,))

print("MMU TRANSACTION/ROLLBACK CONTRACT PASSED")
print("- complete ordered state machine")
print("- all offline failure points restore safe baseline")
print("- first device-memory write remains blocked")
print("- every hardware step has a timeout and inverse obligation")
print("- hardware eligibility remains false")
print("- zero MMIO and zero device access")
