"""Persistent migration journal and explicit state machine.

The journal is evidence of what the engine *attempted*, never proof of what the
system currently contains. After interruption the engine must re-discover and
verify postconditions before resuming. This module owns only journal state and
legal transitions; the executor owns mutations.
"""
from __future__ import annotations

import json
import tempfile
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping

from .release import content_digest
from .versions import VersionSet

STATES = (
    "Discovery", "Planning", "PlanReview", "Prepared", "Executing",
    "Validation", "CommitReady", "Committed", "Interrupted", "Failed",
    "RolledBack", "ResumeRecovery",
)
OPERATION_STATES = (
    "Pending", "Prepared", "Running", "Completed", "Failed", "Interrupted",
    "Recovering", "Recovered", "Skipped", "RequiresIntervention",
)

ALLOWED: dict[str, tuple[str, ...]] = {
    "Discovery": ("Planning", "Failed"),
    "Planning": ("PlanReview", "Failed"),
    "PlanReview": ("Prepared", "Planning", "Failed"),
    "Prepared": ("Executing", "PlanReview", "Failed"),
    "Executing": ("Validation", "Interrupted", "Failed", "ResumeRecovery"),
    "Validation": ("CommitReady", "Executing", "Failed", "ResumeRecovery"),
    "CommitReady": ("Committed", "Validation", "Failed", "ResumeRecovery"),
    "Committed": (),
    "Interrupted": ("ResumeRecovery", "Failed"),
    "Failed": ("ResumeRecovery", "RolledBack"),
    "RolledBack": (),
    "ResumeRecovery": ("Executing", "Validation", "Failed", "Interrupted"),
}


def utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class OperationRecord:
    operation_id: str
    state: str = "Pending"
    start_time: str = ""
    completion_time: str = ""
    input_hash: str = ""
    output_hash: str = ""
    result: str = ""
    recovery_state: str = ""
    error: str = ""
    idempotency: str = "idempotent"
    recovery: str = ""
    approval_policy: str = "automatic"

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "OperationRecord":
        return cls(**{
            key: (str(data[key]) if key in data and key != "operation_id" else data.get(key, ""))
            for key in cls.__dataclass_fields__
        })

    def to_dict(self) -> dict[str, Any]:
        return {key: getattr(self, key) for key in self.__dataclass_fields__}


