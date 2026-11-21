"""Read-only, root-scoped systemd unit-file repair assessment.

This module identifies filesystem evidence needed before a repair can be
planned. It does not rewrite unit files or call systemctl: vendor ownership,
package integrity, and administrator intent must be established separately.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from .systemd_inventory import UNIT_NAME


@dataclass(frozen=True)
class UnitFileFinding:
    unit: str
    vendor_path: str
    admin_path: str
    state: str
    detail: str


@dataclass(frozen=True)
class SystemdRepairAssessment:
    root: str
    complete: bool
    findings: tuple[UnitFileFinding, ...]
    blockers: tuple[str, ...] = ()
    commands: tuple[tuple[str, ...], ...] = ()

    def to_dict(self) -> dict[str, object]:
        return {
            "root": self.root,
            "complete": self.complete,
            "findings": [
                {
                    "unit": f.unit,
                    "vendor_path": f.vendor_path,
                    "admin_path": f.admin_path,
                    "state": f.state,
                    "detail": f.detail,
                }
                for f in self.findings
            ],
            "blockers": list(self.blockers),
            "commands": [list(command) for command in self.commands],
        }


def assess_systemd_unit_files(
    root: str | Path, units: Iterable[str]
) -> SystemdRepairAssessment:
    """Inspect vendor/admin unit-file layers under ``root`` without mutation.

    Absolute symlink targets are interpreted inside the supplied root, as in
    a chrooted filesystem view. Relative symlinks are resolved normally. Any
    resolved path outside that root blocks the entire assessment.
    """
    base = Path(root).resolve()
    names = tuple(dict.fromkeys(units))
    invalid = tuple(name for name in names if not UNIT_NAME.fullmatch(name))
    if invalid:
        return SystemdRepairAssessment(
            str(base), False, (), ("invalid systemd unit identifiers: " + ", ".join(invalid),)
        )

    findings: list[UnitFileFinding] = []
    for name in names:
        vendor = base / "usr/lib/systemd/system" / name
        admin = base / "etc/systemd/system" / name
        resolved: list[Path] = []
        for candidate in (vendor, admin):
            if candidate == admin and os_readlink_is_dev_null(candidate):
                resolved.append(candidate)
                continue
            try:
                target = candidate.resolve(strict=False)
                target.relative_to(base)
            except (OSError, ValueError):
                return SystemdRepairAssessment(
                    str(base), False, tuple(findings),
                    (f"unit path escapes observed root: {candidate}",),
                )
            resolved.append(target)

        vendor_target, admin_target = resolved
        vendor_exists = vendor_target.is_file()
        admin_exists = admin_target.is_file()
        if admin.is_symlink() and os_readlink_is_dev_null(admin):
            state, detail = "masked", "administrator unit path masks the unit"
        elif admin_exists and admin_target.stat().st_size == 0:
            state, detail = "empty-admin", "administrator unit file is empty"
        elif vendor_exists and vendor_target.stat().st_size == 0:
            state, detail = "empty-vendor", "vendor unit file is empty"
        elif admin_exists and vendor_exists:
            state, detail = "admin-override", "both vendor definition and administrator override exist"
        elif admin_exists:
            state, detail = "admin-only", "administrator unit exists without a vendor definition"
        elif vendor_exists:
            state, detail = "vendor-only", "vendor unit definition exists"
        else:
            state, detail = "missing", "no regular vendor or administrator unit file found"
        findings.append(UnitFileFinding(
            name,
            str(vendor_target) if vendor_exists else str(vendor),
            str(admin_target) if admin_exists else str(admin),
            state,
            detail,
        ))
    return SystemdRepairAssessment(str(base), True, tuple(findings))


def os_readlink_is_dev_null(path: Path) -> bool:
    """Recognize a conventional mask without following its /dev/null target."""
    try:
        return path.is_symlink() and path.readlink() == Path("/dev/null")
    except OSError:
        return False
