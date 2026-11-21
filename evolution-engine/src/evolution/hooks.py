"""Sandboxed, journaled milestone hooks.

Hooks never use ``shell=True`` and never perform network access. A ``command``
hook is split with :func:`shlex.split`, checked against an allowlist, and run
with a minimal environment, a fixed working directory and a timeout. An
``adapter`` hook must be satisfied by a caller-supplied invoker that goes
through the existing signed adapter runtime; without one it fails closed.

Every outcome is appended to a JSONL journal under ``state_root`` so hook order
and results are auditable after an interrupted upgrade.
"""
from __future__ import annotations

import json
import shlex
import subprocess
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping

from .milestones import HOOK_PHASES, HookSpec

# The built-in command hooks are deliberately limited to commands that cannot
# read arbitrary files or change system state. Operations such as filesystem
# repair, migration execution, and artifact inspection must go through a
# signed adapter, or be explicitly enabled by the trusted caller.
DEFAULT_ALLOWED = ("true", "echo", "sync")
NETWORK_TOKENS = ("curl", "wget", "http://", "https://", "git clone", "ssh", "scp", "rsync://")

AdapterInvoker = Callable[[str], tuple[bool, str]]


class HookPhase(str, Enum):
    """Named phases in the declared hook lifecycle."""

    PRE_UPGRADE = "pre_upgrade"
    POST_MILESTONE = "post_milestone"
    ON_FAILURE = "on_failure"

    def __str__(self) -> str:
        return self.value


def utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(frozen=True)
class HookOutcome:
    hook_id: str
    phase: str
    ok: bool
    output: str = ""
    command: str = ""
    at: str = field(default_factory=utcnow)

    def to_dict(self) -> dict[str, Any]:
        return {
            "hook_id": self.hook_id, "phase": self.phase, "ok": self.ok,
            "output": self.output, "command": self.command, "at": self.at,
        }


class HookRunner:
    """Execute hooks in declared phase order and journal every result."""

    def __init__(
        self,
        state_root: str | Path,
        *,
        allowed_commands: Iterable[str] = DEFAULT_ALLOWED,
        timeout: int = 120,
        adapter_invoker: AdapterInvoker | None = None,
        executor: Callable[[list[str], dict[str, str], int], tuple[int, str, str]] | None = None,
    ) -> None:
        self.state_root = Path(state_root)
        self.allowed = tuple(allowed_commands)
        self.timeout = timeout
        self.adapter_invoker = adapter_invoker
        self.executor = executor
        self.journal_path = self.state_root / "hooks.jsonl"
        self.state_root.mkdir(parents=True, exist_ok=True)

    def _journal(self, outcome: HookOutcome) -> None:
        with self.journal_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(outcome.to_dict(), sort_keys=True) + "\n")

    def validate_command(self, command: str) -> list[str]:
        errors: list[str] = []
        lowered = command.lower()
        if any(token in lowered for token in NETWORK_TOKENS):
            errors.append("network access is forbidden in hooks")
        try:
            argv = shlex.split(command)
        except ValueError as exc:
            return [f"invalid command quoting: {exc}"]
        if not argv:
            errors.append("empty hook command")
        elif argv[0] not in self.allowed:
            errors.append(f"command {argv[0]!r} is not in the hook allowlist")
        return errors

    def run_one(self, hook: HookSpec) -> HookOutcome:
        if hook.phase not in HOOK_PHASES:
            outcome = HookOutcome(hook.id, hook.phase, False, "invalid hook phase")
            self._journal(outcome)
            return outcome
        if hook.adapter:
            if self.adapter_invoker is None:
                outcome = HookOutcome(
                    hook.id, hook.phase, False,
                    f"adapter {hook.adapter}: no signed adapter invoker is active",
                )
                self._journal(outcome)
                return outcome
            try:
                ok, output = self.adapter_invoker(hook.adapter)
            except Exception as exc:  # fail closed
                ok, output = False, f"adapter hook error: {exc}"
            outcome = HookOutcome(hook.id, hook.phase, bool(ok), output, f"adapter:{hook.adapter}")
            self._journal(outcome)
            return outcome

        errors = self.validate_command(hook.command)
        if errors:
            outcome = HookOutcome(hook.id, hook.phase, False, "; ".join(errors), hook.command)
            self._journal(outcome)
            return outcome
        argv = shlex.split(hook.command)
        env = {"PATH": "/usr/bin:/bin", "LC_ALL": "C"}
        try:
            if self.executor is not None:
                rc, stdout, stderr = self.executor(argv, env, self.timeout)
            else:
                completed = subprocess.run(  # noqa: S603 - argv list, never shell=True
                    argv, cwd=str(self.state_root), env=env, timeout=self.timeout,
                    capture_output=True, text=True, check=False,
                )
                rc, stdout, stderr = completed.returncode, completed.stdout, completed.stderr
            output = (stdout + stderr).strip()
        except Exception as exc:  # timeout, OSError -> fail closed
            rc, output = 1, f"hook execution error: {exc}"
        outcome = HookOutcome(hook.id, hook.phase, rc == 0, output, hook.command)
        self._journal(outcome)
        return outcome

    def run(self, hooks: Iterable[HookSpec], phase: str) -> list[HookOutcome]:
        """Run hooks for one phase in declaration order.

        A required hook that fails stops later hooks in the same phase; optional
        hook failures are recorded but do not stop the phase.
        """
        outcomes: list[HookOutcome] = []
        for hook in hooks:
            if hook.phase != phase:
                continue
            outcome = self.run_one(hook)
            outcomes.append(outcome)
            if hook.required and not outcome.ok:
                break
        return outcomes

    def history(self) -> list[dict[str, Any]]:
        if not self.journal_path.is_file():
            return []
        return [
            json.loads(line)
            for line in self.journal_path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]


def run_hooks(
    hooks: Iterable[HookSpec],
    phase: str,
    state_root: str | Path,
    **runner_kwargs: Any,
) -> list[HookOutcome]:
    """Convenience wrapper for callers that need one phase without a runner."""
    return HookRunner(state_root, **runner_kwargs).run(hooks, phase)
