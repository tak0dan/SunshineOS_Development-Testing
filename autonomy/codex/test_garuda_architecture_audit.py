"""Regression checks for source-level Garuda architecture enforcement."""
from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path

from garuda_architecture_audit import CHECKS, audit

PIN = "430de5bc5356468318a5c677d8b2f6d2c4565a75"
SOURCE = Path("/home/tak_0/.local/state/sunshine-orchestrator/iso/repos/garuda-toolbox")


class GarudaArchitectureAuditTests(unittest.TestCase):
    def test_GARUDA_ARCH_001_pinned_checkout_has_all_catalogued_architecture_evidence(self):
        result = audit(SOURCE, PIN)
        self.assertEqual(len(result["findings"]), 9)
        self.assertTrue(all(item["line"] > 0 and item["evidence"] for item in result["findings"]))

    def test_GARUDA_ARCH_004_app_update_and_os_update_are_distinct_paths(self):
        result = audit(SOURCE, PIN)
        by_id = {item["id"]: item for item in result["findings"]}
        self.assertEqual(by_id["GARUDA-ARCH-007"]["source_path"], "packages/main/src/modules/AutoUpdater.ts")
        self.assertEqual(by_id["GARUDA-ARCH-009"]["source_path"], "packages/renderer/src/app/components/system-status/system-status.component.ts")
        self.assertIn("application updater", by_id["GARUDA-ARCH-007"]["description"])
        self.assertIn("System update", by_id["GARUDA-ARCH-009"]["description"])

    def test_GARUDA_ARCH_002_unexpected_revision_fails_closed(self):
        with self.assertRaisesRegex(ValueError, "revision mismatch"):
            audit(SOURCE, "0" * 40)

    def test_GARUDA_ARCH_003_missing_safety_evidence_fails_closed(self):
        with tempfile.TemporaryDirectory() as temp:
            checkout = Path(temp)
            subprocess.run(["git", "init", "-q", str(checkout)], check=True)
            subprocess.run(["git", "-C", str(checkout), "-c", "user.name=test", "-c",
                            "user.email=test@example.invalid", "commit", "--allow-empty", "-qm", "fixture"], check=True)
            for relative, _, _ in CHECKS.values():
                path = checkout / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("safe placeholder\n", encoding="utf-8")
            rev = subprocess.run(["git", "-C", str(checkout), "rev-parse", "HEAD"],
                                 check=True, capture_output=True, text=True).stdout.strip()
            with self.assertRaisesRegex(ValueError, "expected source behavior not found"):
                audit(checkout, rev)


if __name__ == "__main__":
    unittest.main()
