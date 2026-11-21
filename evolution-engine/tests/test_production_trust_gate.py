"""Production CLI operations cannot start discovery without Stage A trust."""
from __future__ import annotations

import contextlib
import io
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.engine import cmd_health, main  # noqa: E402


class ProductionTrustGateTests(unittest.TestCase):
    def test_real_check_and_apply_require_trust_before_discovery(self) -> None:
        for command in ("--check", "--apply"):
            with self.subTest(command=command):
                err = io.StringIO()
                with contextlib.redirect_stderr(err):
                    status = main([command])
                self.assertEqual(status, 3)
                self.assertIn("Stage A trust verification is mandatory", err.getvalue())

    def test_fixture_mode_remains_available_without_trust(self) -> None:
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            status = main(["--fixture", "clean-arch", "--check"])
        self.assertEqual(status, 0, err.getvalue())
        self.assertIn('"distribution": "arch"', out.getvalue())

    def test_health_is_read_only_and_does_not_require_stage_a(self) -> None:
        commands = []
        results = {
            ("pacman", "-Dk"): (0, "", ""),
            ("pacman", "-Qk"): (0, "base: 10 total files, 0 missing files", ""),
            ("pacman", "-Qdtq"): (0, "", ""),
        }
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            status = cmd_health(lambda argv: commands.append(tuple(argv)) or results[tuple(argv)])
        self.assertEqual(status, 0)
        self.assertEqual(commands, list(results))
        self.assertIn('"healthy": true', out.getvalue())


if __name__ == "__main__":
    unittest.main()
