"""Regression checks for Garuda catalog provenance and safety policy."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from garuda_catalog import load_catalog, validate_catalog

CATALOG = Path(__file__).with_name("garuda-wave1-catalog.json")


class GarudaCatalogTests(unittest.TestCase):
    def test_GARUDA_CAT_001_source_revision_and_records_validate(self):
        data = load_catalog(CATALOG)
        self.assertEqual(len(data["source"]["revision"]), 40)
        self.assertEqual(len(data["findings"]), 5)

    def test_GARUDA_CAT_002_adoption_needs_plan_journal_and_verification(self):
        data = load_catalog(CATALOG)
        for finding in data["findings"]:
            if finding["verdict"] in {"ADAPT", "COPY"}:
                self.assertTrue({"plan-before-mutation", "journal-operation", "verify-postcondition"} <= set(finding["controls"]))

    def test_GARUDA_CAT_003_duplicate_ids_fail_closed(self):
        data = load_catalog(CATALOG)
        data["findings"][1]["id"] = data["findings"][0]["id"]
        with self.assertRaisesRegex(ValueError, "duplicate"):
            validate_catalog(data)

    def test_GARUDA_CAT_004_adopted_pattern_without_journal_is_rejected(self):
        data = load_catalog(CATALOG)
        data["findings"][0]["controls"].remove("journal-operation")
        with self.assertRaisesRegex(ValueError, "journal-operation"):
            validate_catalog(data)

    def test_GARUDA_CAT_005_invalid_invariant_reference_is_rejected(self):
        data = load_catalog(CATALOG)
        data["findings"][0]["invariants"] = ["M-99"]
        with self.assertRaisesRegex(ValueError, "invariant"):
            validate_catalog(data)


if __name__ == "__main__":
    unittest.main()
