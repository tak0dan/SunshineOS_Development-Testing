"""Regression coverage for root-scoped systemd unit-file assessment."""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ENGINE_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ENGINE_ROOT))

from src.evolution.tools.systemd_repair import assess_systemd_unit_files  # noqa: E402


class SystemdRepairAssessmentTests(unittest.TestCase):
    def test_T_ARCH2026_SYSTEMD_REPAIR_001_catalogues_vendor_and_override(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            vendor = root / "usr/lib/systemd/system/sshd.service"
            admin = root / "etc/systemd/system/sshd.service"
            vendor.parent.mkdir(parents=True)
            admin.parent.mkdir(parents=True)
            vendor.write_text("[Service]\nExecStart=/usr/bin/sshd\n", encoding="utf-8")
            admin.write_text("[Service]\nRestart=on-failure\n", encoding="utf-8")
            result = assess_systemd_unit_files(root, ["sshd.service"])
        self.assertTrue(result.complete)
        self.assertEqual(result.findings[0].state, "admin-override")
        self.assertEqual(result.commands, ())

    def test_T_ARCH2026_SYSTEMD_REPAIR_002_masks_are_reported_without_following(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            admin = root / "etc/systemd/system/blocked.service"
            admin.parent.mkdir(parents=True)
            admin.symlink_to("/dev/null")
            result = assess_systemd_unit_files(root, ["blocked.service"])
        self.assertEqual(result.findings[0].state, "masked")

    def test_T_ARCH2026_SYSTEMD_REPAIR_003_external_symlink_blocks_assessment(self):
        with tempfile.TemporaryDirectory() as temporary, tempfile.TemporaryDirectory() as outside:
            root = Path(temporary)
            vendor = root / "usr/lib/systemd/system/sshd.service"
            vendor.parent.mkdir(parents=True)
            vendor.symlink_to(Path(outside) / "sshd.service")
            result = assess_systemd_unit_files(root, ["sshd.service"])
        self.assertFalse(result.complete)
        self.assertIn("escapes observed root", result.blockers[0])
        self.assertEqual(result.commands, ())

    def test_T_ARCH2026_SYSTEMD_REPAIR_004_empty_and_missing_files_are_distinct(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            empty = root / "usr/lib/systemd/system/empty.service"
            empty.parent.mkdir(parents=True)
            empty.touch()
            result = assess_systemd_unit_files(root, ["empty.service", "gone.service"])
        self.assertEqual([item.state for item in result.findings], ["empty-vendor", "missing"])

    def test_T_ARCH2026_SYSTEMD_REPAIR_005_invalid_unit_name_fails_closed(self):
        with tempfile.TemporaryDirectory() as temporary:
            result = assess_systemd_unit_files(temporary, ["../../outside.service"])
        self.assertFalse(result.complete)
        self.assertEqual(result.findings, ())
        self.assertIn("invalid systemd unit", result.blockers[0])


if __name__ == "__main__":
    unittest.main()
