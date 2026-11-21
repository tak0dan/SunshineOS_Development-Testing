"""Fail-closed structural checks for ALPM hook definitions.

This deliberately validates metadata only. It never executes the hook's Exec.
"""
from __future__ import annotations

from dataclasses import dataclass
import re


@dataclass(frozen=True)
class HookIssue:
    code: str
    detail: str


_KEY = re.compile(r"^([A-Za-z][A-Za-z0-9]*)\s*=\s*(.*?)\s*$")
_ALLOWED = {
    "Trigger": {"Type", "Operation", "Target"},
    "Action": {"Description", "When", "Exec", "NeedsTargets"},
}


def audit_alpm_hook(source: str) -> tuple[HookIssue, ...]:
    """Validate the minimal safe contract of a libalpm hook.

    Repeated Operation and Target fields are legal. Unknown fields, malformed
    sections, missing trigger/action metadata, and non-absolute Exec are errors.
    """
    sections: dict[str, dict[str, list[str]]] = {}
    current: str | None = None
    issues: list[HookIssue] = []
    for number, raw in enumerate(source.splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith(("#", ";")):
            continue
        if line.startswith("[") and line.endswith("]"):
            current = line[1:-1]
            if current not in ("Trigger", "Action") or current in sections:
                issues.append(HookIssue("HOOK_SECTION_INVALID", f"line {number}: unexpected or repeated section"))
                current = None
            else:
                sections[current] = {}
            continue
        match = _KEY.fullmatch(line)
        if current is None or not match:
            issues.append(HookIssue("HOOK_SYNTAX_INVALID", f"line {number}: key outside valid section or malformed"))
            continue
        key, value = match.groups()
        if key not in _ALLOWED[current]:
            issues.append(HookIssue("HOOK_KEY_UNKNOWN", f"line {number}: unknown {current} key {key!r}"))
            continue
        values = sections[current].setdefault(key, [])
        if key not in ("Operation", "Target") and values:
            issues.append(HookIssue("HOOK_KEY_DUPLICATE", f"line {number}: duplicate {key}"))
        if not value:
            issues.append(HookIssue("HOOK_VALUE_EMPTY", f"line {number}: {current}.{key} must not be empty"))
        values.append(value)

    trigger = sections.get("Trigger", {})
    action = sections.get("Action", {})
    for key in ("Type", "Operation", "Target"):
        if not trigger.get(key):
            issues.append(HookIssue("HOOK_TRIGGER_INCOMPLETE", f"missing Trigger.{key}"))
    if trigger.get("Type") and any(v not in {"Path", "Package"} for v in trigger["Type"]):
        issues.append(HookIssue("HOOK_TRIGGER_TYPE_INVALID", "Trigger.Type must be Path or Package"))
    if trigger.get("Operation") and any(v not in {"Install", "Upgrade", "Remove"} for v in trigger["Operation"]):
        issues.append(HookIssue("HOOK_OPERATION_INVALID", "Trigger.Operation contains an unsupported operation"))
    for key in ("Description", "When", "Exec"):
        if not action.get(key):
            issues.append(HookIssue("HOOK_ACTION_INCOMPLETE", f"missing Action.{key}"))
    if action.get("When") and any(v not in {"PreTransaction", "PostTransaction"} for v in action["When"]):
        issues.append(HookIssue("HOOK_TIMING_INVALID", "Action.When must be PreTransaction or PostTransaction"))
    if action.get("Exec") and any(not v.startswith("/") for v in action["Exec"]):
        issues.append(HookIssue("HOOK_EXEC_NOT_ABSOLUTE", "Action.Exec must use an absolute executable path"))
    return tuple(issues)


def audit_boot_transition_hook(source: str) -> tuple[HookIssue, ...]:
    """Apply SunshineOS boot-transition constraints to a parsed ALPM hook.

    Boot artifact changes run after the package transaction so the observed
    installed package state is coherent. Triggers must identify paths because
    kernel and bootloader artifacts can be supplied by more than one package.
    This validates policy metadata only; it does not prove the command's
    behavior or replace staged boot artifact verification.
    """
    issues = list(audit_alpm_hook(source))
    parsed: dict[str, dict[str, list[str]]] = {"Trigger": {}, "Action": {}}
    current: str | None = None
    for raw in source.splitlines():
        line = raw.strip()
        if line.startswith("[") and line.endswith("]"):
            current = line[1:-1]
            continue
        match = _KEY.fullmatch(line)
        if current in parsed and match and match.group(1) in _ALLOWED[current]:
            parsed[current].setdefault(match.group(1), []).append(match.group(2))
    trigger, action = parsed["Trigger"], parsed["Action"]
    if trigger.get("Type") and any(value != "Path" for value in trigger["Type"]):
        issues.append(HookIssue("BOOT_HOOK_TRIGGER_NOT_PATH", "boot transition hooks must observe artifact paths"))
    if action.get("When") and any(value != "PostTransaction" for value in action["When"]):
        issues.append(HookIssue("BOOT_HOOK_NOT_POST_TRANSACTION", "boot transition hooks must run after package state changes"))
    if not any(op in {"Install", "Upgrade", "Remove"} for op in trigger.get("Operation", [])):
        issues.append(HookIssue("BOOT_HOOK_OPERATION_MISSING", "boot transition hook must cover an artifact lifecycle operation"))
    return tuple(issues)
