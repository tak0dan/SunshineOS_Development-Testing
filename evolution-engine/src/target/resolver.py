"""Desired-state resolution: turn observations into a concrete target.

``resolve_target()`` takes the published target (which describes *what* a
Sunshine system must be) and the observed machine (which describes *what is
there*) and returns a customised target plus a list of decisions. It never
mutates its inputs.

The guiding rule is to decide automatically whenever the observation is strong
enough, and to ask at most one focused question when it is not:

* exactly one supported desktop seen with high/medium confidence -> select it;
* several desktops seen, one marked as the configured default -> keep it;
* several desktops with no clear default -> one user decision with the candidates;
* existing bootloader / network / audio choices that the target supports are
  preserved verbatim by activating their corresponding package set;
* Nix integration is activated only when Nix is actually present.

The resulting ``TargetSpec`` is still declarative: profile packages and
preserved choices are expressed as package sets and capability contracts, so
the planner remains the only component that decides *how* to converge.
"""
from __future__ import annotations

import re
from copy import deepcopy
from pathlib import Path
from typing import Any, Iterable, Mapping

from ..core import Confidence, ObservedState, Status, TargetSpec
from .profiles import (
    DesktopDetection,
    DesktopProfile,
    choose_profile,
    detect_desktop_sessions,
    load_profiles,
)

_PRESERVED_CATEGORIES = ("bootloader", "network", "audio")
_GENERIC_VALUES = {
    "configured",
    "installed",
    "enabled",
    "running",
    "functional",
    "present",
    "detected",
    "yes",
    "true",
    "unknown",
}
_NEGATIVE_VALUES = {"absent", "none", "false", "disabled", "no", "not-installed", "not installed"}


def _decision(
    decision_id: str,
    kind: str,
    *,
    selected: str | None = None,
    options: Iterable[str] = (),
    auto: bool = True,
    action: str = "select",
    reason: str = "",
    evidence: Iterable[str] = (),
    question: str = "",
    confidence: str = "",
    conflicts: Iterable[str] = (),
) -> dict[str, Any]:
    """Build a uniform decision record consumable by planners and the CLI.

    ``auto`` decisions are informational facts the resolver settled itself;
    ``requires_user_input`` is the single flag callers should check before
    prompting. All records carry the same keys so consumers never need to guess
    which fields exist.
    """
    return {
        "id": decision_id,
        "kind": kind,
        "action": action,
        "auto": bool(auto),
        "requires_user_input": not auto,
        "selected": selected,
        "options": list(options),
        "question": question,
        "reason": reason,
        "evidence": list(evidence),
        "confidence": confidence,
        "conflicts": list(conflicts),
    }


def _dedupe(items: Iterable[str]) -> list[str]:
    return list(dict.fromkeys(items))


def resolve_target(
    observed: ObservedState,
    target: TargetSpec,
    profiles_dir: str | Path | None = None,
) -> tuple[TargetSpec, list[dict[str, Any]]]:
    """Resolve the published target against a simulated or real observed state.

    Returns a deep copy of ``target`` specialised for this machine and the
    decisions that led there. A copy guarantees that repeated resolution with
    different observations cannot leak one machine's profile into another's.
    """
    resolved = deepcopy(target)
    decisions: list[dict[str, Any]] = []
    profiles = load_profiles(profiles_dir)
    detections = detect_desktop_sessions(observed, profiles)

    _resolve_desktop(observed, resolved, profiles, detections, decisions)
    for category in _PRESERVED_CATEGORIES:
        _preserve_choice(observed, resolved, category, decisions)
    _resolve_nix(observed, resolved, decisions)
    return resolved, decisions


def _resolve_desktop(
    observed: ObservedState,
    target: TargetSpec,
    profiles: Mapping[str, DesktopProfile],
    detections: Mapping[str, DesktopDetection],
    decisions: list[dict[str, Any]],
) -> None:
    """Select a desktop profile, automatically where the evidence allows it."""
    chosen, options, needs_input = choose_profile(detections, profiles.keys())
    if needs_input:
        details = ", ".join(options) if options else "none of the supported profiles"
        decisions.append(
            _decision(
                "desktop-profile",
                "desktop_profile",
                options=options,
                auto=False,
                question="Which desktop profile should Sunshine manage?",
                reason=f"Desktop intent is ambiguous or undetected ({details}).",
                evidence=[
                    f"{pid}: {det.confidence.value}" for pid, det in sorted(detections.items())
                ],
            )
        )
        return

    assert chosen is not None  # choose_profile guarantees this when needs_input is False
    profile = profiles[chosen]
    component = target.components.get("desktop_integration")

    target.package_sets["desktop_integration"] = _dedupe(
        list(target.package_sets.get("desktop_integration", [])) + list(profile.packages)
    )
    if component is not None:
        component.requires = _dedupe(
            list(component.requires) + list(profile.required_capabilities)
        )
        component.provides = _dedupe(
            list(component.provides) + [f"desktop-profile:{profile.id}"]
        )

    detection = detections.get(chosen)
    evidence = list(detection.evidence) if detection else []
    if detection is not None and detection.is_default:
        reason = f"'{chosen}' is the configured default desktop; preserving it."
    elif detection is not None:
        reason = f"Exactly one supported desktop ('{chosen}') was detected with sufficient confidence."
    else:
        reason = f"Selected desktop profile '{chosen}'."

    decisions.append(
        _decision(
            "desktop-profile",
            "desktop_profile",
            selected=chosen,
            options=[chosen],
            action="preserve",
            reason=reason,
            evidence=evidence,
            confidence=detection.confidence.value if detection else "",
            conflicts=profile.conflicts,
        )
    )


