"""Omarchy-informed checks for the final update completion gate."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.evolution.update_evidence import validate_update_completion_evidence  # noqa: E402


class OmarchyUpdateCompletionTests(unittest.TestCase):
    def test_OMR_011_completion_requires_ordered_package_migration_boot_evidence(self) -> None:
        self.assertEqual(
            validate_update_completion_evidence((
                "package_transaction", "migrations", "aur_packages", "boot_verification",
            )),
            [],
        )

    def test_OMR_012_failed_boot_verification_blocks_completion(self) -> None:
        errors = validate_update_completion_evidence(
            ("package_transaction", "migrations", "boot_verification"),
            ("boot_verification",),
        )
        self.assertTrue(any("boot_verification" in error and "failed" in error for error in errors))

    def test_OMR_013_missing_boot_evidence_blocks_completion(self) -> None:
        errors = validate_update_completion_evidence(("package_transaction", "migrations"))
        self.assertIn("required update stage 'boot_verification' was not completed", errors)

    def test_OMR_014_out_of_order_or_duplicated_stage_evidence_blocks_completion(self) -> None:
        errors = validate_update_completion_evidence((
            "migrations", "package_transaction", "package_transaction", "boot_verification",
        ))
        self.assertTrue(any("out of order" in error for error in errors))
        self.assertTrue(any("more than once" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
