"""Automatic migration planning inside the ordinary upgrade flow."""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.evolution.baseline import BASELINE_ID  # noqa: E402
from src.evolution.recovery import BRIDGE_ID, RECOVERY_BASELINE_ID  # noqa: E402
from src.evolution.scheme import Scheme, load_scheme  # noqa: E402
from src.evolution.updater import EvolutionUpdater, plan_automatic_migration  # noqa: E402


def migration_scheme() -> Scheme:
    """Scheme whose source release is the Arch 2015 epoch and target is 2026."""
    return Scheme.from_dict({
        "format_version": 1,
        "current": "0.9",
        "baseline_epoch": "arch-2015-baseline-01",
        "milestones": [
            {
                "id": "arch-2015",
                "version": "0",
                "label": "Arch 2015 source",
                "target_release": "arch-2015",
                "rollback": "none",
            },
            {
                "id": "sunshine-2026",
                "version": "0.9",
                "label": "SunshineOS 2026 target",
                "predecessor": "0",
                "target_release": "sunshine-2026.1",
                "rollback": "checkpoint",
            },
        ],
    })


class AutomaticUpgradeMigrationTests(unittest.TestCase):
    def test_same_version_upgrade_has_no_migration_step(self) -> None:
        with tempfile.TemporaryDirectory(prefix="sunshine-upgrade-same-") as tmp:
            updater = EvolutionUpdater(
                load_scheme(), tmp,
                apply_fn=lambda: (True, "not called"),
                verify_fn=lambda: (True, "not called"),
            )
            report = updater.upgrade("0.9", "0.9", dry_run=True)
        self.assertTrue(report.ok)
        self.assertFalse(report.migration_required)
        self.assertEqual(report.migration_lineage, ())
        self.assertEqual(report.recovery_inputs, {})
        self.assertFalse(any(s["phase"] == "AutomaticMigration" for s in report.steps))
        self.assertEqual(report.chain, ())

    def test_major_release_records_b1_bridge_b0_target_lineage(self) -> None:
        plan = plan_automatic_migration(RECOVERY_BASELINE_ID, "E040")
        self.assertTrue(plan.required)
        self.assertEqual(
            plan.lineage, (RECOVERY_BASELINE_ID, BRIDGE_ID, BASELINE_ID, "E040"),
        )
        self.assertEqual(plan.update_scope, ("base", "kernel", "packages"))
        payload = plan.to_dict()
        self.assertFalse(payload["mutation_authorized"])
        self.assertEqual(payload["commands"], [])
        self.assertEqual(payload["lock_deletion"], "never")

        with tempfile.TemporaryDirectory(prefix="sunshine-upgrade-major-") as tmp:
            report = EvolutionUpdater(load_scheme(), tmp).upgrade(
                RECOVERY_BASELINE_ID, "E040", dry_run=True,
            )
        self.assertTrue(report.migration_required)
        self.assertEqual(
            report.migration_lineage,
            (RECOVERY_BASELINE_ID, BRIDGE_ID, BASELINE_ID, "E040"),
        )
        step = next(s for s in report.steps if s["phase"] == "AutomaticMigration")
        self.assertEqual(step["lineage"][1], BRIDGE_ID)
        self.assertFalse(step["mutation_authorized"])

    def test_broken_upgrade_recovery_uses_b1_and_b0_inputs(self) -> None:
        with tempfile.TemporaryDirectory(prefix="sunshine-upgrade-broken-") as tmp:
            updater = EvolutionUpdater(
                migration_scheme(), tmp,
                apply_fn=lambda: (False, "upgrade broke"),
                verify_fn=lambda: (True, "unused"),
                checkpoint_fn=lambda: "checkpoint-ref",
                restore_fn=lambda ref: (True, f"restored {ref}"),
            )
            report = updater.upgrade("0", "0.9")
        self.assertFalse(report.ok)
        self.assertTrue(report.migration_required)
        self.assertEqual(report.recovery_inputs["base"], RECOVERY_BASELINE_ID)
        self.assertEqual(report.recovery_inputs["merge_with"], BASELINE_ID)
        self.assertEqual(report.recovery_inputs["current_state"]["chain"], ["0.9"])
        self.assertIn("evolutionary upgrade steps", report.recovery_inputs["continue_with"])
        self.assertTrue(any(s["phase"] == "RecoveryPlan" for s in report.steps))
        self.assertEqual(report.recovery_inputs["commands"], [])

    def test_plan_mode_never_mutates(self) -> None:
        def forbidden(*_args, **_kwargs):
            raise AssertionError("plan mode must not execute mutating callbacks")

        with tempfile.TemporaryDirectory(prefix="sunshine-upgrade-plan-") as tmp:
            updater = EvolutionUpdater(
                migration_scheme(), tmp,
                apply_fn=forbidden,
                verify_fn=forbidden,
                checkpoint_fn=forbidden,
                restore_fn=forbidden,
            )
            report = updater.upgrade("0", "0.9", dry_run=True)
            self.assertEqual(list(Path(tmp).iterdir()), [])
        self.assertTrue(report.ok)
        self.assertTrue(report.dry_run)
        self.assertTrue(report.migration_required)
        self.assertFalse(report.migration_plan["mutation_authorized"])
        self.assertFalse(any(s["phase"] == "RecoveryPlan" for s in report.steps))


if __name__ == "__main__":
    unittest.main()
