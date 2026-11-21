"""Cross-check that the Garuda wave deliverables stay complete and grounded."""

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CODEX = ROOT / "autonomy" / "codex"
SOURCE = Path("/home/tak_0/.local/state/sunshine-orchestrator/iso/repos/garuda-toolbox")


class GarudaDeliverableConsolidationTests(unittest.TestCase):
    def test_GARUDA_CONSOL_001_catalog_source_revision_and_paths_are_present(self):
        catalog = json.loads((CODEX / "garuda-wave1-catalog.json").read_text())
        self.assertEqual(catalog["source"]["revision"], "430de5bc5356468318a5c677d8b2f6d2c4565a75")
        self.assertTrue(SOURCE.is_dir(), "pinned Garuda checkout is unavailable")
        for finding in catalog["findings"]:
            for source_file in finding["source_paths"]:
                self.assertTrue((SOURCE / source_file).is_file(), source_file)

    def test_GARUDA_CONSOL_002_audit_and_regression_evidence_are_linked(self):
        audit = json.loads((CODEX / "garuda-wave1-architecture-audit.json").read_text())
        self.assertEqual(len(audit["findings"]), 6)
        for path in (
            "test_garuda_catalog.py",
            "test_garuda_architecture_audit.py",
            "test_pacman_lock_repair.py",
            "garuda_catalog.py",
            "garuda_architecture_audit.py",
            "pacman_lock_repair.py",
            "garuda-ci-hardening-wave1.md",
            "garuda-wave1-integration.md",
            "garuda-repair-wave1.md",
            "garuda-migration-engine-wave1.md",
        ):
            self.assertTrue((CODEX / path).is_file(), path)

    def test_GARUDA_CONSOL_003_consolidation_summary_has_test_and_evidence_ids(self):
        summary = (CODEX / "garuda-deliverable-consolidation-wave1.md").read_text()
        for required in (
            "GARUDA_CAT_001–GARUDA_CAT_011",
            "GARUDA-ARCH-001–GARUDA-ARCH-006",
            "GARUDA_REPAIR_001–GARUDA_REPAIR_004",
            "GARUDA_CONSOL_001–GARUDA_CONSOL_003",
            "garuda-deliverable-consolidation-wave1-test.log",
        ):
            self.assertIn(required, summary)


if __name__ == "__main__":
    unittest.main()
