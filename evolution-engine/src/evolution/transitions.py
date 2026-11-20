"""Semantic transition registry.

Transitions describe *component state* changes (network schema 2 -> 3,
service A -> B, boot config v1 -> v2), not release-to-release scripts. Their
applicability is decided from observed state, so a machine at evolution 1 and
one at evolution 20 can use the same transition when both have the same old
component schema.

Definitions are retained even after executable support is retired; a retired
transition still records why and when, so future engineers understand the
decision instead of rediscovering it.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Mapping


@dataclass(frozen=True)
class TransitionSpec:
    id: str
    component: str
    source_schema: int
    target_schema: int
    actions: tuple[str, ...] = ()
    preconditions: tuple[str, ...] = ()
    postconditions: tuple[str, ...] = ()
    recovery: tuple[str, ...] = ()
    supported: bool = True
    deprecated_at: str = ""
    retired_reason: str = ""

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "TransitionSpec":
        return cls(
            id=str(data.get("id", "")).strip(),
            component=str(data.get("component", "")).strip(),
            source_schema=int(data.get("source_schema", 0)),
            target_schema=int(data.get("target_schema", 0)),
            actions=tuple(str(a) for a in data.get("actions", [])),
            preconditions=tuple(str(p) for p in data.get("preconditions", [])),
            postconditions=tuple(str(p) for p in data.get("postconditions", [])),
            recovery=tuple(str(r) for r in data.get("recovery", [])),
            supported=bool(data.get("supported", True)),
            deprecated_at=str(data.get("deprecated_at", "")),
            retired_reason=str(data.get("retired_reason", "")),
        )

    def applies_to(self, component: str, source_schema: int, target_schema: int) -> bool:
        return (
            self.component == component
            and self.source_schema == source_schema
            and self.target_schema == target_schema
        )

    def to_dict(self) -> dict[str, Any]:
        result = {
            "id": self.id,
            "component": self.component,
            "source_schema": self.source_schema,
            "target_schema": self.target_schema,
            "actions": list(self.actions),
            "preconditions": list(self.preconditions),
            "postconditions": list(self.postconditions),
            "recovery": list(self.recovery),
            "supported": self.supported,
        }
        if self.deprecated_at:
            result["deprecated_at"] = self.deprecated_at
        if self.retired_reason:
            result["retired_reason"] = self.retired_reason
        return result


class TransitionRegistry:
    """Validated set of semantic transitions and their compatibility contracts."""

    def __init__(self, transitions: Iterable[TransitionSpec]) -> None:
        self.transitions = tuple(transitions)
        errors = self.validate()
        if errors:
            raise ValueError("invalid transition registry: " + "; ".join(errors))

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "TransitionRegistry":
        raw = data.get("transitions", data)
        if isinstance(raw, Mapping):
            raw = raw.get("items", [])
        return cls([
            TransitionSpec.from_dict(t) for t in raw if isinstance(t, Mapping)
        ])

    def validate(self) -> list[str]:
        errors: list[str] = []
        seen: set[str] = set()
        for t in self.transitions:
            if not t.id:
                errors.append("transition has no id")
            if t.id in seen:
                errors.append(f"duplicate transition id {t.id}")
            seen.add(t.id)
            if not t.component:
                errors.append(f"{t.id}: no component")
            if t.target_schema <= t.source_schema:
                errors.append(f"{t.id}: target_schema must be greater than source_schema")
            if t.supported and not t.actions:
                errors.append(f"{t.id}: supported transition has no actions")
            if not t.supported and not t.retired_reason:
                errors.append(f"{t.id}: retired transition has no retired_reason")
        # Ambiguity: two supported transitions for the same contract.
        contracts: dict[tuple[str, int, int], list[str]] = {}
        for t in self.transitions:
            if t.supported:
                contracts.setdefault(
                    (t.component, t.source_schema, t.target_schema), []
                ).append(t.id)
        for contract, ids in contracts.items():
            if len(ids) > 1:
                errors.append(f"ambiguous transitions for {contract}: {ids}")
        return errors

    def find(self, component: str, source_schema: int, target_schema: int) -> TransitionSpec | None:
        for t in self.transitions:
            if t.applies_to(component, source_schema, target_schema) and t.supported:
                return t
        return None

    def any_for(self, component: str, source_schema: int, target_schema: int) -> TransitionSpec | None:
        """Find a definition even if it is retired (for reporting)."""
        for t in self.transitions:
            if t.applies_to(component, source_schema, target_schema):
                return t
        return None

    def chain(self, component: str, source_schema: int, target_schema: int) -> list[TransitionSpec]:
        """Build the shortest supported schema chain for one component.

        Returns an empty list when no chain exists; the caller must treat that
        as a compatibility failure rather than silently skipping the migration.
        """
        if target_schema <= source_schema:
            return []
        best: dict[int, list[TransitionSpec]] = {source_schema: []}
        for _ in range(len(self.transitions) + 1):
            changed = False
            for t in self.transitions:
                if not t.supported or t.component != component:
                    continue
                if t.source_schema not in best:
                    continue
                candidate = best[t.source_schema] + [t]
                if (
                    t.target_schema not in best
                    or len(candidate) < len(best[t.target_schema])
                ):
                    best[t.target_schema] = candidate
                    changed = True
            if not changed:
                break
        return best.get(target_schema, [])

    def required_for(
        self, component_schemas: Mapping[str, int], target_schemas: Mapping[str, int]
    ) -> list[TransitionSpec]:
        """Collect transitions for all components whose schema must advance."""
        needed: list[TransitionSpec] = []
        for component, target_schema in sorted(target_schemas.items()):
            source_schema = int(component_schemas.get(component, 0))
            if target_schema <= source_schema:
                continue
            steps = self.chain(component, source_schema, target_schema)
            if not steps:
                continue
            needed.extend(steps)
        return needed

    def to_dict(self) -> dict[str, Any]:
        return {"transitions": [t.to_dict() for t in self.transitions]}
