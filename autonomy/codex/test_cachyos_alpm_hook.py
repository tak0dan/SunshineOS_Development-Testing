"""Regression coverage for CachyOS-derived ALPM hook metadata checks."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from cachyos_alpm_hook import audit_alpm_hook  # noqa: E402


CACHYOS_KERNEL_HOOK = """[Trigger]
Type = Path
Operation = Install
Operation = Upgrade
Target = usr/lib/modules/*/vmlinuz
Target = boot/vmlinuz*

[Action]
Description = Updating systemd-boot entries
When = PostTransaction
Exec = /usr/bin/sdboot-manage autogen
"""


class CachyOSAlpmHookTests(unittest.TestCase):
    def test_HOOK_001_cachyos_kernel_hook_satisfies_contract(self) -> None:
        self.assertEqual(audit_alpm_hook(CACHYOS_KERNEL_HOOK), ())

    def test_HOOK_002_missing_target_fails_closed(self) -> None:
        issues = audit_alpm_hook("[Trigger]\nType=Path\nOperation=Upgrade\n[Action]\nDescription=x\nWhen=PostTransaction\nExec=/bin/x\n")
        self.assertIn("HOOK_TRIGGER_INCOMPLETE", {issue.code for issue in issues})

    def test_HOOK_003_unknown_key_is_rejected(self) -> None:
        issues = audit_alpm_hook(CACHYOS_KERNEL_HOOK.replace("Type = Path", "Type = Path\nNetwork = true"))
        self.assertIn("HOOK_KEY_UNKNOWN", {issue.code for issue in issues})

    def test_HOOK_004_relative_exec_is_rejected(self) -> None:
        issues = audit_alpm_hook(CACHYOS_KERNEL_HOOK.replace("/usr/bin/sdboot-manage", "sdboot-manage"))
        self.assertIn("HOOK_EXEC_NOT_ABSOLUTE", {issue.code for issue in issues})


if __name__ == "__main__":
    unittest.main()
