"""Regression tests for fail-closed package lock assessment."""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from pacman_lock_repair import assess_pacman_lock


class PacmanLockRepairTests(unittest.TestCase):
    def test_GARUDA_REPAIR_001_missing_lock_is_reported_without_mutation(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            result = assess_pacman_lock(root / "db.lck", root / "proc")
            self.assertEqual(result.state, "missing")
            self.assertFalse(result.repair_allowed)

    def test_GARUDA_REPAIR_002_live_package_manager_blocks_repair(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            lock = root / "db.lck"
            lock.touch()
            proc = root / "proc" / "123"
            proc.mkdir(parents=True)
            (proc / "comm").write_text("pacman\n")
            result = assess_pacman_lock(lock, root / "proc")
            self.assertEqual(result.state, "active-owner")
            self.assertEqual(result.owners, (123,))
            self.assertTrue(lock.exists())
            self.assertFalse(result.repair_allowed)

    def test_GARUDA_REPAIR_003_ownerless_lock_is_candidate_not_authorization(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            lock = root / "db.lck"
            lock.touch()
            (root / "proc").mkdir()
            result = assess_pacman_lock(lock, root / "proc")
            self.assertEqual(result.state, "stale-candidate")
            self.assertTrue(lock.exists())
            self.assertFalse(result.repair_allowed)

    def test_GARUDA_REPAIR_004_unavailable_process_table_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            lock = root / "db.lck"
            lock.touch()
            result = assess_pacman_lock(lock, root / "missing-proc")
            self.assertEqual(result.state, "owner-unknown")
            self.assertFalse(result.repair_allowed)


if __name__ == "__main__":
    unittest.main()
