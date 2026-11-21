"""Regression tests for read-only Arch SysV service repair assessment."""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ENGINE_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ENGINE_ROOT))

from src.discovery.sysvinit import parse_rc_conf  # noqa: E402
from src.evolution.tools.sysvinit_repair import assess_sysv_services  # noqa: E402


class SysVInitRepairTests(unittest.TestCase):
    def test_required_missing_script_is_reported_without_commands(self) -> None:
        """T-ARCH2015-SYSV-010: missing service is actionable but never invoked."""
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "etc/rc.d").mkdir(parents=True)
            (root / "etc/rc.d/network").write_text("#!/bin/sh\n", encoding="utf-8")
            result = assess_sysv_services(
                parse_rc_conf("DAEMONS=(network)\n"), root, ("crond",)
            )
        self.assertEqual(result.checked, ("network", "crond"))
        self.assertEqual(result.missing_scripts, ("crond",))
        self.assertFalse(result.repairable)
        self.assertEqual(result.commands, ())

    def test_incomplete_inventory_blocks_all_probes(self) -> None:
        """T-ARCH2015-SYSV-011: ambiguous source cannot drive repair assessment."""
        with tempfile.TemporaryDirectory() as temporary:
            result = assess_sysv_services(parse_rc_conf("DAEMONS=($SERVICES)\n"), temporary)
        self.assertEqual(result.checked, ())
        self.assertIn("incomplete", result.blockers[0])
        self.assertEqual(result.commands, ())

    def test_service_symlink_outside_root_is_blocked(self) -> None:
        """T-ARCH2015-SYSV-012: script evidence cannot escape the observed root."""
        with tempfile.TemporaryDirectory() as temporary, tempfile.TemporaryDirectory() as outside:
            root = Path(temporary)
            (root / "etc/rc.d").mkdir(parents=True)
            (Path(outside) / "network").write_text("external", encoding="utf-8")
            (root / "etc/rc.d/network").symlink_to(Path(outside) / "network")
            result = assess_sysv_services(parse_rc_conf("DAEMONS=(network)\n"), root)
        self.assertTrue(any("escapes root" in blocker for blocker in result.blockers))
        self.assertEqual(result.commands, ())


if __name__ == "__main__":
    unittest.main()
