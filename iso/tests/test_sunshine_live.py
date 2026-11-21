from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "iso" / "tools"))
sys.path.insert(0, str(REPO / "evolution-engine"))

import sunshine_live as sl  # noqa: E402


class FakeRoot:
    def __init__(self, base: Path):
        self.base = base
        (base / "etc").mkdir(parents=True, exist_ok=True)
        (base / "boot").mkdir(exist_ok=True)
        (base / "var/lib/pacman").mkdir(parents=True, exist_ok=True)
        (base / "proc").mkdir(exist_ok=True)
        (base / "proc/meminfo").write_text("MemTotal: 8000000 kB\nMemAvailable: 4000000 kB\n")
        (base / "proc/loadavg").write_text("1.25 1.10 1.00 1/100 1234\n")
        (base / "etc/os-release").write_text('ID=arch\nID_LIKE="arch"\nPRETTY_NAME="Test Root"\n')


def result(argv: list[str], rc: int = 0, stdout: str = "", stderr: str = "") -> dict:
    return {"argv": list(argv), "rc": rc, "stdout": stdout, "stderr": stderr, "timed_out": False}


class ToolkitTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        self.root = self.base / "root"
        FakeRoot(self.root)
        self.calls: list[list[str]] = []
        os.environ["SUNSHINE_STATE_DIR"] = str(self.base / "state")
        os.environ["SUNSHINE_LOG_DIR"] = str(self.base / "log")
        os.environ["SUNSHINE_ENGINE_DIR"] = str(REPO / "evolution-engine")
        os.environ["SUNSHINE_ALLOW_UNPRIVILEGED_TEST"] = "1"
        self.addCleanup(self._clean_env)

    def _clean_env(self):
        for key in ("SUNSHINE_STATE_DIR", "SUNSHINE_LOG_DIR", "SUNSHINE_ENGINE_DIR",
                    "SUNSHINE_ALLOW_UNPRIVILEGED_TEST"):
            os.environ.pop(key, None)

    def runner(self, table: dict[str, dict] | None = None):
        table = table or {}

        def run(argv: list[str], timeout: int) -> dict:
            self.calls.append(list(argv))
            for pattern, response in table.items():
                if all(token in argv for token in pattern.split()):
                    return response
            if argv[0] == "uname":
                return result(argv, stdout="Linux test 7.3.5 #1 SMP x86_64")
            if argv[0] == "findmnt":
                return result(argv, stdout="/dev/nvme0n1p2 / btrfs rw,relatime")
            if argv[0] == "pacman" and argv[1:] == ["-Q"]:
                return result(argv, stdout="base-1.0-1\nlinux-7.3.5-1\n")
            if argv[0] == "pacman" and argv[1:] == ["-Qu"]:
                return result(argv, stdout="python-3.15-1 -> 3.15.1-1\n")
            if argv[0] == "pacman" and argv[1:] == ["-Qk"]:
                return result(argv, stdout="python: /usr/lib/python3.14/x.py: No such file or directory\n")
            if argv[0] == "pacman" and "-Syu" in argv:
                return result(argv, stdout=":: Starting full system upgrade...\n")
            if argv[0] == "timedatectl":
                return result(argv, stdout="yes\n")
            if argv[0] == "snapper" and "list" in argv:
                return result(argv, stdout="12\n13\n")
            if argv[0] == "snapper" and "create" in argv:
                return result(argv, stdout="Created snapshot with id '42'\n")
            if argv[0] == "pgrep":
                return result(argv, rc=1)
            if argv[0] == "steamos-readonly":
                return result(argv, stdout="enabled\n")
            if argv[0] == "steamos-devmode":
                return result(argv, stdout="disabled\n")
            if argv[0] == "python3" or argv[0].endswith("python3"):
                return result(argv, stdout='{"healthy": true, "checks": []}')
            return result(argv)

        return run

    def test_health_collects_facts_without_mutation(self):
        report = sl.health(self.root, self.runner(), deep=False)
        self.assertEqual(report["facts"]["os_release"]["ID"], "arch")
        self.assertEqual(report["facts"]["installed_packages"], 2)
        self.assertTrue(any(item["name"] == "disk-space" for item in report["evidence"]))
        self.assertFalse(any(" -S" in " ".join(call) for call in self.calls))

    def test_sanity_blocks_readonly_root(self):
        runner = self.runner({"findmnt -no": result([], stdout="/dev/root / btrfs ro,relatime")})
        report = sl.sanity(self.root, runner)
        self.assertEqual(report["status"], "fail")
        self.assertTrue(any(item["name"] == "root-mount" and item["status"] == "fail"
                            for item in report["evidence"]))

    def test_sanity_fails_closed_on_missing_trust(self):
        report = sl.sanity(self.root, self.runner(), trust={"index": "missing.json", "policy": "", "keyring": ""})
        self.assertEqual(report["status"], "fail")
        self.assertTrue(any(item["name"] == "trust-policy" and item["status"] == "fail"
                            for item in report["evidence"]))

    def test_update_preview_never_mutates(self):
        args = sl.build_parser().parse_args(["--root", str(self.root), "update"])
        report = sl.cmd_update(args, self.runner())
        self.assertEqual(report["status"], "preview")
        self.assertFalse(any("-Syu" in call for call in self.calls))

    def test_update_apply_is_blocked_without_snapshot(self):
        args = sl.build_parser().parse_args(["--root", str(self.root), "update", "--apply"])
        failing = self.runner({
            "findmnt -no": result([], stdout="/dev/root / btrfs rw,relatime"),
            "snapper create": result([], rc=1, stderr="no snapshots configured"),
        })
        report = sl.cmd_update(args, failing)
        self.assertEqual(report["status"], "blocked")
        self.assertFalse(any("-Syu" in call for call in self.calls))

    def test_update_apply_journals_and_updates_when_explicit(self):
        args = sl.build_parser().parse_args([
            "--root", str(self.root), "update", "--apply", "--allow-no-snapshot",
        ])
        report = sl.cmd_update(args, self.runner())
        self.assertEqual(report["status"], "pass")
        self.assertTrue(any("-Syu" in call for call in self.calls))
        journal = self.base / "log" / "journal.jsonl"
        self.assertTrue(journal.is_file())
        record = json.loads(journal.read_text().splitlines()[-1])
        self.assertEqual(record["command"], "update")
        self.assertTrue(record["apply"])

    def test_engine_plan_argv_binds_trust_and_fixture(self):
        index = self.base / "index.json"
        policy = self.base / "policy.json"
        keyring = self.base / "keyring.gpg"
        for path in (index, policy, keyring):
            path.write_text("{}")
        args = sl.build_parser().parse_args([
            "--root", str(self.root), "--state-root", str(self.base / "state"),
            "--trust-index", str(index), "--trust-policy", str(policy),
            "--trust-keyring", str(keyring), "--fixture", "clean-arch",
            "upgrade",
        ])
        argv, directory = sl.engine_argv(args, "plan")
        self.assertIn("--plan", argv)
        self.assertIn("--fixture", argv)
        self.assertNotIn("--root", argv)
        self.assertIn(str(index), argv)
        self.assertEqual(directory, REPO / "evolution-engine")

    def test_repair_defaults_to_assessment_only(self):
        args = sl.build_parser().parse_args(["--root", str(self.root), "repair"])
        report = sl.cmd_repair(args, self.runner())
        self.assertEqual(report["status"], "assessment")
        self.assertFalse(report["assessment"]["slot_activation"]["evaluated"])
        self.assertFalse(any("-S" in call and "-Syu" not in call for call in self.calls))

    def test_servicing_assessment_consumes_only_valid_evidence(self):
        evidence = self.base / "servicing"
        evidence.mkdir()
        commands = {
            "dism-checkhealth": ["DISM", "/Online", "/Cleanup-Image", "/CheckHealth"],
            "dism-scanhealth": ["DISM", "/Online", "/Cleanup-Image", "/ScanHealth"],
            "sfc-verifyonly": ["sfc", "/verifyonly"],
        }
        for name, command in commands.items():
            (evidence / f"{name}.json").write_text(json.dumps({
                "name": name, "command": command, "return_code": 0,
                "output": "No component store corruption detected."
                if "dism" in name else "Windows Resource Protection did not find any integrity violations.",
            }))
        (evidence / "reboot-pending.json").write_text(json.dumps({"pending": False}))
        report = sl._servicing_assessment(str(evidence))
        self.assertTrue(report["collected"])
        self.assertTrue(report["healthy"])
        self.assertFalse(report["blocked"])

    def test_parse_missing_packages(self):
        text = "python: /usr/lib/x.py: No such file or directory\nother: warning: mismatch\n"
        self.assertEqual(sl.parse_missing_packages(text), ["other", "python"])

    def test_rescue_is_read_only_and_uses_arch_native_evidence(self):
        (self.root / "boot" / "vmlinuz-linux").write_text("kernel")
        (self.root / "boot" / "initramfs-linux.img").write_text("initramfs")
        (self.root / "boot" / "loader").mkdir()
        (self.root / "boot" / "loader" / "loader.conf").write_text("default arch.conf\n")
        runner = self.runner({
            "pacman -Dk": result([], stdout="checking dependencies...\n"),
            "pacman -Qk": result([], stdout="base: 2 total files, 0 missing files\n"),
            "systemd-analyze verify": result([], stdout=""),
        })
        args = sl.build_parser().parse_args([
            "--root", str(self.root), "rescue", "--reboot-state", "settled",
        ])
        report = sl.cmd_rescue(args, runner)
        self.assertEqual(report["status"], "pass")
        self.assertTrue(report["assessment"]["healthy"])
        self.assertFalse(report["assessment"]["blocked"])
        self.assertTrue(report["assessment"]["safe_to_mutate"])
        self.assertFalse(any("-S" in call for call in self.calls))
        self.assertFalse(any("rm" in call for call in self.calls))

    def test_rescue_fails_closed_without_explicit_reboot_state(self):
        args = sl.build_parser().parse_args(["--root", str(self.root), "rescue"])
        report = sl.cmd_rescue(args, self.runner())
        self.assertEqual(report["status"], "blocked")
        self.assertTrue(report["assessment"]["blocked"])
        self.assertFalse(report["assessment"]["safe_to_mutate"])

    def test_rescue_marks_degraded_evidence_as_blocked(self):
        (self.root / "boot" / "vmlinuz-linux").write_text("kernel")
        runner = self.runner({
            "pacman -Dk": result([], stdout="checking dependencies...\n"),
            "pacman -Qk": result([], stdout="base: 1 total files, 0 missing files\n"),
            "systemd-analyze verify": result([], stdout=""),
        })
        args = sl.build_parser().parse_args([
            "--root", str(self.root), "rescue", "--reboot-state", "settled",
        ])
        report = sl.cmd_rescue(args, runner)
        self.assertEqual(report["status"], "blocked")
        self.assertTrue(report["assessment"]["degraded"])
        self.assertFalse(report["assessment"]["safe_to_mutate"])

    def test_repair_never_deletes_a_pacman_lock(self):
        lock = self.root / "var" / "lib" / "pacman" / "db.lck"
        lock.parent.mkdir(parents=True, exist_ok=True)
        lock.write_text("999999\n")
        args = sl.build_parser().parse_args([
            "--root", str(self.root), "repair", "--apply", "--allow-no-snapshot",
            "--fix-lock", "--reboot-state", "settled",
        ])
        report = sl.cmd_repair(args, self.runner())
        self.assertEqual(report["status"], "blocked")
        self.assertTrue(lock.is_file())
        self.assertFalse(any("rm" in call for call in self.calls))
        self.assertTrue(report["actions"][0]["skipped"])

    def test_report_includes_arch_native_rescue_assessment(self):
        args = sl.build_parser().parse_args(["--root", str(self.root), "report"])
        report = sl.cmd_report(args, self.runner())
        rescue = report["repair"]["assessment"]["arch_native_rescue"]
        self.assertTrue(rescue["collected"])
        self.assertIn("assessment", rescue)
        self.assertFalse(report["repair"]["assessment"]["windows_servicing"]["collected"])

    def test_report_runs_with_minimal_arguments(self):
        args = sl.build_parser().parse_args(["--root", str(self.root), "report"])
        report = sl.cmd_report(args, self.runner())
        self.assertIn("health", report)
        self.assertIn("sanity", report)
        self.assertEqual(report["repair"]["status"], "assessment")
        self.assertFalse(hasattr(args, "apply"))

    def test_migrate_arch_apply_accepts_arch_identity(self):
        index = self.base / "index.json"
        policy = self.base / "policy.json"
        keyring = self.base / "keyring.gpg"
        for path in (index, policy, keyring):
            path.write_text("{}\n")
        args = sl.build_parser().parse_args([
            "--root", str(self.root), "--state-root", str(self.base / "state"),
            "--trust-index", str(index), "--trust-policy", str(policy),
            "--trust-keyring", str(keyring),
            "migrate", "--apply", "--allow-no-snapshot", "--source", "arch",
        ])
        report = sl.cmd_migrate(args, self.runner())
        self.assertEqual(report["status"], "pass")
        self.assertTrue(all(item["status"] != "fail" for item in report["sanity"]["evidence"]))
        self.assertTrue(any(item["name"] == "os-identity" and item["status"] == "pass"
                            for item in report["sanity"]["evidence"]))

    def test_migrate_accepts_legacy_sunshineos_identity(self):
        (self.root / "etc/os-release").write_text(
            'NAME="Sunshine OS"\nID=sunshineos\nID_LIKE="arch"\nPRETTY_NAME="Sunshine OS"\n')
        args = sl.build_parser().parse_args([
            "--root", str(self.root), "--state-root", str(self.base / "state"),
            "--fixture", "clean-arch", "migrate", "--source", "sunshine",
        ])
        report = sl.cmd_migrate(args, self.runner())
        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["detected_id"], "sunshineos")


if __name__ == "__main__":
    unittest.main()
