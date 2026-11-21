"""Recovery data selection cannot escape through unsafe paths."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.evolution.recovery import DataPreservationPlan, RecoveryBridge  # noqa: E402


class RecoveryDataPlanSafetyTests(unittest.TestCase):
    def test_rejects_root_relative_and_parent_traversal_paths(self) -> None:
        for path in ("/", "relative/home", "/home/../etc", "/home/user/../../etc"):
            with self.subTest(path=path):
                plan = DataPreservationPlan(include=(path,))
                self.assertTrue(any("unsafe included data path" in e for e in plan.validate()))

    def test_rejects_exclusion_that_covers_included_data(self) -> None:
        plan = DataPreservationPlan(
            include=("/home/user/documents",), exclude=("/home",),
        )
        self.assertTrue(any("hides an included" in e for e in plan.validate()))
        valid = DataPreservationPlan(
            include=("/home",), exclude=("/home/.cache",),
        )
        self.assertEqual(valid.validate(), [])

    def test_recovery_bridge_requires_well_formed_manifest_digest(self) -> None:
        bridge = RecoveryBridge(
            independent_toolchain=True, artifact_manifest_hash="manifest",
            supported_conditions=("offline-media",),
        )
        self.assertTrue(any("SHA-256" in e for e in bridge.validate()))


if __name__ == "__main__":
    unittest.main()
