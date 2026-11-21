"""Regression tests for the local external-CI policy auditor."""

import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path

from ci_policy_audit import audit_workflow, main, workflows


class CiPolicyAuditTests(unittest.TestCase):
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
