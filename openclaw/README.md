# OpenClaw

OpenClaw is a small, dependency-free Python framework for orchestrating
multiple development and audit agents working on the SunshineOS evolutionary
migration. It keeps a durable task queue, dispatches work through pluggable
backends, retries bounded failures, and streams progress events to reporters
(a Telegram reporter is included but stays silent until configured).

Layout:

```
openclaw/             # this directory; also the Python package root
  __init__.py         package exports and overview
  core.py             Task, TaskStore, AgentBackend, LocalShellBackend, StubBackend, Orchestrator
  reporter.py         Reporter protocol, TelegramReporter, CompositeReporter
  cli.py              argparse CLI
  __main__.py         `python3 -m openclaw`
  README.md
  tests/              unittest suite
```

## Quick start

Run these from the parent of this `openclaw/` directory (so the package is
importable):

```sh
# Queue work. The command is one quoted argument; use --repo for its cwd.
python3 -m openclaw add "Audit migration docs" "python3 -m pytest -q" --repo /path/to/repo

# Inspect the queue.
python3 -m openclaw status
python3 -m openclaw status --status failed --json

# Run one pending task, or drain the whole queue.
python3 -m openclaw run
python3 -m openclaw run --all --max-tasks 5 --timeout 600 --max-attempts 3

# Dry-run the event/reporting path without executing anything.
python3 -m openclaw run --backend stub --stub-result "looks good"

# Send a test message through all configured reporters.
python3 -m openclaw report --message "OpenClaw check-in"
```

The task file defaults to `./.openclaw/tasks.json`. Override it per command
with `--store PATH` or globally with `OPENCLAW_TASKS_FILE`. Writes are atomic
(temp file in the same directory followed by `os.replace`); there is no file
locking, so use one writer/orchestrator process per store.

## Telegram configuration

Set both environment variables before starting OpenClaw:

| Variable | Purpose |
| --- | --- |
| `TELEGRAM_BOT_TOKEN` | Bot API token issued by Telegram |
| `TELEGRAM_CHAT_ID` | Destination chat identifier |

If either is missing or empty, `TelegramReporter` becomes a silent no-op and
performs no network I/O. Credentials are read from the environment only, are
never written to disk or logs, and are redacted from stored error text.
Messages use compact legacy Markdown with fenced blocks and are truncated to
4096 characters. HTTP/network errors are captured in `last_error` and never
raised into the orchestrator.

`CompositeReporter` fans out to multiple reporters; errors from one reporter do
not block the others.

## Adding a new backend

Subclass `AgentBackend` and implement `run(task) -> str`. Return captured output
on success; raise on failure (the orchestrator records `error` and retries).

```python
from openclaw.core import AgentBackend, Task

class MyBackend(AgentBackend):
    def __init__(self, client):
        self.client = client

    def run(self, task: Task) -> str:
        return self.client.execute(task.instructions, repo=task.repo_path)
```

Then pass it to `Orchestrator(store, backend, event_callback=..., max_attempts=3)`.
Event callbacks receive `(event, task)` where `event` is one of
`task.claimed`, `attempt.started`, `attempt.failed`, `task.retry`,
`task.succeeded`, or `task.failed`. Wrap your reporter as that callback;
callback exceptions are isolated from task execution.

## Plugging into the evolution engine

The SunshineOS evolution engine follows
`Discover → Resolve → Plan → Preflight → Execute → Validate → Commit`.
OpenClaw sits at the Execute/Validate boundary:

1. The engine's planner emits a reviewable plan; each step becomes an OpenClaw
   `Task` with `title`, `instructions`, and the target `repo_path`.
2. OpenClaw claims tasks one at a time, runs them through the configured backend
   (a local command runner today, an agent-client backend later), and applies
   bounded retries before marking them `done` or `failed`.
3. Progress events feed the reporter, so the operator receives compact updates
   without polling the machine.
4. The engine consumes the resulting task states as its execution/validation
   evidence before it proceeds to Commit. Failed tasks stop promotion instead
   of being silently skipped.

See `../evolution-engine/src/engine.py` for the engine pipeline this complements.

## Safety rules

- No API keys, tokens, or chat IDs in code, docs, or the task store — environment
  variables only.
- No `shell=True`. Instructions are parsed with `shlex.split` (or a JSON list of
  strings) and passed as an argv vector to `subprocess.run`.
- Every command has a bounded timeout (`--timeout`, default 300s) and every task
  has bounded attempts (`--max-attempts`, default 3).
- Captured output is truncated before being stored or reported.
- Run agents only against repositories you intend to modify; review plans before
  queueing them.

## Tests

From the parent of this directory:

```sh
python3 -m unittest discover -s openclaw/tests -t . -v
```

Tests use `StubBackend`, temporary files, and a patched `urlopen`; they never
touch the network.
