"""Archived artifacts must verify signatures against a configured trust set."""
from __future__ import annotations

import hashlib
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.evolution.artifacts import (  # noqa: E402
    ArtifactManifest,
    ArtifactRecord,
    ContentAddressedArchive,
)
from src.trust.model import canonical_bytes  # noqa: E402


class ArtifactSignatureVerificationTests(unittest.TestCase):
    def test_signature_and_signer_are_verified(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "artifact.bin"
            source.write_bytes(b"archived baseline")
            record = ArtifactRecord(
                artifact_id="baseline", artifact_type="baseline_iso",
                content_hash=hashlib.sha256(source.read_bytes()).hexdigest(),
                size=source.stat().st_size, signature="valid-signature",
                signer="AABBCC", compatibility={"architecture": "x86_64"},
            )
            archive = ContentAddressedArchive(Path(tmp) / "archive")
            archive.store(source, record)
            seen = []

            def verify(signer: str, payload: bytes, signature: str) -> bool:
                seen.append((signer, payload, signature))
                return signer == "AABBCC" and signature == "valid-signature"

            report = archive.verify(
                record, require_signature=True, verifier=verify,
                trusted_signers={"aabbcc"},
            )
            self.assertTrue(report["passed"], report["errors"])
            self.assertEqual(seen[0][1], canonical_bytes(record.signable()))
            self.assertFalse(archive.verify(record, require_signature=True)["passed"])
            self.assertFalse(archive.verify(
                record, require_signature=True, verifier=verify,
                trusted_signers={"ddeeff"},
            )["passed"])

    def test_compatibility_metadata_round_trips(self) -> None:
        record = ArtifactRecord.from_dict({
            "artifact_id": "manifest", "artifact_type": "migration_manifest",
            "content_hash": "a" * 64, "size": 12,
            "compatibility": {"engine": "ME12", "schema": "INV7"},
        })
        self.assertEqual(record.to_dict()["compatibility"], {
            "engine": "ME12", "schema": "INV7",
        })

    def test_store_repairs_corrupt_object_and_rejects_wrong_size(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "artifact.bin"
            source.write_bytes(b"recovery tooling")
            record = ArtifactRecord(
                artifact_id="recovery", artifact_type="recovery_tooling",
                content_hash=hashlib.sha256(source.read_bytes()).hexdigest(),
                size=source.stat().st_size,
            )
            archive = ContentAddressedArchive(Path(tmp) / "archive")
            destination = archive.store(source, record)
            destination.write_bytes(b"partial")
            self.assertEqual(archive.store(source, record), destination)
            self.assertTrue(archive.verify(record)["passed"])
            wrong_size = ArtifactRecord(**{**record.__dict__, "size": record.size + 1})
            with self.assertRaisesRegex(ValueError, "size mismatch"):
                archive.store(source, wrong_size)

    def test_manifest_signature_binds_the_entire_sorted_artifact_set(self) -> None:
        record = ArtifactRecord(
            artifact_id="baseline", artifact_type="baseline_manifest",
            content_hash="a" * 64, size=5,
        )
        manifest = ArtifactManifest((record,), signed_by="AABBCC", signature="sig")
        payload = canonical_bytes(manifest.payload())
        envelope = manifest.to_dict()
        loaded = ArtifactManifest.from_dict(envelope)
        self.assertTrue(loaded.verify(
            lambda _signer, signed, signature: signed == payload and signature == "sig",
            {"aabbcc"},
        )["passed"])

        altered = dict(envelope)
        altered["artifacts"] = [dict(envelope["artifacts"][0], size=6)]
        tampered = ArtifactManifest.from_dict(altered)
        self.assertFalse(tampered.verify(
            lambda _signer, signed, _signature: signed == payload,
            {"AABBCC"},
        )["passed"])
        self.assertFalse(loaded.verify(lambda *_: True, {"DDEEFF"})["passed"])


if __name__ == "__main__":
    unittest.main()
