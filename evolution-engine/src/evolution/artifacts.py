"""Content-addressed artifact manager with retention tiers.

Migration knowledge must not depend on today's live repositories. Artifacts are
identified by content hash, signed, classified by retention tier, and verified
periodically. No network access is performed here: retrieval is a separate
concern, and offline fixtures work with local files only.
"""
from __future__ import annotations

import hashlib
import os
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping

from ..trust.model import canonical_bytes

SignatureVerifier = Callable[[str, bytes, str], bool]

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
    compatibility: Mapping[str, str] = field(default_factory=dict)
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
            compatibility={
                str(k): str(v) for k, v in (data.get("compatibility") or {}).items()
            },
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
        elif any(char not in "0123456789abcdef" for char in self.content_hash):
            errors.append(f"artifact {self.artifact_id}: content_hash is not hexadecimal")
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

    def signable(self) -> dict[str, Any]:
        """Return stable artifact metadata covered by the detached signature."""
        payload = self.to_dict()
        payload.pop("signature")
        payload.pop("verification_status")
        return payload


@dataclass(frozen=True)
class VerificationReport:
    passed: bool
    results: tuple[dict[str, Any], ...]

    def to_dict(self) -> dict[str, Any]:
        return {"passed": self.passed, "results": list(self.results)}


@dataclass(frozen=True)
class ArtifactManifest:
    """Signed inventory of the exact historical artifacts a release depends on."""

    artifacts: tuple[ArtifactRecord, ...]
    signed_by: str = ""
    signature: str = ""
    format: str = "sunshine-artifact-manifest-1"

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "ArtifactManifest":
        raw = data.get("artifacts", [])
        if not isinstance(raw, list):
            raise ValueError("artifact manifest 'artifacts' must be a list")
        if any(not isinstance(item, Mapping) for item in raw):
            raise ValueError("artifact manifest contains a malformed artifact record")
        return cls(
            artifacts=tuple(ArtifactRecord.from_dict(item) for item in raw),
            signed_by=str(data.get("signed_by", "")),
            signature=str(data.get("signature", "")),
            format=str(data.get("format", "")),
        )

    def payload(self) -> dict[str, Any]:
        return {
            "format": self.format,
            "artifacts": [
                record.to_dict()
                for record in sorted(self.artifacts, key=lambda item: item.artifact_id)
            ],
        }

    def validate(self) -> list[str]:
        errors: list[str] = []
        if self.format != "sunshine-artifact-manifest-1":
            errors.append(f"unsupported artifact manifest format {self.format!r}")
        ids: set[str] = set()
        for record in self.artifacts:
            if record.artifact_id in ids:
                errors.append(f"duplicate artifact id {record.artifact_id!r}")
            ids.add(record.artifact_id)
            errors.extend(record.validate())
        if not self.artifacts:
            errors.append("artifact manifest is empty")
        return errors

    def to_dict(self) -> dict[str, Any]:
        return {**self.payload(), "signed_by": self.signed_by, "signature": self.signature}

    def verify(
        self,
        verifier: SignatureVerifier,
        trusted_signers: Iterable[str],
    ) -> dict[str, Any]:
        errors = self.validate()
        signer = self.signed_by.strip().upper()
        trusted = {str(value).strip().upper() for value in trusted_signers}
        if not self.signature:
            errors.append("artifact manifest signature is absent")
        if not signer or signer not in trusted:
            errors.append(f"artifact manifest signer {signer or '(empty)'} is not trusted")
        if self.signature and signer and signer in trusted:
            try:
                if not verifier(signer, canonical_bytes(self.payload()), self.signature):
                    errors.append(f"artifact manifest signature from {signer} is invalid")
            except Exception as exc:
                errors.append(f"artifact manifest signature verification error: {exc}")
        return {"passed": not errors, "errors": errors}


