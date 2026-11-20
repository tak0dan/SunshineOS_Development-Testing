"""Fine-grained evolution events and their content integrity.

A milestone record is a convenient publication unit; an *event* is the atomic
unit of knowledge: one domain, one entity, one operation, with an expected
previous state, a desired state, and references to transition, validation and
recovery knowledge. Events make the ledger auditable and independently
verifiable without tying knowledge to a particular release script.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Mapping

from .ledger import EvolutionLedger
from .release import content_digest

DOMAINS = (
    "packages", "services", "configuration", "boot", "filesystem",
    "security", "network", "desktop", "users", "os_identity",
)
OPERATIONS = ("add", "modify", "replace", "retire", "adopt", "transition")


@dataclass(frozen=True)
class EvolutionEvent:
    event_id: str
    release_id: str
    domain: str
    entity_id: str
    operation: str
    previous_state: str = ""
    desired_state: str = ""
    transition_ref: str = ""
    dependencies: tuple[str, ...] = ()
    compatibility: Mapping[str, str] = frozenset()  # type: ignore[assignment]
    validation: tuple[str, ...] = ()
    recovery_ref: str = ""
    artifact_refs: tuple[str, ...] = ()
    event_hash: str = ""

    @classmethod
    def create(
        cls,
        *,
        release_id: str,
        domain: str,
        entity_id: str,
        operation: str,
        **fields: Any,
    ) -> "EvolutionEvent":
        base = {
            "release_id": str(release_id),
            "domain": str(domain),
            "entity_id": str(entity_id),
            "operation": str(operation),
            "previous_state": str(fields.get("previous_state", "")),
            "desired_state": str(fields.get("desired_state", "")),
            "transition_ref": str(fields.get("transition_ref", "")),
            "dependencies": [str(d) for d in fields.get("dependencies", [])],
            "compatibility": {
                str(k): str(v) for k, v in (fields.get("compatibility") or {}).items()
            },
            "validation": [str(v) for v in fields.get("validation", [])],
            "recovery_ref": str(fields.get("recovery_ref", "")),
            "artifact_refs": [str(a) for a in fields.get("artifact_refs", [])],
        }
        event_id = str(fields.get("event_id", "")) or content_digest(base)[:16]
        return cls(
            event_id=event_id,
            release_id=base["release_id"],
            domain=base["domain"],
            entity_id=base["entity_id"],
            operation=base["operation"],
            previous_state=base["previous_state"],
            desired_state=base["desired_state"],
            transition_ref=base["transition_ref"],
            dependencies=tuple(base["dependencies"]),
            compatibility=dict(base["compatibility"]),
            validation=tuple(base["validation"]),
            recovery_ref=base["recovery_ref"],
            artifact_refs=tuple(base["artifact_refs"]),
            event_hash=content_digest(base),
        )

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "EvolutionEvent":
        return cls(
            event_id=str(data.get("event_id", "")),
            release_id=str(data.get("release_id", "")),
            domain=str(data.get("domain", "")),
            entity_id=str(data.get("entity_id", "")),
            operation=str(data.get("operation", "")),
            previous_state=str(data.get("previous_state", "")),
            desired_state=str(data.get("desired_state", "")),
            transition_ref=str(data.get("transition_ref", "")),
            dependencies=tuple(str(d) for d in data.get("dependencies", [])),
            compatibility=frozenset(
                (str(k), str(v)) for k, v in (data.get("compatibility") or {}).items()
            ),
            validation=tuple(str(v) for v in data.get("validation", [])),
            recovery_ref=str(data.get("recovery_ref", "")),
            artifact_refs=tuple(str(a) for a in data.get("artifact_refs", [])),
            event_hash=str(data.get("event_hash", "")).lower(),
        )

    def validate(self) -> list[str]:
        errors: list[str] = []
        if not self.event_id:
            errors.append(f"event for {self.entity_id}: no event_id")
        if not self.release_id:
            errors.append(f"event {self.event_id}: no release_id")
        if self.domain not in DOMAINS:
            errors.append(f"event {self.event_id}: unknown domain {self.domain!r}")
        if self.operation not in OPERATIONS:
            errors.append(f"event {self.event_id}: unknown operation {self.operation!r}")
        if not self.entity_id:
            errors.append(f"event {self.event_id}: no entity_id")
        if len(self.event_hash) != 64:
            errors.append(f"event {self.event_id}: malformed event_hash")
        return errors

    def to_dict(self) -> dict[str, Any]:
        return {
            "event_id": self.event_id,
            "release_id": self.release_id,
            "domain": self.domain,
            "entity_id": self.entity_id,
            "operation": self.operation,
            "previous_state": self.previous_state,
            "desired_state": self.desired_state,
            "transition_ref": self.transition_ref,
            "dependencies": list(self.dependencies),
            "compatibility": {k: self.compatibility[k] for k in sorted(self.compatibility)},
            "validation": list(self.validation),
            "recovery_ref": self.recovery_ref,
            "artifact_refs": list(self.artifact_refs),
            "event_hash": self.event_hash,
        }


class EventCatalog:
    """Validated, immutable collection of evolution events."""

    def __init__(self, events: Iterable[EvolutionEvent]) -> None:
        self.events = tuple(events)
        errors: list[str] = []
        seen: set[str] = set()
        for event in self.events:
            errors.extend(event.validate())
            if event.event_id in seen:
                errors.append(f"duplicate event_id {event.event_id}")
            seen.add(event.event_id)
        if errors:
            raise ValueError("invalid evolution event catalog: " + "; ".join(errors))

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "EventCatalog":
        raw = data.get("events", data)
        if isinstance(raw, Mapping):
            raw = raw.get("items", [])
        return cls([EvolutionEvent.from_dict(e) for e in raw if isinstance(e, Mapping)])

    @classmethod
    def from_ledger(cls, ledger: EvolutionLedger) -> "EventCatalog":
        """Project milestone changes into atomic events for audit/verification."""
        events: list[EvolutionEvent] = []
        for record in ledger.ordered():
            change = record.changes
            for name in change.packages_desired:
                events.append(EvolutionEvent.create(
                    release_id=record.release_id, domain="packages",
                    entity_id=name, operation="add", desired_state="present",
                    validation=record.validations,
                ))
            for name in change.packages_removed:
                events.append(EvolutionEvent.create(
                    release_id=record.release_id, domain="packages",
                    entity_id=name, operation="retire", desired_state="absent",
                    validation=record.validations,
                ))
            for name in change.services_desired:
                events.append(EvolutionEvent.create(
                    release_id=record.release_id, domain="services",
                    entity_id=name, operation="add", desired_state="enabled",
                ))
            for name in change.services_disabled:
                events.append(EvolutionEvent.create(
                    release_id=record.release_id, domain="services",
                    entity_id=name, operation="retire", desired_state="disabled",
                ))
            for resource in change.configuration:
                events.append(EvolutionEvent.create(
                    release_id=record.release_id, domain="configuration",
                    entity_id=resource.id,
                    operation="add" if resource.state == "present" else "retire",
                    desired_state=resource.state,
                    compatibility={"schema": str(resource.schema)},
                    validation=record.validations,
                    recovery_ref="restore-previous-configuration",
                    artifact_refs=([resource.baseline_digest] if resource.baseline_digest else []),
                ))
            for transition in record.transitions:
                events.append(EvolutionEvent.create(
                    release_id=record.release_id, domain="boot" if "boot" in transition else "configuration",
                    entity_id=transition, operation="transition",
                    transition_ref=transition,
                    validation=record.validations,
                    recovery_ref="checkpoint-rollback",
                ))
        return cls(events)

    def digest(self) -> str:
        return content_digest([e.to_dict() for e in self.events])

    def to_dict(self) -> dict[str, Any]:
        return {"events": [e.to_dict() for e in self.events]}
