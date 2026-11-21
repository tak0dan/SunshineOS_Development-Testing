"""Regression coverage for CachyOS-derived ALPM hook metadata checks."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from cachyos_alpm_hook import audit_alpm_hook, audit_boot_transition_hook  # noqa: E402


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

    def test_HOOK_005_boot_policy_accepts_cachyos_kernel_update_pattern(self) -> None:
        self.assertEqual(audit_boot_transition_hook(CACHYOS_KERNEL_HOOK), ())

    def test_HOOK_006_empty_metadata_value_fails_closed(self) -> None:
        issues = audit_alpm_hook(CACHYOS_KERNEL_HOOK.replace("Description = Updating systemd-boot entries", "Description = "))
        self.assertIn("HOOK_VALUE_EMPTY", {issue.code for issue in issues})

    def test_HOOK_007_boot_policy_rejects_package_only_trigger(self) -> None:
        hook = CACHYOS_KERNEL_HOOK.replace("Type = Path", "Type = Package").replace(
            "Target = usr/lib/modules/*/vmlinuz\nTarget = boot/vmlinuz*", "Target = linux"
        )
        self.assertIn("BOOT_HOOK_TRIGGER_NOT_PATH", {issue.code for issue in audit_boot_transition_hook(hook)})

    def test_HOOK_008_boot_policy_rejects_pre_transaction_timing(self) -> None:
        hook = CACHYOS_KERNEL_HOOK.replace("When = PostTransaction", "When = PreTransaction")
        self.assertIn("BOOT_HOOK_NOT_POST_TRANSACTION", {issue.code for issue in audit_boot_transition_hook(hook)})

    def test_HOOK_009_cachyos_remove_hook_pattern_passes_boot_policy(self) -> None:
        hook = """[Trigger]
Type = Path
Operation = Remove
Target = boot/linux*.kver

[Action]
Description = Cleaning up systemd-boot entries
When = PostTransaction
Exec = /usr/bin/sdboot-manage remove
"""
        self.assertEqual(audit_boot_transition_hook(hook), ())


if __name__ == "__main__":
    unittest.main()
