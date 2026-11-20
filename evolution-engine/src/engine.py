#!/usr/bin/env python3
"""Sunshine Evolution Engine orchestrator and CLI.

Pipeline: Discover → Resolve → Plan → Preflight → Execute → Validate → Commit.

The CLI mirrors the intended production interface:

    sunshine-evolve --check          # discover + report only
    sunshine-evolve --plan           # produce a reviewable plan (JSON)
    sunshine-evolve --apply          # execute the plan (with journaling)
    sunshine-evolve --verify         # validate current capabilities
    sunshine-evolve --repair         # replan + resume from journal
    sunshine-evolve --history        # show journal

The same executable enters transformation mode on a pure Arch machine and
normal reconciliation mode on an existing Sunshine OS — there is one engine.
"""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.core import ObservedState, Plan  # noqa: E402
from src.discovery import discover  # noqa: E402
from src.target import load_target, resolve_target  # noqa: E402
from src.planner import plan as build_plan  # noqa: E402
from src.executor import execute_plan, ExecutionResult  # noqa: E402
from src.validation import validate_system, ValidationReport  # noqa: E402

DEFAULT_ROOT = "/"
STATE_ROOT = Path("/var/lib/sunshine")


def _json(obj) -> str:
    if hasattr(obj, "to_dict"):
        obj = obj.to_dict()
    elif hasattr(obj, "__dataclass_fields__"):
        obj = asdict(obj)
    return json.dumps(obj, indent=2, ensure_ascii=False, default=str)


def _discover(root: str) -> ObservedState:
    return discover(root=root)


def _resolve(root: str, observed: ObservedState):
    target = load_target()
    return resolve_target(observed, target, profiles_dir=Path(__file__).resolve().parent / "target" / "profiles")


def cmd_check(root: str) -> int:
    observed = _discover(root)
    target, decisions = _resolve(root, observed)
    print("Sunshine Evolution Engine — discovery report")
    print(_json({
        "observed": observed.to_dict(),
        "target_release": target.release,
        "repository_generation": target.repository_generation,
        "required_components": {k: c.schema for k, c in target.components.items() if c.required},
        "decisions_required": decisions,
    }))
    return 0


def cmd_plan(root: str) -> int:
    observed = _discover(root)
    target, decisions = _resolve(root, observed)
    plan = build_plan(observed, target, decisions=decisions)
    print(_json(plan))
    return 0


def _apply_decisions(decisions: list[dict], answers: list[str]) -> list[dict]:
    """Apply ``--decide id=value`` answers to unresolved decisions."""
    parsed: dict[str, str] = {}
    for answer in answers:
        if "=" not in answer:
            raise ValueError(f"invalid decision '{answer}'; expected id=value")
        key, value = answer.split("=", 1)
        parsed[key.strip()] = value.strip()
    for decision in decisions:
        answer = parsed.get(str(decision.get("id", "")))
        if answer is None:
            continue
        options = [str(o) for o in decision.get("options", [])]
        if options and answer not in options:
            raise ValueError(f"invalid value '{answer}' for {decision['id']}; "
                             f"expected one of {options}")
        decision["auto"] = True
        decision["requires_user_input"] = False
        decision["selected"] = answer
        decision["reason"] = f"operator selected '{answer}'"
    return decisions


def cmd_apply(root: str, state_root: str, resume: bool, dry_run: bool,
              decide: Optional[list[str]] = None) -> int:
    observed = _discover(root)
    target, decisions = _resolve(root, observed)
    decisions = _apply_decisions(decisions, decide or [])
    plan = build_plan(observed, target, decisions=decisions)
    unresolved = [d for d in plan.decisions if d.get("requires_user_input")]
    if unresolved and not resume:
        print("Unresolved decisions:\n" + _json(unresolved), file=sys.stderr)
        return 2
    result = execute_plan(plan, state_root=state_root, resume=resume, dry_run=dry_run)
    print(_json(result))
    return 0 if result.status in ("completed", "no-op") else 1


def cmd_verify(root: str) -> int:
    observed = _discover(root)
    target, _ = _resolve(root, observed)
    reports = validate_system(observed, target, root=root)
    print(_json({"passed": all(r.passed for r in reports), "reports": reports}))
    return 0 if all(r.passed for r in reports) else 1


def cmd_repair(root: str, state_root: str, decide: Optional[list[str]] = None) -> int:
    # Re-discover first: the machine, not the journal, is the source of truth.
    return cmd_apply(root, state_root, resume=True, dry_run=False, decide=decide)


def cmd_history(state_root: str) -> int:
    from src.executor.journal import Journal
    j = Journal(state_root)
    print(_json(j.load()))
    return 0


def main(argv: Optional[list[str]] = None) -> int:
    ap = argparse.ArgumentParser(prog="sunshine-evolve", description="Sunshine Evolution Engine")
    ap.add_argument("--root", default=DEFAULT_ROOT, help="filesystem root for discovery (testing)")
    ap.add_argument("--state-root", default=str(STATE_ROOT), help="Sunshine state directory")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--check", action="store_true")
    g.add_argument("--plan", action="store_true")
    g.add_argument("--apply", action="store_true")
    g.add_argument("--verify", action="store_true")
    g.add_argument("--repair", action="store_true")
    g.add_argument("--history", action="store_true")
    ap.add_argument("--resume", action="store_true", help="with --apply: resume from journal after re-discovery")
    ap.add_argument("--dry-run", action="store_true", help="with --apply: simulate without changes")
    ap.add_argument("--decide", action="append", default=[], metavar="ID=VALUE",
                    help="answer a decision, e.g. --decide desktop-profile=hyprland")
    a = ap.parse_args(argv)
    if a.history:
        return cmd_history(a.state_root)
    if a.check:
        return cmd_check(a.root)
    if a.plan:
        return cmd_plan(a.root)
    if a.verify:
        return cmd_verify(a.root)
    if a.apply:
        return cmd_apply(a.root, a.state_root, a.resume, a.dry_run, a.decide)
    if a.repair:
        return cmd_repair(a.root, a.state_root, a.decide)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
