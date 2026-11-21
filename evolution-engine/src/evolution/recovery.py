"""Independent recovery lineage and baseline reconstruction.

Recovery is a separate architecture, not a fallback branch of the ordinary
migration engine. The primary lineage is B0 -> E001 -> ... -> E080. The recovery
lineage is B-1 (Arch 2015) -> M (qualified bridge) -> B0 -> target. The bridge
must not depend on the primary engine, a single repository, the old package
database, legacy TLS, or the primary ledger being intact.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import PurePosixPath
from typing import Any, Iterable, Mapping

from .baseline import BASELINE_ID
from .release import content_digest

RECOVERY_BASELINE_ID = "B-1-2015"
BRIDGE_ID = "M-recovery-bridge"


@dataclass(frozen=True)
class LineageAnchor:
    id: str
    label: str
    kind: str                      # baseline | bridge | evolution | target

    def to_dict(self) -> dict[str, Any]:
        return {"id": self.id, "label": self.label, "kind": self.kind}


PRIMARY_LINEAGE: tuple[LineageAnchor, ...] = (
    LineageAnchor(BASELINE_ID, "Canonical Arch 2026", "baseline"),
    LineageAnchor("E001", "First SunshineOS evolution", "evolution"),
    LineageAnchor("E040", "Fortieth evolution (minimum horizon)", "evolution"),
    LineageAnchor("E080", "Eightieth evolution (architectural horizon)", "evolution"),
)

RECOVERY_LINEAGE: tuple[LineageAnchor, ...] = (
    LineageAnchor(RECOVERY_BASELINE_ID, "Arch 2015 reconstruction anchor", "baseline"),
    LineageAnchor(BRIDGE_ID, "Independent recovery bridge", "bridge"),
    LineageAnchor(BASELINE_ID, "Reconstructed canonical baseline", "baseline"),
    LineageAnchor("E001", "First evolution after reconstruction", "evolution"),
)


@dataclass(frozen=True)
class ReconstructionStep:
    """A semantic reconstruction requirement, not a filesystem diff."""

    domain: str
    requirement: str
    verification: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "domain": self.domain,
            "requirement": self.requirement,
            "verification": self.verification,
        }


RECONSTRUCTION_SPEC: tuple[ReconstructionStep, ...] = (
    ReconstructionStep("package_management", "Establish a compatible pacman/libalpm environment",
                       "pacman --version and database consistency"),
    ReconstructionStep("trust", "Establish verified repository and artifact trust",
                       "signed index verification passes"),
    ReconstructionStep("repository", "Configure target repositories and metadata",
                       "repository inventory matches baseline"),
    ReconstructionStep("package_database", "Handle obsolete/incompatible package DB states",
                       "pacman -Qk reports no missing files"),
    ReconstructionStep("kernel", "Install target kernel and required modules",
                       "/boot/vmlinuz-linux exists"),
    ReconstructionStep("initramfs", "Reconstruct target initramfs configuration",
                       "initramfs image exists and matches preset"),
    ReconstructionStep("boot", "Establish a bootable target architecture",
                       "boot entry valid and efibootmgr lists entry"),
    ReconstructionStep("filesystem", "Verify target filesystem layout",
                       "fstab mounts resolve"),
    ReconstructionStep("services", "Establish target service definitions",
                       "required units enabled"),
    ReconstructionStep("configuration", "Reconstruct compatible target configuration",
                       "configuration schema validation passes"),
    ReconstructionStep("os_identity", "Establish baseline identity and metadata",
                       "os-release matches archived baseline"),
    ReconstructionStep("validation", "Verify the reconstructed baseline",
                       "engine --verify passes"),
)


@dataclass(frozen=True)
class RecoveryBridge:
    source: str = RECOVERY_BASELINE_ID
    bridge_id: str = BRIDGE_ID
    target: str = BASELINE_ID
    independent_toolchain: bool = False
    artifact_manifest_hash: str = ""
    supported_conditions: tuple[str, ...] = ()
    qualified: bool = False

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "RecoveryBridge":
        return cls(
            source=str(data.get("source", RECOVERY_BASELINE_ID)),
            bridge_id=str(data.get("bridge_id", BRIDGE_ID)),
            target=str(data.get("target", BASELINE_ID)),
            independent_toolchain=bool(data.get("independent_toolchain", False)),
            artifact_manifest_hash=str(data.get("artifact_manifest_hash", "")),
            supported_conditions=tuple(str(c) for c in data.get("supported_conditions", [])),
            qualified=bool(data.get("qualified", False)),
        )

    def validate(self) -> list[str]:
        errors: list[str] = []
        if not self.independent_toolchain:
            errors.append("recovery bridge must use a separately maintained toolchain")
        digest = self.artifact_manifest_hash.lower()
        if len(digest) != 64 or any(char not in "0123456789abcdef" for char in digest):
            errors.append("recovery bridge needs a valid SHA-256 artifact manifest hash")
        if not self.supported_conditions:
            errors.append("recovery bridge needs explicit supported conditions")
        if self.qualified and errors:
            errors.append("an unqualified bridge cannot be marked qualified")
        return errors

    def to_dict(self) -> dict[str, Any]:
        return {
            "source": self.source,
            "bridge_id": self.bridge_id,
            "target": self.target,
            "independent_toolchain": self.independent_toolchain,
            "artifact_manifest_hash": self.artifact_manifest_hash,
            "supported_conditions": list(self.supported_conditions),
            "qualified": self.qualified,
            "digest": content_digest({
                "source": self.source, "bridge_id": self.bridge_id,
                "target": self.target,
                "conditions": list(self.supported_conditions),
            }),
        }


@dataclass(frozen=True)
class DataPreservationPlan:
    """User data preservation is separate from OS reconstruction."""

    include: tuple[str, ...] = ()
    exclude: tuple[str, ...] = ()
    preserve_ownership: bool = True
    home_separate: bool = True
    report_path: str = ""

    def validate(self) -> list[str]:
        errors: list[str] = []
        for label, values in (("included", self.include), ("excluded", self.exclude)):
            if len(set(values)) != len(values):
                errors.append(f"duplicate {label} data paths")
            for value in values:
                path = PurePosixPath(value)
                if not path.is_absolute() or value == "/" or ".." in path.parts:
                    errors.append(f"unsafe {label} data path {value!r}")
        conflicts = [
            (included, excluded)
            for included in self.include for excluded in self.exclude
            if PurePosixPath(included) == PurePosixPath(excluded)
            or PurePosixPath(excluded) in PurePosixPath(included).parents
        ]
        if conflicts:
            pairs = [f"{included} ↔ {excluded}" for included, excluded in conflicts]
            errors.append("excluded path hides an included data path: " + ", ".join(pairs))
        if self.report_path:
            report = PurePosixPath(self.report_path)
            if not report.is_absolute() or self.report_path == "/" or ".." in report.parts:
                errors.append(f"unsafe preservation report path {self.report_path!r}")
        if not self.home_separate:
            errors.append("user home preservation must be independent of OS reconstruction")
        return errors

    def to_dict(self) -> dict[str, Any]:
        return {
            "include": list(self.include),
            "exclude": list(self.exclude),
            "preserve_ownership": self.preserve_ownership,
            "home_separate": self.home_separate,
            "report_path": self.report_path,
        }


@dataclass(frozen=True)
class RecoveryQualification:
    source: str
    steps: tuple[dict[str, Any], ...]
    final_target_reachable: bool = False

    @property
    def qualified(self) -> bool:
        return all(step.get("passed", False) for step in self.steps) and self.final_target_reachable

    def to_dict(self) -> dict[str, Any]:
        return {
            "source": self.source,
            "steps": list(self.steps),
            "final_target_reachable": self.final_target_reachable,
            "qualified": self.qualified,
        }


def reconstruction_spec() -> tuple[ReconstructionStep, ...]:
    return RECONSTRUCTION_SPEC


def recovery_path(source: str, target: str) -> list[str]:
    """Return the semantic recovery path anchors."""
    if source not in (RECOVERY_BASELINE_ID, BASELINE_ID):
        raise ValueError(f"unsupported recovery source {source!r}")
    path = [source]
    if source == RECOVERY_BASELINE_ID:
        path.append(BRIDGE_ID)
        path.append(BASELINE_ID)
    path.append(target)
    return path


def qualification_from_results(
    source: str, results: Iterable[tuple[str, bool, str]], final_target: bool
) -> RecoveryQualification:
    steps = tuple(
        {"name": name, "passed": bool(passed), "detail": detail}
        for name, passed, detail in results
    )
    return RecoveryQualification(source, steps, final_target)
