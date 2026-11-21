"""Static, read-only policy checks for CI workflow text.

This intentionally does not execute workflow commands or claim to parse all of
GitHub Actions YAML. Findings are review gates for high-risk patterns.
"""
from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True, order=True)
class WorkflowFinding:
    code: str
    line: int
    message: str

    def to_dict(self) -> dict[str, object]:
        return {"code": self.code, "line": self.line, "message": self.message}


_ACTION = re.compile(r"^\s*(?:-\s*)?uses:\s*([^\s#]+)", re.IGNORECASE)
_SHA = re.compile(r"^[^@]+@[0-9a-fA-F]{40}$")
_CONTAINER = re.compile(r"^\s*container:\s*([^\s#]+)", re.IGNORECASE)
def _logical_lines(lines: list[str]):
    """Join shell continuations so checks can see multiline docker commands."""
    start = 1
    pending = ""
    for number, line in enumerate(lines, 1):
        if not pending:
            start = number
        pending += line.rstrip().removesuffix("\\").strip() + " "
        if line.rstrip().endswith("\\"):
            continue
        yield start, pending.strip()
        pending = ""
    if pending:
        yield start, pending.strip()


def audit_workflow(text: str) -> tuple[WorkflowFinding, ...]:
    """Return deterministic findings for known CI trust and reproducibility risks."""
    lines = text.splitlines()
    findings: list[WorkflowFinding] = []
    has_permissions = any(re.match(r"^\s{0,4}permissions\s*:", line) for line in lines)
    if not has_permissions:
        findings.append(WorkflowFinding(
            "CI_PERMISSIONS_UNSCOPED", 1,
            "Workflow does not declare a top-level or job-level permissions block",
        ))

    for number, line in enumerate(lines, 1):
        action = _ACTION.match(line)
        if action and not _SHA.fullmatch(action.group(1)):
            findings.append(WorkflowFinding(
                "CI_ACTION_NOT_IMMUTABLE", number,
                "Third-party action reference is not pinned to a full commit SHA",
            ))
        container = _CONTAINER.match(line)
        if container and (container.group(1).endswith(":latest") or ":" not in container.group(1)):
            findings.append(WorkflowFinding(
                "CI_CONTAINER_MUTABLE", number,
                "Build container is unpinned or uses the mutable latest tag",
            ))
        lowered = line.lower()
        if re.search(r"\bpull_request_target\s*:", lowered):
            findings.append(WorkflowFinding(
                "CI_PRIVILEGED_PULL_REQUEST", number,
                "Privileged pull_request_target trigger requires explicit trust-boundary review",
            ))
        if re.search(r"nopasswd\s*:\s*all", line, re.IGNORECASE):
            findings.append(WorkflowFinding(
                "CI_UNRESTRICTED_SUDO", number,
                "CI grants the build user unrestricted passwordless sudo",
            ))
        if re.search(r"--skippgpcheck\b", line):
            findings.append(WorkflowFinding(
                "CI_SIGNATURE_CHECK_BYPASS", number,
                "Package build disables PGP signature verification",
            ))
    # A workflow can bypass the declarative `container:` field by invoking
    # docker in a run step. Inspect only docker run commands, not arbitrary
    # text that happens to mention a container image.
    for number, line in _logical_lines(lines):
        if not re.search(r"\bdocker\s+run\b", line):
            continue
        tokens = line.split()
        for index, token in enumerate(tokens):
            if token != "run":
                continue
            for candidate in tokens[index + 1:]:
                if candidate.startswith("-"):
                    continue
                if not candidate.startswith("/") and (
                    candidate.startswith(("ghcr.io/", "docker.io/", "quay.io/", "gcr.io/"))
                    or ("/" in candidate and not candidate.startswith(("$", "\"", "'")))
                ):
                    image = candidate.strip("'\";")
                    if image.endswith(":latest") or (":" not in image.rsplit("/", 1)[-1] and "@sha256:" not in image):
                        findings.append(WorkflowFinding(
                            "CI_DOCKER_IMAGE_MUTABLE", number,
                            "docker run uses an unpinned image tag; pin a version or content digest",
                        ))
                    break
    return tuple(sorted(findings))
