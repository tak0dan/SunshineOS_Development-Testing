"""Regression tests for the local external-CI policy auditor."""

import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path

from ci_policy_audit import audit_workflow, main, workflows


class CiPolicyAuditTests(unittest.TestCase):
    def test_ci_005_arch2015_sysv_workflow_is_present_and_policy_clean(self):
        """CI_005: the focused legacy-init suite is wired into read-only CI."""
        repository = Path(__file__).resolve().parents[2]
        workflow = repository / ".github/workflows/arch2015-sysvinit.yml"
        self.assertTrue(workflow.is_file(), "Arch 2015 SysV CI workflow is missing")
        self.assertEqual([], audit_workflow(workflow))
        contents = workflow.read_text(encoding="utf-8")
        self.assertIn("test_arch2015_sysvinit", contents)
        self.assertIn("test_sysvinit_inventory", contents)
        self.assertIn("test_sysvinit_repair", contents)

    def test_ci_006_arch2026_systemd_workflow_is_present_and_policy_clean(self):
        """CI_006: systemd inventory, repair, discovery and compatibility run in CI."""
        repository = Path(__file__).resolve().parents[2]
        workflow = repository / ".github/workflows/arch2026-systemd.yml"
        self.assertTrue(workflow.is_file(), "Arch 2026 systemd CI workflow is missing")
        self.assertEqual([], audit_workflow(workflow))
        contents = workflow.read_text(encoding="utf-8")
        for suite in (
            "tests.test_systemd_inventory",
            "tests.test_systemd_repair",
            "tests.test_discovery",
            "tests.test_compatibility",
        ):
            with self.subTest(suite=suite):
                self.assertIn(suite, contents)
        self.assertIn("pull_request:", contents)
        self.assertIn("push:", contents)

    def test_ci_007_endeavouros_regressions_are_wired_and_policy_clean(self):
        """CI_007: EndeavourOS lineage and package ownership checks run in read-only CI."""
        repository = Path(__file__).resolve().parents[2]
        workflow = repository / ".github/workflows/endeavouros.yml"
        self.assertTrue(workflow.is_file(), "EndeavourOS CI workflow is missing")
        self.assertEqual([], audit_workflow(workflow))
        contents = workflow.read_text(encoding="utf-8")
        for suite in (
            "tests.test_compatibility",
            "tests.test_discovery",
            "tests.test_source_matrix",
        ):
            with self.subTest(suite=suite):
                self.assertIn(suite, contents)
        self.assertIn("pull_request:", contents)
        self.assertIn("push:", contents)
        self.assertIn("contents: read", contents)

    def test_ci_001_flags_mutable_actions_broad_write_and_fork_trigger(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "workflow.yml"
            path.write_text(
                "on:\n  pull_request_target:\njobs:\n  build:\n    permissions:\n"
                "      contents: write\n    steps:\n      - uses: example/action@v1\n",
                encoding="utf-8",
            )
            findings = audit_workflow(path)
        self.assertEqual(3, len(findings))
        self.assertTrue(any("pull_request_target" in item for item in findings))
        self.assertTrue(any("full commit SHA" in item for item in findings))
        self.assertTrue(any("write permission" in item for item in findings))

    def test_ci_002_accepts_sha_pinned_read_only_workflow(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "workflow.yml"
            path.write_text(
                "on:\n  pull_request:\njobs:\n  build:\n"
                "    permissions:\n      contents: read\n    steps:\n"
                "      - uses: example/action@0123456789abcdef0123456789abcdef01234567\n",
                encoding="utf-8",
            )
            self.assertEqual([], audit_workflow(path))

    def test_ci_003_distinguishes_absent_workflow_tree(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual([], workflows(Path(tmp)))

    def test_ci_004_absent_workflow_tree_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = StringIO()
            with redirect_stdout(output):
                status = main(["ci_policy_audit.py", tmp])
        self.assertEqual(1, status)
        self.assertIn("NO_WORKFLOWS", output.getvalue())
        self.assertIn("REVIEW_REQUIRED", output.getvalue())


if __name__ == "__main__":
    unittest.main()
