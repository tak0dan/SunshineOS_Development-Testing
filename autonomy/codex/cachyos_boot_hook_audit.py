"""Static audit for boot artifact generation scripts.

This is a review aid, not a shell parser or an execution authorization tool.
It flags suppressed initramfs/UKI generation failures unless the script has an
explicit artifact validation path nearby. It never runs the inspected script.
"""
from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class Finding:
    line: int
    code: str
    detail: str


_GENERATOR = re.compile(r"\b(mkinitcpio|dracut|kernel-install)\b")
_SUPPRESSION = re.compile(r"\|\|\s*(?:true|:)(?:\s|$)")
_VALIDATION = re.compile(
    r"(\blsinitcpio\b|test\s+-[se]|(?<!\w)-[se]\s+[^\n]*|"
    r"no (?:uki|initramfs|image)|failed to regenerate)",
    re.IGNORECASE,
)


def audit_boot_generation_script(source: str, context_lines: int = 16) -> tuple[Finding, ...]:
    """Find suppressed boot-image generation without a nearby validation.

    A validation is accepted only in the same logical window as the suppressed
    call. This intentionally favors false positives for human review over
    treating a failed boot artifact build as successful.
    """
    lines = source.splitlines()
    findings: list[Finding] = []
    for index, line in enumerate(lines):
        if not _GENERATOR.search(line) or not _SUPPRESSION.search(line):
            continue
        start = index + 1
        end = min(len(lines), index + context_lines + 1)
        window = "\n".join(lines[start:end])
        if not _VALIDATION.search(window):
            findings.append(Finding(
                line=index + 1,
                code="BOOTGEN_SUPPRESSED_UNVERIFIED",
                detail="boot artifact generation error is suppressed without nearby artifact validation",
            ))
    return tuple(findings)
