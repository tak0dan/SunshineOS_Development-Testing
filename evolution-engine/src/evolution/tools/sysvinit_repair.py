"""Fail-closed repair assessment for historical Arch SysV services.

This module diagnoses service declaration/script mismatches. It deliberately
does not execute rc scripts or manufacture replacement scripts: old SysV
service semantics require an independently qualified recovery adapter.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
from typing import Iterable

from ...discovery.sysvinit import SysVServiceInventory

_SERVICE_ID = re.compile(r"^[A-Za-z0-9_.+-]+$")


@dataclass(frozen=True)
class SysVRepairAssessment:
    """Read-only findings for required services on a rooted legacy system."""

    root: str
    checked: tuple[str, ...]
    missing_scripts: tuple[str, ...]
    blockers: tuple[str, ...]
    commands: tuple[tuple[str, ...], ...] = ()

    @property
    def repairable(self) -> bool:
        return not self.blockers and not self.missing_scripts

    def to_dict(self) -> dict[str, object]:
        return {
            "root": self.root,
            "checked": list(self.checked),
            "missing_scripts": list(self.missing_scripts),
            "blockers": list(self.blockers),
            "commands": [list(command) for command in self.commands],
            "repairable": self.repairable,
        }


def assess_sysv_services(
    inventory: SysVServiceInventory,
    root: str | Path,
    required_services: Iterable[str] = (),
) -> SysVRepairAssessment:
    """Check declared/required services against ``root/etc/rc.d``.

    The caller must supply a complete parser result. A blocked or incomplete
    inventory yields no path probes and no proposed commands. Only regular
    files beneath the resolved root are accepted as script evidence.
    """
    base = Path(root).resolve()
    if not inventory.complete:
        return SysVRepairAssessment(str(base), (), (), ("SysV inventory is incomplete",))

    required = tuple(required_services)
    names = tuple(dict.fromkeys((*inventory.enabled, *required)))
    invalid = tuple(name for name in names if not _SERVICE_ID.fullmatch(name))
    if invalid:
        return SysVRepairAssessment(
            str(base), (), (), ("invalid service identifiers: " + ", ".join(invalid),)
        )

    checked: list[str] = []
    missing: list[str] = []
    service_dir = (base / "etc" / "rc.d").resolve()
    try:
        service_dir.relative_to(base)
    except ValueError:
        return SysVRepairAssessment(str(base), (), (), ("service directory escapes root",))

    for name in names:
        candidate = (service_dir / name).resolve()
        try:
            candidate.relative_to(service_dir)
        except ValueError:
            return SysVRepairAssessment(str(base), tuple(checked), tuple(missing),
                                        (f"service path escapes root: {name}",))
        checked.append(name)
        if not candidate.is_file():
            missing.append(name)
    return SysVRepairAssessment(str(base), tuple(checked), tuple(missing), ())
