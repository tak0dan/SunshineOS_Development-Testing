"""Regression coverage for the SteamOS-inspired workflow activation boundary.

Test IDs: STEAMOS_FLOW_001..004.
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.evolution.inventory import Inventory  # noqa: E402
from src.evolution.staging import PHASES, WorkflowRun, assess_staging  # noqa: E402
from src.evolution.steamos_workflow import validate_steamos_workflow_activation  # noqa: E402


class SteamOSWorkflowActivationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.assessment = assess_staging(Inventory(boot={
            "active_slot": "A", "inactive_slot": "B",
            "inactive_slot_available": True, "slot_switch_supported": True,
        }), mode="evolution")
        self.evidence = {
            "candidate_slot": "B", "candidate_os": "SunshineOS",
            "staged_validation_passed": True, "previous_slot_bootable": True,
        }

    def workflow_at(self, phase: str) -> WorkflowRun:
        completed = list(PHASES[:PHASES.index(phase)])
        return WorkflowRun("ab_slot", completed=completed, current=phase)

    def test_STEAMOS_FLOW_001_only_validate_staged_may_enter_activation(self) -> None:
        validate_steamos_workflow_activation(
            self.workflow_at("Activate"), self.assessment, self.evidence,
            expected_os="SunshineOS")
        for phase in ("Build", "ValidateStaged", "BootValidate", "Discover"):
            with self.subTest(phase=phase), self.assertRaisesRegex(ValueError, "staged validation"):
                validate_steamos_workflow_activation(
                    self.workflow_at(phase), self.assessment, self.evidence,
                    expected_os="SunshineOS")

    def test_STEAMOS_FLOW_002_aborted_workflow_cannot_activate(self) -> None:
        workflow = self.workflow_at("Activate")
        workflow.abort("Activate")
        with self.assertRaisesRegex(ValueError, "aborted workflow"):
            validate_steamos_workflow_activation(
                workflow, self.assessment, self.evidence, expected_os="SunshineOS")

    def test_STEAMOS_FLOW_003_assessment_must_match_workflow(self) -> None:
        with self.assertRaisesRegex(ValueError, "does not match"):
            validate_steamos_workflow_activation(
                self.workflow_at("Activate"), assess_staging(Inventory()), self.evidence,
                expected_os="SunshineOS")

    def test_STEAMOS_FLOW_004_fresh_candidate_gate_still_blocks_bad_evidence(self) -> None:
        evidence = {**self.evidence, "previous_slot_bootable": False}
        with self.assertRaisesRegex(ValueError, "not confirmed bootable"):
            validate_steamos_workflow_activation(
                self.workflow_at("Activate"), self.assessment, evidence,
                expected_os="SunshineOS")


if __name__ == "__main__":
    unittest.main()
