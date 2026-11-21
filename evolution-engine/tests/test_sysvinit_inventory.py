"""Regression tests for read-only historical Arch SysV inventory parsing."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ENGINE_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ENGINE_ROOT))

from src.discovery.sysvinit import parse_rc_conf  # noqa: E402


class SysVInitInventoryTests(unittest.TestCase):
    def test_literal_daemons_preserve_enable_disable_and_background(self) -> None:
        """T-ARCH2015-SYSV-006: rc.conf markers survive normalization."""
        result = parse_rc_conf('DAEMONS=( network @crond !hwclock )\n')
        self.assertTrue(result.complete)
        self.assertEqual(result.enabled, ("network", "crond"))
        self.assertEqual(result.disabled, ("hwclock",))
        self.assertEqual(result.background, ("crond",))

    def test_shell_expansion_is_rejected_without_execution(self) -> None:
        """T-ARCH2015-SYSV-007: dynamic rc.conf cannot become trusted intent."""
        result = parse_rc_conf('DAEMONS=( network $(touch /tmp/pwned) )\n')
        self.assertFalse(result.complete)
        self.assertEqual(result.enabled, ())
        self.assertIn("shell syntax", result.errors[0])

    def test_missing_or_ambiguous_assignment_is_incomplete(self) -> None:
        """T-ARCH2015-SYSV-008: absent/duplicate historical state fails closed."""
        self.assertFalse(parse_rc_conf("# no service declaration\n").complete)
        duplicate = parse_rc_conf("DAEMONS=(a)\nDAEMONS=(b)\n")
        self.assertFalse(duplicate.complete)
        self.assertIn("multiple", duplicate.errors[0])

    def test_duplicate_services_are_rejected(self) -> None:
        """T-ARCH2015-SYSV-009: duplicated entries are not silently collapsed."""
        result = parse_rc_conf("DAEMONS=( network @network )\n")
        self.assertFalse(result.complete)
        self.assertIn("duplicate", result.errors[0])


if __name__ == "__main__":
    unittest.main()
