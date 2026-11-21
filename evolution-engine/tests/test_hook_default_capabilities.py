"""The built-in hook allowlist must not grant broad root capabilities."""
from __future__ import annotations

import tempfile
import unittest
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.evolution.hooks import DEFAULT_ALLOWED, HookRunner  # noqa: E402


class HookDefaultCapabilityTests(unittest.TestCase):
    def test_default_hooks_reject_file_access_and_mutation_tools(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            runner = HookRunner(tmp)
            self.assertEqual(DEFAULT_ALLOWED, ("true", "echo", "sync"))
            for command in (
                "cat /etc/shadow",
                "test -e /etc/shadow",
                "btrfs subvolume delete /",
                "sunshine-evolve apply",
            ):
                with self.subTest(command=command):
                    self.assertTrue(runner.validate_command(command))

            for command in ("true", "echo ready", "sync"):
                with self.subTest(command=command):
                    self.assertEqual(runner.validate_command(command), [])

    def test_trusted_caller_can_register_a_specific_extra_command(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            runner = HookRunner(tmp, allowed_commands=(*DEFAULT_ALLOWED, "sunshine-evolve"))
            self.assertEqual(runner.validate_command("sunshine-evolve validate"), [])


if __name__ == "__main__":
    unittest.main()
