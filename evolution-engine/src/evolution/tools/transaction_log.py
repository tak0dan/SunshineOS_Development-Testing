"""Crash-safe transaction journal with explicit compensations.

The log records intent and evidence around every mutation. It never pretends a
journal entry proves a postcondition: after an interrupted transaction the
engine must re-observe the machine. Every non-idempotent operation must carry a
compensation identifier before it can be recorded.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping, Sequence

Compensate = Callable[[str, "Differential"], tuple[bool, str]]


def utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(frozen=True)
class Differential:
    """One observed before/after state transition and its undo reference."""

    operation_id: str
    target: str
    before_hash: str
    after_hash: str
    reversible: bool = True
    compensation: str = ""
    metadata: Mapping[str, str] = field(default_factory=dict)

    def validate(self) -> list[str]:
        errors: list[str] = []
        if not self.operation_id:
            errors.append("differential has no operation_id")
        if not self.target:
            errors.append(f"operation {self.operation_id}: no target")
        if not self.before_hash or not self.after_hash:
            errors.append(f"operation {self.operation_id}: missing before/after hash")
        if not self.reversible and not self.compensation:
            errors.append(f"operation {self.operation_id}: irreversible without compensation")
        return errors

    def to_dict(self) -> dict[str, Any]:
        return {
            "operation_id": self.operation_id,
            "target": self.target,
            "before_hash": self.before_hash,
            "after_hash": self.after_hash,
            "reversible": self.reversible,
            "compensation": self.compensation,
            "metadata": dict(sorted(self.metadata.items())),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "Differential":
        return cls(
            operation_id=str(data.get("operation_id", "")),
            target=str(data.get("target", "")),
            before_hash=str(data.get("before_hash", "")),
            after_hash=str(data.get("after_hash", "")),
            reversible=bool(data.get("reversible", True)),
            compensation=str(data.get("compensation", "")),
            metadata={str(k): str(v) for k, v in (data.get("metadata") or {}).items()},
        )


@dataclass
class TransactionSession:
    transaction_id: str
    state: str = "open"
    started_at: str = field(default_factory=utcnow)
    metadata: dict[str, str] = field(default_factory=dict)
    records: list[Differential] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "transaction_id": self.transaction_id,
            "state": self.state,
            "started_at": self.started_at,
            "metadata": dict(sorted(self.metadata.items())),
            "records": [record.to_dict() for record in self.records],
        }


class TransactionLog:
    """Append-only JSONL log with bounded, ordered rollback."""

    def __init__(
        self,
        state_root: str | Path,
        *,
        compensate_fn: Compensate | None = None,
        time_fn: Callable[[], str] = utcnow,
        name: str = "transactions.jsonl",
    ) -> None:
        self.root = Path(state_root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.path = self.root / name
        self.compensate_fn = compensate_fn
        self.time_fn = time_fn

    def _append(self, entry: Mapping[str, Any]) -> dict[str, Any]:
        payload = dict(entry)
        payload.setdefault("at", self.time_fn())
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, sort_keys=True, ensure_ascii=True) + "\n")
        return payload

    def begin(
        self, transaction_id: str, metadata: Mapping[str, str] | None = None
    ) -> TransactionSession:
        if not transaction_id:
            raise ValueError("transaction needs an id")
        if transaction_id in {s.transaction_id for s in self.open_sessions()}:
            raise ValueError(f"transaction already open: {transaction_id}")
        session = TransactionSession(
            transaction_id=transaction_id,
            started_at=self.time_fn(),
            metadata={str(k): str(v) for k, v in (metadata or {}).items()},
        )
        self._append({
            "event": "BEGIN", "transaction_id": transaction_id,
            "metadata": session.metadata, "at": session.started_at,
        })
        return session

    def record(self, session: TransactionSession, differential: Differential) -> None:
        errors = differential.validate()
        if errors:
            raise ValueError("; ".join(errors))
        if session.state != "open":
            raise ValueError(f"transaction {session.transaction_id} is {session.state}")
        if any(r.operation_id == differential.operation_id for r in session.records):
            raise ValueError(f"duplicate operation {differential.operation_id}")
        session.records.append(differential)
        self._append({
            "event": "RECORD", "transaction_id": session.transaction_id,
            "operation": differential.to_dict(),
        })

    def commit(self, session: TransactionSession) -> None:
        if session.state != "open":
            raise ValueError(f"transaction {session.transaction_id} is {session.state}")
        self._append({"event": "COMMIT", "transaction_id": session.transaction_id})
        session.state = "committed"

    def rollback(self, session: TransactionSession) -> list[str]:
        if session.state != "open":
            raise ValueError(f"transaction {session.transaction_id} is {session.state}")
        completed: list[str] = []
        for record in reversed(session.records):
            self._append({
                "event": "ROLLBACK", "transaction_id": session.transaction_id,
                "operation_id": record.operation_id, "compensation": record.compensation,
            })
            if self.compensate_fn is None:
                session.state = "rollback_failed"
                self._append({
                    "event": "ROLLBACK_FAILED", "transaction_id": session.transaction_id,
                    "error": f"no compensation runtime for {record.compensation}",
                })
                raise RuntimeError(f"no compensation runtime for {record.compensation}")
            ok, detail = self.compensate_fn(record.compensation, record)
            if not ok:
                session.state = "rollback_failed"
                self._append({
                    "event": "ROLLBACK_FAILED", "transaction_id": session.transaction_id,
                    "error": detail,
                })
                raise RuntimeError(f"compensation {record.compensation} failed: {detail}")
            completed.append(record.operation_id)
        session.state = "rolled_back"
        self._append({"event": "ROLLBACK_COMPLETE", "transaction_id": session.transaction_id})
        return completed

    def events(self) -> list[dict[str, Any]]:
        if not self.path.is_file():
            return []
        return [
            json.loads(line) for line in self.path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]

    def open_sessions(self) -> list[TransactionSession]:
        sessions: dict[str, TransactionSession] = {}
        for event in self.events():
            txid = str(event.get("transaction_id", ""))
            kind = str(event.get("event", ""))
            if kind == "BEGIN":
                sessions[txid] = TransactionSession(
                    transaction_id=txid,
                    started_at=str(event.get("at", utcnow())),
                    metadata=dict(event.get("metadata") or {}),
                )
            elif txid not in sessions:
                continue
            elif kind == "RECORD":
                sessions[txid].records.append(Differential.from_dict(event.get("operation") or {}))
            elif kind in ("COMMIT", "ROLLBACK_COMPLETE"):
                sessions[txid].state = kind.lower().replace("_complete", "")
            elif kind == "ROLLBACK_FAILED":
                sessions[txid].state = "rollback_failed"
        return [session for session in sessions.values() if session.state == "open"]
