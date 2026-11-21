"""SteamOS-inspired A/B activation gate regression tests.

Test IDs STEAMOS_ACT_001..007.
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.evolution.inventory import Inventory  # noqa: E402
from src.evolution.slot_activation import validate_slot_activation  # noqa: E402
from src.evolution.staging import assess_staging  # noqa: E402


class SteamOsSlotActivationTests(unittest.TestCase):
    def setUp(self) -> None:
        inventory = Inventory(boot={
            "active_slot": "A", "inactive_slot": "B",
            "inactive_slot_available": True, "slot_switch_supported": True,
        })
        self.plan = assess_staging(inventory, mode="evolution")
        self.evidence = {
            "candidate_slot": "B", "candidate_os": "SunshineOS",
            "staged_validation_passed": True, "previous_slot_bootable": True,
        }

    def test_STEAMOS_ACT_001_qualified_candidate_can_activate(self) -> None:
        self.assertIsNone(validate_slot_activation(
            self.plan, self.evidence, expected_os="SunshineOS"))

    def test_STEAMOS_ACT_002_unexpected_os_in_inactive_slot_blocks(self) -> None:
        self.evidence["candidate_os"] = "Windows"
        with self.assertRaisesRegex(ValueError, "does not match the target"):
            validate_slot_activation(self.plan, self.evidence, expected_os="SunshineOS")

    def test_STEAMOS_ACT_003_missing_identity_blocks(self) -> None:
        self.evidence["candidate_os"] = ""
        with self.assertRaisesRegex(ValueError, "does not match the target"):
            validate_slot_activation(self.plan, self.evidence, expected_os="SunshineOS")

    def test_STEAMOS_ACT_004_unvalidated_candidate_blocks(self) -> None:
        self.evidence["staged_validation_passed"] = False
        with self.assertRaisesRegex(ValueError, "has not passed"):
            validate_slot_activation(self.plan, self.evidence, expected_os="SunshineOS")

    def test_STEAMOS_ACT_005_unbootable_previous_slot_blocks(self) -> None:
        self.evidence["previous_slot_bootable"] = False
        with self.assertRaisesRegex(ValueError, "not confirmed bootable"):
            validate_slot_activation(self.plan, self.evidence, expected_os="SunshineOS")

    def test_STEAMOS_ACT_006_wrong_candidate_slot_blocks(self) -> None:
        self.evidence["candidate_slot"] = "C"
        with self.assertRaisesRegex(ValueError, "does not match the planned"):
            validate_slot_activation(self.plan, self.evidence, expected_os="SunshineOS")

    def test_STEAMOS_ACT_007_non_ab_plan_blocks(self) -> None:
        with self.assertRaisesRegex(ValueError, "requires an A/B"):
            validate_slot_activation(assess_staging(Inventory()), self.evidence,
                                     expected_os="SunshineOS")


if __name__ == "__main__":
    unittest.main()
