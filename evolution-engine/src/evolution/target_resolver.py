"""Resolve a baseline plus evolution ledger into a resolved target.

This is a *logical* operation. It never executes migrations and never walks a
machine through every historical release. The output is the complete desired
state of one release, published as a stable, content-addressed artifact that
the migration planner consumes.

    T_n = R(B, E_1, ..., E_n)

Determinism is a hard requirement: identical inputs must produce byte-identical
``to_dict()`` output, so resolved targets can be signed and compared over time.
"""
from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Any, Mapping

from .baseline import BaselineSpec
from .ledger import ConfigResourceChange, EvolutionLedger, EvolutionRecord
from .release import content_digest


@dataclass(frozen=True)
class ResolvedTarget:
    baseline_epoch: str
    release_id: str
    release_version: str
    evolution_index: int
    manifest_schema: int
    channel: str
    packages: frozenset[str]
    removed_packages: frozenset[str]
    services: frozenset[str]
    disabled_services: frozenset[str]
    repositories: frozenset[str]
    resources: Mapping[str, ConfigResourceChange]
    policies: Mapping[str, bool]
    transitions: tuple[str, ...]
    validations: tuple[str, ...]
    ledger_digest: str
    content_digest: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "baseline_epoch": self.baseline_epoch,
            "release_id": self.release_id,
            "release_version": self.release_version,
            "evolution_index": self.evolution_index,
            "manifest_schema": self.manifest_schema,
            "channel": self.channel,
            "packages": sorted(self.packages),
            "removed_packages": sorted(self.removed_packages),
            "services": sorted(self.services),
            "disabled_services": sorted(self.disabled_services),
            "repositories": sorted(self.repositories),
            "resources": {
                key: self.resources[key].to_dict()
                for key in sorted(self.resources)
            },
            "policies": {k: self.policies[k] for k in sorted(self.policies)},
            "transitions": list(self.transitions),
            "validations": list(self.validations),
            "ledger_digest": self.ledger_digest,
            "content_digest": self.content_digest,
        }


class TargetResolver:
    """Merge cumulative changes and validate the resulting desired state."""

    def __init__(self, ledger: EvolutionLedger, baseline: BaselineSpec | None = None) -> None:
        self.ledger = ledger
        self.baseline = baseline or ledger.baseline

    def resolve(
        self,
        release_id: str | None = None,
        evolution: int | None = None,
    ) -> ResolvedTarget:
        records = self.ledger.up_to(release_id=release_id, evolution=evolution)
        last = records[-1]

        packages: set[str] = set()
        removed: set[str] = set()
        services: set[str] = set()
        disabled: set[str] = set()
        repositories: set[str] = set()
        resources: dict[str, ConfigResourceChange] = {}
        policies: dict[str, bool] = {}
        transitions: list[str] = []
        validations: list[str] = []

        for record in records:
            change = record.changes
            for name in change.packages_desired:
                packages.add(name)
                removed.discard(name)
            for name in change.packages_removed:
                removed.add(name)
                packages.discard(name)
            services.update(change.services_desired)
            disabled.difference_update(change.services_desired)
            disabled.update(change.services_disabled)
            services.difference_update(change.services_disabled)
            repositories.update(change.repositories_desired)
            for resource in change.configuration:
                if resource.state == "absent":
                    resources.pop(resource.id, None)
                else:
                    resources[resource.id] = resource
            policies.update(change.policies)
            for transition in record.transitions:
                if transition not in transitions:
                    transitions.append(transition)
            for validation in record.validations:
                if validation not in validations:
                    validations.append(validation)

        # Superseded removals: a package removed in an earlier evolution may be
        # reintroduced later; the final desired state is what matters.
        packages.difference_update(removed)

        # Fold baseline package state in as immutable foundation, then reapply
        # explicit removals (an evolution may legitimately retire a baseline
        # package, e.g. replacing a bootloader).
        foundation = set(self.baseline.package_state)
        foundation.difference_update(removed)
        packages = foundation | packages

        # Preserve declarative policies from the frozen baseline epoch where
        # the ledger has not overridden them.
        policies.setdefault("preserve_user_configuration", True)
        policies.setdefault("preserve_user_packages", True)
        policies.setdefault("require_signed_packages", True)

        target = ResolvedTarget(
            baseline_epoch=self.baseline.id,
            release_id=last.release_id,
            release_version=last.release_version,
            evolution_index=last.evolution,
            manifest_schema=last.manifest_schema,
            channel=last.channel,
            packages=frozenset(packages),
            removed_packages=frozenset(removed),
            services=frozenset(services),
            disabled_services=frozenset(disabled),
            repositories=frozenset(repositories),
            resources=dict(resources),
            policies=dict(policies),
            transitions=tuple(transitions),
            validations=tuple(validations),
            ledger_digest=self.ledger.digest(),
            content_digest="",
        )
        digest = content_digest(target.to_dict())
        return replace(target, content_digest=digest)

    def resolve_all(self) -> dict[str, ResolvedTarget]:
        return {
            record.release_id: self.resolve(evolution=record.evolution)
            for record in self.ledger.ordered()
        }

    @staticmethod
    def validate_resolved(target: ResolvedTarget) -> list[str]:
        """Check a resolved target for contradictions before it is published."""
        errors: list[str] = []
        overlap = target.packages & target.removed_packages
        if overlap:
            errors.append("packages both present and removed: " + ", ".join(sorted(overlap)))
        overlap = target.services & target.disabled_services
        if overlap:
            errors.append("services both desired and disabled: " + ", ".join(sorted(overlap)))
        for key, resource in target.resources.items():
            if key != resource.id:
                errors.append(f"resource key {key!r} != id {resource.id!r}")
            if resource.state == "present" and resource.schema < 1:
                errors.append(f"resource {key}: schema must be >= 1")
        if not target.packages:
            errors.append("resolved target has no packages")
        return errors
