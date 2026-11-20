"""Frozen baseline epoch for long-term evolutionary migration.

The baseline is *not* a floating "latest Arch" and not an image the engine
boots. It is an immutable reference point: an archived Arch 2026 ISO plus the
package, repository, configuration and procedure metadata needed to interpret
that state ten or twenty years later.

Rules enforced here:

* a baseline cannot be modified in place (``mutable=False`` on the published
  epoch and a guard in :meth:`BaselineSpec.validate`);
* replacing it requires a *new* epoch id (there is no "edit" API);
* verification fails closed when the archived digest or signature is absent.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

BASELINE_ID = "arch-2026-baseline-01"


@dataclass(frozen=True)
class BaselineVerification:
    passed: bool
    errors: tuple[str, ...] = ()
    iso_sha256: str = ""
    verified_files: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "passed": self.passed,
            "errors": list(self.errors),
            "iso_sha256": self.iso_sha256,
            "verified_files": list(self.verified_files),
        }


@dataclass(frozen=True)
class BaselineSpec:
    """Immutable description of one baseline epoch."""

    id: str
    label: str
    iso_name: str
    iso_sha256: str
    iso_signature: str
    archived_at: str
    manifest_digest: str
    package_state: tuple[str, ...] = ()
    repository_state: tuple[str, ...] = ()
    configuration_state: tuple[str, ...] = ()
    installation_procedure: str = ""
    artifacts: Mapping[str, str] = frozenset()  # type: ignore[assignment]
    mutable: bool = False

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "BaselineSpec":
        artifacts = {
            str(k): str(v)
            for k, v in (data.get("artifacts") or {}).items()
        }
        return cls(
            id=str(data.get("id", "")).strip(),
            label=str(data.get("label", "")),
            iso_name=str(data.get("iso_name", "")),
            iso_sha256=str(data.get("iso_sha256", "")).lower(),
            iso_signature=str(data.get("iso_signature", "")),
            archived_at=str(data.get("archived_at", "")),
            manifest_digest=str(data.get("manifest_digest", "")).lower(),
            package_state=tuple(str(p) for p in data.get("package_state", [])),
            repository_state=tuple(str(r) for r in data.get("repository_state", [])),
            configuration_state=tuple(str(c) for c in data.get("configuration_state", [])),
            installation_procedure=str(data.get("installation_procedure", "")),
            artifacts=frozenset(artifacts.items()),
            mutable=bool(data.get("mutable", False)),
        )

    def validate(self) -> list[str]:
        errors: list[str] = []
        if not self.id:
            errors.append("baseline has no id")
        if self.mutable:
            errors.append(f"baseline {self.id}: baselines must be immutable")
        if not self.iso_name:
            errors.append(f"baseline {self.id}: no archived ISO name")
        if not self.iso_sha256:
            errors.append(f"baseline {self.id}: ISO SHA-256 is not archived")
        elif len(self.iso_sha256) != 64:
            errors.append(f"baseline {self.id}: malformed ISO SHA-256")
        if not self.iso_signature:
            errors.append(f"baseline {self.id}: ISO signature is not archived")
        if not self.manifest_digest:
            errors.append(f"baseline {self.id}: manifest digest is not archived")
        if not self.archived_at:
            errors.append(f"baseline {self.id}: no archival date")
        if not self.installation_procedure:
            errors.append(f"baseline {self.id}: installation procedure is not preserved")
        if not self.package_state:
            errors.append(f"baseline {self.id}: package state is not recorded")
        if not self.configuration_state:
            errors.append(f"baseline {self.id}: configuration state is not recorded")
        return errors

    def verify_iso(self, path: str | Path) -> BaselineVerification:
        """Verify an archived ISO against this epoch. No network, no shell."""
        errors = list(self.validate())
        candidate = Path(path)
        if not candidate.is_file():
            errors.append(f"baseline {self.id}: ISO not found at {candidate}")
            return BaselineVerification(False, tuple(errors))
        digest = hashlib.sha256()
        with candidate.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
        actual = digest.hexdigest()
        if actual != self.iso_sha256:
            errors.append(
                f"baseline {self.id}: ISO digest mismatch ({actual} != {self.iso_sha256})"
            )
        return BaselineVerification(
            passed=not errors,
            errors=tuple(errors),
            iso_sha256=actual,
            verified_files=(candidate.name,) if not errors else (),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "label": self.label,
            "iso_name": self.iso_name,
            "iso_sha256": self.iso_sha256,
            "iso_signature": self.iso_signature,
            "archived_at": self.archived_at,
            "manifest_digest": self.manifest_digest,
            "package_state": list(self.package_state),
            "repository_state": list(self.repository_state),
            "configuration_state": list(self.configuration_state),
            "installation_procedure": self.installation_procedure,
            "artifacts": dict(self.artifacts),
            "mutable": self.mutable,
        }


# Published epoch. Digests and the signature are filled by the release archive
# pipeline at freeze time; an empty value makes verify_iso() fail closed, which
# is intentional -- an unverifiable baseline must never authorize a migration.
ARCH_2026_BASELINE = BaselineSpec(
    id=BASELINE_ID,
    label="Arch Linux 2026 baseline epoch",
    iso_name="archlinux-2026.01.01-x86_64.iso",
    iso_sha256="",
    iso_signature="",
    archived_at="2026-01-01",
    manifest_digest="",
    package_state=(
        "base", "systemd", "pacman", "linux", "linux-firmware", "mkinitcpio",
    ),
    repository_state=("core", "extra", "multilib"),
    configuration_state=(
        "/etc/pacman.conf", "/etc/mkinitcpio.conf", "/etc/fstab",
    ),
    installation_procedure="evolution/docs/BASELINE_ARCH_2026.md",
    artifacts=frozenset({
        ("iso", "archlinux-2026.01.01-x86_64.iso"),
        ("manifest", "baseline-arch-2026.manifest.json"),
    }),
    mutable=False,
)


def replace_baseline(current: BaselineSpec, replacement: BaselineSpec) -> BaselineSpec:
    """Create a *new* epoch; mutating an existing one is never allowed."""
    if replacement.id == current.id:
        raise ValueError(
            f"baseline replacement requires a new epoch id (got {current.id!r})"
        )
    errors = replacement.validate()
    if errors:
        raise ValueError("invalid replacement baseline: " + "; ".join(errors))
    return replacement
