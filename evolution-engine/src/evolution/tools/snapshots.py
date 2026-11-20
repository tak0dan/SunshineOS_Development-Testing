"""Capability-based snapshots and rollback points.

Btrfs snapshots are one implementation, not an architecture requirement. The
manager also supports a tar workspace fallback so ext4/LUKS systems receive the
same recovery contract. All mutations are argv-based and routed through an
injectable executor; the journal is written only under ``state_root``.
"""
from __future__ import annotations

import json
import shutil
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping, Sequence

Executor = Callable[[Sequence[str]], tuple[int, str, str]]


def utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(frozen=True)
class SnapshotRecord:
    name: str
    path: str
    backend: str
    source: str
    created_at: str
    metadata: Mapping[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "path": self.path,
            "backend": self.backend,
            "source": self.source,
            "created_at": self.created_at,
            "metadata": dict(sorted(self.metadata.items())),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "SnapshotRecord":
        return cls(
            name=str(data.get("name", "")),
            path=str(data.get("path", "")),
            backend=str(data.get("backend", "")),
            source=str(data.get("source", "")),
            created_at=str(data.get("created_at", "")),
            metadata={
                str(k): str(v) for k, v in (data.get("metadata") or {}).items()
            },
        )


@dataclass(frozen=True)
class SpaceReport:
    total_bytes: int
    used_bytes: int
    free_bytes: int
    required_bytes: int

    @property
    def enough(self) -> bool:
        return self.free_bytes >= self.required_bytes

    def to_dict(self) -> dict[str, Any]:
        return {
            "total_bytes": self.total_bytes,
            "used_bytes": self.used_bytes,
            "free_bytes": self.free_bytes,
            "required_bytes": self.required_bytes,
            "enough": self.enough,
        }


class SnapshotManager:
    """Create, list, prune and restore recovery snapshots deterministically."""

    BACKENDS = ("btrfs", "tar")

    def __init__(
        self,
        state_root: str | Path,
        *,
        executor: Executor | None = None,
        can_snapshot: bool = False,
        time_fn: Callable[[], str] = utcnow,
    ) -> None:
        self.root = Path(state_root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.executor = executor
        self.can_snapshot = bool(can_snapshot)
        self.time_fn = time_fn
        self.record_path = self.root / "snapshots.json"

    def _run(self, argv: Sequence[str]) -> tuple[int, str, str]:
        if self.executor is None:
            import subprocess
            completed = subprocess.run(  # noqa: S603 - argv only, never shell=True
                list(argv), capture_output=True, text=True, check=False
            )
            return completed.returncode, completed.stdout, completed.stderr
        return self.executor(argv)

    def choose_backend(self, requested: str = "auto") -> str:
        if requested == "auto":
            return "btrfs" if self.can_snapshot else "tar"
        if requested not in self.BACKENDS:
            raise ValueError(f"unknown snapshot backend {requested!r}")
        if requested == "btrfs" and not self.can_snapshot:
            raise ValueError("btrfs snapshot backend is not available on this inventory")
        return requested

    def create_commands(self, source: str | Path, destination: str | Path, backend: str) -> list[str]:
        if backend == "btrfs":
            return ["btrfs", "subvolume", "snapshot", "-r", str(source), str(destination)]
        return ["tar", "-C", str(source), "-cf", str(destination), "."]

    def create(
        self,
        source: str | Path,
        name: str,
        *,
        backend: str = "auto",
        metadata: Mapping[str, str] | None = None,
    ) -> SnapshotRecord:
        selected = self.choose_backend(backend)
        if not name or name in {record.name for record in self.list()}:
            raise ValueError(f"invalid or duplicate snapshot name {name!r}")
        destination = self.root / "snapshots" / f"{name}.{'btrfs' if selected == 'btrfs' else 'tar'}"
        destination.parent.mkdir(parents=True, exist_ok=True)
        argv = self.create_commands(source, destination, selected)
        rc, _stdout, stderr = self._run(argv)
        if rc != 0:
            raise RuntimeError(f"snapshot {name} failed: {stderr.strip() or rc}")
        record = SnapshotRecord(
            name=name,
            path=str(destination),
            backend=selected,
            source=str(source),
            created_at=self.time_fn(),
            metadata=dict(metadata or {}),
        )
        records = self.list()
        records.append(record)
        self._save(records)
        return record

    def restore_commands(self, record: SnapshotRecord, target: str | Path) -> list[str]:
        if record.backend == "btrfs":
            return ["btrfs", "subvolume", "snapshot", record.path, str(target)]
        return ["tar", "-C", str(target), "-xf", record.path]

    def restore(self, name: str, target: str | Path) -> list[str]:
        record = self.get(name)
        argv = self.restore_commands(record, target)
        rc, _stdout, stderr = self._run(argv)
        if rc != 0:
            raise RuntimeError(f"snapshot restore {name} failed: {stderr.strip() or rc}")
        return argv

    def list(self) -> list[SnapshotRecord]:
        if not self.record_path.is_file():
            return []
        payload = json.loads(self.record_path.read_text(encoding="utf-8"))
        return [SnapshotRecord.from_dict(item) for item in payload.get("snapshots", [])]

    def get(self, name: str) -> SnapshotRecord:
        for record in self.list():
            if record.name == name:
                return record
        raise KeyError(f"unknown snapshot {name!r}")

    def prune(self, keep: int = 3) -> list[str]:
        if keep < 0:
            raise ValueError("keep must be non-negative")
        records = self.list()
        removable = records[: len(records) - keep] if keep else records
        kept: list[SnapshotRecord] = []
        for record in records:
            if record in removable:
                rc, _stdout, stderr = self._run(["rm", "-f", record.path])
                if rc != 0:
                    raise RuntimeError(f"snapshot prune failed: {stderr.strip() or rc}")
            else:
                kept.append(record)
        self._save(kept)
        return [record.name for record in removable]

    def space_report(self, required_bytes: int, path: str | Path | None = None) -> SpaceReport:
        usage = shutil.disk_usage(str(path or self.root))
        return SpaceReport(
            total_bytes=usage.total, used_bytes=usage.used,
            free_bytes=usage.free, required_bytes=int(required_bytes),
        )

    def _save(self, records: Iterable[SnapshotRecord]) -> None:
        payload = json.dumps(
            {"format": "sunshine-snapshot-journal-1",
             "snapshots": [record.to_dict() for record in records]},
            indent=2, sort_keys=True,
        )
        temp = self.record_path.with_suffix(".json.tmp")
        temp.write_text(payload, encoding="utf-8")
        temp.replace(self.record_path)
