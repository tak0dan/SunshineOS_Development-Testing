"""Regression checks for Garuda catalog provenance and safety policy."""
from __future__ import annotations

import sys
import subprocess
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

    def test_GARUDA_CAT_006_non_object_catalog_fails_closed(self):
        for malformed in (None, [], "catalog"):
            with self.subTest(malformed=malformed), self.assertRaisesRegex(ValueError, "catalog must be an object"):
                validate_catalog(malformed)

    def test_GARUDA_CAT_007_revision_must_be_full_lowercase_hex(self):
        data = load_catalog(CATALOG)
        data["source"]["revision"] = "g" * 40
        with self.assertRaisesRegex(ValueError, "full commit revision"):
            validate_catalog(data)

    def test_GARUDA_CAT_008_non_object_finding_fails_closed(self):
        data = load_catalog(CATALOG)
        data["findings"][0] = None
        with self.assertRaisesRegex(ValueError, "finding must be an object"):
            validate_catalog(data)

    def test_GARUDA_CAT_009_source_path_traversal_is_rejected(self):
        data = load_catalog(CATALOG)
        data["findings"][0]["source_paths"] = ["../outside.ts"]
        with self.assertRaisesRegex(ValueError, "source_paths"):
            validate_catalog(data)

    def test_GARUDA_CAT_010_malformed_control_shape_fails_closed(self):
        data = load_catalog(CATALOG)
        data["findings"][0]["controls"] = "journal-operation"
        with self.assertRaisesRegex(ValueError, "controls must be a list"):
            validate_catalog(data)

    def test_GARUDA_CAT_011_pinned_checkout_contains_every_cited_source(self):
        data = load_catalog(CATALOG)
        checkout = Path(data["source"]["checkout"])
        self.assertTrue(checkout.is_dir(), "source checkout unavailable; provenance check cannot run")
        revision = subprocess.run(
            ["git", "-C", str(checkout), "rev-parse", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        self.assertEqual(revision, data["source"]["revision"])
        for finding in data["findings"]:
            for source_path in finding["source_paths"]:
                with self.subTest(source_path=source_path):
                    self.assertTrue((checkout / source_path).is_file())


if __name__ == "__main__":
    unittest.main()
