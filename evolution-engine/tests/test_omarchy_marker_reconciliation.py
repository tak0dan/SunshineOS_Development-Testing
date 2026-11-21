"""Omarchy-inspired regression tests for user markers surviving root rollback."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.evolution.markers import validate_user_completion_markers  # noqa: E402


class OmarchyMarkerReconciliationTests(unittest.TestCase):
    def test_OMR_005_accepts_marker_only_when_journal_and_root_agree(self) -> None:
        digest = "a" * 64
        self.assertEqual(
            validate_user_completion_markers(
                {"root-transition": digest},
                {"root-transition": digest},
                {"root-transition": digest},
            ),
            [],
        )

    def test_OMR_006_rejects_marker_whose_root_effect_was_rolled_back(self) -> None:
        errors = validate_user_completion_markers(
            {"root-transition": "a" * 64},
            {"root-transition": "a" * 64},
            {"root-transition": "b" * 64},
        )
        self.assertTrue(any("current system output differs" in error for error in errors))

    def test_OMR_007_rejects_orphan_marker_without_completed_journal_record(self) -> None:
        errors = validate_user_completion_markers(
            {"root-transition": "a" * 64}, {}, {"root-transition": "a" * 64},
        )
        self.assertTrue(any("no matching completed journal operation" in error for error in errors))

    def test_OMR_008_missing_current_observation_fails_closed(self) -> None:
        digest = "a" * 64
        errors = validate_user_completion_markers(
            {"root-transition": digest}, {"root-transition": digest}, {},
        )
        self.assertTrue(any("was not observed" in error for error in errors))

    def test_OMR_009_malformed_hash_evidence_fails_closed(self) -> None:
        errors = validate_user_completion_markers(
            {"root-transition": "not-a-digest"},
            {"root-transition": "not-a-digest"},
            {"root-transition": "not-a-digest"},
        )
        self.assertEqual(len(errors), 1)
        self.assertIn("invalid SHA-256", errors[0])

    def test_OMR_010_malformed_observation_cannot_confirm_marker(self) -> None:
        digest = "a" * 64
        errors = validate_user_completion_markers(
            {"root-transition": digest},
            {"root-transition": digest},
            {"root-transition": "a" * 63},
        )
        self.assertEqual(len(errors), 1)
        self.assertIn("current system output has an invalid SHA-256", errors[0])


if __name__ == "__main__":
    unittest.main()
