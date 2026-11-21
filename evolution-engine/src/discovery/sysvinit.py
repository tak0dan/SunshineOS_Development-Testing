"""Read-only parsing helpers for historical Arch SysV service declarations.

This module does not execute rc.conf.  It accepts only a literal ``DAEMONS``
array and returns observations for migration planning; shell expressions and
ambiguous declarations are reported as errors.
"""
from __future__ import annotations

from dataclasses import dataclass
import re
import shlex


_NAME = re.compile(r"^[A-Za-z0-9_.+-]+$")


@dataclass(frozen=True)
class SysVServiceInventory:
    """Literal service intent read from an Arch ``/etc/rc.conf`` file."""

    source_path: str
    enabled: tuple[str, ...] = ()
    disabled: tuple[str, ...] = ()
    background: tuple[str, ...] = ()
    errors: tuple[str, ...] = ()

    @property
    def complete(self) -> bool:
        return not self.errors

    def to_dict(self) -> dict[str, object]:
        return {
            "source_path": self.source_path,
            "enabled": list(self.enabled),
            "disabled": list(self.disabled),
            "background": list(self.background),
            "complete": self.complete,
            "errors": list(self.errors),
        }


def parse_rc_conf(text: str, source_path: str = "/etc/rc.conf") -> SysVServiceInventory:
    """Parse one literal ``DAEMONS=(...)`` assignment without shell evaluation.

    Arch's historical rc.conf uses shell syntax.  We intentionally support a
    small, static subset. Any variable expansion, command substitution,
    duplicate assignment, or unsupported token makes the observation
    incomplete rather than guessing.
    """
    assignments: list[str] = []
    for line in text.splitlines():
        # Service entries are simple tokens; quoted strings and comments are
        # accepted by shlex below. Locate assignment lines without sourcing.
        if re.match(r"^\s*DAEMONS\s*=", line):
            assignments.append(line)
    if len(assignments) != 1:
        message = "DAEMONS assignment missing" if not assignments else "multiple DAEMONS assignments"
        return SysVServiceInventory(source_path, errors=(message,))

    declaration = assignments[0].split("=", 1)[1].strip()
    if not declaration.startswith("(") or not declaration.endswith(")"):
        return SysVServiceInventory(source_path, errors=("DAEMONS must be a single-line literal array",))
    body = declaration[1:-1]
    if any(char in body for char in ("$", "`", ";", "|", "&", "<", ">", "\\")):
        return SysVServiceInventory(source_path, errors=("DAEMONS contains shell syntax",))
    try:
        tokens = shlex.split(body, comments=True, posix=True)
    except ValueError:
        return SysVServiceInventory(source_path, errors=("DAEMONS quoting is malformed",))

    enabled: list[str] = []
    disabled: list[str] = []
    background: list[str] = []
    seen: set[str] = set()
    for token in tokens:
        is_disabled = token.startswith("!")
        is_background = token.startswith("@") and not is_disabled
        name = token[1:] if token[:1] in ("!", "@") else token
        if not name or not _NAME.fullmatch(name):
            return SysVServiceInventory(source_path, errors=(f"unsupported DAEMONS token {token!r}",))
        if name in seen:
            return SysVServiceInventory(source_path, errors=(f"duplicate DAEMONS service {name!r}",))
        seen.add(name)
        if is_disabled:
            disabled.append(name)
        else:
            enabled.append(name)
            if is_background:
                background.append(name)
    return SysVServiceInventory(
        source_path, tuple(enabled), tuple(disabled), tuple(background)
    )
