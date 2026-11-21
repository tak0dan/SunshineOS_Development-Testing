"""Regression coverage for native Arch rescue assessment."""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.evolution.tools.arch_rescue import (  # noqa: E402
    REQUIRED_PROBES,
    ArchRescueProbe,
    assess_arch_rescue,
    assess_pacman_lock,
    observe_arch_rescue_root,
)


def clean_probes() -> dict[str, ArchRescueProbe]:
    return {
        "pacman-db-check": ArchRescueProbe(
            "pacman-db-check", REQUIRED_PROBES["pacman-db-check"], 0,
            "checking dependencies...\n",
        ),
        "pacman-file-check": ArchRescueProbe(
            "pacman-file-check", REQUIRED_PROBES["pacman-file-check"], 0,
            "base: 12 total files, 0 missing files\nlinux: 240 total files, 0 missing files\n",
        ),
        "systemd-unit-verify": ArchRescueProbe(
            "systemd-unit-verify", REQUIRED_PROBES["systemd-unit-verify"], 0, "",
        ),
    }


def clean_observations() -> dict[str, object]:
    return {
        "kernel_present": True,
        "initramfs_present": True,
        "bootloader_config_present": True,
        "boot_entries_present": True,
        "lock_state": "missing",
        "snapshot_available": True,
        "pending_reboot": False,
    }


class ArchRescueTests(unittest.TestCase):
    def test_native_readonly_checks_and_settled_state_are_healthy(self) -> None:
        report = assess_arch_rescue(clean_probes(), observed=clean_observations())
        self.assertTrue(report.healthy)
        self.assertFalse(report.degraded)
        self.assertFalse(report.blocked)
        self.assertTrue(report.safe_to_mutate)
        self.assertEqual(len(report.findings), 7)
        self.assertEqual(
            report.findings[1].windows_counterpart,
            "DISM /ScanHealth; SFC /verifyonly",
        )

    def test_missing_probe_and_unobserved_facts_fail_closed(self) -> None:
        report = assess_arch_rescue({}, observed={})
        self.assertFalse(report.healthy)
        self.assertTrue(report.blocked)
        self.assertFalse(report.safe_to_mutate)
        self.assertTrue(all(item.status == "unknown" for item in report.findings))

    def test_mutating_or_unexpected_command_is_blocked(self) -> None:
        probes = clean_probes()
        probes["pacman-file-check"] = ArchRescueProbe(
            "pacman-file-check", ("pacman", "-S", "base"), 0, "ok",
        )
        report = assess_arch_rescue(probes, observed=clean_observations())
        self.assertEqual(report.findings[1].status, "blocked")
        self.assertFalse(report.healthy)
        self.assertFalse(report.safe_to_mutate)

    def test_missing_files_are_degraded_and_pending_reboot_is_blocked(self) -> None:
        probes = clean_probes()
        probes["pacman-file-check"] = ArchRescueProbe(
            "pacman-file-check", REQUIRED_PROBES["pacman-file-check"], 0,
            "python: /usr/lib/python3.14/x.py: No such file or directory\n",
        )
        observations = clean_observations()
        observations["pending_reboot"] = True
        report = assess_arch_rescue(probes, observed=observations)
        self.assertTrue(report.degraded)
        self.assertTrue(report.blocked)
        self.assertEqual(report.findings[1].status, "degraded")
        self.assertEqual(report.findings[-1].status, "blocked")
        self.assertFalse(report.safe_to_mutate)

    def test_systemd_unit_problem_is_degraded(self) -> None:
        probes = clean_probes()
        probes["systemd-unit-verify"] = ArchRescueProbe(
            "systemd-unit-verify", REQUIRED_PROBES["systemd-unit-verify"], 0,
            "Failed to load default.target: No such file or directory\n",
        )
        report = assess_arch_rescue(probes, observed=clean_observations())
        self.assertEqual(report.findings[2].status, "degraded")
        self.assertFalse(report.healthy)

    def test_lock_states_never_authorize_deletion(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            lock = root / "var/lib/pacman/db.lck"
            proc = root / "proc"
            self.assertEqual(assess_pacman_lock(lock, proc).state, "missing")
            lock.parent.mkdir(parents=True)
            proc.mkdir(parents=True)
            lock.write_text("123\n")
            self.assertEqual(assess_pacman_lock(lock, proc).state, "stale-candidate")
            owner = proc / "123"
            owner.mkdir(parents=True)
            (owner / "comm").write_text("pacman\n")
            active = assess_pacman_lock(lock, proc)
            self.assertEqual(active.state, "active-owner")
            self.assertEqual(active.owners, (123,))
            self.assertFalse(active.repair_allowed)
            blocked = assess_arch_rescue(
                clean_probes(), observed={**clean_observations(), "lock_state": active.state}
            )
            self.assertEqual(blocked.findings[4].status, "blocked")

    def test_root_observation_reads_only_boot_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            boot = root / "boot"
            (boot / "loader" / "entries").mkdir(parents=True)
            (boot / "vmlinuz-linux").write_text("kernel")
            (boot / "initramfs-linux.img").write_text("initramfs")
            (boot / "loader" / "loader.conf").write_text("default arch.conf\n")
            (boot / "loader" / "entries" / "arch.conf").write_text("title SunshineOS\n")
            observed = observe_arch_rescue_root(root)
            self.assertTrue(observed["kernel_present"])
            self.assertTrue(observed["initramfs_present"])
            self.assertTrue(observed["bootloader_config_present"])
            self.assertTrue(observed["boot_entries_present"])


if __name__ == "__main__":
    unittest.main()
