"""Declarative evolution ledger.

Each record describes a *change to the desired state*, not a script to run on
every machine. Records are retained indefinitely for auditability and target
resolution; execution is derived later from an actual inventory and a resolved
target. A small imperative escape hatch is represented by signed transition
ids (see :mod:`transitions`), never by arbitrary shell text.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from .baseline import ARCH_2026_BASELINE, BASELINE_ID, BaselineSpec
from .release import ReleaseIdentity, content_digest


@dataclass(frozen=True)
class ConfigResourceChange:
    id: str
    state: str = "present"          # present | absent
    path: str = ""
    schema: int = 0
    ownership: str = "managed-merge"  # see configuration reconciliation strategies
    strategy: str = "three-way"
    baseline_digest: str = ""

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "ConfigResourceChange":
        return cls(
            id=str(data.get("id", "")).strip(),
            state=str(data.get("state", "present")),
            path=str(data.get("path", "")),
            schema=int(data.get("schema", 0)),
            ownership=str(data.get("ownership", "managed-merge")),
            strategy=str(data.get("strategy", "three-way")),
            baseline_digest=str(data.get("baseline_digest", "")),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id, "state": self.state, "path": self.path,
            "schema": self.schema, "ownership": self.ownership,
            "strategy": self.strategy, "baseline_digest": self.baseline_digest,
        }


@dataclass(frozen=True)
class EvolutionChanges:
    packages_desired: tuple[str, ...] = ()
    packages_removed: tuple[str, ...] = ()
    services_desired: tuple[str, ...] = ()
    services_disabled: tuple[str, ...] = ()
    repositories_desired: tuple[str, ...] = ()
    configuration: tuple[ConfigResourceChange, ...] = ()
    policies: Mapping[str, bool] = frozenset()  # type: ignore[assignment]

    @classmethod
    def from_dict(cls, data: Mapping[str, Any] | None) -> "EvolutionChanges":
        data = data or {}
        packages = data.get("packages") or {}
        services = data.get("services") or {}
        repositories = data.get("repositories") or {}
        configuration = data.get("configuration") or {}
        resources = configuration.get("resources", []) if isinstance(configuration, Mapping) else []
        return cls(
            packages_desired=tuple(str(p) for p in (
                packages.get("desired", []) if isinstance(packages, Mapping) else [])),
            packages_removed=tuple(str(p) for p in (
                packages.get("removed", []) if isinstance(packages, Mapping) else [])),
            services_desired=tuple(str(s) for s in (
                services.get("desired", []) if isinstance(services, Mapping) else [])),
            services_disabled=tuple(str(s) for s in (
                services.get("disabled", []) if isinstance(services, Mapping) else [])),
            repositories_desired=tuple(str(r) for r in (
                repositories.get("desired", []) if isinstance(repositories, Mapping) else [])),
            configuration=tuple(
                ConfigResourceChange.from_dict(r)
                for r in resources if isinstance(r, Mapping)
            ),
            policies=frozenset(
                (str(k), bool(v))
                for k, v in (data.get("policies") or {}).items()
            ),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "packages": {
                "desired": list(self.packages_desired),
                "removed": list(self.packages_removed),
            },
            "services": {
                "desired": list(self.services_desired),
                "disabled": list(self.services_disabled),
            },
            "repositories": {"desired": list(self.repositories_desired)},
            "configuration": {
                "resources": [r.to_dict() for r in self.configuration],
            },
            "policies": dict(self.policies),
        }


@dataclass(frozen=True)
class EvolutionRecord:
    """One evolution: a cumulative desired-state delta plus its gates."""

    evolution: int
    release_id: str
    release_version: str
    parent: str | None
    baseline_epoch: str
    manifest_schema: int
    changes: EvolutionChanges
    transitions: tuple[str, ...] = ()
    validations: tuple[str, ...] = ()
    channel: str = "stable"
    notes: str = ""

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "EvolutionRecord":
        return cls(
            evolution=int(data.get("evolution", 0)),
            release_id=str(data.get("release_id", "")).strip(),
            release_version=str(data.get("release_version", "")),
            parent=str(data["parent"]) if data.get("parent") else None,
            baseline_epoch=str(data.get("baseline_epoch", BASELINE_ID)),
            manifest_schema=int(data.get("manifest_schema", 1)),
            changes=EvolutionChanges.from_dict(data.get("changes")),
            transitions=tuple(str(t) for t in data.get("transitions", [])),
            validations=tuple(str(v) for v in data.get("validations", [])),
            channel=str(data.get("channel", "stable")),
            notes=str(data.get("notes", "")),
        )

    def identity(self, metadata: Mapping[str, Any] | None = None) -> ReleaseIdentity:
        return ReleaseIdentity.create(
            release_id=self.release_id,
            evolution_index=self.evolution,
            baseline_epoch=self.baseline_epoch,
            manifest_schema=self.manifest_schema,
            metadata=metadata or {},
            release_version=self.release_version,
            channel=self.channel,
            parent_release_id=self.parent or "",
        )

    def to_dict(self) -> dict[str, Any]:
        result = {
            "evolution": self.evolution,
            "release_id": self.release_id,
            "release_version": self.release_version,
            "parent": self.parent,
            "baseline_epoch": self.baseline_epoch,
            "manifest_schema": self.manifest_schema,
            "changes": self.changes.to_dict(),
            "transitions": list(self.transitions),
            "validations": list(self.validations),
            "channel": self.channel,
        }
        if self.notes:
            result["notes"] = self.notes
        return result


class EvolutionLedger:
    """Ordered, validated set of evolution records for one baseline epoch."""

    def __init__(
        self,
        records: list[EvolutionRecord],
        baseline: BaselineSpec = ARCH_2026_BASELINE,
    ) -> None:
        self.baseline = baseline
        self.records = tuple(sorted(records, key=lambda r: (r.evolution, r.release_id)))
        errors = self.validate()
        if errors:
            raise ValueError("invalid evolution ledger: " + "; ".join(errors))

    @classmethod
    def from_dict(
        cls,
        data: Mapping[str, Any],
        baseline: BaselineSpec = ARCH_2026_BASELINE,
    ) -> "EvolutionLedger":
        raw = data.get("evolutions", data.get("milestones", []))
        if not isinstance(raw, (list, tuple)):
            raise ValueError("ledger 'evolutions' must be a list")
        return cls([EvolutionRecord.from_dict(r) for r in raw if isinstance(r, Mapping)], baseline)

    def validate(self) -> list[str]:
        errors: list[str] = []
        if not self.records:
            return ["evolution ledger is empty"]
        indices: list[int] = []
        ids: set[str] = set()
        for record in self.records:
            indices.append(record.evolution)
            if record.evolution < 1:
                errors.append(f"{record.release_id}: evolution index must be >= 1")
            if not record.release_id:
                errors.append(f"evolution {record.evolution}: no release_id")
            if record.release_id in ids:
                errors.append(f"duplicate release_id {record.release_id}")
            ids.add(record.release_id)
            if record.baseline_epoch != self.baseline.id:
                errors.append(
                    f"{record.release_id}: baseline {record.baseline_epoch} != "
                    f"registered baseline {self.baseline.id}"
                )
            c = record.changes
            overlap = set(c.packages_desired) & set(c.packages_removed)
            if overlap:
                errors.append(
                    f"{record.release_id}: packages both desired and removed: "
                    + ", ".join(sorted(overlap))
                )
            overlap = set(c.services_desired) & set(c.services_disabled)
            if overlap:
                errors.append(
                    f"{record.release_id}: services both desired and disabled: "
                    + ", ".join(sorted(overlap))
                )
            resource_ids = [r.id for r in c.configuration]
            if len(resource_ids) != len(set(resource_ids)):
                errors.append(f"{record.release_id}: duplicate configuration resource ids")
            for resource in c.configuration:
                if not resource.id:
                    errors.append(f"{record.release_id}: configuration resource has no id")
                if resource.state not in ("present", "absent"):
                    errors.append(
                        f"{record.release_id}: resource {resource.id} has invalid state "
                        f"{resource.state!r}"
                    )
        if len(indices) != len(set(indices)):
            errors.append("duplicate evolution indices")
        if sorted(indices) != list(range(1, len(indices) + 1)):
            errors.append("evolution indices must be contiguous starting at 1")
        for index, record in enumerate(self.records):
            if index == 0:
                if record.parent is not None:
                    errors.append(f"{record.release_id}: first evolution must have no parent")
            elif record.parent != self.records[index - 1].release_id:
                errors.append(
                    f"{record.release_id}: parent {record.parent!r} != "
                    f"preceding {self.records[index - 1].release_id!r}"
                )
            if index and record.manifest_schema < self.records[index - 1].manifest_schema:
                errors.append(f"{record.release_id}: manifest_schema regressed")
        return errors

    def ordered(self) -> tuple[EvolutionRecord, ...]:
        return self.records

    def up_to(self, release_id: str | None = None, evolution: int | None = None) -> list[EvolutionRecord]:
        if release_id is not None:
            for index, record in enumerate(self.records):
                if record.release_id == release_id:
                    return list(self.records[: index + 1])
            raise ValueError(f"unknown release_id {release_id!r}")
        if evolution is not None:
            if evolution < 1 or evolution > len(self.records):
                raise ValueError(f"evolution {evolution} out of range")
            return list(self.records[:evolution])
        return list(self.records)

    def latest(self) -> EvolutionRecord:
        return self.records[-1]

    def get(self, release_id: str) -> EvolutionRecord | None:
        for record in self.records:
            if record.release_id == release_id:
                return record
        return None

    def digest(self) -> str:
        return content_digest([r.to_dict() for r in self.records])

    def to_dict(self) -> dict[str, Any]:
        return {
            "baseline_epoch": self.baseline.id,
            "ledger_digest": self.digest(),
            "evolutions": [r.to_dict() for r in self.records],
        }
