"""Source compatibility evaluation and migration mode selection.

Bootstrap (external Arch-family -> current SunshineOS) and evolution (existing
SunshineOS -> newer release) share the same discovery, inventory, planner,
executor and validation core. They differ only in compatibility assumptions
and transition rules.

Support is defined by *source-state compatibility*, not by the number of
sequential upgrades: a machine at evolution 1 may migrate directly to evolution
40 if its observed component states have supported semantic transitions.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Mapping

from .inventory import Inventory
from .qualification import SUPPORT_TIERS, SourceCapabilities
from .transitions import TransitionRegistry


@dataclass(frozen=True)
class SupportPolicy:
    """Explicit support horizon, stated in years *and* evolution counts."""

    minimum_years: int = 10
    minimum_evolutions: int = 40
    architectural_years: int = 20
    architectural_evolutions: int = 80

    def within_minimum(self, age_years: int, evolution_count: int) -> bool:
        return age_years <= self.minimum_years or evolution_count <= self.minimum_evolutions

    def within_architectural(self, age_years: int, evolution_count: int) -> bool:
        return (
            age_years <= self.architectural_years
            or evolution_count <= self.architectural_evolutions
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "minimum_years": self.minimum_years,
            "minimum_evolutions": self.minimum_evolutions,
            "architectural_years": self.architectural_years,
            "architectural_evolutions": self.architectural_evolutions,
        }


DEFAULT_POLICY = SupportPolicy()


@dataclass(frozen=True)
class SourceProfile:
    """Compatibility *hint* for a source distribution; never a final verdict."""

    name: str
    markers: tuple[str, ...] = ()
    known_repositories: tuple[str, ...] = ()
    known_packages: tuple[str, ...] = ()
    known_incompatibilities: tuple[str, ...] = ()

    def confidence_for(self, inv: Inventory) -> str:
        distribution = str(inv.identity.get("distribution", "")).strip().lower()
        repositories = {
            str(r).lower() for r in inv.repositories.get("configured", [])
        }
        if distribution in {m.lower() for m in self.markers}:
            return "high"
        if repositories & {r.lower() for r in self.known_repositories}:
            return "medium"
        return "low"

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "markers": list(self.markers),
            "known_repositories": list(self.known_repositories),
            "known_packages": list(self.known_packages),
            "known_incompatibilities": list(self.known_incompatibilities),
        }


SOURCE_PROFILES: tuple[SourceProfile, ...] = (
    SourceProfile("arch", ("arch", "archlinux"), ("core", "extra", "multilib")),
    SourceProfile("endeavouros", ("endeavouros",), ("endeavouros", "artix-archlinux-support")),
    SourceProfile("garuda", ("garuda",), ("garuda", "chaotic-aur")),
    SourceProfile("cachyos", ("cachyos",), ("cachyos", "cachyos-v3")),
    SourceProfile("manjaro", ("manjaro",), ("manjaro-stable", "manjaro-testing")),
    SourceProfile("artix", ("artix", "artixlinux"), ("system", "world", "galaxy")),
    SourceProfile("obarun", ("obarun",), ("obarun", "obrepo")),
    SourceProfile("steamos", ("steamos", "steam os"), ("steamos",)),
    SourceProfile("omarchy", ("omarchy",), ("omarchy",)),
    SourceProfile("unknown-arch-family", (), ()),
)


@dataclass(frozen=True)
class CompatibilityReport:
    mode: str                      # bootstrap | evolution
    source_confidence: str
    supported: bool
    reasons: tuple[str, ...] = ()
    required_transitions: tuple[str, ...] = ()
    profile: str = "unknown-arch-family"
    support_tier: str = "unsupported"

    def to_dict(self) -> dict[str, Any]:
        return {
            "mode": self.mode,
            "source_confidence": self.source_confidence,
            "supported": self.supported,
            "reasons": list(self.reasons),
            "required_transitions": list(self.required_transitions),
            "profile": self.profile,
            "support_tier": self.support_tier,
        }


class CompatibilityEngine:
    """Decide whether a source state can safely converge on a target."""

    def __init__(
        self,
        profiles: Iterable[SourceProfile] = SOURCE_PROFILES,
        policy: SupportPolicy = DEFAULT_POLICY,
        transitions: TransitionRegistry | None = None,
    ) -> None:
        self.profiles = tuple(profiles)
        self.policy = policy
        self.transitions = transitions

    @staticmethod
    def select_mode(inv: Inventory) -> str:
        """Evolution requires adopted Sunshine state; otherwise bootstrap."""
        metadata = inv.migration_metadata
        adopted = bool(
            metadata.get("sunshine_adopted")
            or metadata.get("migration_history")
            or metadata.get("ownership_registry")
        )
        return "evolution" if adopted else "bootstrap"

    def classify(
        self,
        inv: Inventory,
        target_schemas: Mapping[str, int] | None = None,
        source_schemas: Mapping[str, int] | None = None,
        *,
        age_years: int = 0,
        evolution_count: int = 0,
        capabilities: SourceCapabilities | None = None,
    ) -> CompatibilityReport:
        reasons: list[str] = []
        mode = self.select_mode(inv)

        best_profile = "unknown-arch-family"
        best_confidence = "low"
        rank = {"low": 0, "medium": 1, "high": 2}
        for profile in self.profiles:
            confidence = profile.confidence_for(inv)
            if rank[confidence] > rank[best_confidence]:
                best_profile, best_confidence = profile.name, confidence
        reasons.append(f"source profile {best_profile} (confidence {best_confidence})")

        package_manager = str(inv.identity.get("package_manager", "")).lower()
        supported = True
        if package_manager and "pacman" not in package_manager and "alpm" not in package_manager:
            supported = False
            reasons.append(f"unsupported package manager {package_manager!r}")
        if best_confidence == "low":
            reasons.append("unknown source: generic bootstrap path with stricter checks")
        if mode == "bootstrap" and best_confidence == "low":
            # Unknown critical infrastructure blocks automatic migration.
            if not inv.boot.get("capabilities") and not inv.runtime.get("capabilities"):
                supported = False
                reasons.append("unknown critical boot/runtime infrastructure")

        within_min = self.policy.within_minimum(age_years, evolution_count)
        within_arch = self.policy.within_architectural(age_years, evolution_count)
        if not within_min:
            reasons.append(
                f"outside minimum support horizon ({age_years}y / {evolution_count} evolutions)"
            )
            if not within_arch:
                supported = False
                reasons.append("outside architectural horizon; migration refused")
            else:
                supported = False
                reasons.append("architectural horizon only; manual qualification required")

        transition_ids: list[str] = []
        if self.transitions and target_schemas:
            for step in self.transitions.required_for(
                dict(source_schemas or {}), dict(target_schemas)
            ):
                transition_ids.append(step.id)
            for component, schema in sorted(target_schemas.items()):
                source = int((source_schemas or {}).get(component, 0))
                if schema > source and not any(
                    t.component == component for t in self.transitions.transitions
                ):
                    supported = False
                    reasons.append(f"no transition knowledge for {component} schema {source}->{schema}")

        tier = "unsupported"
        if capabilities is not None:
            tier = capabilities.tier()
            reasons.append(f"capability support tier {tier}")
            if tier in ("unsupported", "assessment_only"):
                supported = False
            if tier not in SUPPORT_TIERS:
                supported = False
        elif supported:
            tier = "qualified_with_intervention" if best_confidence == "low" else "qualified"

        return CompatibilityReport(
            mode=mode,
            source_confidence=best_confidence,
            supported=supported,
            reasons=tuple(reasons),
            required_transitions=tuple(transition_ids),
            profile=best_profile,
            support_tier=tier,
        )
