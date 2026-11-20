"""Migration qualification records and the release gate.

Support is earned by testing, not by shipping a migration file. Every release
must carry a machine-readable qualification record, and the release gate must
fail when any required migration evidence is absent.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Iterable, Mapping

from .release import content_digest
from .versions import VersionSet

TEST_LAYERS = (
    "unit", "schema", "planner", "adapter", "integration", "vm_migration",
    "recovery", "fault_injection", "hardware", "security", "regression",
)

SUPPORT_TIERS = (
    "qualified",
    "qualified_with_intervention",
    "assessment_only",
    "unsupported",
)

HISTORICAL_SOURCES = (
    "B0", "E001", "E010", "E020", "E030", "E039", "E040",
    "external-arch", "external-derivative", "unknown-arch", "B-1",
)


@dataclass(frozen=True)
class SourceCapabilities:
    """Capability-based qualification input (more scalable than release pairs)."""

    package_database: str = "unknown"       # compatible | incompatible | unknown
    package_manager: str = "unknown"
    boot_architecture: str = "unknown"     # supported | unsupported | unknown
    filesystem: str = "unknown"            # supported | unsupported | unknown
    repository_trust: str = "unknown"      # reconstructable | absent | unknown
    inventory: str = "unknown"             # complete | partial | unknown
    configuration_schema: str = "unknown"  # identified | unknown
    migration_workspace: str = "unknown"   # available | unavailable | unknown

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "SourceCapabilities":
        return cls(**{
            key: str(data.get(key, "unknown"))
            for key in cls.__dataclass_fields__
        })

    def tier(self) -> str:
        """Map capabilities to a support tier without silently upgrading them."""
        required_ok = (
            self.package_database == "compatible"
            and self.package_manager == "compatible"
            and self.boot_architecture == "supported"
            and self.filesystem == "supported"
            and self.repository_trust in ("reconstructable", "verified")
            and self.inventory == "complete"
            and self.configuration_schema == "identified"
        )
        if required_ok and self.migration_workspace == "available":
            return "qualified"
        if required_ok:
            return "qualified_with_intervention"
        if self.inventory in ("complete", "partial") and self.package_manager == "compatible":
            return "assessment_only"
        return "unsupported"

    def to_dict(self) -> dict[str, Any]:
        return {key: getattr(self, key) for key in self.__dataclass_fields__}


@dataclass
class QualificationRecord:
    source_identity: str
    source_inventory_hash: str
    target_identity: str
    target_manifest_hash: str
    engine_version: str
    transition_catalog_version: str
    artifact_manifest_hash: str
    vm_profile: str = ""
    scenario: str = ""
    execution_result: str = ""
    validation_result: str = ""
    failure_recovery_result: str = ""
    layers: tuple[str, ...] = ()
    support_tier: str = "unsupported"
    qualified_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def validate(self) -> list[str]:
        errors: list[str] = []
        if not self.source_identity or not self.target_identity:
            errors.append("qualification record needs source and target identities")
        if not self.source_inventory_hash or not self.target_manifest_hash:
            errors.append("qualification record needs inventory and target hashes")
        for layer in self.layers:
            if layer not in TEST_LAYERS:
                errors.append(f"unknown test layer {layer!r}")
        if self.support_tier not in SUPPORT_TIERS:
            errors.append(f"unknown support tier {self.support_tier!r}")
        if self.support_tier == "qualified":
            needed = {"vm_migration", "fault_injection", "recovery"}
            if not needed.issubset(set(self.layers)):
                errors.append(
                    "qualified tier requires vm_migration, fault_injection and recovery layers"
                )
            if not self.validation_result or self.failure_recovery_result != "passed":
                errors.append("qualified tier requires passing validation and recovery results")
        return errors

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_identity": self.source_identity,
            "source_inventory_hash": self.source_inventory_hash,
            "target_identity": self.target_identity,
            "target_manifest_hash": self.target_manifest_hash,
            "engine_version": self.engine_version,
            "transition_catalog_version": self.transition_catalog_version,
            "artifact_manifest_hash": self.artifact_manifest_hash,
            "vm_profile": self.vm_profile,
            "scenario": self.scenario,
            "execution_result": self.execution_result,
            "validation_result": self.validation_result,
            "failure_recovery_result": self.failure_recovery_result,
            "layers": list(self.layers),
            "support_tier": self.support_tier,
            "qualified_at": self.qualified_at,
            "digest": content_digest({
                "source": self.source_identity,
                "target": self.target_identity,
                "scenario": self.scenario,
                "tier": self.support_tier,
            }),
        }


@dataclass(frozen=True)
class GateReport:
    passed: bool
    checks: tuple[dict[str, Any], ...]

    def to_dict(self) -> dict[str, Any]:
        return {"passed": self.passed, "checks": list(self.checks)}


REQUIRED_RELEASE_ARTIFACTS = (
    "evolution_definition", "resolved_target_manifest", "transition_catalog_changes",
    "engine_compatibility", "inventory_schema_compatibility", "package_repository_manifest",
    "configuration_reconciliation", "recovery_requirements", "artifact_integrity_manifest",
    "migration_qualification_results", "historical_migration_results",
    "rollback_recovery_qualification",
)


def release_gate(
    artifacts: Mapping[str, Any],
    qualifications: Iterable[QualificationRecord],
    versions: VersionSet,
) -> GateReport:
    """Fail closed unless migration evidence for a release is complete."""
    checks: list[dict[str, Any]] = []
    for artifact in REQUIRED_RELEASE_ARTIFACTS:
        present = bool(artifacts.get(artifact))
        checks.append({
            "name": f"artifact:{artifact}", "passed": present,
            "detail": "present" if present else "missing",
        })
    version_errors = versions.validate()
    checks.append({
        "name": "versions:valid", "passed": not version_errors,
        "detail": "; ".join(version_errors) or "valid",
    })

    records = list(qualifications)
    for source in ("B0", "E001", "E039", "external-arch"):
        matching = [r for r in records if r.source_identity == source]
        qualifies = any(
            not r.validate() and r.support_tier == "qualified"
            for r in matching
        )
        checks.append({
            "name": f"qualification:{source}", "passed": qualifies,
            "detail": "qualified" if qualifies else "no qualified record",
        })
    return GateReport(all(c["passed"] for c in checks), tuple(checks))
