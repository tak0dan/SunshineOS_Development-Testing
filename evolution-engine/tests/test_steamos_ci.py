"""Guard the CI coverage and least-privilege policy for SteamOS regressions."""
from __future__ import annotations

import re
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = REPO_ROOT / ".github/workflows/steamos-regressions.yml"


class SteamOSCiWorkflowTests(unittest.TestCase):
    def test_STEAMOS_CI_001_runs_staging_activation_and_repair_regressions(self) -> None:
        text = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("test_steam_os_ab_*.py", text)
        self.assertIn("test_steamos_repair.py", text)

    def test_STEAMOS_CI_002_uses_read_only_permissions_and_immutable_checkout(self) -> None:
        text = WORKFLOW.read_text(encoding="utf-8")
        self.assertRegex(text, r"(?m)^permissions:\n  contents: read\s*$")
        checkout_refs = re.findall(r"(?m)^\s*- uses: actions/checkout@([^\s#]+)", text)
        self.assertEqual(len(checkout_refs), 1)
        self.assertRegex(checkout_refs[0], r"^[0-9a-f]{40}$")
        self.assertNotRegex(text, r"(?m)^\s*(?:contents|packages|id-token): write\s*$")

    def test_STEAMOS_CI_003_audits_workflow_trust_policy(self) -> None:
        text = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("autonomy/codex/ci_policy_audit.py .", text)


if __name__ == "__main__":
    unittest.main()
