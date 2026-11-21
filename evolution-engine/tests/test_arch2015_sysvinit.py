"""Focused regression tests for Arch 2015 SysV init evidence handling."""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ENGINE_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ENGINE_ROOT))

from src.core import Status  # noqa: E402
from src.discovery import discover_system  # noqa: E402
from src.target.compatibility import classify_source  # noqa: E402


class Arch2015SysvinitTests(unittest.TestCase):
    """Ensure historical SysV artifacts cannot override live init evidence."""

    def test_sysvinit_remnants_do_not_override_named_pid1(self) -> None:
        """T-ARCH2015-SYSV-004: runtime PID 1 outranks installed SysV remnants."""
        with tempfile.TemporaryDirectory(prefix="sunshine-arch2015-sysv-") as root:
            etc = Path(root, "etc")
            etc.mkdir()
            (etc / "inittab").write_text("id:3:initdefault:\n", encoding="utf-8")

            commands = {
                "cat /proc/1/comm": (0, "systemd\n", ""),
                "systemctl --version": (127, "", "systemctl unavailable"),
                "init --version": (0, "init (sysvinit 2.88)\n", ""),
            }
            state = discover_system(
                root=root,
                execute=lambda command: commands.get(command, (127, "", "unavailable")),
            )

        self.assertEqual(state.init_system, "systemd")
        self.assertIs(state.observations["system.init"].status, Status.RUNNING)

    def test_detected_sysv_source_is_blocked_from_ordinary_transformation(self) -> None:
        """T-ARCH2015-SYSV-005: discovered SysV cannot enter Arch transformer."""
        with tempfile.TemporaryDirectory(prefix="sunshine-arch2015-sysv-") as root:
            etc = Path(root, "etc")
            etc.mkdir()
            (etc / "inittab").write_text("id:3:initdefault:\n", encoding="utf-8")

            commands = {
                "cat /proc/1/comm": (0, "init\n", ""),
                "systemctl --version": (127, "", "systemctl unavailable"),
                "init --version": (0, "init (sysvinit 2.88)\n", ""),
            }
            state = discover_system(
                root=root,
                execute=lambda command: commands.get(command, (127, "", "unavailable")),
            )

        report = classify_source(state)
        self.assertEqual(state.init_system, "sysvinit")
        self.assertFalse(report.supported)
        self.assertTrue(any("sysvinit" in blocker for blocker in report.blockers))


if __name__ == "__main__":
    unittest.main()
