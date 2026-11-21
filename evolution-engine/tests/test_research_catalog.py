"""Regression tests for durable, fail-closed external research provenance."""
from __future__ import annotations

import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.evolution.research_catalog import ResearchCatalog  # noqa: E402


class ResearchCatalogTests(unittest.TestCase):
    def test_CAT_006_omarchy_update_recovery_catalog_is_pinned_and_complete(self) -> None:
        catalog = ResearchCatalog.load(ROOT / "fixtures/research/omarchy-update-recovery-wave1.json")
        expected_paths = {
            "docs/update-process.md", "bin/omarchy-update", "bin/omarchy-migrate",
            "bin/omarchy-update-pacman-guard", "manual/30-updates.md",
            "manual/47-system-snapshots.md",
        }
        self.assertEqual(catalog.project, "basecamp/omarchy")
        self.assertEqual(catalog.commit, "e4635a4eea887d5c8dbd70427386f570c37a2a61")
        self.assertEqual({record.relative_path for record in catalog.sources}, expected_paths)
        self.assertEqual(catalog.validate(), [])

    def test_CAT_001_cachyos_catalog_has_unique_verified_records(self) -> None:
        catalog = ResearchCatalog.load(ROOT / "fixtures/research/cachyos-wave1.json")
        self.assertEqual(catalog.project, "CachyOS/CachyOS-PKGBUILDS")
        self.assertEqual(catalog.commit, "97a55536e5f756d22199f043de4aa1a0d8eebc8a")
        self.assertEqual(len(catalog.sources), 9)
        self.assertEqual(catalog.validate(), [])
        self.assertEqual(len({item.source_id for item in catalog.sources}), 9)

    def test_CAT_002_matching_snapshot_passes_content_verification(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            payload = b"pinned research input\n"
            (root / "hooks").mkdir()
            (root / "hooks/input.hook").write_bytes(payload)
            record = {
                "source_id": "hook", "relative_path": "hooks/input.hook",
                "sha256": hashlib.sha256(payload).hexdigest(), "finding": "Observed hook metadata.",
                "adoption": "Use explicit trigger boundaries.", "limitation": "No runtime claim.",
                "status": "verified",
            }
            catalog_file = root / "catalog.json"
            catalog_file.write_text(json.dumps({
                "catalog_id": "test", "schema": 1, "project": "test", "commit": "a" * 40,
                "sources": [record],
            }), encoding="utf-8")
            self.assertEqual(ResearchCatalog.load(catalog_file).verify_sources(root), [])

    def test_CAT_003_changed_snapshot_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "input"
            source.write_bytes(b"changed")
            record = {
                "source_id": "item", "relative_path": "input", "sha256": "0" * 64,
                "finding": "Finding", "adoption": "Decision", "limitation": "Limit",
                "status": "verified",
            }
            from src.evolution.research_catalog import ResearchSource  # noqa: PLC0415
            catalog = ResearchCatalog("test", 1, "test", "a" * 40, (ResearchSource.from_dict(record),))
            self.assertIn("SHA-256 mismatch", " ".join(catalog.verify_sources(root)))

    def test_CAT_004_parent_traversal_is_rejected(self) -> None:
        from src.evolution.research_catalog import ResearchSource  # noqa: PLC0415
        catalog = ResearchCatalog("test", 1, "test", "a" * 40, (ResearchSource(
            "escape", "../outside", "a" * 64, "Finding", "Decision", "Limit",
        ),))
        self.assertTrue(any("safe relative path" in error for error in catalog.validate()))

    def test_CAT_005_unverified_claim_is_not_accepted_as_catalogue_evidence(self) -> None:
        from src.evolution.research_catalog import ResearchSource  # noqa: PLC0415
        catalog = ResearchCatalog("test", 1, "test", "a" * 40, (ResearchSource(
            "claim", "hook", "a" * 64, "Finding", "Decision", "Limit", "unverified",
        ),))
        self.assertTrue(any("unsupported evidence status" in error for error in catalog.validate()))


    def test_CAT_007_native_arch_rescue_catalog_is_pinned_and_complete(self) -> None:
        catalog = ResearchCatalog.load(
            ROOT / "fixtures/research/native-arch-rescue-wave1.json"
        )
        self.assertEqual(catalog.catalog_id, "native-arch-rescue-wave1")
        self.assertEqual(catalog.commit, "b25032d370b39170e52e6c268bac94195e865448")
        self.assertEqual(len(catalog.sources), 10)
        self.assertEqual(catalog.validate(), [])
        self.assertEqual(catalog.verify_sources(ROOT.parent), [])


if __name__ == "__main__":
    unittest.main()
