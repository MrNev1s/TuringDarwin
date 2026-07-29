#!/usr/bin/env python3
"""Offline transaction and rollback model for a future TU116 MMU experiment.

The module is intentionally incapable of device access. It documents ordering,
preconditions, evidence gates, timeouts, and rollback obligations. Any step
whose inverse is not independently proven keeps the whole plan ineligible for
hardware execution.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Iterable, Mapping


class PlanError(ValueError):
    pass


class Phase(str, Enum):
    SAFE_BASELINE = "safe-baseline"
    HOST_ALLOCATED = "host-allocated"
    TABLES_BUILT = "tables-built"
    TABLES_VERIFIED = "tables-verified"
    DEVICE_MEMORY_STAGED = "device-memory-staged"
    INSTANCE_BUILT = "instance-built"
    PDB_PROGRAMMED = "pdb-programmed"
    TLB_INVALIDATED = "tlb-invalidated"
    TRANSLATION_VERIFIED = "translation-verified"
    ROLLED_BACK = "rolled-back"
    FAILED = "failed"


class EvidenceStatus(str, Enum):
    PROVEN_OFFLINE = "proven-offline"
    SOURCE_BACKED = "source-backed"
    HARDWARE_UNPROVEN = "hardware-unproven"
    BLOCKED = "blocked"


@dataclass(frozen=True)
class TransactionStep:
    name: str
    source_phase: Phase
    target_phase: Phase
    device_access: bool
    device_write: bool
    timeout_ms: int | None
    required_evidence: tuple[str, ...]
    inverse_name: str | None
    inverse_status: EvidenceStatus
    notes: str

    @property
    def hardware_eligible(self) -> bool:
        if self.device_write and self.inverse_status != EvidenceStatus.PROVEN_OFFLINE:
            return False
        return self.inverse_status != EvidenceStatus.BLOCKED


DEFAULT_STEPS: tuple[TransactionStep, ...] = (
    TransactionStep(
        name="allocate-host-model",
        source_phase=Phase.SAFE_BASELINE,
        target_phase=Phase.HOST_ALLOCATED,
        device_access=False,
        device_write=False,
        timeout_ms=None,
        required_evidence=("bounded CPU allocator", "canaries", "zeroization"),
        inverse_name="release-host-model",
        inverse_status=EvidenceStatus.PROVEN_OFFLINE,
        notes="Ordinary CPU memory only; v0.6.0 host self-test is the runtime candidate.",
    ),
    TransactionStep(
        name="build-page-tables",
        source_phase=Phase.HOST_ALLOCATED,
        target_phase=Phase.TABLES_BUILT,
        device_access=False,
        device_write=False,
        timeout_ms=None,
        required_evidence=("golden vectors", "multi-page builder"),
        inverse_name="discard-page-tables",
        inverse_status=EvidenceStatus.PROVEN_OFFLINE,
        notes="Produces byte-exact synthetic page-table images.",
    ),
    TransactionStep(
        name="verify-page-tables",
        source_phase=Phase.TABLES_BUILT,
        target_phase=Phase.TABLES_VERIFIED,
        device_access=False,
        device_write=False,
        timeout_ms=None,
        required_evidence=("independent walker", "conflict tests"),
        inverse_name="discard-page-tables",
        inverse_status=EvidenceStatus.PROVEN_OFFLINE,
        notes="No device state exists yet.",
    ),
    TransactionStep(
        name="stage-tables-in-device-memory",
        source_phase=Phase.TABLES_VERIFIED,
        target_phase=Phase.DEVICE_MEMORY_STAGED,
        device_access=True,
        device_write=True,
        timeout_ms=100,
        required_evidence=(
            "authorised VRAM allocator",
            "authorised CPU-to-VRAM write path",
            "readback verification",
        ),
        inverse_name="zero-and-release-staged-memory",
        inverse_status=EvidenceStatus.HARDWARE_UNPROVEN,
        notes="No authorised allocator or write/readback path exists.",
    ),
    TransactionStep(
        name="build-instance-block",
        source_phase=Phase.DEVICE_MEMORY_STAGED,
        target_phase=Phase.INSTANCE_BUILT,
        device_access=True,
        device_write=True,
        timeout_ms=100,
        required_evidence=("instance layout", "bounded write/readback"),
        inverse_name="restore-instance-block",
        inverse_status=EvidenceStatus.HARDWARE_UNPROVEN,
        notes="Instance-block placement and ownership are not proven.",
    ),
    TransactionStep(
        name="program-pdb",
        source_phase=Phase.INSTANCE_BUILT,
        target_phase=Phase.PDB_PROGRAMMED,
        device_access=True,
        device_write=True,
        timeout_ms=50,
        required_evidence=("saved original PDB", "exact write whitelist"),
        inverse_name="restore-original-pdb",
        inverse_status=EvidenceStatus.HARDWARE_UNPROVEN,
        notes="Would change GPU address-translation state.",
    ),
    TransactionStep(
        name="invalidate-tlb",
        source_phase=Phase.PDB_PROGRAMMED,
        target_phase=Phase.TLB_INVALIDATED,
        device_access=True,
        device_write=True,
        timeout_ms=2000,
        required_evidence=("TU102 invalidate sequence", "bounded poll", "timeout rollback"),
        inverse_name="restore-pdb-and-reinvalidate",
        inverse_status=EvidenceStatus.HARDWARE_UNPROVEN,
        notes="Operational register sequence; not a passive probe.",
    ),
    TransactionStep(
        name="verify-translation",
        source_phase=Phase.TLB_INVALIDATED,
        target_phase=Phase.TRANSLATION_VERIFIED,
        device_access=True,
        device_write=True,
        timeout_ms=100,
        required_evidence=("isolated engine", "fault capture", "known test buffer"),
        inverse_name="stop-engine-and-restore-baseline",
        inverse_status=EvidenceStatus.BLOCKED,
        notes="Requires an engine/channel path that does not exist yet.",
    ),
)


@dataclass(frozen=True)
class SimulationResult:
    completed_steps: tuple[str, ...]
    final_phase: Phase
    rollback_steps: tuple[str, ...]
    safe_baseline_restored: bool
    blocked_reason: str | None


class TransactionPlan:
    def __init__(self, steps: Iterable[TransactionStep] = DEFAULT_STEPS):
        self.steps = tuple(steps)
        if not self.steps:
            raise PlanError("transaction plan must contain at least one step")
        expected = Phase.SAFE_BASELINE
        names: set[str] = set()
        for step in self.steps:
            if step.name in names:
                raise PlanError(f"duplicate transaction step: {step.name}")
            names.add(step.name)
            if step.source_phase != expected:
                raise PlanError(
                    f"step {step.name} starts at {step.source_phase}, expected {expected}"
                )
            expected = step.target_phase

    @property
    def first_hardware_step(self) -> TransactionStep:
        for step in self.steps:
            if step.device_access:
                return step
        raise PlanError("plan has no hardware step")

    @property
    def hardware_eligible(self) -> bool:
        return all(step.hardware_eligible for step in self.steps)

    @property
    def offline_prefix(self) -> tuple[TransactionStep, ...]:
        result = []
        for step in self.steps:
            if step.device_access:
                break
            result.append(step)
        return tuple(result)

    def evidence_matrix(self) -> tuple[Mapping[str, object], ...]:
        return tuple(
            {
                "step": step.name,
                "source": step.source_phase.value,
                "target": step.target_phase.value,
                "device_access": step.device_access,
                "device_write": step.device_write,
                "timeout_ms": step.timeout_ms,
                "inverse": step.inverse_name,
                "inverse_status": step.inverse_status.value,
                "hardware_eligible": step.hardware_eligible,
                "required_evidence": step.required_evidence,
                "notes": step.notes,
            }
            for step in self.steps
        )

    def simulate(self, *, stop_before_hardware: bool = True, fail_at: str | None = None) -> SimulationResult:
        phase = Phase.SAFE_BASELINE
        completed: list[TransactionStep] = []
        blocked_reason = None

        for step in self.steps:
            if phase != step.source_phase:
                raise PlanError("internal phase mismatch")
            if stop_before_hardware and step.device_access:
                blocked_reason = f"hardware boundary reached at {step.name}"
                break
            if not step.hardware_eligible:
                blocked_reason = f"step is not hardware-eligible: {step.name}"
                break
            if fail_at == step.name:
                rollback = self._rollback(completed)
                return SimulationResult(
                    completed_steps=tuple(item.name for item in completed),
                    final_phase=Phase.ROLLED_BACK if rollback[1] else Phase.FAILED,
                    rollback_steps=rollback[0],
                    safe_baseline_restored=rollback[1],
                    blocked_reason=f"injected failure at {step.name}",
                )
            completed.append(step)
            phase = step.target_phase

        return SimulationResult(
            completed_steps=tuple(item.name for item in completed),
            final_phase=phase,
            rollback_steps=(),
            safe_baseline_restored=phase == Phase.SAFE_BASELINE,
            blocked_reason=blocked_reason,
        )

    @staticmethod
    def _rollback(completed: list[TransactionStep]) -> tuple[tuple[str, ...], bool]:
        rollback_steps: list[str] = []
        for step in reversed(completed):
            if step.inverse_name is None or step.inverse_status != EvidenceStatus.PROVEN_OFFLINE:
                return tuple(rollback_steps), False
            rollback_steps.append(step.inverse_name)
        return tuple(rollback_steps), True


if __name__ == "__main__":
    import json

    plan = TransactionPlan()
    print(json.dumps({
        "hardware_eligible": plan.hardware_eligible,
        "first_hardware_step": plan.first_hardware_step.name,
        "offline_prefix": [step.name for step in plan.offline_prefix],
        "matrix": plan.evidence_matrix(),
    }, indent=2))
