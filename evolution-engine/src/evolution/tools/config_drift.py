"""Read-only assessment of pacman .pacnew/.pacsave configuration drift.

EndeavourOS exposes pacdiff through eos-pacdiff. SunshineOS records candidates
for review but never replaces administrator configuration automatically.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

_CRITICAL = frozenset({
    "/etc/fstab", "/etc/crypttab", "/etc/passwd", "/etc/group",
    "/etc/shadow", "/etc/gshadow", "/etc/sudoers",
})


@dataclass(frozen=True)
class ConfigDriftItem:
    candidate: str
    current: str
    kind: str
    disposition: str

    def to_dict(self) -> dict[str, str]:
        return {
            "candidate": self.candidate,
            "current": self.current,
            "kind": self.kind,
            "disposition": self.disposition,
        }


@dataclass(frozen=True)
class ConfigDriftReport:
    items: tuple[ConfigDriftItem, ...]
    errors: tuple[str, ...] = ()

    @property
    def complete(self) -> bool:
        return not self.errors

    def to_dict(self) -> dict[str, object]:
        return {
            "complete": self.complete,
            "items": [item.to_dict() for item in self.items],
            "errors": list(self.errors),
            "policy": "read-only; configuration candidates require operator review",
        }


def _candidate_kind(name: str) -> tuple[str, str] | None:
    if name.endswith(".pacnew"):
        return name[:-7], "pacnew"
    if name.endswith(".pacsave"):
        return name[:-8], "pacsave"
    return None


def assess_config_drift(root: str | os.PathLike[str] = "/") -> ConfigDriftReport:
    """Inventory regular pacnew/pacsave files under rooted ``/etc``.

    Symlink directories and symlink candidates are ignored. A failed or
    unreadable walk is reported as incomplete, never as a clean result.
    """
    root_path = Path(root)
    etc = root_path / "etc"
    items: list[ConfigDriftItem] = []
    errors: list[str] = []
    if not etc.is_dir():
        return ConfigDriftReport((), ("configuration root is absent or unreadable",))

    def onerror(exc: OSError) -> None:
        errors.append(f"unable to inspect configuration path: {exc.filename or 'unknown'}")

    for directory, dirnames, filenames in os.walk(etc, followlinks=False, onerror=onerror):
        base = Path(directory)
        dirnames[:] = sorted(
            name for name in dirnames
            if not (base / name).is_symlink()
        )
        for name in sorted(filenames):
            matched = _candidate_kind(name)
            if matched is None:
                continue
            candidate = base / name
            if candidate.is_symlink() or not candidate.is_file():
                continue
            original_name, kind = matched
            original = candidate.with_name(original_name)
            try:
                relative_candidate = "/" + candidate.relative_to(root_path).as_posix()
                relative_original = "/" + original.relative_to(root_path).as_posix()
            except ValueError:
                errors.append("configuration candidate escaped the selected root")
                continue
            sensitive = relative_original in _CRITICAL
            exists = original.exists()
            disposition = (
                "manual-review-critical" if sensitive else
                "compare-with-existing" if exists and kind == "pacnew" else
                "review-before-restore" if kind == "pacsave" else
                "review-before-install"
            )
            items.append(ConfigDriftItem(relative_candidate, relative_original, kind, disposition))
    return ConfigDriftReport(tuple(items), tuple(errors))
