"""Command-line interface for OpenClaw (``python3 -m openclaw``)."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Optional, Sequence

from .core import (
    STATUSES,
    AgentBackend,
    LocalShellBackend,
    Orchestrator,
    StubBackend,
    Task,
    TaskStore,
)
from .backends import DEFAULT_FREE_MODELS, MODEL_ROLES, OpenRouterBackend
from .reporter import CompositeReporter, TelegramReporter

DEFAULT_STORE = str(Path.cwd() / ".openclaw" / "tasks.json")


class _StdoutReporter:
    """Always-on local observer; never prints credentials."""

    def send(self, message: str) -> None:
        print(message)

    def task_event(self, event: str, task: Task) -> None:
        print(f"[{event}] {task.id} {task.status} attempt={task.attempts} {task.title}")
        detail = task.result or task.error
        if detail:
            print("    " + detail.splitlines()[0])


def configured_reporters() -> CompositeReporter:
    """Return local stdout plus Telegram (a no-op until env vars are set)."""
    return CompositeReporter([_StdoutReporter(), TelegramReporter()])


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python3 -m openclaw",
        description="Orchestrate SunshineOS development/audit agents.",
    )
    parser.add_argument(
        "--store",
        default=os.environ.get("OPENCLAW_TASKS_FILE", DEFAULT_STORE),
        help="task JSON file (default: $OPENCLAW_TASKS_FILE or ./.openclaw/tasks.json)",
    )
    commands = parser.add_subparsers(dest="command", required=True)

    status = commands.add_parser("status", help="list tasks")
    status.add_argument("--status", choices=sorted(STATUSES), help="filter by status")
    status.add_argument("--json", action="store_true", help="emit JSON")

    add = commands.add_parser("add", help="queue a task")
    add.add_argument("title", help="short human-readable title")
    add.add_argument("instructions", help="command to run (quoted as one argument)")
    add.add_argument("--repo", default="", help="repository path to run in")
    add.add_argument("--model", default="", help="model id for model-backed agents")
    add.add_argument("--id", default=None, help="explicit task id (default: generated)")

    run = commands.add_parser("run", help="execute pending tasks")
    run.add_argument("--id", dest="task_id", help="run a specific pending task")
    run.add_argument("--all", action="store_true", help="drain all pending tasks")
    run.add_argument("--max-tasks", type=int, help="cap the number of tasks for --all")
    run.add_argument(
        "--backend", choices=("shell", "stub", "openrouter"), default="shell"
    )
    run.add_argument("--timeout", type=float, default=300.0, help="per-command seconds")
    run.add_argument("--max-attempts", type=int, default=3)
    run.add_argument("--stub-result", default="", help="result text for the stub backend")
    run.add_argument(
        "--model",
        default=os.environ.get("OPENCLAW_MODEL", ""),
        help="OpenRouter model id override (task --model wins)",
    )
    run.add_argument(
        "--model-role",
        choices=tuple(sorted(MODEL_ROLES)),
        help="use a named free model role (reviewer, architect, researcher)",
    )
    run.add_argument(
        "--free-models", action="store_true", help="print the curated free model list and exit"
    )

    report = commands.add_parser("report", help="send a test message to reporters")
    report.add_argument("--message", default="OpenClaw test message")
    return parser


def _make_backend(args: argparse.Namespace) -> AgentBackend:
    if args.backend == "stub":
        return StubBackend([args.stub_result] if args.stub_result else [])
    if args.backend == "openrouter":
        role_model = MODEL_ROLES.get(args.model_role, "") if args.model_role else ""
        model = args.model or role_model or None
        return OpenRouterBackend(model, timeout=args.timeout)
    return LocalShellBackend(timeout=args.timeout)


def _run(args: argparse.Namespace, store: TaskStore) -> int:
    if args.task_id and args.all:
        raise ValueError("use either --id or --all, not both")
    if args.max_tasks is not None and not args.all:
        raise ValueError("--max-tasks requires --all")
    if args.timeout <= 0:
        raise ValueError("--timeout must be positive")

    reporter = configured_reporters()

    def on_event(event: str, task: Task) -> None:
        reporter.task_event(event, task)

    orchestrator = Orchestrator(
        store=store,
        backend=_make_backend(args),
        event_callback=on_event,
        max_attempts=args.max_attempts,
    )
    if args.task_id:
        task = orchestrator.run_one(args.task_id)
        completed = [task] if task is not None else []
        if task is None:
            print(f"No pending task with id {args.task_id}")
    elif args.all:
        completed = orchestrator.run_all(max_tasks=args.max_tasks)
        if not completed:
            print("No pending tasks.")
    else:
        task = orchestrator.run_one()
        completed = [task] if task is not None else []
        if task is None:
            print("No pending tasks.")

    failures = [task for task in completed if task.status == "failed"]
    for task in completed:
        print(f"{task.id}: {task.status} after {task.attempts} attempt(s)")
    if orchestrator.last_event_error is not None:
        print(f"warning: event callback failed: {orchestrator.last_event_error}")
    return 1 if failures else 0


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    if getattr(args, "free_models", False):
        for model in DEFAULT_FREE_MODELS:
            print(model)
        return 0
    try:
        store = TaskStore(args.store)
        if args.command == "status":
            tasks = store.list(status=args.status)
            if args.json:
                print(json.dumps([task.to_dict() for task in tasks], indent=2))
            elif not tasks:
                print("No tasks.")
            else:
                print(f"{'ID':<14} {'STATUS':<9} {'ATTEMPTS':<9} TITLE")
                for task in tasks:
                    print(
                        f"{task.id:<14} {task.status:<9} "
                        f"{task.attempts:<9} {task.title}"
                    )
            return 0
        if args.command == "add":
            task_id = args.id or Task().id
            task = Task(
                id=task_id,
                title=args.title,
                instructions=args.instructions,
                repo_path=args.repo,
                model=args.model,
            )
            store.add(task)
            print(task.id)
            return 0
        if args.command == "run":
            return _run(args, store)
        if args.command == "report":
            configured_reporters().send(args.message)
            return 0
    except (ValueError, KeyError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    return 2


if __name__ == "__main__":  # allows direct `python3 openclaw/cli.py` debugging
    raise SystemExit(main())
