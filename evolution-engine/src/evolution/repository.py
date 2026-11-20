"""Signed milestone repository with offline fixtures and tamper detection.

The published milestone manifest is a signed JSON envelope. Its payload carries
the scheme digest, milestone chain metadata and artifact references. Verification
uses the existing Stage A trust primitives (``canonical_bytes`` and
``verify_signed_document``) so a rotated Stage A trust root governs milestone
publications too. No network access is performed: all reads are local files.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from ..trust.model import SignedDocument, verify_signed_document
from .release import content_digest
from .scheme import Scheme

Verifier = Any  # Callable[[str, bytes, str], bool] from the Stage A trust package


@dataclass(frozen=True)
class MilestoneManifest:
    format_version: int
    repository_generation: int
    scheme_digest: str
    current: str
    milestones: tuple[dict[str, Any], ...]
    artifacts: Mapping[str, str]
    signed_by: str
    signature: str

    @classmethod
    def from_envelope(cls, envelope: Mapping[str, Any]) -> "MilestoneManifest":
        payload = dict(envelope.get("payload") or {})
        return cls(
            format_version=int(payload.get("format_version", 0)),
            repository_generation=int(payload.get("repository_generation", 0)),
            scheme_digest=str(payload.get("scheme_digest", "")).lower(),
            current=str(payload.get("current", "")),
            milestones=tuple(
                dict(m) for m in payload.get("milestones", []) if isinstance(m, Mapping)
            ),
            artifacts=frozenset(
                (str(k), str(v)) for k, v in (payload.get("artifacts") or {}).items()
            ),  # type: ignore[arg-type]
            signed_by=str(envelope.get("signed_by", "")),
            signature=str(envelope.get("signature", "")),
        )

    def payload(self) -> dict[str, Any]:
        return {
            "format_version": self.format_version,
            "repository_generation": self.repository_generation,
            "scheme_digest": self.scheme_digest,
            "current": self.current,
            "milestones": [dict(m) for m in self.milestones],
            "artifacts": dict(self.artifacts),
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "payload": self.payload(),
            "signed_by": self.signed_by,
            "signature": self.signature,
        }


@dataclass(frozen=True)
class RepositoryReport:
    passed: bool
    errors: tuple[str, ...] = ()
    signed_by: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "passed": self.passed,
            "errors": list(self.errors),
            "signed_by": self.signed_by,
        }


class MilestoneRepository:
    """Load and verify a local signed milestone manifest."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    @classmethod
    def publish(
        cls,
        path: str | Path,
        scheme: Scheme,
        repository_generation: int,
        *,
        signed_by: str,
        sign: Any,
        artifacts: Mapping[str, str] | None = None,
    ) -> MilestoneManifest:
        """Create a signed fixture/publication using an injected signer."""
        payload = {
            "format_version": 1,
            "repository_generation": int(repository_generation),
            "scheme_digest": content_digest(scheme.to_dict()),
            "current": str(scheme.registry.current),
            "milestones": [
                {"version": str(m.version), "id": m.id, "published": m.published}
                for m in scheme.registry.milestones
            ],
            "artifacts": dict(artifacts or {}),
        }
        signature = sign(signed_by, json.dumps(
            payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True
        ).encode("utf-8"))
        envelope = {"payload": payload, "signed_by": signed_by, "signature": signature}
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(envelope, indent=2, sort_keys=True), encoding="utf-8")
        return MilestoneManifest.from_envelope(envelope)

    def load(self) -> MilestoneManifest:
        if not self.path.is_file():
            raise ValueError(f"milestone manifest not found: {self.path}")
        return MilestoneManifest.from_envelope(
            json.loads(self.path.read_text(encoding="utf-8"))
        )

    def verify(
        self,
        manifest: MilestoneManifest,
        *,
        trusted_keys: set[str],
        verifier: Verifier,
        expected_scheme: Scheme | None = None,
    ) -> RepositoryReport:
        errors: list[str] = []
        from ..trust.model import canonical_bytes  # local import avoids cycles

        document = SignedDocument(
            payload=manifest.payload(),
            signature=manifest.signature,
            signed_by=manifest.signed_by,
        )
        if not verify_signed_document(document, set(trusted_keys), verifier, errors, "milestone manifest"):
            return RepositoryReport(False, tuple(errors), manifest.signed_by)
        if manifest.format_version != 1:
            errors.append(f"unsupported milestone manifest format {manifest.format_version}")
        if manifest.repository_generation <= 0:
            errors.append("repository_generation must be positive")
        if not manifest.scheme_digest or len(manifest.scheme_digest) != 64:
            errors.append("malformed scheme_digest")
        if expected_scheme is not None:
            actual = content_digest(expected_scheme.to_dict())
            if actual != manifest.scheme_digest:
                errors.append(
                    f"scheme digest mismatch ({actual} != {manifest.scheme_digest})"
                )
        versions = sorted(str(m.get("version", "")) for m in manifest.milestones)
        if len(versions) != len(set(versions)):
            errors.append("manifest has duplicate milestone versions")
        return RepositoryReport(not errors, tuple(errors), manifest.signed_by)

    def verify_file(
        self,
        *,
        trusted_keys: set[str],
        verifier: Verifier,
        expected_scheme: Scheme | None = None,
    ) -> tuple[MilestoneManifest | None, RepositoryReport]:
        manifest = self.load()
        report = self.verify(
            manifest, trusted_keys=trusted_keys, verifier=verifier,
            expected_scheme=expected_scheme,
        )
        return (manifest if report.passed else None), report
