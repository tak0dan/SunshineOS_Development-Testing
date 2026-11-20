"""Milestone versions, declarative steps, and upgrade-chain resolution.

A milestone is not a source-version branch. It is a published desired-state
gate with a predecessor, invariants and hooks. The engine observes the machine
and converges; the milestone chain only says which gates must be crossed and
in which order. That is why an unknown old Sunshine release can still upgrade:
the chain resumes at the nearest registered predecessor and convergence does
the rest from observed state.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from functools import total_ordering
from typing import Any, Iterable, Mapping

HOOK_PHASES = ("pre_upgrade", "post_milestone", "on_failure")
ROLLBACK_STRATEGIES = ("checkpoint", "snapshot", "none")


@total_ordering
@dataclass(frozen=True)
class MilestoneVersion:
    """A dotted numeric milestone identifier (0, 0.9, 1.0, 1.1, ...)."""

    parts: tuple[int, ...]

    @classmethod
    def parse(cls, value: Any) -> "MilestoneVersion":
        text = str(value or "").strip().lower()
        # Accept release-style aliases such as "sunshine-2026.1" and "v1.0";
        # aliases are resolved by the registry, but parsing must be forgiving.
        text = re.sub(r"^[a-z][a-z0-9_+-]*[-_/]", "", text)
        text = text.lstrip("v")
        if not text:
            raise ValueError(f"invalid milestone version: {value!r}")
        parts: list[int] = []
        for token in text.split("."):
            digits = "".join(ch for ch in token if ch.isdigit())
            if not digits:
                raise ValueError(f"invalid milestone version: {value!r}")
            parts.append(int(digits))
        return cls(tuple(parts))

    def __str__(self) -> str:
        return ".".join(str(p) for p in self.parts)

    def __lt__(self, other: object) -> bool:
        if not isinstance(other, MilestoneVersion):
            return NotImplemented
        left, right = self.parts, other.parts
        for a, b in zip(left, right):
            if a != b:
                return a < b
        return len(left) < len(right)

    def __eq__(self, other: object) -> bool:
        return isinstance(other, MilestoneVersion) and self.parts == other.parts

    def __hash__(self) -> int:
        return hash(self.parts)


@dataclass(frozen=True)
class HookSpec:
    """A sandboxed, journaled hook attached to a milestone phase."""

    id: str
    phase: str
    command: str = ""
    adapter: str = ""
    required: bool = False
    description: str = ""

    @classmethod
    def from_dict(cls, phase: str, data: Mapping[str, Any]) -> "HookSpec":
        return cls(
            id=str(data.get("id", "")).strip(),
            phase=phase,
            command=str(data.get("command", "")).strip(),
            adapter=str(data.get("adapter", "")).strip(),
            required=bool(data.get("required", False)),
            description=str(data.get("description", "")),
        )


@dataclass(frozen=True)
class Milestone:
    """One published evolutionary step."""

    id: str
    version: MilestoneVersion
    label: str
    predecessor: MilestoneVersion | None
    target_release: str
    invariants: tuple[str, ...] = ()
    hooks: tuple[HookSpec, ...] = ()
    rollback: str = "checkpoint"
    published: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "version": str(self.version),
            "label": self.label,
            "predecessor": str(self.predecessor) if self.predecessor else None,
            "target_release": self.target_release,
            "invariants": list(self.invariants),
            "hooks": [
                {
                    "id": h.id, "phase": h.phase, "command": h.command,
                    "adapter": h.adapter, "required": h.required,
                }
                for h in self.hooks
            ],
            "rollback": self.rollback,
            "published": self.published,
        }


class MilestoneRegistry:
    """Validated, ordered set of milestones and release aliases."""

    def __init__(
        self,
        current: MilestoneVersion,
        milestones: Iterable[Milestone],
        aliases: Mapping[str, MilestoneVersion] | None = None,
    ) -> None:
        self.current = current
        self.milestones = tuple(sorted(milestones, key=lambda m: m.version))
        self.aliases = dict(aliases or {})
        errors = self.validate()
        if errors:
            raise ValueError("invalid milestone scheme: " + "; ".join(errors))

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "MilestoneRegistry":
        current = MilestoneVersion.parse(data.get("current", "0"))
        aliases: dict[str, MilestoneVersion] = {}
        for key, value in (data.get("aliases") or {}).items():
            aliases[str(key).strip().lower()] = MilestoneVersion.parse(value)

        milestones: list[Milestone] = []
        seen: set[str] = set()
        for raw in data.get("milestones", []):
            if not isinstance(raw, Mapping):
                raise ValueError("milestone entry must be a table")
            version = MilestoneVersion.parse(raw.get("version", ""))
            mid = str(raw.get("id", "")).strip() or str(version)
            if mid in seen:
                raise ValueError(f"duplicate milestone id '{mid}'")
            seen.add(mid)
            predecessor_raw = raw.get("predecessor")
            predecessor = MilestoneVersion.parse(predecessor_raw) if predecessor_raw else None
            hooks: list[HookSpec] = []
            for phase in HOOK_PHASES:
                for hook in raw.get(phase, []) or []:
                    if isinstance(hook, Mapping):
                        hooks.append(HookSpec.from_dict(phase, hook))
            milestones.append(Milestone(
                id=mid,
                version=version,
                label=str(raw.get("label", mid)),
                predecessor=predecessor,
                target_release=str(raw.get("target_release", "")),
                invariants=tuple(str(c) for c in raw.get("invariants", []) or []),
                hooks=tuple(hooks),
                rollback=str(raw.get("rollback", "checkpoint")),
                published=bool(raw.get("published", True)),
            ))
        return cls(current, milestones, aliases)

    def validate(self) -> list[str]:
        errors: list[str] = []
        if not self.milestones:
            return ["no milestones defined"]
        versions = [m.version for m in self.milestones]
        if len(set(versions)) != len(versions):
            errors.append("duplicate milestone versions")
        if versions[0] != MilestoneVersion.parse("0"):
            errors.append("first milestone must be version 0 (vanilla Arch)")
        for left, right in zip(versions, versions[1:]):
            if right <= left:
                errors.append(f"milestones are not strictly increasing at {right}")
        if self.milestones[0].predecessor is not None:
            errors.append("milestone 0 must have no predecessor")
        known = set(versions)
        for m in self.milestones[1:]:
            if m.predecessor is None:
                errors.append(f"{m.version}: missing predecessor")
            elif m.predecessor not in known:
                errors.append(f"{m.version}: predecessor {m.predecessor} is not registered")
            elif m.predecessor >= m.version:
                errors.append(f"{m.version}: predecessor is not older")
            if m.rollback not in ROLLBACK_STRATEGIES:
                errors.append(f"{m.version}: unknown rollback strategy '{m.rollback}'")
            for h in m.hooks:
                if h.phase not in HOOK_PHASES:
                    errors.append(f"{m.version}: invalid hook phase '{h.phase}'")
                if not h.id:
                    errors.append(f"{m.version}: hook has no id")
                if not h.command and not h.adapter:
                    errors.append(f"{m.version}: hook '{h.id}' has no command or adapter")
        if self.current not in known:
            errors.append(f"current milestone {self.current} is not registered")
        current = self.get(self.current)
        if current is not None and not current.published:
            errors.append("current milestone is not published")
        for alias, version in self.aliases.items():
            if version not in known:
                errors.append(f"alias '{alias}' points to unknown milestone {version}")
        return errors

    def get(self, version: MilestoneVersion) -> Milestone | None:
        for m in self.milestones:
            if m.version == version:
                return m
        return None

    def resolve_version(self, value: Any) -> MilestoneVersion:
        text = str(value or "").strip().lower()
        if text in self.aliases:
            return self.aliases[text]
        try:
            return MilestoneVersion.parse(text)
        except ValueError as exc:
            raise ValueError(f"unknown milestone or release '{value}'") from exc

    def chain(
        self, source: Any, target: Any | None = None
    ) -> list[Milestone]:
        """Return the ordered steps needed to reach ``target`` from ``source``.

        An unregistered source is mapped to the greatest registered milestone
        that is not newer than it. Desired-state convergence, not step replay,
        handles the actual state between that milestone and the current one.
        """
        source_version = self.resolve_version(source)
        target_version = self.resolve_version(target if target is not None else self.current)
        target_milestone = self.get(target_version)
        if target_milestone is None:
            raise ValueError(f"target milestone {target_version} is not registered")
        if not target_milestone.published:
            raise ValueError(f"target milestone {target_version} is not published")
        if source_version > target_version:
            raise ValueError(
                f"refusing downgrade from {source_version} to {target_version}"
            )
        if source_version not in {m.version for m in self.milestones}:
            older = [m.version for m in self.milestones if m.version < source_version]
            if not older:
                raise ValueError(
                    f"source {source_version} is older than every registered milestone"
                )
            source_version = max(older)
        return [
            m for m in self.milestones
            if source_version < m.version <= target_version
        ]

    def to_dict(self) -> dict[str, Any]:
        return {
            "current": str(self.current),
            "aliases": {k: str(v) for k, v in sorted(self.aliases.items())},
            "milestones": [m.to_dict() for m in self.milestones],
        }
