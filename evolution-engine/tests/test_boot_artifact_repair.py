"""Fail-closed boot artifact assessment tests (CachyOS repair research)."""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ENGINE_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ENGINE_ROOT))

from src.evolution.tools.boot_artifact_repair import assess_boot_artifacts  # noqa: E402


class BootArtifactRepairTests(unittest.TestCase):
    def test_T_CACHYOS_BOOT_REPAIR_001_requires_every_artifact(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            kernel = root / "boot/vmlinuz-linux-cachyos"
            kernel.parent.mkdir()
            kernel.write_bytes(b"kernel")
            result = assess_boot_artifacts(root, ["boot/vmlinuz-linux-cachyos", "boot/initramfs-linux-cachyos.img"])
        self.assertTrue(result.complete)
        self.assertFalse(result.repairable)
        self.assertEqual([item.state for item in result.findings], ["present", "missing"])

    def test_T_CACHYOS_BOOT_REPAIR_002_empty_generated_image_is_degraded(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            image = root / "boot/initramfs-linux-cachyos.img"
            image.parent.mkdir()
            image.touch()
            result = assess_boot_artifacts(root, ["boot/initramfs-linux-cachyos.img"])
        self.assertEqual(result.findings[0].state, "empty")
        self.assertFalse(result.repairable)

    def test_T_CACHYOS_BOOT_REPAIR_003_escaping_symlink_fails_closed(self):
        with tempfile.TemporaryDirectory() as temporary, tempfile.TemporaryDirectory() as outside:
            root = Path(temporary)
            artifact = root / "boot/vmlinuz-linux"
            artifact.parent.mkdir()
            artifact.symlink_to(Path(outside) / "kernel")
            result = assess_boot_artifacts(root, ["boot/vmlinuz-linux"])
        self.assertFalse(result.complete)
        self.assertEqual(result.findings[0].state, "unsafe")

    def test_T_CACHYOS_BOOT_REPAIR_004_rejects_traversal_and_empty_request(self):
        with tempfile.TemporaryDirectory() as temporary:
            traversal = assess_boot_artifacts(temporary, ["../etc/passwd"])
            empty = assess_boot_artifacts(temporary, [])
        self.assertFalse(traversal.complete)
        self.assertFalse(empty.complete)
        self.assertFalse(traversal.repairable)


if __name__ == "__main__":
    unittest.main()
