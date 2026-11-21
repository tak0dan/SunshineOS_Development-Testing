"""Regression coverage for fail-closed Windows servicing assessment."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.evolution.tools.windows_servicing import (  # noqa: E402
    REQUIRED_PROBES,
    ServicingProbe,
    assess_windows_servicing,
)


def healthy_probes():
    clean = {
        "dism-checkhealth": "No component store corruption detected.",
        "dism-scanhealth": "No component store corruption detected.",
        "sfc-verifyonly": "Windows Resource Protection did not find any integrity violations.",
    }
    return {name: ServicingProbe(name, command, 0, clean[name])
            for name, command in REQUIRED_PROBES.items()}


class WindowsServicingTests(unittest.TestCase):
    def test_all_integrity_probes_and_settled_reboot_state_are_healthy(self):
        report = assess_windows_servicing(healthy_probes(), reboot_pending=False)
        self.assertTrue(report.healthy)
        self.assertFalse(report.blocked)

    def test_missing_probe_or_unknown_reboot_state_fails_closed(self):
        report = assess_windows_servicing({}, reboot_pending=None)
        self.assertFalse(report.healthy)
        self.assertTrue(report.blocked)
        self.assertEqual(report.findings[0].status, "unknown")

    def test_corruption_and_pending_reboot_never_report_healthy(self):
        probes = healthy_probes()
        probes["dism-scanhealth"] = ServicingProbe(
            "dism-scanhealth", REQUIRED_PROBES["dism-scanhealth"], 0,
            "The component store is repairable.",
        )
        report = assess_windows_servicing(probes, reboot_pending=True)
        self.assertFalse(report.healthy)
        self.assertEqual(report.findings[1].status, "degraded")
        self.assertEqual(report.findings[-1].status, "blocked")

    def test_unexpected_command_is_blocked(self):
        probes = healthy_probes()
        probes["sfc-verifyonly"] = ServicingProbe("sfc-verifyonly", ("sfc", "/scannow"), 0)
        report = assess_windows_servicing(probes, reboot_pending=False)
        self.assertEqual(report.findings[2].status, "blocked")

    def test_unrecognized_success_output_is_unknown(self):
        probes = healthy_probes()
        probes["dism-scanhealth"] = ServicingProbe(
            "dism-scanhealth", REQUIRED_PROBES["dism-scanhealth"], 0,
            "The operation completed successfully.",
        )
        report = assess_windows_servicing(probes, reboot_pending=False)
        self.assertEqual(report.findings[1].status, "unknown")
        self.assertFalse(report.healthy)
        self.assertTrue(report.blocked)

    def test_evidence_key_and_probe_identity_must_match(self):
        probes = healthy_probes()
        probes["dism-checkhealth"] = ServicingProbe(
            "dism-scanhealth", REQUIRED_PROBES["dism-checkhealth"], 0,
            "No component store corruption detected.",
        )
        report = assess_windows_servicing(probes, reboot_pending=False)
        self.assertEqual(report.findings[0].status, "blocked")


if __name__ == "__main__":
    unittest.main()