def _supported_choices(target: TargetSpec, category: str) -> dict[str, list[str]]:
    """Derive the supported choices from ``<category>.<choice>`` package sets."""
    prefix = category + "."
    return {
        name[len(prefix) :]: list(packages)
        for name, packages in target.package_sets.items()
        if name.startswith(prefix) and isinstance(packages, list)
    }


def _choice_from_text(value: str, choices: Iterable[str]) -> str | None:
    """Match a free-form observed value against known choice identifiers."""
    text = re.sub(r"[^a-z0-9]+", "-", str(value).lower()).strip("-")
    known = set(choices)
    if text in known:
        return text
    for token in text.split("-"):
        if token in known:
            return token
    compact = text.replace("-", "")
    for choice in known:
        if choice.replace("-", "") in compact:
            return choice
    return None


def _observed_choice(
    observed: ObservedState, category: str
) -> tuple[str, list[str], Confidence] | None:
    """Find a raw user choice for ``category`` in observations/capabilities."""
    needle = category.lower()
    pattern = re.compile(rf"(?:^|[-_:./ ]){re.escape(needle)}[-_:./ ]?")
    for key, observation in observed.observations.items():
        if observation.status == Status.ABSENT:
            continue
        # The category must be part of the observation's identity (key or
        # component), not merely mentioned in free-form evidence.  Otherwise a
        # generic observation such as ``services.systemd`` whose evidence
        # mentions "network" would be misread as the network backend choice.
        identity = f"{key} {observation.component}".lower()
        if not re.search(rf"(?:^|[-_:./ ]){re.escape(needle)}(?:[-_:./ ]|$)", identity):
            continue
        candidates: list[str] = []
        # Prefer the value encoded in the key suffix, e.g.
        # ``network.networkmanager`` -> ``networkmanager``.
        for source in (key, observation.component):
            split = pattern.split(str(source).lower(), maxsplit=1)
            if len(split) == 2 and split[1].strip():
                candidates.append(split[1].strip())
        candidates.append(str(observation.detected))
        candidates.extend(str(e) for e in observation.evidence)
        for candidate in candidates:
            token = candidate.strip()
            if token and token.lower() not in _GENERIC_VALUES:
                return token, [f"{key}: {observation.detected}"], observation.confidence

    for capability in sorted(observed.capabilities):
        split = re.split(rf"^{re.escape(needle)}[-_:]", str(capability).lower(), maxsplit=1)
        if len(split) == 2 and split[1].strip():
            return split[1].strip(), [f"capability: {capability}"], Confidence.MEDIUM
    return None


def _preserve_choice(
    observed: ObservedState,
    target: TargetSpec,
    category: str,
    decisions: list[dict[str, Any]],
) -> None:
    """Keep an existing compatible choice, or ask one question if incompatible."""
    supported = _supported_choices(target, category)
    if not supported:
        return
    found = _observed_choice(observed, category)
    if found is None:
        return
    raw, evidence, confidence = found
    choice = _choice_from_text(raw, supported)

    if choice is None:
        decisions.append(
            _decision(
                f"{category}-choice",
                category,
                options=sorted(supported),
                auto=False,
                question=f"Which {category} should replace the observed '{raw}'?",
                reason=f"Observed {category} '{raw}' is not supported by this target.",
                evidence=evidence,
                confidence=confidence.value,
            )
        )
        return

    target.package_sets[category] = _dedupe(list(supported[choice]))
    decisions.append(
        _decision(
            f"{category}-choice",
            category,
            selected=choice,
            options=[choice],
            action="preserve",
            reason=f"Preserving the existing compatible {category} choice '{choice}'.",
            evidence=evidence,
            confidence=confidence.value,
        )
    )


def _is_negative(value: str) -> bool:
    return str(value).strip().lower() in _NEGATIVE_VALUES


def _resolve_nix(
    observed: ObservedState,
    target: TargetSpec,
    decisions: list[dict[str, Any]],
) -> None:
    """Activate the optional Nix component only when Nix is really present."""
    evidence: list[str] = []
    for key, observation in observed.observations.items():
        blob = f"{key} {observation.component} {observation.detected}".lower()
        if (
            "nix" in blob
            and observation.status != Status.ABSENT
            and not _is_negative(observation.detected)
        ):
            evidence.append(f"{key}: {observation.detected}")
    for package in observed.packages:
        name = str(package).lower()
        if name == "nix" or name.startswith("nix-") or name.startswith("nixpkgs"):
            evidence.append(f"package: {package}")
    for capability in observed.capabilities:
        if "nix" in str(capability).lower():
            evidence.append(f"capability: {capability}")

    if not evidence:
        return

    component = target.components.get("nix_integration")
    if component is not None:
        component.required = True
    optional = target.package_sets.get("nix.optional") or ["nix"]
    target.package_sets["nix_integration"] = _dedupe(
        list(target.package_sets.get("nix_integration", [])) + list(optional)
    )
    decisions.append(
        _decision(
            "nix-integration",
            "nix",
            selected="enabled",
            options=["enabled"],
            action="preserve",
            reason="Nix is present; integrating it keeps foreign packages visible to ownership policy.",
            evidence=evidence,
        )
    )
