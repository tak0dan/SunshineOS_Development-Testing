"""Regression coverage for stale completion markers after snapshot rollback."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.evolution.journal_state import MigrationJournal, OperationRecord  # noqa: E402
from src.evolution.research_catalog import ResearchCatalog  # noqa: E402


class OmarchyRecoveryConsistencyTests(unittest.TestCase):
    def test_OMR_004_catalogued_omarchy_hazards_keep_enforcement_controls(self) -> None:
        catalog = ResearchCatalog.load(
            ROOT / "fixtures/research/omarchy-update-recovery-wave1.json"
        )
        by_id = {source.source_id: source for source in catalog.sources}
        required_controls = {
            "migration-runner": ("per user", "observed system postconditions"),
            "pacman-guard": ("bypasses", "full planned transaction"),
            "snapshots-manual": ("re-probe", "completion marker"),
            "updates-manual": ("transaction plans", "configuration ownership"),
            "update-process": ("separately observed state", "notifications"),
        }
        self.assertEqual(catalog.validate(), [])
        self.assertEqual(len(by_id), len(catalog.sources))
        for source_id, phrases in required_controls.items():
            with self.subTest(source_id=source_id):
                self.assertIn(source_id, by_id)
                adoption = by_id[source_id].adoption.casefold()
                for phrase in phrases:
                    self.assertIn(phrase, adoption)

    def setUp(self) -> None:
        self.journal = MigrationJournal("snapshot-rollback")
        self.journal.add_operation(OperationRecord("root-transition"))
        self.journal.set_operation(
            "root-transition", "Completed", result="applied", output_hash="a" * 64,
        )

    def test_OMR_001_completed_operation_requires_matching_observed_output(self) -> None:
        self.assertEqual(
            self.journal.verify_completed_outputs({"root-transition": "a" * 64}), [],
        )
        self.assertTrue(any(
            "differs from completed record" in error
            for error in self.journal.verify_completed_outputs({"root-transition": "b" * 64})
        ))

    def test_OMR_002_missing_observation_or_recorded_hash_fails_closed(self) -> None:
        self.assertTrue(any(
            "was not observed" in error
            for error in self.journal.verify_completed_outputs({})
        ))
        self.journal.operations["root-transition"].output_hash = ""
        self.assertTrue(any(
            "no recorded hash" in error
            for error in self.journal.verify_completed_outputs({"root-transition": "a" * 64})
        ))


if __name__ == "__main__":
    unittest.main()
