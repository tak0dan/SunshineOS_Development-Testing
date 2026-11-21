"""Capability-based snapshots and rollback points.

Btrfs snapshots are one implementation, not an architecture requirement. The
manager also supports a tar workspace fallback so ext4/LUKS systems receive the
same recovery contract. All mutations are argv-based and routed through an
injectable executor; the journal is written only under ``state_root``.
"""
from __future__ import annotations

import json
import os
import re
import shutil
import tempfile
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping, Sequence

from ..release import content_digest

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
    NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")

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
        if not self.NAME.fullmatch(name) or name in {record.name for record in self.list()}:
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
        if not Path(record.path).exists():
            raise FileNotFoundError(f"snapshot data is missing: {record.name}")
        argv = self.restore_commands(record, target)
        rc, _stdout, stderr = self._run(argv)
        if rc != 0:
            raise RuntimeError(f"snapshot restore {name} failed: {stderr.strip() or rc}")
        return argv

    def list(self) -> list[SnapshotRecord]:
        if not self.record_path.is_file():
            return []
        payload = json.loads(self.record_path.read_text(encoding="utf-8"))
        format_name = str(payload.get("format", "sunshine-snapshot-journal-1"))
        if format_name not in ("sunshine-snapshot-journal-1", "sunshine-snapshot-journal-2"):
            raise ValueError(f"unsupported snapshot journal format {format_name!r}")
        if format_name == "sunshine-snapshot-journal-2":
            digest = str(payload.get("digest", ""))
            unsigned = {key: value for key, value in payload.items() if key != "digest"}
            if not digest or digest != content_digest(unsigned):
                raise ValueError("snapshot journal digest is missing or invalid")
        raw_records = payload.get("snapshots", [])
        if not isinstance(raw_records, list) or any(
            not isinstance(item, Mapping) for item in raw_records
        ):
            raise ValueError("snapshot journal records are malformed")
        records = [SnapshotRecord.from_dict(item) for item in raw_records]
        seen: set[str] = set()
        allowed_root = (self.root / "snapshots").resolve()
        for record in records:
            if not self.NAME.fullmatch(record.name) or record.name in seen:
                raise ValueError("snapshot journal has an invalid or duplicate name")
            seen.add(record.name)
            if record.backend not in self.BACKENDS:
                raise ValueError(f"snapshot {record.name}: unsupported backend {record.backend!r}")
            suffix = "btrfs" if record.backend == "btrfs" else "tar"
            candidate = Path(record.path)
            if not candidate.is_absolute() or candidate.is_symlink():
                raise ValueError(f"snapshot {record.name}: unsafe snapshot path")
            try:
                candidate.resolve(strict=False).relative_to(allowed_root)
            except (OSError, ValueError):
                raise ValueError(f"snapshot {record.name}: path escapes snapshot storage")
            if candidate.name != f"{record.name}.{suffix}":
                raise ValueError(f"snapshot {record.name}: path does not match its identity")
        return records

    def get(self, name: str) -> SnapshotRecord:
        for record in self.list():
            if record.name == name:
                return record
        raise KeyError(f"unknown snapshot {name!r}")

    def prune(self, keep: int = 3) -> list[str]:
        if keep < 0:
            raise ValueError("keep must be non-negative")
        records = self.list()
        removable = records[:max(0, len(records) - keep)]
        kept: list[SnapshotRecord] = []
        for record in records:
            if record in removable:
                snapshot_path = Path(record.path)
                if snapshot_path.exists():
                    command = (
                        ["btrfs", "subvolume", "delete", record.path]
                        if record.backend == "btrfs" else ["unlink", record.path]
                    )
                    rc, _stdout, stderr = self._run(command)
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
        document = {
            "format": "sunshine-snapshot-journal-2",
            "snapshots": [record.to_dict() for record in records],
        }
        document["digest"] = content_digest(document)
        payload = json.dumps(document, indent=2, sort_keys=True)
        fd, temporary = tempfile.mkstemp(prefix="snapshots.", dir=self.root)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                handle.write(payload)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary, self.record_path)
            directory_fd = os.open(self.root, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
            try:
                os.fsync(directory_fd)
            finally:
                os.close(directory_fd)
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)
