"""Versioned, hash-verifiable catalogue of external system research evidence.

Research conclusions must remain tied to exact source files. This module records
provenance and checks local snapshots; it never executes source content or
promotes a finding into migration policy by itself.
"""
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_COMMIT = re.compile(r"^[0-9a-f]{40,64}$")


@dataclass(frozen=True)
class ResearchSource:
    source_id: str
    relative_path: str
    sha256: str
    finding: str
    adoption: str
    limitation: str
    status: str = "verified"

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "ResearchSource":
        return cls(**{key: str(data.get(key, "")) for key in (
            "source_id", "relative_path", "sha256", "finding", "adoption",
            "limitation", "status",
        )})


@dataclass(frozen=True)
class ResearchCatalog:
    catalog_id: str
    schema: int
    project: str
    commit: str
    sources: tuple[ResearchSource, ...]

    @classmethod
    def load(cls, path: str | Path) -> "ResearchCatalog":
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        if not isinstance(data, dict) or not isinstance(data.get("sources"), list):
            raise ValueError("research catalog must be an object with a sources list")
        return cls(
            catalog_id=str(data.get("catalog_id", "")),
            schema=int(data.get("schema", 0)),
            project=str(data.get("project", "")),
            commit=str(data.get("commit", "")),
            sources=tuple(ResearchSource.from_dict(item) for item in data["sources"]),
        )

    def validate(self) -> list[str]:
        errors: list[str] = []
        if not self.catalog_id:
            errors.append("catalog has no id")
        if self.schema != 1:
            errors.append(f"unsupported research catalog schema {self.schema}")
        if not _COMMIT.fullmatch(self.commit):
            errors.append("catalog commit must be a full hexadecimal commit id")
        if not self.sources:
            errors.append("catalog has no source records")
        seen: set[str] = set()
        for record in self.sources:
            prefix = f"source {record.source_id or '<empty>'}"
            if not record.source_id or record.source_id in seen:
                errors.append(f"{prefix}: missing or duplicate id")
            seen.add(record.source_id)
            rel = Path(record.relative_path)
            if not record.relative_path or rel.is_absolute() or ".." in rel.parts:
                errors.append(f"{prefix}: path must be a safe relative path")
            if not _SHA256.fullmatch(record.sha256):
                errors.append(f"{prefix}: malformed SHA-256")
            if record.status != "verified":
                errors.append(f"{prefix}: unsupported evidence status {record.status!r}")
            for field_name in ("finding", "adoption", "limitation"):
                if not getattr(record, field_name).strip():
                    errors.append(f"{prefix}: {field_name} is required")
        return errors

    def verify_sources(self, source_root: str | Path) -> list[str]:
        """Compare catalogue hashes with files below the supplied source root."""
        errors = self.validate()
        if errors:
            return errors
        root = Path(source_root).resolve()
        for record in self.sources:
            candidate = (root / record.relative_path).resolve()
            if not candidate.is_relative_to(root):
                errors.append(f"source {record.source_id}: resolved path escapes source root")
                continue
            if not candidate.is_file():
                errors.append(f"source {record.source_id}: source file is missing")
                continue
            digest = hashlib.sha256(candidate.read_bytes()).hexdigest()
            if digest != record.sha256:
                errors.append(f"source {record.source_id}: SHA-256 mismatch")
        return errors
