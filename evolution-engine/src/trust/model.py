"""Typed trust model and Stage A verification (stdlib only)."""
from __future__ import annotations

import hashlib
import json
import subprocess
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Mapping

Verifier = Callable[[str, bytes, str], bool]


def canonical_bytes(value: Any) -> bytes:
    """Canonical JSON used for signatures and digests."""
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, default=str
    ).encode("utf-8")


def sha256_file(path: str | Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _version_tuple(value: str) -> tuple[int, ...]:
    parts: list[int] = []
    for token in str(value or "0").replace("-", ".").split("."):
        digits = "".join(ch for ch in token if ch.isdigit())
        parts.append(int(digits) if digits else 0)
    return tuple(parts)


@dataclass(frozen=True)
class TrustRoot:
    fingerprint: str
    description: str = ""

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "TrustRoot":
        return cls(
            fingerprint=str(data.get("fingerprint", "")).strip().upper(),
            description=str(data.get("description", "")),
        )


@dataclass(frozen=True)
class KeyRotation:
    """A new trust key, signed by a key that is already trusted."""

    new_fingerprint: str
    signed_by: str
    signature: str
    valid_after: str = ""
    revokes: tuple[str, ...] = ()
    reason: str = ""

    def signable(self) -> dict[str, Any]:
        return {
            "new_fingerprint": self.new_fingerprint,
            "valid_after": self.valid_after,
            "revokes": list(self.revokes),
            "reason": self.reason,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "KeyRotation":
        return cls(
            new_fingerprint=str(data.get("new_fingerprint", "")).strip().upper(),
            signed_by=str(data.get("signed_by", "")).strip().upper(),
            signature=str(data.get("signature", "")),
            valid_after=str(data.get("valid_after", "")),
            revokes=tuple(str(r).strip().upper() for r in data.get("revokes", [])),
            reason=str(data.get("reason", "")),
        )


@dataclass(frozen=True)
class Artifact:
    name: str
    path: str
    sha256: str
    signature: str
    signed_by: str = ""

    @classmethod
    def from_dict(cls, name: str, data: Mapping[str, Any]) -> "Artifact":
        return cls(
            name=name,
            path=str(data.get("path", "")),
            sha256=str(data.get("sha256", "")).lower(),
            signature=str(data.get("signature", "")),
            signed_by=str(data.get("signed_by", "")).strip().upper(),
        )


@dataclass(frozen=True)
class SignedDocument:
    payload: dict[str, Any]
    signature: str
    signed_by: str


@dataclass(frozen=True)
class TrustPolicy:
    pinned_roots: tuple[str, ...]
    local_protocol: int = 1
    local_bootstrap_version: str = "1.0.0"
    require_artifact_signatures: bool = True
    allow_key_rotation: bool = True
    required_privileged_channel: str = "polkit"

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "TrustPolicy":
        return cls(
            pinned_roots=tuple(str(r).strip().upper() for r in data.get("pinned_roots", [])),
            local_protocol=int(data.get("local_protocol", 1)),
            local_bootstrap_version=str(data.get("local_bootstrap_version", "1.0.0")),
            require_artifact_signatures=bool(data.get("require_artifact_signatures", True)),
            allow_key_rotation=bool(data.get("allow_key_rotation", True)),
            required_privileged_channel=str(data.get("required_privileged_channel", "polkit")),
        )


@dataclass(frozen=True)
class TrustIndex:
    format_version: int
    repository_generation: int
    target_release: str
    bootstrap: dict[str, Any]
    compatibility: dict[str, Any]
    handoff: dict[str, Any]
    artifacts: dict[str, Artifact] = field(default_factory=dict)
    key_rotations: tuple[KeyRotation, ...] = ()

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "TrustIndex":
        artifacts = {
            str(name): Artifact.from_dict(str(name), value)
            for name, value in (data.get("artifacts") or {}).items()
            if isinstance(value, Mapping)
        }
        rotations = tuple(
            KeyRotation.from_dict(value)
            for value in (data.get("key_rotations") or [])
            if isinstance(value, Mapping)
        )
        return cls(
            format_version=int(data.get("format_version", 0)),
            repository_generation=int(data.get("repository_generation", 0)),
            target_release=str(data.get("target", {}).get("release", "")),
            bootstrap=dict(data.get("bootstrap") or {}),
            compatibility=dict(data.get("compatibility") or {}),
            handoff=dict(data.get("handoff") or {}),
            artifacts=artifacts,
            key_rotations=rotations,
        )


@dataclass(frozen=True)
class StageAReport:
    passed: bool
    errors: tuple[str, ...] = ()
    trusted_keys: tuple[str, ...] = ()
    rotated_keys: tuple[str, ...] = ()
    artifacts_verified: tuple[str, ...] = ()
    target_release: str = ""
    repository_generation: int = 0
    handoff: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "passed": self.passed,
            "errors": list(self.errors),
            "trusted_keys": list(self.trusted_keys),
            "rotated_keys": list(self.rotated_keys),
            "artifacts_verified": list(self.artifacts_verified),
            "target_release": self.target_release,
            "repository_generation": self.repository_generation,
            "handoff": self.handoff,
        }


def verify_signed_document(
    document: SignedDocument,
    trusted_keys: set[str],
    verifier: Verifier,
    errors: list[str],
    label: str,
) -> bool:
    signer = str(document.signed_by).strip().upper()
    if signer not in trusted_keys:
        errors.append(f"{label}: signer {signer or '(empty)'} is not in the pinned trust chain")
        return False
    if not document.signature:
        errors.append(f"{label}: missing signature")
        return False
    try:
        ok = verifier(signer, canonical_bytes(document.payload), document.signature)
    except Exception as exc:  # a verifier failure must fail closed
        errors.append(f"{label}: signature verification error: {exc}")
        return False
    if not ok:
        errors.append(f"{label}: invalid signature from {signer}")
        return False
    return True


def verify_stage_a(
    index_path: str | Path,
    policy: TrustPolicy,
    verifier: Verifier,
    *,
    artifact_root: str | Path | None = None,
) -> StageAReport:
    """Verify repository trust before any transformation is attempted.

    ``index_path`` is a signed JSON document with a ``payload`` containing the
    target index and top-level ``signed_by``/``signature`` fields.  The
    ``verifier`` receives ``(fingerprint, canonical_payload_bytes, signature)``.
    """
    errors: list[str] = []
    index_path = Path(index_path)
    if not index_path.is_file():
        return StageAReport(False, (f"trust index not found: {index_path}",))
    try:
        envelope = json.loads(index_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return StageAReport(False, (f"cannot read trust index: {exc}",))

    if not policy.pinned_roots:
        return StageAReport(False, ("trust policy has no pinned roots",))
    trusted = set(policy.pinned_roots)
    document = SignedDocument(
        payload=dict(envelope.get("payload") or {}),
        signature=str(envelope.get("signature", "")),
        signed_by=str(envelope.get("signed_by", "")),
    )
    if not verify_signed_document(document, trusted, verifier, errors, "repository index"):
        return StageAReport(False, tuple(errors), trusted_keys=tuple(sorted(trusted)))

    index = TrustIndex.from_dict(document.payload)
    if index.format_version != 1:
        errors.append(f"unsupported trust index format: {index.format_version}")
    if index.repository_generation <= 0:
        errors.append("repository_generation must be positive")

    # Key rotation: a downloaded key becomes trusted only after the rotation
    # record verifies against a key that was already trusted.  Self-signed
    # rotation records are rejected even if the verifier accepts them.
    rotated: list[str] = []
    if index.key_rotations and not policy.allow_key_rotation:
        errors.append("key rotation present but disabled by trust policy")
    for rotation in index.key_rotations:
        if rotation.signed_by == rotation.new_fingerprint:
            errors.append(f"key rotation {rotation.new_fingerprint} is self-signed")
            continue
        rotation_doc = SignedDocument(
            payload=rotation.signable(),
            signature=rotation.signature,
            signed_by=rotation.signed_by,
        )
        if verify_signed_document(rotation_doc, trusted, verifier, errors,
                                  f"key rotation {rotation.new_fingerprint}"):
            trusted.add(rotation.new_fingerprint)
            for old in rotation.revokes:
                trusted.discard(old)
            rotated.append(rotation.new_fingerprint)

    bootstrap = index.bootstrap
    min_protocol = int(bootstrap.get("minimum_protocol", 1))
    if policy.local_protocol < min_protocol:
        errors.append(
            f"bootstrap protocol {policy.local_protocol} is older than required {min_protocol}; "
            "upgrade the bootstrap before transforming"
        )
    min_core = str(index.compatibility.get("minimum_core", ""))
    if min_core and _version_tuple(policy.local_bootstrap_version) < _version_tuple(min_core):
        errors.append(
            f"local bootstrap {policy.local_bootstrap_version} is older than minimum core {min_core}"
        )

    channel = str(bootstrap.get("privileged_channel", ""))
    if policy.required_privileged_channel and channel != policy.required_privileged_channel:
        errors.append(
            f"privileged channel '{channel or '(unset)'}'; policy requires "
            f"'{policy.required_privileged_channel}' (no broad sudoers rule)"
        )

    base = Path(artifact_root) if artifact_root is not None else index_path.parent
    verified: list[str] = []
    for name, artifact in sorted(index.artifacts.items()):
        artifact_path = Path(artifact.path)
        if not artifact_path.is_absolute():
            artifact_path = base / artifact_path
        if not artifact_path.is_file():
            errors.append(f"artifact {name}: file not found at {artifact_path}")
            continue
        actual = sha256_file(artifact_path)
        if actual != artifact.sha256:
            errors.append(f"artifact {name}: digest mismatch ({actual} != {artifact.sha256})")
            continue
        signer = artifact.signed_by or document.signed_by
        if policy.require_artifact_signatures:
            try:
                ok = verifier(signer, artifact_path.read_bytes(), artifact.signature)
            except Exception as exc:
                ok = False
                errors.append(f"artifact {name}: verifier error: {exc}")
            if signer not in trusted:
                errors.append(f"artifact {name}: signer {signer} is not in the trust chain")
                ok = False
            if not ok and not any(f"artifact {name}:" in e for e in errors):
                errors.append(f"artifact {name}: invalid signature from {signer}")
            if not ok:
                continue
        verified.append(name)

    handoff = dict(index.handoff)
    handoff_artifact = str(handoff.get("artifact", ""))
    if not handoff_artifact:
        errors.append("handoff descriptor does not identify a verified artifact")
    elif handoff_artifact not in verified:
        errors.append(f"handoff artifact '{handoff_artifact}' was not verified")
    handoff_protocol = int(handoff.get("protocol", 0))
    if handoff_protocol <= 0 or handoff_protocol < policy.local_protocol:
        errors.append("handoff protocol is missing or older than the local bootstrap")

    return StageAReport(
        passed=not errors,
        errors=tuple(errors),
        trusted_keys=tuple(sorted(trusted)),
        rotated_keys=tuple(rotated),
        artifacts_verified=tuple(verified),
        target_release=index.target_release,
        repository_generation=index.repository_generation,
        handoff=handoff,
    )


def gpg_verifier(keyring: str | Path, gpg: str = "gpg") -> Verifier:
    """Create a verifier backed by a dedicated GPG keyring.

    Production bootstraps should use the Rust implementation, but this helper
    lets the protocol be exercised on a host without adding Python crypto
    dependencies.
    """
    keyring_path = Path(keyring).resolve()

    def verify(fingerprint: str, payload: bytes, signature: str) -> bool:
        del fingerprint  # gpg selects the key from the signature
        with tempfile.TemporaryDirectory(prefix="sunshine-trust-") as tmp:
            tmpdir = Path(tmp)
            payload_path = tmpdir / "payload"
            sig_path = tmpdir / "payload.sig"
            payload_path.write_bytes(payload)
            try:
                sig_path.write_bytes(bytes.fromhex(signature))
            except ValueError:
                return False
            result = subprocess.run(
                [gpg, "--no-default-keyring", "--keyring", str(keyring_path),
                 "--batch", "--verify", str(sig_path), str(payload_path)],
                capture_output=True,
                text=True,
                check=False,
            )
            return result.returncode == 0

    return verify
