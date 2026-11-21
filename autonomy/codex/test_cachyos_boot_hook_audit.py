"""Regression tests for the boot artifact failure policy auditor."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))

from cachyos_boot_hook_audit import audit_boot_generation_script  # noqa: E402


class CachyBootHookAuditTests(unittest.TestCase):
    def test_audit_001_suppressed_failure_without_validation_is_reported(self) -> None:
        source = "mkinitcpio -p linux || true\necho done\n"
        findings = audit_boot_generation_script(source)
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0].line, 1)
        self.assertEqual(findings[0].code, "BOOTGEN_SUPPRESSED_UNVERIFIED")

    def test_audit_002_nearby_validation_closes_finding(self) -> None:
        source = "mkinitcpio -P || true\nif [[ ! -s /boot/initramfs.img ]]; then die\n"
        self.assertEqual(audit_boot_generation_script(source), ())

    def test_audit_003_checked_generation_is_not_reported(self) -> None:
        source = "mkinitcpio -P || exit 1\necho done\n"
        self.assertEqual(audit_boot_generation_script(source), ())

    def test_audit_004_cachyos_uki_branch_has_artifact_validation(self) -> None:
        """The cached CachyOS branch validates UKIs after its kernel loop."""
        source = "mkinitcpio -p \"${kernel}\" || true\n" + ("# intervening work\n" * 11)
        source += 'if [[ -z "$(ls -A "${ESP}/EFI/Linux")" ]]; then\n die "Error: There are no UKI images after entry generation"\nfi\n'
        self.assertEqual(audit_boot_generation_script(source), ())

    def test_audit_005_cached_cachyos_validation_distance_is_included(self) -> None:
        """Match sdboot-manage: line 259 generation, line 272 UKI gate."""
        lines = [
            'mkinitcpio -p "${kernel}" || true',
            "fi",
            "# Remove existing entries to not create duplicates with UKI",
            'if [[ -e "${uki}" ]] && ((preset_created)); then',
            'rm -f "${ESP}/initramfs-${kernel}.img" "${ESP}/vmlinuz-${kernel}" || true',
            'remove_entry "${entry}" || true',
            "# Drop leftovers from older versions",
            'remove_entry "${fallback_entry}" || true',
            "fi",
            "done < <(get_installed_kernels)",
            "",
            "# Two additional source lines place the check at offset 13.",
            "",
            'if [[ -z "$(ls -A "${ESP}/EFI/Linux")" ]]; then',
            'die "Error: There are no UKI images after entry generation"',
            "fi",
        ]
        self.assertEqual(audit_boot_generation_script("\n".join(lines)), ())

    def test_audit_006_validation_after_context_window_does_not_clear_finding(self) -> None:
        source = "mkinitcpio -P || true\n" + ("echo working\n" * 17)
        source += 'if [[ ! -s /boot/initramfs.img ]]; then die "no image"; fi\n'
        self.assertEqual(len(audit_boot_generation_script(source)), 1)


if __name__ == "__main__":
    unittest.main()
