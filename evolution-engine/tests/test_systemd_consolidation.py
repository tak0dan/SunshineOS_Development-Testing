"""Regression tests for the consolidated, read-only systemd evidence boundary."""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ENGINE_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ENGINE_ROOT))

from src.evolution.tools.systemd_consolidation import consolidate_systemd_evidence  # noqa: E402


class SystemdConsolidationTests(unittest.TestCase):
    def test_T_ARCH2026_SYSTEMD_CONSOLIDATION_001_joins_policy_and_file_evidence(self):
        with tempfile.TemporaryDirectory() as temporary:
            vendor = Path(temporary) / "usr/lib/systemd/system/sshd.service"
            vendor.parent.mkdir(parents=True)
            vendor.write_text("[Service]\n", encoding="utf-8")
            result = consolidate_systemd_evidence(
                temporary, "sshd.service enabled enabled\n",
                command_succeeded=True, desired={"sshd.service": "enabled"},
            )
        self.assertTrue(result.complete)
        self.assertEqual(result.findings[0].action, "satisfied")
        self.assertEqual(result.unit_files.findings[0].state, "vendor-only")
        self.assertEqual(result.to_dict()["commands"], [])

    def test_T_ARCH2026_SYSTEMD_CONSOLIDATION_002_failed_probe_stays_blocked(self):
        with tempfile.TemporaryDirectory() as temporary:
            vendor = Path(temporary) / "usr/lib/systemd/system/sshd.service"
            vendor.parent.mkdir(parents=True)
            vendor.touch()
            result = consolidate_systemd_evidence(
                temporary, "", command_succeeded=False,
                desired={"sshd.service": "enabled"},
            )
        self.assertFalse(result.complete)
        self.assertEqual(result.findings[0].action, "block")
        self.assertTrue(any("inventory" in blocker for blocker in result.blockers))

    def test_T_ARCH2026_SYSTEMD_CONSOLIDATION_003_mask_is_preserved_across_layers(self):
        with tempfile.TemporaryDirectory() as temporary:
            admin = Path(temporary) / "etc/systemd/system/sshd.service"
            admin.parent.mkdir(parents=True)
            admin.symlink_to("/dev/null")
            result = consolidate_systemd_evidence(
                temporary, "sshd.service masked -\n",
                command_succeeded=True, desired={"sshd.service": "enabled"},
            )
        self.assertFalse(result.complete)
        self.assertEqual(result.findings[0].action, "block")
        self.assertEqual(result.unit_files.findings[0].state, "masked")


if __name__ == "__main__":
    unittest.main()
