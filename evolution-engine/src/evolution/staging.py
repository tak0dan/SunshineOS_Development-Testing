"""Staging capability abstraction and the 14-phase migration workflow.

Staging is a capability, not a filesystem requirement. Btrfs snapshots are one
way to stage; a separate partition, temporary root or external recovery
environment are others. The planner chooses an execution strategy from observed
capabilities instead of prescribing a single storage layout.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping

from .inventory import Inventory

STRATEGIES = ("in_place", "staged_root", "ab_slot", "bootstrap", "recovery_reconstruction")

PHASES: tuple[str, ...] = (
    "Discover", "Qualify", "Resolve", "Plan", "Review", "Protect",
    "Prepare", "Reconcile", "Build", "ValidateStaged", "Activate",
    "BootValidate", "Commit", "Retain",
)


@dataclass(frozen=True)
class StagingCapability:
    filesystem: str = "unknown"
    can_snapshot: bool = False
    can_subvolume: bool = False
    separate_workspace: bool = False
    recovery_environment: bool = False
    encrypted: bool = False
    inactive_slot_available: bool = False
    slot_switch_supported: bool = False

    @classmethod
    def from_inventory(cls, inv: Inventory) -> "StagingCapability":
        storage = inv.storage
        boot = inv.boot
        security = inv.security
        filesystem = str(storage.get("filesystem", "unknown")).lower()
        return cls(
            filesystem=filesystem or "unknown",
            can_snapshot=bool(storage.get("can_snapshot", filesystem == "btrfs")),
            can_subvolume=bool(storage.get("can_subvolume", filesystem == "btrfs")),
            separate_workspace=bool(storage.get("separate_workspace", False)),
            recovery_environment=bool(boot.get("recovery_environment", False)),
            encrypted=bool(security.get("encrypted", False)),
            inactive_slot_available=boot.get("inactive_slot_available") is True,
            slot_switch_supported=boot.get("slot_switch_supported") is True,
        )

    def staged_root_possible(self) -> bool:
        return self.can_subvolume or self.separate_workspace

    def ab_slot_possible(self) -> bool:
        # A slot is usable only when both the destination and an explicit
        # activation mechanism were observed. Never infer A/B from distro name.
        return self.inactive_slot_available and self.slot_switch_supported


@dataclass(frozen=True)
class StagingAssessment:
    strategy: str
    workspace: str
    reasons: tuple[str, ...]
    can_retain_previous: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "strategy": self.strategy,
            "workspace": self.workspace,
            "reasons": list(self.reasons),
            "can_retain_previous": self.can_retain_previous,
        }


def assess_staging(
    inv: Inventory,
    *,
    mode: str = "bootstrap",
    recovery_needed: bool = False,
    forced: str | None = None,
) -> StagingAssessment:
    """Choose an execution strategy from observed storage capability."""
    cap = StagingCapability.from_inventory(inv)
    reasons = [f"filesystem={cap.filesystem}", f"mode={mode}"]
    if forced == "ab_slot" and not cap.ab_slot_possible():
        raise ValueError("A/B slot staging requires an observed inactive slot and boot switch capability")
    if forced == "staged_root" and not cap.staged_root_possible():
        raise ValueError("staged-root strategy is not available on this inventory")
    if forced == "recovery_reconstruction" and not cap.recovery_environment:
        raise ValueError("recovery reconstruction requires an observed recovery environment")
    if forced:
        if forced not in STRATEGIES:
            raise ValueError(f"unknown migration strategy {forced!r}")
        reasons.append(f"strategy forced to {forced}")
        return StagingAssessment(
            forced,
            "staged-root" if cap.staged_root_possible() else "workspace",
            tuple(reasons),
            cap.can_snapshot or cap.separate_workspace,
        )
    if recovery_needed:
        reasons.append("recovery environment required")
        return StagingAssessment(
            "recovery_reconstruction", "workspace", tuple(reasons),
            cap.can_snapshot or cap.separate_workspace,
        )
    if cap.ab_slot_possible():
        reasons.append("inactive root slot and boot switch capability observed")
        return StagingAssessment("ab_slot", "inactive-slot", tuple(reasons), True)
    if mode == "bootstrap" and cap.staged_root_possible():
        reasons.append("staged root available for bootstrap")
        return StagingAssessment("staged_root", "staged-root", tuple(reasons), True)
    if cap.can_snapshot:
        reasons.append("snapshot capability enables in-place with rollback")
        return StagingAssessment("in_place", "snapshot", tuple(reasons), True)
    reasons.append("no staging capability: in-place with journal checkpoints")
    return StagingAssessment("in_place", "workspace", tuple(reasons), False)


@dataclass
class WorkflowRun:
    strategy: str
    completed: list[str] = field(default_factory=list)
    current: str | None = PHASES[0]
    aborted: bool = False

    def advance(self, phase: str) -> None:
        if self.aborted:
            raise ValueError("cannot advance an aborted workflow")
        if phase not in PHASES:
            raise ValueError(f"unknown workflow phase {phase!r}")
        expected = PHASES[len(self.completed)] if len(self.completed) < len(PHASES) else None
        if phase != expected:
            raise ValueError(f"expected phase {expected!r}, got {phase!r}")
        self.completed.append(phase)
        self.current = (
            PHASES[len(self.completed)] if len(self.completed) < len(PHASES) else None
        )

    def abort(self, at: str) -> None:
        self.aborted = True
        self.current = at

    @property
    def done(self) -> bool:
        return not self.aborted and len(self.completed) == len(PHASES)

    def to_dict(self) -> dict[str, Any]:
        return {
            "strategy": self.strategy,
            "phases": list(PHASES),
            "completed": list(self.completed),
            "current": self.current,
            "aborted": self.aborted,
            "done": self.done,
        }


def plan_workflow(strategy: str) -> list[str]:
    if strategy not in STRATEGIES:
        raise ValueError(f"unknown migration strategy {strategy!r}")
    return list(PHASES)
