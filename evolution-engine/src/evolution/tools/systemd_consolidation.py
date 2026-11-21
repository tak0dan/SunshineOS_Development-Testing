"""Read-only consolidation of systemd inventory, policy and unit-file evidence.

This is the hand-off boundary for service migration and repair assessment. It
joins independently collected evidence without treating filesystem presence as
proof that systemd loaded or started a unit, and never emits commands.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

from .systemd_inventory import UnitFinding, parse_unit_file_inventory, assess_unit_inventory
from .systemd_repair import SystemdRepairAssessment, assess_systemd_unit_files


@dataclass(frozen=True)
class SystemdConsolidation:
    inventory_complete: bool
    findings: tuple[UnitFinding, ...]
    unit_files: SystemdRepairAssessment
    blockers: tuple[str, ...]

    @property
    def complete(self) -> bool:
        return self.inventory_complete and self.unit_files.complete and not self.blockers

    def to_dict(self) -> dict[str, object]:
        return {
            "complete": self.complete,
            "inventory_complete": self.inventory_complete,
            "findings": [
                {"unit": item.unit, "observed": item.observed,
                 "desired": item.desired, "action": item.action}
                for item in self.findings
            ],
            "unit_files": self.unit_files.to_dict(),
            "blockers": list(self.blockers),
            "commands": [],
        }


def consolidate_systemd_evidence(
    root: str | Path,
    unit_file_output: str,
    *,
    command_succeeded: bool,
    desired: Mapping[str, str],
) -> SystemdConsolidation:
    """Join systemctl unit-file inventory with filesystem and desired-state evidence.

    Every requested unit is inspected in the rooted vendor/admin layers. A
    failed or malformed systemctl observation remains a blocker; successful
    filesystem inspection cannot downgrade that uncertainty.
    """
    inventory = parse_unit_file_inventory(
        unit_file_output, command_succeeded=command_succeeded
    )
    findings = assess_unit_inventory(inventory, desired)
    file_assessment = assess_systemd_unit_files(root, desired.keys())
    blockers = [
        f"systemd inventory: {error}" for error in inventory.errors
    ]
    blockers.extend(
        f"{item.unit}: desired {item.desired}, observed {item.observed} requires {item.action}"
        for item in findings if item.action == "block"
    )
    blockers.extend(file_assessment.blockers)
    return SystemdConsolidation(
        inventory.complete, findings, file_assessment, tuple(blockers)
    )
