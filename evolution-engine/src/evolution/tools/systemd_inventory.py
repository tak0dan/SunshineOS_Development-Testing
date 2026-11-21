"""Fail-closed parsing and assessment of systemd unit-file inventory.

This is intentionally read-only. ``systemctl list-unit-files`` is the source of
the observed state; failed collection and malformed output remain unknown and
must never be interpreted as an absent unit.
"""
from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Iterable, Mapping

# Keep this aligned with systemd's unit types.  ``busname`` is still emitted by
# older systems and ``snapshot`` can occur in inventories from legacy hosts;
# rejecting either would make an otherwise complete observation look corrupt.
UNIT_NAME = re.compile(r"^[A-Za-z0-9@_.:-]+\.(service|socket|target|timer|path|mount|automount|swap|slice|scope|device|busname|snapshot)$")
KNOWN_STATES = frozenset({"enabled", "enabled-runtime", "linked", "linked-runtime", "alias", "static", "indirect", "disabled", "masked", "masked-runtime", "generated", "transient", "bad"})


@dataclass(frozen=True)
class UnitInventory:
    units: Mapping[str, str]
    complete: bool
    errors: tuple[str, ...] = ()


@dataclass(frozen=True)
class UnitFinding:
    unit: str
    observed: str
    desired: str
    action: str


def parse_unit_file_inventory(stdout: str, *, command_succeeded: bool) -> UnitInventory:
    """Parse ``systemctl list-unit-files --no-legend`` output conservatively."""
    if not command_succeeded:
        return UnitInventory({}, False, ("systemctl list-unit-files failed",))
    units: dict[str, str] = {}
    errors: list[str] = []
    for number, line in enumerate(stdout.splitlines(), 1):
        fields = line.split()
        if not fields:
            continue
        if len(fields) < 2:
            errors.append(f"line {number}: expected unit and state")
            continue
        name, state = fields[:2]
        if not UNIT_NAME.fullmatch(name):
            errors.append(f"line {number}: invalid unit name")
            continue
        if state not in KNOWN_STATES:
            errors.append(f"line {number}: unknown unit-file state {state!r}")
            continue
        if name in units:
            errors.append(f"line {number}: duplicate unit {name}")
            continue
        units[name] = state
    return UnitInventory(units, not errors, tuple(errors))


def assess_unit_inventory(
    inventory: UnitInventory, desired: Mapping[str, str]
) -> tuple[UnitFinding, ...]:
    """Compare desired enabled/disabled/present/absent states without mutation."""
    allowed = {"enabled", "disabled", "present", "absent"}
    findings: list[UnitFinding] = []
    for unit, target in sorted(desired.items()):
        if not UNIT_NAME.fullmatch(unit):
            raise ValueError(f"invalid systemd unit name {unit!r}")
        if target not in allowed:
            raise ValueError(f"invalid desired unit state {target!r}")
        if not inventory.complete:
            observed, action = "unknown", "block"
        else:
            observed = inventory.units.get(unit, "absent")
            if observed == "bad":
                # systemd reports this unit-file state when it cannot load or
                # parse the unit. Do not convert that observation into a
                # service command proposal; repair/reconciliation must resolve
                # the broken definition first.
                action = "block"
            elif observed in {"masked", "masked-runtime"} and target in {"enabled", "present"}:
                action = "block"
            elif target in {"enabled", "present"} and observed == "absent":
                action = "review-install"
            elif target == "enabled" and observed not in {"enabled", "enabled-runtime", "linked", "linked-runtime", "alias"}:
                action = "review-enable"
            elif target == "disabled" and observed in {"enabled", "enabled-runtime", "linked", "linked-runtime"}:
                action = "review-disable"
            elif target == "absent" and observed != "absent":
                action = "review-remove"
            else:
                action = "satisfied"
        findings.append(UnitFinding(unit, observed, target, action))
    return tuple(findings)
