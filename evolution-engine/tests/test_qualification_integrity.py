"""Qualification digests bind the complete reproducibility and result record."""
from __future__ import annotations

import sys
import unittest
from dataclasses import replace
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.evolution.qualification import (  # noqa: E402
    REQUIRED_RELEASE_ARTIFACTS,
    QualificationRecord,
    release_gate,
)
from src.evolution.scheme import load_scheme  # noqa: E402


class QualificationIntegrityTests(unittest.TestCase):
    def test_digest_changes_when_evidence_or_tested_engine_changes(self) -> None:
        record = QualificationRecord(
            source_identity="B0", source_inventory_hash="a" * 64,
            target_identity="E040", target_manifest_hash="b" * 64,
            engine_version="ME12", transition_catalog_version="TC18",
            artifact_manifest_hash="c" * 64, vm_profile="btrfs-grub",
            scenario="source-to-target", execution_result="passed",
            validation_result="passed", failure_recovery_result="passed",
            layers=("vm_migration", "fault_injection", "recovery"),
            support_tier="qualified", qualified_at="2026-11-21T00:00:00+00:00",
        )
        digest = record.to_dict()["digest"]
        self.assertNotEqual(digest, replace(record, engine_version="ME13").to_dict()["digest"])
        self.assertNotEqual(digest, replace(record, source_inventory_hash="d" * 64).to_dict()["digest"])
        self.assertNotEqual(digest, replace(record, failure_recovery_result="failed").to_dict()["digest"])

    def test_qualified_evidence_requires_sha256_identities(self) -> None:
        record = QualificationRecord(
            source_identity="B0", source_inventory_hash="source",
            target_identity="E040", target_manifest_hash="target",
            engine_version="ME12", transition_catalog_version="TC18",
            artifact_manifest_hash="artifacts", support_tier="qualified",
            layers=("vm_migration", "fault_injection", "recovery"),
            validation_result="passed", failure_recovery_result="passed",
        )
        self.assertTrue(any("SHA-256" in error for error in record.validate()))

    def test_loaded_digest_detects_tampered_evidence(self) -> None:
        record = QualificationRecord(
            source_identity="B0", source_inventory_hash="a" * 64,
            target_identity="E040", target_manifest_hash="b" * 64,
            engine_version="ME12", transition_catalog_version="TC18",
            artifact_manifest_hash="c" * 64, support_tier="qualified",
            layers=("vm_migration", "fault_injection", "recovery"),
            validation_result="passed", failure_recovery_result="passed",
        )
        serialized = record.to_dict()
        loaded = QualificationRecord.from_dict(serialized)
        self.assertEqual(loaded.validate(), [])
        tampered = QualificationRecord.from_dict({
            **serialized, "engine_version": "ME13",
        })
        self.assertTrue(any("digest does not match" in error for error in tampered.validate()))

    def test_release_gate_can_require_additional_architectural_source_states(self) -> None:
        record = QualificationRecord.from_dict(QualificationRecord(
            source_identity="B0", source_inventory_hash="a" * 64,
            target_identity="E040", target_manifest_hash="b" * 64,
            engine_version="ME12", transition_catalog_version="TC18",
            artifact_manifest_hash="c" * 64,
            layers=("vm_migration", "fault_injection", "recovery"),
            support_tier="qualified", validation_result="passed",
            failure_recovery_result="passed",
        ).to_dict())
        artifacts = {name: "present" for name in REQUIRED_RELEASE_ARTIFACTS}
        report = release_gate(
            artifacts, (record,), load_scheme().versions,
            required_sources=("B0", "E020"),
        )
        self.assertFalse(report.passed)
        self.assertTrue(any(check["name"] == "qualification:E020"
                            and not check["passed"] for check in report.checks))


if __name__ == "__main__":
    unittest.main()
