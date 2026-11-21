#!/usr/bin/env python3
"""Small, dependency-free audit for GitHub Actions trust-boundary mistakes."""

from __future__ import annotations

import re
import sys
from pathlib import Path


SHA_ACTION = re.compile(r"^\s*(?:-\s*)?uses:\s*[^#\s]+@([0-9a-fA-F]{40})(?:\s+#.*)?$")
USES_ACTION = re.compile(r"^\s*(?:-\s*)?uses:\s*([^#\s]+)(?:\s+#.*)?$")
WRITE_PERMISSION = re.compile(r"^\s*(?:contents|actions|checks|packages|pull-requests|id-token):\s*write\s*(?:#.*)?$", re.I)


def audit_workflow(path: Path) -> list[str]:
    """Return findings for one workflow; an empty result means no detected issue."""
    lines = path.read_text(encoding="utf-8").splitlines()
    findings: list[str] = []
    for number, line in enumerate(lines, 1):
        if re.match(r"^\s*pull_request_target\s*:", line):
            findings.append(f"{path}:{number}: pull_request_target requires explicit fork-safe review")
        match = USES_ACTION.match(line)
        if match and not SHA_ACTION.match(line):
            findings.append(f"{path}:{number}: action is not pinned to a full commit SHA ({match.group(1)})")
        if WRITE_PERMISSION.match(line):
            findings.append(f"{path}:{number}: write permission must be justified and job-scoped")
        if "secrets." in line and any(token in line for token in ("pull_request", "github.event")):
            findings.append(f"{path}:{number}: review secret use on an untrusted pull request path")
    return findings


def workflows(root: Path) -> list[Path]:
    return sorted(p for p in (root / ".github" / "workflows").glob("*") if p.is_file())


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print(f"usage: {argv[0]} REPOSITORY", file=sys.stderr)
        return 2
    root = Path(argv[1])
    paths = workflows(root)
    if not paths:
        print(f"NO_WORKFLOWS: {root}/.github/workflows")
        return 0
    all_findings = [finding for path in paths for finding in audit_workflow(path)]
    print(f"WORKFLOWS: {len(paths)}")
    for finding in all_findings:
        print(f"FINDING: {finding}")
    print(f"RESULT: {'REVIEW_REQUIRED' if all_findings else 'NO_DETECTED_POLICY_FINDINGS'}")
    return 1 if all_findings else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
