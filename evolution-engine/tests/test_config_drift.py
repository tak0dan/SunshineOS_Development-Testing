"""Regression coverage for fail-closed pacnew/pacsave assessment."""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.evolution.tools.config_drift import assess_config_drift  # noqa: E402


class ConfigDriftTests(unittest.TestCase):
    def test_lists_pacnew_pacsave_and_flags_critical_files(self) -> None:
        """T-EOS-REPAIR-001: candidates are classified without modification."""
        with tempfile.TemporaryDirectory() as tmp:
            etc = Path(tmp) / "etc"
            (etc / "pacman.conf").parent.mkdir(parents=True)
            (etc / "pacman.conf").write_text("admin config\n")
            (etc / "pacman.conf.pacnew").write_text("new config\n")
            (etc / "fstab.pacnew").write_text("new mount config\n")
            (etc / "old.conf.pacsave").write_text("saved config\n")

            report = assess_config_drift(tmp)

            self.assertTrue(report.complete)
            self.assertEqual(
                [(i.kind, i.disposition) for i in report.items],
                [("pacnew", "manual-review-critical"),
                 ("pacsave", "review-before-restore"),
                 ("pacnew", "compare-with-existing")],
            )
            self.assertEqual((etc / "pacman.conf").read_text(), "admin config\n")

    def test_absent_config_root_is_incomplete_not_clean(self) -> None:
        """T-EOS-REPAIR-002: missing evidence cannot report healthy."""
        with tempfile.TemporaryDirectory() as tmp:
            report = assess_config_drift(tmp)
        self.assertFalse(report.complete)
        self.assertEqual(report.items, ())

    def test_symlink_candidates_and_symlink_directories_are_not_followed(self) -> None:
        """T-EOS-REPAIR-003: do not follow candidates outside the root."""
        with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as outside:
            etc = Path(tmp) / "etc"
            etc.mkdir()
            external = Path(outside) / "outside.pacnew"
            external.write_text("external\n")
            (etc / "link.pacnew").symlink_to(external)
            (etc / "linked-dir").symlink_to(Path(outside), target_is_directory=True)
            report = assess_config_drift(tmp)
        self.assertTrue(report.complete)
        self.assertEqual(report.items, ())


if __name__ == "__main__":
    unittest.main()
