"""Fail-closed assessment of SteamOS read-only/developer-mode repair state.

SteamOS exposes separate readonly and developer-mode controls. A reported
"disabled" state does not prove that the root is writable or that developer
mode completed. This module consumes observations only; it never remounts,
changes the root, invokes pacman, or modifies the boot slots.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Any


@dataclass(frozen=True)
class SteamOSRepairAssessment:
    state: str  # healthy | readonly | partial_devmode | contradictory | unknown
    repairable: bool
    blockers: tuple[str, ...]
    next_step: str

    def to_dict(self) -> dict[str, object]:
        return {
            "state": self.state,
            "repairable": self.repairable,
            "blockers": list(self.blockers),
            "next_step": self.next_step,
            "policy": "assessment-only; no rootfs or slot mutation",
        }


def assess_steamos_repair(observed: Mapping[str, Any]) -> SteamOSRepairAssessment:
    """Classify fresh read-only/devmode evidence, rejecting missing or invalid data.

    Required keys: ``root_mount_readonly`` (bool), ``readonly_status``
    ("enabled"/"disabled"), ``devmode_status`` ("enabled"/"disabled"), and
    ``devmode_marker_present`` (bool). Unknown evidence never authorizes repair.
    """
    required = {
        "root_mount_readonly": bool,
        "readonly_status": str,
        "devmode_status": str,
        "devmode_marker_present": bool,
    }
    blockers = tuple(
        f"missing or invalid observation: {key}"
        for key, expected in required.items()
        if key not in observed or type(observed[key]) is not expected
    )
    if blockers:
        return SteamOSRepairAssessment(
            "unknown", False, blockers,
            "collect complete observations from the installed system; do not mutate it",
        )

    readonly = observed["readonly_status"].casefold()
    devmode = observed["devmode_status"].casefold()
    if readonly not in {"enabled", "disabled"} or devmode not in {"enabled", "disabled"}:
        return SteamOSRepairAssessment(
            "unknown", False, ("unrecognized control status",),
            "verify the installed SteamOS tool version and collect fresh observations",
        )

    mount_ro = observed["root_mount_readonly"]
    marker = observed["devmode_marker_present"]
    if readonly == "disabled" and mount_ro:
        return SteamOSRepairAssessment(
            "contradictory", False,
            ("readonly control reports disabled while the root mount is read-only",),
            "stop package repair; use the vendor recovery path or boot the retained known-good slot",
        )
    if devmode == "enabled" and (mount_ro or readonly != "disabled" or not marker):
        return SteamOSRepairAssessment(
            "contradictory", False,
            ("developer-mode status conflicts with root mount, readonly status, or marker",),
            "stop package repair; inspect the installed image and recover from a verified slot",
        )
    if devmode == "disabled" and (readonly == "disabled" or marker):
        return SteamOSRepairAssessment(
            "partial_devmode", False,
            ("developer-mode state is incomplete or its marker disagrees",),
            "do not retry package operations; preserve evidence and use the vendor recovery path",
        )
    if mount_ro and readonly == "enabled" and devmode == "disabled" and not marker:
        return SteamOSRepairAssessment(
            "readonly", False, (),
            "root is protected; use the normal signed update or recovery workflow",
        )
    if not mount_ro and readonly == "disabled" and devmode == "enabled" and marker:
        return SteamOSRepairAssessment(
            "healthy", True, (),
            "developer mode is internally consistent; take a checkpoint before any separate repair",
        )
    return SteamOSRepairAssessment(
        "contradictory", False,
        ("root mount and readonly/developer-mode status do not form a recognized consistent state",),
        "stop package repair; verify observations and use the vendor recovery path if the conflict persists",
    )
