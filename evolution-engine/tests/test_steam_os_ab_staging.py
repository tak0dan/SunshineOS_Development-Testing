"""SteamOS-inspired A/B staging is selected only from observed capabilities."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.evolution.inventory import Inventory  # noqa: E402
from src.evolution.staging import assess_staging  # noqa: E402


class SteamOsABStagingTests(unittest.TestCase):
    def test_STEAMOS_AB_001_observed_slots_select_atomic_staging(self) -> None:
        inventory = Inventory(
            storage={"filesystem": "btrfs"},
            boot={"active_slot": "A", "inactive_slot_available": True,
                  "slot_switch_supported": True},
        )
        plan = assess_staging(inventory, mode="evolution")
        self.assertEqual(plan.strategy, "ab_slot")
        self.assertEqual(plan.workspace, "inactive-slot")
        self.assertTrue(plan.can_retain_previous)
        self.assertIn("inactive root slot and boot switch capability observed", plan.reasons)

    def test_STEAMOS_AB_002_partial_or_unobserved_slots_fail_closed(self) -> None:
        cases = (
            {"inactive_slot_available": True},
            {"slot_switch_supported": True},
            {"inactive_slot_available": "true", "slot_switch_supported": True},
        )
        for boot in cases:
            with self.subTest(boot=boot):
                inventory = Inventory(boot=boot)
                self.assertEqual(assess_staging(inventory).strategy, "in_place")
                with self.assertRaisesRegex(ValueError, "A/B slot staging requires"):
                    assess_staging(inventory, forced="ab_slot")

    def test_STEAMOS_AB_003_recovery_takes_precedence_over_slot_activation(self) -> None:
        inventory = Inventory(
            boot={"inactive_slot_available": True, "slot_switch_supported": True,
                  "recovery_environment": True},
        )
        self.assertEqual(
            assess_staging(inventory, recovery_needed=True).strategy,
            "recovery_reconstruction",
        )

    def test_STEAMOS_AB_004_forced_staged_root_requires_capability(self) -> None:
        with self.assertRaisesRegex(ValueError, "staged-root strategy is not available"):
            assess_staging(Inventory(), forced="staged_root")


if __name__ == "__main__":
    unittest.main()
