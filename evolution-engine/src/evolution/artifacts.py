"""Content-addressed artifact manager with retention tiers.

Migration knowledge must not depend on today's live repositories. Artifacts are
identified by content hash, signed, classified by retention tier, and verified
periodically. No network access is performed here: retrieval is a separate
concern, and offline fixtures work with local files only.
"""
from __future__ import annotations

import hashlib
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping

RETENTION_TIERS = ("A", "B", "C", "D")
ARTIFACT_TYPES = (
    "baseline_iso", "baseline_manifest", "evolution_ledger", "transition_catalog",
    "migration_engine", "inventory_schema", "evolution_schema", "package_metadata",
    "system_package", "recovery_tooling", "migration_manifest", "test_results",
    "repository_metadata", "package_archive", "trust_metadata",
)


def sha256_file(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


@dataclass(frozen=True)
class ArtifactRecord:
    artifact_id: str
    artifact_type: str
    content_hash: str
    size: int
    source: str = ""
    signature: str = ""
    signer: str = ""
    dependencies: tuple[str, ...] = ()
    compatibility: Mapping[str, str] = frozenset()  # type: ignore[assignment]
    retention_class: str = "A"
    verification_status: str = "unverified"

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "ArtifactRecord":
        return cls(
            artifact_id=str(data.get("artifact_id", "")),
            artifact_type=str(data.get("artifact_type", "")),
            content_hash=str(data.get("content_hash", "")).lower(),
            size=int(data.get("size", 0)),
            source=str(data.get("source", "")),
            signature=str(data.get("signature", "")),
            signer=str(data.get("signer", "")),
            dependencies=tuple(str(d) for d in data.get("dependencies", [])),
            compatibility=frozenset(
                (str(k), str(v)) for k, v in (data.get("compatibility") or {}).items()
            ),
            retention_class=str(data.get("retention_class", "A")).upper(),
            verification_status=str(data.get("verification_status", "unverified")),
        )

    def validate(self) -> list[str]:
        errors: list[str] = []
        if not self.artifact_id:
            errors.append("artifact has no id")
        if self.artifact_type not in ARTIFACT_TYPES:
            errors.append(f"artifact {self.artifact_id}: unknown type {self.artifact_type!r}")
        if len(self.content_hash) != 64:
            errors.append(f"artifact {self.artifact_id}: malformed content_hash")
        if self.size < 0:
            errors.append(f"artifact {self.artifact_id}: negative size")
        if self.retention_class not in RETENTION_TIERS:
            errors.append(
                f"artifact {self.artifact_id}: unknown retention class {self.retention_class!r}"
            )
        if self.verification_status not in ("unverified", "verified", "failed"):
            errors.append(
                f"artifact {self.artifact_id}: unknown verification status "
                f"{self.verification_status!r}"
            )
        return errors

    def to_dict(self) -> dict[str, Any]:
        return {
            "artifact_id": self.artifact_id,
            "artifact_type": self.artifact_type,
            "content_hash": self.content_hash,
            "size": self.size,
            "source": self.source,
            "signature": self.signature,
            "signer": self.signer,
            "dependencies": list(self.dependencies),
            "compatibility": {k: self.compatibility[k] for k in sorted(self.compatibility)},
            "retention_class": self.retention_class,
            "verification_status": self.verification_status,
        }


@dataclass(frozen=True)
class VerificationReport:
    passed: bool
    results: tuple[dict[str, Any], ...]

    def to_dict(self) -> dict[str, Any]:
        return {"passed": self.passed, "results": list(self.results)}


class ContentAddressedArchive:
    """Store and verify artifacts under ``root/<hash[:2]>/<hash>``."""

    def __init__(self, root: str | Path) -> None:
        self.root = Path(root)

    def path_for(self, content_hash: str) -> Path:
        key = str(content_hash).lower()
        if len(key) != 64:
            raise ValueError(f"malformed content hash {content_hash!r}")
        return self.root / key[:2] / key

    def store(self, path: str | Path, record: ArtifactRecord) -> Path:
        actual = sha256_file(path)
        if actual != record.content_hash:
            raise ValueError(
                f"artifact {record.artifact_id}: digest mismatch ({actual} != {record.content_hash})"
            )
        destination = self.path_for(record.content_hash)
        destination.parent.mkdir(parents=True, exist_ok=True)
        if not destination.exists():
            shutil.copy2(path, destination)
        return destination

    def locate(self, record: ArtifactRecord) -> Path | None:
        candidate = self.path_for(record.content_hash)
        return candidate if candidate.is_file() else None

    def verify(self, record: ArtifactRecord, *, require_signature: bool = False) -> dict[str, Any]:
        errors = list(record.validate())
        path = self.locate(record)
        if path is None:
            errors.append(f"artifact {record.artifact_id}: not present in archive")
        else:
            actual = sha256_file(path)
            if actual != record.content_hash:
                errors.append(
                    f"artifact {record.artifact_id}: stored digest mismatch ({actual})"
                )
            if actual != str(path.name):
                errors.append(f"artifact {record.artifact_id}: path does not match content hash")
        if require_signature and not record.signature:
            errors.append(f"artifact {record.artifact_id}: signature is required but absent")
        return {
            "artifact_id": record.artifact_id,
            "passed": not errors,
            "errors": errors,
        }

    def verify_all(
        self, records: Iterable[ArtifactRecord], *, require_signature: bool = False
    ) -> VerificationReport:
        results = tuple(
            self.verify(record, require_signature=require_signature) for record in records
        )
        return VerificationReport(all(r["passed"] for r in results), results)

    def manifest(self, records: Iterable[ArtifactRecord]) -> dict[str, Any]:
        return {
            "format": "sunshine-artifact-manifest-1",
            "artifacts": [r.to_dict() for r in sorted(records, key=lambda a: a.artifact_id)],
        }
