"""CLI-level coverage for read-only Arch rescue assessment."""
from __future__ import annotations

import contextlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.engine import main  # noqa: E402
from src.evolution.tools.arch_rescue import REQUIRED_PROBES  # noqa: E402


def clean_evidence() -> dict:
    return {
        "schema": 1,
        "probes": {
            "pacman-db-check": {
                "name": "pacman-db-check",
                "command": list(REQUIRED_PROBES["pacman-db-check"]),
                "return_code": 0,
                "output": "checking dependencies...\n",
            },
            "pacman-file-check": {
                "name": "pacman-file-check",
                "command": list(REQUIRED_PROBES["pacman-file-check"]),
                "return_code": 0,
                "output": "base: 12 total files, 0 missing files\n",
            },
            "systemd-unit-verify": {
                "name": "systemd-unit-verify",
                "command": list(REQUIRED_PROBES["systemd-unit-verify"]),
                "return_code": 0,
                "output": "",
            },
        },
        "observations": {
            "boot-artifacts": {
                "kernel_present": True,
                "initramfs_present": True,
                "bootloader_config_present": True,
                "boot_entries_present": True,
            },
            "lock_state": "missing",
            "snapshot_available": True,
            "pending_reboot": False,
        },
    }


def write_evidence(directory: str | Path, payload: dict, name: str = "captured.json") -> str:
    path = Path(directory) / name
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return str(path)


def run_cli(*args: str) -> tuple[int, str, str]:
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = main(list(args))
    return code, out.getvalue(), err.getvalue()


