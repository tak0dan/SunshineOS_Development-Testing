"""SteamOS-inspired A/B planning requires a named, switchable inactive slot."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.evolution.inventory import Inventory  # noqa: E402
from src.evolution.staging import WorkflowRun, assess_staging  # noqa: E402


class SteamOsABStagingTests(unittest.TestCase):
    def test_STEAMOS_AB_001_plan_identifies_candidate_and_retained_slots(self) -> None:
        inv = Inventory(boot={
            "active_slot": "A", "inactive_slot": "B",
            "inactive_slot_available": True, "slot_switch_supported": True,
        })
        plan = assess_staging(inv, mode="evolution")
        self.assertEqual(plan.strategy, "ab_slot")
        self.assertEqual(plan.workspace, "inactive-slot")
        self.assertEqual(plan.active_slot, "A")
        self.assertEqual(plan.candidate_slot, "B")
        self.assertTrue(plan.can_retain_previous)
        self.assertEqual(plan.to_dict()["candidate_slot"], "B")
        forced = assess_staging(inv, forced="ab_slot")
        self.assertEqual(forced.workspace, "inactive-slot")
        self.assertEqual(forced.candidate_slot, "B")

    def test_STEAMOS_AB_002_incomplete_or_ambiguous_evidence_fails_closed(self) -> None:
        cases = (
            {"inactive_slot_available": True, "slot_switch_supported": True},
            {"active_slot": "A", "inactive_slot": "B", "slot_switch_supported": True},
            {"active_slot": "A", "inactive_slot": "B", "inactive_slot_available": True},
            {"active_slot": "A", "inactive_slot": "A", "inactive_slot_available": True,
             "slot_switch_supported": True},
            {"active_slot": "A", "inactive_slot": " ", "inactive_slot_available": True,
             "slot_switch_supported": True},
        )
        for boot in cases:
            with self.subTest(boot=boot):
                inv = Inventory(boot=boot)
                self.assertEqual(assess_staging(inv).strategy, "in_place")
                with self.assertRaisesRegex(ValueError, "distinct observed active and inactive"):
                    assess_staging(inv, forced="ab_slot")

    def test_STEAMOS_AB_003_recovery_reconstruction_precedes_ab_activation(self) -> None:
        inv = Inventory(boot={
            "active_slot": "A", "inactive_slot": "B",
            "inactive_slot_available": True, "slot_switch_supported": True,
            "recovery_environment": True,
        })
        self.assertEqual(assess_staging(inv, recovery_needed=True).strategy,
                         "recovery_reconstruction")

    def test_STEAMOS_AB_004_forced_staged_root_requires_capability(self) -> None:
        with self.assertRaisesRegex(ValueError, "staged-root strategy is not available"):
            assess_staging(Inventory(), forced="staged_root")

    def test_STEAMOS_AB_005_activation_requires_validated_staged_root(self) -> None:
        with self.assertRaisesRegex(ValueError, "unknown migration strategy"):
            WorkflowRun("unverified-slot")

        workflow = WorkflowRun("ab_slot")
        for phase in ("Discover", "Qualify", "Resolve", "Plan", "Review", "Protect",
                      "Prepare", "Reconcile", "Build"):
            workflow.advance(phase)
        workflow.abort("ValidateStaged")
        with self.assertRaisesRegex(ValueError, "aborted workflow"):
            workflow.advance("ValidateStaged")
        self.assertNotIn("Activate", workflow.completed)

    def test_STEAMOS_AB_006_forged_history_cannot_skip_staged_validation(self) -> None:
        with self.assertRaisesRegex(ValueError, "valid phase prefix"):
            WorkflowRun("ab_slot", completed=["Discover", "Build"])
        with self.assertRaisesRegex(ValueError, "current phase"):
            WorkflowRun("ab_slot", completed=["Discover"], current="Activate")

        workflow = WorkflowRun("ab_slot")
        with self.assertRaisesRegex(ValueError, "only abort at current phase"):
            workflow.abort("Activate")
        self.assertEqual(workflow.current, "Discover")


if __name__ == "__main__":
    unittest.main()
