"""Snapshot cleanup is path-confined and journal-integrity checked."""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.evolution.release import content_digest  # noqa: E402
from src.evolution.tools.snapshots import SnapshotManager  # noqa: E402


class SnapshotManagerSafetyTests(unittest.TestCase):
    def test_prune_uses_backend_specific_operations(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            calls = []

            def execute(argv):
                calls.append(list(argv))
                if argv[0] == "btrfs" and argv[2] == "snapshot":
                    Path(argv[-1]).parent.mkdir(parents=True, exist_ok=True)
                    Path(argv[-1]).write_bytes(b"snapshot")
                elif argv[0] == "tar":
                    Path(argv[argv.index("-cf") + 1]).write_bytes(b"archive")
                return 0, "", ""

            manager = SnapshotManager(Path(tmp) / "state", executor=execute, can_snapshot=True)
            manager.create("/rootfs", "before", backend="btrfs")
            manager.create("/rootfs", "after", backend="tar")
            self.assertEqual(manager.prune(keep=3), [])
            self.assertFalse(any(argv[:3] == ["btrfs", "subvolume", "delete"] for argv in calls))
            manager.prune(keep=1)
            self.assertIn(["btrfs", "subvolume", "delete", str(
                Path(tmp) / "state/snapshots/before.btrfs"
            )], calls)

    def test_modified_journal_cannot_redirect_prune_outside_snapshot_root(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            state = Path(tmp) / "state"
            state.mkdir()
            journal = {
                "format": "sunshine-snapshot-journal-2",
                "snapshots": [{
                    "name": "owned", "path": "/etc/passwd", "backend": "tar",
                    "source": "/rootfs", "created_at": "now", "metadata": {},
                }],
            }
            journal["digest"] = content_digest(journal)
            (state / "snapshots.json").write_text(json.dumps(journal), encoding="utf-8")
            calls = []
            manager = SnapshotManager(state, executor=lambda argv: calls.append(list(argv)) or (0, "", ""))
            with self.assertRaisesRegex(ValueError, "escapes snapshot storage"):
                manager.prune(keep=0)
            self.assertEqual(calls, [])

    def test_v2_digest_tampering_and_unsafe_snapshot_names_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            manager = SnapshotManager(Path(tmp) / "state", executor=lambda _argv: (0, "", ""))
            with self.assertRaisesRegex(ValueError, "invalid or duplicate"):
                manager.create("/rootfs", "../escape")
            manager._save([])
            stored = json.loads(manager.record_path.read_text(encoding="utf-8"))
            stored["snapshots"].append({"name": "x", "path": "/etc/passwd", "backend": "tar"})
            manager.record_path.write_text(json.dumps(stored), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "digest is missing or invalid"):
                manager.list()


if __name__ == "__main__":
    unittest.main()
