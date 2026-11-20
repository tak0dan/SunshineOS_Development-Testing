"""Multi-dimensional version identities.

One number cannot describe a system that has 40-80 OS milestones, a separately
evolving engine, several inventory/evolution schemas, a transition catalog,
two baselines and per-target profiles. Each dimension is an immutable,
independently verifiable identity; OS releases do not force engine releases.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from .release import content_digest


@dataclass(frozen=True)
class VersionSet:
    """The version vector that fully describes a migration transaction."""

    os_evolution: str          # E040
    migration_engine: str      # ME12
    inventory_schema: str      # INV7
    evolution_schema: str      # EVS4
    transition_catalog: str    # TC18
    baseline: str              # B0-2026
    recovery_baseline: str = ""  # B-1-2015, empty when not applicable
    target_profile: str = ""   # TP040

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "VersionSet":
        return cls(
            os_evolution=str(data.get("os_evolution", "")),
            migration_engine=str(data.get("migration_engine", "")),
            inventory_schema=str(data.get("inventory_schema", "")),
            evolution_schema=str(data.get("evolution_schema", "")),
            transition_catalog=str(data.get("transition_catalog", "")),
            baseline=str(data.get("baseline", "")),
            recovery_baseline=str(data.get("recovery_baseline", "")),
            target_profile=str(data.get("target_profile", "")),
        )

    def validate(self) -> list[str]:
        errors: list[str] = []
        required = {
            "os_evolution": self.os_evolution,
            "migration_engine": self.migration_engine,
            "inventory_schema": self.inventory_schema,
            "evolution_schema": self.evolution_schema,
            "transition_catalog": self.transition_catalog,
            "baseline": self.baseline,
        }
        for name, value in required.items():
            if not value:
                errors.append(f"{name} is missing")
        if self.os_evolution and not self.os_evolution.upper().startswith("E"):
            errors.append(f"os_evolution {self.os_evolution!r} must look like E040")
        if self.migration_engine and not self.migration_engine.upper().startswith("ME"):
            errors.append(f"migration_engine {self.migration_engine!r} must look like ME12")
        if self.inventory_schema and not self.inventory_schema.upper().startswith("INV"):
            errors.append(f"inventory_schema {self.inventory_schema!r} must look like INV7")
        if self.evolution_schema and not self.evolution_schema.upper().startswith("EVS"):
            errors.append(f"evolution_schema {self.evolution_schema!r} must look like EVS4")
        if self.transition_catalog and not self.transition_catalog.upper().startswith("TC"):
            errors.append(f"transition_catalog {self.transition_catalog!r} must look like TC18")
        return errors

    @property
    def digest(self) -> str:
        return content_digest(self.to_dict())

    def to_dict(self) -> dict[str, Any]:
        return {
            "os_evolution": self.os_evolution,
            "migration_engine": self.migration_engine,
            "inventory_schema": self.inventory_schema,
            "evolution_schema": self.evolution_schema,
            "transition_catalog": self.transition_catalog,
            "baseline": self.baseline,
            "recovery_baseline": self.recovery_baseline,
            "target_profile": self.target_profile,
        }