@dataclass
class MigrationJournal:
    migration_id: str
    state: str = "Discovery"
    source_inventory_hash: str = ""
    target_manifest_hash: str = ""
    plan_hash: str = ""
    versions: VersionSet | None = None
    transition_catalog_hash: str = ""
    artifact_manifest_hash: str = ""
    operations: dict[str, OperationRecord] = field(default_factory=dict)
    checkpoints: list[dict[str, Any]] = field(default_factory=list)
    validation_results: list[dict[str, Any]] = field(default_factory=list)
    commit_state: str = "pending"
    history: list[dict[str, Any]] = field(default_factory=list)
    created_at: str = field(default_factory=utcnow)
    updated_at: str = field(default_factory=utcnow)

    def transition(self, new_state: str, reason: str = "") -> None:
        if new_state not in STATES:
            raise ValueError(f"unknown migration state {new_state!r}")
        allowed = ALLOWED.get(self.state, ())
        if new_state not in allowed:
            raise ValueError(
                f"illegal migration transition {self.state} -> {new_state}"
            )
        self.history.append({
            "from": self.state, "to": new_state,
            "reason": reason, "at": utcnow(),
        })
        self.state = new_state
        self.updated_at = utcnow()
        if new_state == "Committed":
            self.commit_state = "committed"
        elif new_state in ("Interrupted", "Failed", "RolledBack", "ResumeRecovery"):
            self.commit_state = "pending"

    def add_operation(self, record: OperationRecord) -> None:
        if record.operation_id in self.operations:
            raise ValueError(f"duplicate operation {record.operation_id}")
        if not record.recovery and record.idempotency != "idempotent":
            raise ValueError(
                f"operation {record.operation_id}: non-idempotent operations require recovery"
            )
        self.operations[record.operation_id] = record

    def set_operation(self, operation_id: str, state: str, **fields: Any) -> None:
        if state not in OPERATION_STATES:
            raise ValueError(f"unknown operation state {state!r}")
        record = self.operations.get(operation_id)
        if record is None:
            raise KeyError(f"unknown operation {operation_id}")
        record.state = state
        for key, value in fields.items():
            if key in OperationRecord.__dataclass_fields__:
                setattr(record, key, value)
        if state == "Completed":
            record.completion_time = record.completion_time or utcnow()
        if state == "Running":
            record.start_time = record.start_time or utcnow()
        self.updated_at = utcnow()

    def add_checkpoint(self, ref: str, strategy: str = "checkpoint") -> None:
        self.checkpoints.append({
            "ref": ref, "strategy": strategy, "at": utcnow(),
        })

    def last_checkpoint(self) -> dict[str, Any] | None:
        return self.checkpoints[-1] if self.checkpoints else None

    def add_validation(self, name: str, passed: bool, detail: str = "") -> None:
        self.validation_results.append({
            "name": name, "passed": bool(passed), "detail": detail, "at": utcnow(),
        })

    def validate(self) -> list[str]:
        errors: list[str] = []
        if not self.migration_id:
            errors.append("journal has no migration_id")
        if self.state not in STATES:
            errors.append(f"unknown journal state {self.state!r}")
        if self.versions is not None:
            errors.extend(self.versions.validate())
        for op_id, record in self.operations.items():
            if record.state not in OPERATION_STATES:
                errors.append(f"operation {op_id}: unknown state {record.state!r}")
            if record.state in ("Completed", "Failed", "RequiresIntervention") and not record.result:
                errors.append(f"operation {op_id}: terminal state without result")
        if self.state == "Committed" and self.commit_state != "committed":
            errors.append("committed journal has non-committed commit_state")
        return errors

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "MigrationJournal":
        journal = cls(
            migration_id=str(data.get("migration_id", "")),
            state=str(data.get("state", "Discovery")),
            source_inventory_hash=str(data.get("source_inventory_hash", "")),
            target_manifest_hash=str(data.get("target_manifest_hash", "")),
            plan_hash=str(data.get("plan_hash", "")),
            versions=(VersionSet.from_dict(data["versions"]) if data.get("versions") else None),
            transition_catalog_hash=str(data.get("transition_catalog_hash", "")),
            artifact_manifest_hash=str(data.get("artifact_manifest_hash", "")),
            operations={
                str(key): OperationRecord.from_dict(dict(value))
                for key, value in (data.get("operations") or {}).items()
                if isinstance(value, Mapping)
            },
            checkpoints=[dict(c) for c in data.get("checkpoints", [])],
            validation_results=[dict(v) for v in data.get("validation_results", [])],
            commit_state=str(data.get("commit_state", "pending")),
            history=[dict(h) for h in data.get("history", [])],
            created_at=str(data.get("created_at", utcnow())),
            updated_at=str(data.get("updated_at", utcnow())),
        )
        return journal

    def to_dict(self) -> dict[str, Any]:
        return {
            "format": "sunshine-migration-journal-1",
            "migration_id": self.migration_id,
            "state": self.state,
            "source_inventory_hash": self.source_inventory_hash,
            "target_manifest_hash": self.target_manifest_hash,
            "plan_hash": self.plan_hash,
            "versions": self.versions.to_dict() if self.versions else {},
            "transition_catalog_hash": self.transition_catalog_hash,
            "artifact_manifest_hash": self.artifact_manifest_hash,
            "operations": {
                key: self.operations[key].to_dict() for key in sorted(self.operations)
            },
            "checkpoints": self.checkpoints,
            "validation_results": self.validation_results,
            "commit_state": self.commit_state,
            "history": self.history,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "digest": content_digest({
                "migration_id": self.migration_id,
                "state": self.state,
                "plan_hash": self.plan_hash,
                "operations": {
                    key: self.operations[key].to_dict() for key in sorted(self.operations)
                },
            }),
        }

    def save(self, path: str | Path) -> Path:
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        payload = json.dumps(self.to_dict(), indent=2, sort_keys=True)
        fd, temp = tempfile.mkstemp(prefix=target.name + ".", dir=str(target.parent))
        try:
            with __import__("os").fdopen(fd, "w", encoding="utf-8") as handle:
                handle.write(payload)
                handle.flush()
                __import__("os").fsync(handle.fileno())
            Path(temp).replace(target)
        finally:
            if Path(temp).exists():
                Path(temp).unlink()
        return target

    @classmethod
    def load(cls, path: str | Path) -> "MigrationJournal":
        return cls.from_dict(json.loads(Path(path).read_text(encoding="utf-8")))
