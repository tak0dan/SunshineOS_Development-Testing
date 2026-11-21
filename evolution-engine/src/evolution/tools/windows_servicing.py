"""Fail-closed assessment of Windows servicing evidence.

This module consumes captured, read-only DISM/SFC probe results. It does not
invoke Windows repair operations; callers must stage and authorize mutations
through the normal migration executor.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping


@dataclass(frozen=True)
class ServicingProbe:
    name: str
    command: tuple[str, ...]
    return_code: int | None
    output: str = ""


@dataclass(frozen=True)
class ServicingFinding:
    check: str
    status: str  # healthy | degraded | unknown | blocked
    detail: str
    command: tuple[str, ...] = ()


@dataclass(frozen=True)
class WindowsServicingReport:
    findings: tuple[ServicingFinding, ...]

    @property
    def healthy(self) -> bool:
        return bool(self.findings) and all(item.status == "healthy" for item in self.findings)

    @property
    def blocked(self) -> bool:
        return any(item.status in {"unknown", "blocked"} for item in self.findings)


REQUIRED_PROBES = {
    "dism-checkhealth": ("DISM", "/Online", "/Cleanup-Image", "/CheckHealth"),
    "dism-scanhealth": ("DISM", "/Online", "/Cleanup-Image", "/ScanHealth"),
    "sfc-verifyonly": ("sfc", "/verifyonly"),
}

# A successful process exit is not sufficient evidence of a healthy store.
# Keep this allowlist deliberately narrow: localized or changed output remains
# unknown until a collector supplies a locale-aware parser backed by fixtures.
CLEAN_OUTPUT_MARKERS = {
    "dism-checkhealth": ("no component store corruption detected",),
    "dism-scanhealth": ("no component store corruption detected",),
    "sfc-verifyonly": ("windows resource protection did not find any integrity violations",),
}


def assess_windows_servicing(
    probes: Mapping[str, ServicingProbe], *, reboot_pending: bool | None
) -> WindowsServicingReport:
    """Classify previously collected servicing checks without making changes."""
    findings: list[ServicingFinding] = []
    for name, command in REQUIRED_PROBES.items():
        probe = probes.get(name)
        if probe is None:
            findings.append(ServicingFinding(name, "unknown", "required probe is missing", command))
            continue
        if probe.name != name:
            findings.append(ServicingFinding(name, "blocked", "probe identity does not match its evidence key", probe.command))
            continue
        if probe.command != command:
            findings.append(ServicingFinding(name, "blocked", "probe command does not match the required read-only check", probe.command))
            continue
        if probe.return_code is None or probe.return_code == 127:
            findings.append(ServicingFinding(name, "unknown", "probe result is unavailable", command))
            continue
        if probe.return_code != 0:
            findings.append(ServicingFinding(name, "degraded", f"probe exited with status {probe.return_code}", command))
            continue
        text = probe.output.casefold()
        if any(marker in text for marker in CLEAN_OUTPUT_MARKERS[name]):
            findings.append(ServicingFinding(name, "healthy", "probe reported its recognized clean result", command))
        elif any(token in text for token in ("component store is repairable", "component store cannot be repaired", "corrupt", "repair content")):
            findings.append(ServicingFinding(name, "degraded", "probe output reports corruption or required repair content", command))
        else:
            findings.append(ServicingFinding(name, "unknown", "probe output does not contain a recognized clean result", command))

    if reboot_pending is None:
        findings.append(ServicingFinding("reboot-state", "unknown", "pending-reboot state was not observed"))
    elif reboot_pending:
        findings.append(ServicingFinding("reboot-state", "blocked", "servicing state is not settled until the pending reboot is completed"))
    else:
        findings.append(ServicingFinding("reboot-state", "healthy", "no pending reboot was observed"))
    return WindowsServicingReport(tuple(findings))
