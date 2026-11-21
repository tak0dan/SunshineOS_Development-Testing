"""SteamOS readonly/devmode repair assessment regression tests.

Test IDs: T_STEAMOS_REPAIR_001..008.
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.evolution.tools.steamos_repair import assess_steamos_repair  # noqa: E402


class SteamOSRepairAssessmentTests(unittest.TestCase):
    def setUp(self) -> None:
        self.observed = {
            "root_mount_readonly": False,
            "readonly_status": "disabled",
            "devmode_status": "enabled",
            "devmode_marker_present": True,
        }

    def test_T_STEAMOS_REPAIR_001_consistent_devmode_is_assessed(self) -> None:
        result = assess_steamos_repair(self.observed)
        self.assertEqual(result.state, "healthy")
        self.assertTrue(result.repairable)

    def test_T_STEAMOS_REPAIR_002_readonly_is_not_a_package_repair_target(self) -> None:
        self.observed.update(root_mount_readonly=True, readonly_status="enabled",
                             devmode_status="disabled", devmode_marker_present=False)
        result = assess_steamos_repair(self.observed)
        self.assertEqual(result.state, "readonly")
        self.assertFalse(result.repairable)

    def test_T_STEAMOS_REPAIR_003_readonly_command_mount_conflict_blocks(self) -> None:
        self.observed["root_mount_readonly"] = True
        result = assess_steamos_repair(self.observed)
        self.assertEqual(result.state, "contradictory")
        self.assertFalse(result.repairable)
        self.assertIn("root mount is read-only", result.blockers[0])

    def test_T_STEAMOS_REPAIR_004_disabled_devmode_with_marker_is_partial(self) -> None:
        self.observed.update(readonly_status="enabled", devmode_status="disabled")
        result = assess_steamos_repair(self.observed)
        self.assertEqual(result.state, "partial_devmode")
        self.assertFalse(result.repairable)

    def test_T_STEAMOS_REPAIR_005_enabled_devmode_without_marker_blocks(self) -> None:
        self.observed["devmode_marker_present"] = False
        result = assess_steamos_repair(self.observed)
        self.assertEqual(result.state, "contradictory")

    def test_T_STEAMOS_REPAIR_006_incomplete_or_wrongly_typed_evidence_blocks(self) -> None:
        del self.observed["root_mount_readonly"]
        self.observed["devmode_marker_present"] = 1
        result = assess_steamos_repair(self.observed)
        self.assertEqual(result.state, "unknown")
        self.assertFalse(result.repairable)
        self.assertEqual(len(result.blockers), 2)

    def test_T_STEAMOS_REPAIR_007_unknown_status_fails_closed(self) -> None:
        self.observed["readonly_status"] = "maybe"
        result = assess_steamos_repair(self.observed)
        self.assertEqual(result.state, "unknown")
        self.assertFalse(result.repairable)
        self.assertIn("no rootfs or slot mutation", result.to_dict()["policy"])

    def test_T_STEAMOS_REPAIR_008_unclassified_writable_state_blocks(self) -> None:
        self.observed.update(root_mount_readonly=False, readonly_status="enabled",
                             devmode_status="disabled", devmode_marker_present=False)
        result = assess_steamos_repair(self.observed)
        self.assertEqual(result.state, "contradictory")
        self.assertFalse(result.repairable)


if __name__ == "__main__":
    unittest.main()