class CliRescueTests(unittest.TestCase):
    def test_healthy_captured_evidence(self) -> None:
        with tempfile.TemporaryDirectory(prefix="sunshine-rescue-") as tmp:
            evidence = write_evidence(tmp, clean_evidence())
            code, out, err = run_cli("--rescue", "--rescue-evidence", evidence)
        self.assertEqual(code, 0, err)
        report = json.loads(out)
        self.assertTrue(report["healthy"])
        self.assertTrue(report["safe_to_mutate"])
        self.assertFalse(report["degraded"])
        self.assertFalse(report["blocked"])
        self.assertEqual([item["status"] for item in report["findings"]], ["healthy"] * 7)
        self.assertEqual(report["source"], f"file:{evidence}")
        self.assertEqual(report["lock"], None)

    def test_missing_probe_fails_closed(self) -> None:
        evidence_data = clean_evidence()
        del evidence_data["probes"]["pacman-file-check"]
        with tempfile.TemporaryDirectory(prefix="sunshine-rescue-") as tmp:
            evidence = write_evidence(tmp, evidence_data)
            code, out, err = run_cli("--rescue", "--rescue-evidence", evidence)
        self.assertEqual(code, 1, err)
        report = json.loads(out)
        self.assertFalse(report["healthy"])
        self.assertTrue(report["blocked"])
        self.assertEqual(report["findings"][1]["status"], "unknown")
        self.assertIn("required probe is missing", report["findings"][1]["detail"])

    def test_missing_files_degrade(self) -> None:
        evidence_data = clean_evidence()
        evidence_data["probes"]["pacman-file-check"]["output"] = (
            "python: /usr/lib/python3.14/x.py: 2 missing files\n"
        )
        with tempfile.TemporaryDirectory(prefix="sunshine-rescue-") as tmp:
            evidence = write_evidence(tmp, evidence_data)
            code, out, err = run_cli("--rescue", "--rescue-evidence", evidence)
        self.assertEqual(code, 1, err)
        report = json.loads(out)
        self.assertTrue(report["degraded"])
        self.assertEqual(report["findings"][1]["status"], "degraded")
        self.assertFalse(report["healthy"])

    def test_pending_reboot_blocks(self) -> None:
        evidence_data = clean_evidence()
        evidence_data["observations"]["pending_reboot"] = True
        with tempfile.TemporaryDirectory(prefix="sunshine-rescue-") as tmp:
            evidence = write_evidence(tmp, evidence_data)
            code, out, err = run_cli("--rescue", "--rescue-evidence", evidence)
        self.assertEqual(code, 1, err)
        report = json.loads(out)
        self.assertTrue(report["blocked"])
        self.assertEqual(report["findings"][-1]["status"], "blocked")
        self.assertFalse(report["safe_to_mutate"])

    def test_lock_never_authorizes_deletion(self) -> None:
        with tempfile.TemporaryDirectory(prefix="sunshine-rescue-lock-") as tmp:
            lock = Path(tmp) / "var/lib/pacman/db.lck"
            proc = Path(tmp) / "proc/4242"
            lock.parent.mkdir(parents=True)
            proc.mkdir(parents=True)
            lock.write_text("4242\n", encoding="utf-8")
            (proc / "comm").write_text("pacman\n", encoding="utf-8")
            evidence_data = clean_evidence()
            del evidence_data["observations"]["lock_state"]
            evidence_data["lock"] = {
                "lock_path": "var/lib/pacman/db.lck",
                "proc_root": "proc",
            }
            evidence = write_evidence(tmp, evidence_data)
            code, out, err = run_cli("--rescue", "--rescue-evidence", evidence)
            self.assertTrue(lock.exists(), "assessment must not remove the lock")
        self.assertEqual(code, 1, err)
        report = json.loads(out)
        self.assertEqual(report["lock"]["state"], "active-owner")
        self.assertFalse(report["lock"]["repair_allowed"])
        self.assertEqual(report["findings"][4]["status"], "blocked")
        self.assertFalse(report["safe_to_mutate"])

    def test_no_mutating_subprocess_call(self) -> None:
        with tempfile.TemporaryDirectory(prefix="sunshine-rescue-") as tmp:
            evidence = write_evidence(tmp, clean_evidence())
            with mock.patch("src.engine.subprocess.run",
                            side_effect=AssertionError("rescue must not run commands")) as run:
                with mock.patch("src.engine.subprocess.Popen",
                                side_effect=AssertionError("rescue must not run commands")):
                    code, out, err = run_cli("--rescue", "--rescue-evidence", evidence)
        self.assertEqual(code, 0, err)
        self.assertEqual(json.loads(out)["healthy"], True)
        run.assert_not_called()

    def test_fixture_evidence_is_healthy_and_side_effect_free(self) -> None:
        with tempfile.TemporaryDirectory(prefix="sunshine-rescue-fixture-") as tmp:
            with mock.patch("src.engine.subprocess.run",
                            side_effect=AssertionError("rescue must not run commands")):
                code, out, err = run_cli(
                    "--fixture", "clean-arch", "--state-root", tmp, "--rescue",
                )
            self.assertEqual(list(Path(tmp).iterdir()), [])
        self.assertEqual(code, 0, err)
        report = json.loads(out)
        self.assertTrue(report["healthy"])
        self.assertEqual(report["source"], "fixture:clean-arch")
        self.assertTrue(report["root_observation"]["bootloader_config_present"])

    def test_explicit_root_supplies_boot_observations(self) -> None:
        with tempfile.TemporaryDirectory(prefix="sunshine-rescue-root-") as tmp:
            boot = Path(tmp) / "boot/grub"
            boot.mkdir(parents=True)
            (boot.parent / "vmlinuz-linux").write_text("kernel", encoding="utf-8")
            (boot.parent / "initramfs-linux.img").write_text("initramfs", encoding="utf-8")
            (boot / "grub.cfg").write_text("menuentry arch {}\n", encoding="utf-8")
            evidence_data = clean_evidence()
            del evidence_data["observations"]["boot-artifacts"]
            evidence = write_evidence(tmp, evidence_data)
            code, out, err = run_cli(
                "--rescue", "--root", tmp, "--rescue-evidence", evidence,
            )
        self.assertEqual(code, 0, err)
        report = json.loads(out)
        self.assertTrue(report["healthy"])
        self.assertTrue(report["root_observation"]["kernel_present"])
        self.assertEqual(report["findings"][3]["status"], "healthy")

    def test_no_evidence_fails_closed(self) -> None:
        code, out, err = run_cli("--rescue")
        self.assertEqual(code, 1, err)
        report = json.loads(out)
        self.assertFalse(report["evidence_loaded"])
        self.assertFalse(report["healthy"])
        self.assertTrue(report["blocked"])
        self.assertEqual(
            [item["status"] for item in report["findings"]], ["unknown"] * 7,
        )
        self.assertTrue(report["errors"])

    def test_missing_evidence_file_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory(prefix="sunshine-rescue-") as tmp:
            missing = str(Path(tmp) / "absent.json")
            code, out, err = run_cli("--rescue", "--rescue-evidence", missing)
        self.assertEqual(code, 1, err)
        report = json.loads(out)
        self.assertFalse(report["healthy"])
        self.assertTrue(report["blocked"])
        self.assertEqual(report["findings"][0]["status"], "unknown")
        self.assertTrue(any("cannot read" in item for item in report["errors"]))


if __name__ == "__main__":
    unittest.main()
