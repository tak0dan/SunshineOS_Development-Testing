"""Migration journal digests cover all persistent migration evidence."""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.evolution.journal_state import MigrationJournal, OperationRecord  # noqa: E402
from src.evolution.release import content_digest  # noqa: E402
from src.evolution.versions import VersionSet  # noqa: E402


def journal() -> MigrationJournal:
    return MigrationJournal(
        "migration-1", source_inventory_hash="a" * 64,
        target_manifest_hash="b" * 64, plan_hash="c" * 64,
        versions=VersionSet("E040", "ME12", "INV7", "EVS4", "TC18", "B0-2026"),
        transition_catalog_hash="d" * 64, artifact_manifest_hash="e" * 64,
    )


class MigrationJournalIntegrityTests(unittest.TestCase):
    def test_complete_record_digest_detects_identity_and_checkpoint_tampering(self) -> None:
        record = journal()
        record.add_operation(OperationRecord("op-1"))
        record.set_operation("op-1", "Completed", result="verified")
        record.add_checkpoint("snapshot-1", "btrfs")
        document = record.to_dict()
        self.assertEqual(MigrationJournal.from_dict(document).validate(), [])

        for change in (
            {"source_inventory_hash": "f" * 64},
            {"artifact_manifest_hash": "f" * 64},
            {"checkpoints": [{"ref": "tampered", "strategy": "btrfs", "at": "now"}]},
        ):
            with self.subTest(change=change):
                altered = MigrationJournal.from_dict({**document, **change})
                self.assertTrue(any("digest does not match" in e for e in altered.validate()))

    def test_legacy_partial_digest_is_verified_then_upgraded_to_full_digest(self) -> None:
        legacy = {
            "format": "sunshine-migration-journal-1",
            "migration_id": "legacy-1", "state": "Discovery", "plan_hash": "",
            "operations": {},
        }
        legacy["digest"] = content_digest({
            "migration_id": "legacy-1", "state": "Discovery", "plan_hash": "",
            "operations": {},
        })
        migrated = MigrationJournal.from_dict(legacy)
        upgraded = migrated.to_dict()
        self.assertEqual(upgraded["format"], "sunshine-migration-journal-2")
        self.assertEqual(MigrationJournal.from_dict(upgraded).validate(), [])
        legacy["digest"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "legacy journal digest"):
            MigrationJournal.from_dict(legacy)

    def test_mutation_invalidates_loaded_digest_until_resaved(self) -> None:
        record = MigrationJournal.from_dict(journal().to_dict())
        record.transition("Planning")
        self.assertEqual(record.digest, "")
        self.assertTrue(any("digest is required" in e for e in record.validate()))
        record.add_checkpoint("snapshot-2")
        self.assertTrue(record.to_dict()["digest"])

    def test_persisted_v2_journal_cannot_drop_its_digest(self) -> None:
        document = journal().to_dict()
        document.pop("digest")
        restored = MigrationJournal.from_dict(document)
        self.assertTrue(any("digest is required" in e for e in restored.validate()))


if __name__ == "__main__":
    unittest.main()
