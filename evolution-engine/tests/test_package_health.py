"""Package health assessment stays observational and distinguishes uncertainty."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.evolution.tools.package_health import assess_package_health  # noqa: E402


class PackageHealthTests(unittest.TestCase):
    def test_clean_database_and_file_checks_with_orphan_advisory(self) -> None:
        seen = []
        outputs = {
            ("pacman", "-Dk"): (0, "checking dependencies...", ""),
            ("pacman", "-Qk"): (0, "base: 24 total files, 0 missing files", ""),
            ("pacman", "-Qdtq"): (0, "legacy-tool\n", ""),
        }

        def execute(argv):
            seen.append(tuple(argv))
            return outputs[tuple(argv)]

        report = assess_package_health(execute)
        self.assertTrue(report.healthy)
        self.assertEqual([check.status for check in report.checks], ["healthy"] * 3)
        self.assertEqual(report.checks[2].findings, ("review candidate: legacy-tool",))
        self.assertEqual(len(seen), 3)

    def test_integrity_failure_degrades_and_never_suggests_removal(self) -> None:
        outputs = {
            ("pacman", "-Dk"): (0, "", ""),
            ("pacman", "-Qk"): (0, "damaged: 50 total files, 2 missing files", ""),
            ("pacman", "-Qdtq"): (0, "damaged\n", ""),
        }
        report = assess_package_health(lambda argv: outputs[tuple(argv)])
        self.assertFalse(report.healthy)
        self.assertEqual(report.checks[1].status, "degraded")
        self.assertIn("2 missing files", report.checks[1].findings[0])
        self.assertIn("read-only", report.to_dict()["policy"])

    def test_missing_pacman_is_unknown_not_healthy(self) -> None:
        report = assess_package_health(lambda _argv: (127, "", "not found"))
        self.assertFalse(report.healthy)
        self.assertTrue(all(check.status == "unknown" for check in report.checks))


if __name__ == "__main__":
    unittest.main()