class ContentAddressedArchive:
    """Store and verify artifacts under ``root/<hash[:2]>/<hash>``."""

    def __init__(self, root: str | Path) -> None:
        self.root = Path(root)

    def path_for(self, content_hash: str) -> Path:
        key = str(content_hash).lower()
        if len(key) != 64 or any(char not in "0123456789abcdef" for char in key):
            raise ValueError(f"malformed content hash {content_hash!r}")
        return self.root / key[:2] / key

    def store(self, path: str | Path, record: ArtifactRecord) -> Path:
        source = Path(path)
        actual = sha256_file(source)
        if actual != record.content_hash:
            raise ValueError(
                f"artifact {record.artifact_id}: digest mismatch ({actual} != {record.content_hash})"
            )
        source_size = source.stat().st_size
        if source_size != record.size:
            raise ValueError(
                f"artifact {record.artifact_id}: size mismatch "
                f"({source_size} != {record.size})"
            )
        destination = self.path_for(record.content_hash)
        destination.parent.mkdir(parents=True, exist_ok=True)
        if (destination.is_file() and not destination.is_symlink()
                and sha256_file(destination) == record.content_hash):
            return destination

        # Publish only complete content: a crash leaves an unreferenced temp
        # file rather than a truncated object at the immutable hash path.
        fd, temporary = tempfile.mkstemp(prefix=".artifact-", dir=destination.parent)
        try:
            with source.open("rb") as input_handle, os.fdopen(fd, "wb") as output_handle:
                for chunk in iter(lambda: input_handle.read(1024 * 1024), b""):
                    output_handle.write(chunk)
                output_handle.flush()
                os.fsync(output_handle.fileno())
            if sha256_file(temporary) != record.content_hash:
                raise ValueError(f"artifact {record.artifact_id}: staged copy failed digest check")
            os.replace(temporary, destination)
            directory_fd = os.open(destination.parent, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
            try:
                os.fsync(directory_fd)
            finally:
                os.close(directory_fd)
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)
        return destination

    def locate(self, record: ArtifactRecord) -> Path | None:
        candidate = self.path_for(record.content_hash)
        return candidate if candidate.is_file() and not candidate.is_symlink() else None

    def verify(
        self,
        record: ArtifactRecord,
        *,
        require_signature: bool = False,
        verifier: SignatureVerifier | None = None,
        trusted_signers: Iterable[str] | None = None,
    ) -> dict[str, Any]:
        errors = list(record.validate())
        if require_signature:
            signer = record.signer.strip().upper()
            trusted = {str(value).strip().upper() for value in (trusted_signers or ())}
            if not record.signature:
                errors.append(f"artifact {record.artifact_id}: signature is required but absent")
            elif not signer:
                errors.append(f"artifact {record.artifact_id}: signer is required")
            elif verifier is None:
                errors.append(f"artifact {record.artifact_id}: signature verifier is required")
            elif trusted_signers is None or not trusted:
                errors.append(f"artifact {record.artifact_id}: trusted signer set is required")
            elif signer not in trusted:
                errors.append(f"artifact {record.artifact_id}: signer {signer} is not trusted")
            else:
                try:
                    if not verifier(signer, canonical_bytes(record.signable()), record.signature):
                        errors.append(f"artifact {record.artifact_id}: invalid signature from {signer}")
                except Exception as exc:
                    errors.append(f"artifact {record.artifact_id}: signature verification error: {exc}")
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
            if path.stat().st_size != record.size:
                errors.append(
                    f"artifact {record.artifact_id}: size mismatch "
                    f"({path.stat().st_size} != {record.size})"
                )
        return {
            "artifact_id": record.artifact_id,
            "passed": not errors,
            "errors": errors,
        }

    def verify_all(
        self,
        records: Iterable[ArtifactRecord],
        *,
        require_signature: bool = False,
        verifier: SignatureVerifier | None = None,
        trusted_signers: Iterable[str] | None = None,
    ) -> VerificationReport:
        trusted = tuple(trusted_signers) if trusted_signers is not None else None
        results = tuple(
            self.verify(
                record, require_signature=require_signature, verifier=verifier,
                trusted_signers=trusted,
            ) for record in records
        )
        return VerificationReport(all(r["passed"] for r in results), results)

    def manifest(self, records: Iterable[ArtifactRecord]) -> dict[str, Any]:
        manifest = ArtifactManifest(tuple(records))
        errors = manifest.validate()
        if errors:
            raise ValueError("invalid artifact manifest: " + "; ".join(errors))
        return manifest.payload()

    def signed_manifest(
        self, records: Iterable[ArtifactRecord], *, signed_by: str, signature: str
    ) -> dict[str, Any]:
        """Serialize a manifest signed externally over ``ArtifactManifest.payload()``."""
        manifest = ArtifactManifest(tuple(records), signed_by=signed_by, signature=signature)
        errors = manifest.validate()
        if errors:
            raise ValueError("invalid artifact manifest: " + "; ".join(errors))
        return manifest.to_dict()
