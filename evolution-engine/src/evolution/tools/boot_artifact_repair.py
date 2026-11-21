"""Read-only assessment of kernel/initramfs artifacts before boot repair.

Boot generation tools can return success after suppressing a generator error.
This module checks the expected files under an observed root; it never invokes
mkinitcpio, updates boot entries, or writes to the ESP.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


@dataclass(frozen=True)
class BootArtifactFinding:
    path: str
    state: str  # present | missing | empty | unsafe
    detail: str


@dataclass(frozen=True)
class BootArtifactAssessment:
    root: str
    complete: bool
    findings: tuple[BootArtifactFinding, ...]
    blockers: tuple[str, ...] = ()

    @property
    def repairable(self) -> bool:
        return self.complete and not self.blockers and all(
            finding.state == "present" for finding in self.findings
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "root": self.root,
            "complete": self.complete,
            "repairable": self.repairable,
            "findings": [
                {"path": item.path, "state": item.state, "detail": item.detail}
                for item in self.findings
            ],
            "blockers": list(self.blockers),
            "policy": "read-only; missing artifacts require checkpointed regeneration and validation",
        }


def assess_boot_artifacts(root: str | Path, paths: Iterable[str]) -> BootArtifactAssessment:
    """Assess required kernel/boot artifacts, refusing path traversal and escapes.

    ``paths`` are root-relative POSIX paths such as ``boot/vmlinuz-linux``.
    Symlinks are accepted only when their resolved targets remain under root.
    """
    base = Path(root).resolve()
    requested = tuple(dict.fromkeys(paths))
    if not requested:
        return BootArtifactAssessment(str(base), False, (), ("no boot artifacts specified",))
    findings: list[BootArtifactFinding] = []
    for raw in requested:
        relative = Path(raw)
        if relative.is_absolute() or ".." in relative.parts or not raw:
            return BootArtifactAssessment(
                str(base), False, tuple(findings), (f"invalid root-relative artifact path: {raw!r}",)
            )
        candidate = base / relative
        try:
            resolved = candidate.resolve(strict=False)
            resolved.relative_to(base)
        except (OSError, ValueError):
            findings.append(BootArtifactFinding(raw, "unsafe", "artifact path escapes observed root"))
            return BootArtifactAssessment(str(base), False, tuple(findings), ("artifact path escapes observed root",))
        if not resolved.exists():
            findings.append(BootArtifactFinding(raw, "missing", "required boot artifact is absent"))
        elif not resolved.is_file():
            findings.append(BootArtifactFinding(raw, "unsafe", "required artifact is not a regular file"))
            return BootArtifactAssessment(str(base), False, tuple(findings), ("artifact is not a regular file",))
        elif resolved.stat().st_size == 0:
            findings.append(BootArtifactFinding(raw, "empty", "required boot artifact is empty"))
        else:
            findings.append(BootArtifactFinding(raw, "present", "non-empty artifact exists"))
    return BootArtifactAssessment(str(base), True, tuple(findings))
