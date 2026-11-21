from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "iso" / "tools"))

import stage_profile  # noqa: E402


class StageProfileTests(unittest.TestCase):
    def test_stage_copies_engine_toolkit_and_wrappers(self):
        with tempfile.TemporaryDirectory() as tmp:
            staged = Path(tmp) / "staged"
            result = stage_profile.stage(REPO, REPO / "iso/profile/sunshine", staged,
                                         build_id="test-build")
            self.assertTrue(result["validation"]["ok"], result["validation"])
            self.assertTrue((staged / "airootfs/opt/sunshine/evolution-engine/src/engine.py").is_file())
            self.assertTrue((staged / "airootfs/usr/local/lib/sunshine/sunshine_live.py").is_file())
            self.assertTrue((staged / "airootfs/usr/share/sunshine/os-release").is_file())
            for name in stage_profile.SUBCOMMANDS:
                wrapper = staged / "airootfs/usr/local/bin" / f"sunshine-{name}"
                self.assertTrue(wrapper.is_file())
                self.assertTrue(os.access(wrapper, os.X_OK))
            dispatcher = staged / "airootfs/usr/local/bin/sunshine-live"
            self.assertIn('sunshine_live.py "$@"', dispatcher.read_text())
            info = json.loads((staged / "airootfs/usr/share/sunshine/BUILD_INFO.json").read_text())
            self.assertEqual(info["build_id"], "test-build")
            self.assertEqual(info["commands"], [f"sunshine-{n}" for n in stage_profile.SUBCOMMANDS])
            self.assertFalse(any(p.name == "__pycache__" for p in staged.rglob("*")))

    def test_engine_target_package_is_staged(self):
        with tempfile.TemporaryDirectory() as tmp:
            staged = Path(tmp) / "staged"
            result = stage_profile.stage(REPO, REPO / "iso/profile/sunshine", staged,
                                         build_id="test-build")
            self.assertTrue(result["validation"]["ok"], result["validation"])
            engine = staged / "airootfs/opt/sunshine/evolution-engine"
            self.assertTrue((engine / "src/target/__init__.py").is_file())
            self.assertTrue((engine / "src/target/resolver.py").is_file())
            self.assertFalse((engine / "bootstrap-rust/target").exists())

            state = Path(tmp) / "state"
            state.mkdir()
            env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}
            proc = subprocess.run(
                [sys.executable, str(engine / "src/engine.py"),
                 "--state-root", str(state), "--fixture", "clean-arch", "--plan"],
                cwd=engine, env=env, capture_output=True, text=True, timeout=180)
            self.assertEqual(proc.returncode, 0, proc.stderr)

    def test_validation_detects_missing_wrapper(self):
        with tempfile.TemporaryDirectory() as tmp:
            staged = Path(tmp) / "staged"
            stage_profile.stage(REPO, REPO / "iso/profile/sunshine", staged, build_id="test-build")
            (staged / "airootfs/usr/local/bin/sunshine-repair").unlink()
            validation = stage_profile.validate(staged)
            self.assertFalse(validation["ok"])
            self.assertIn("/usr/local/bin/sunshine-repair", " ".join(validation["missing"]))


if __name__ == "__main__":
    unittest.main()
