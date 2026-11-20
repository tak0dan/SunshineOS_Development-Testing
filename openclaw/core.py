"""Task persistence, agent backends, and the OpenClaw orchestrator.

Design rules:
    * Tasks live in a single JSON file written atomically via ``os.replace``.
    * Backends receive a parsed argument vector; ``shell=True`` is never used.
    * Every attempt is bounded by a timeout and by ``Orchestrator.max_attempts``.
    * Reporters are observers: failures in an event callback never abort work.
"""

from __future__ import annotations

import json
import os
import re
import shlex
import subprocess
import tempfile
import uuid
from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Optional

PENDING = "pending"
RUNNING = "running"
DONE = "done"
FAILED = "failed"
TERMINAL_STATUSES = frozenset({DONE, FAILED})
STATUSES = frozenset({PENDING, RUNNING, DONE, FAILED})

EventCallback = Callable[[str, "Task"], None]

SECRET_PATTERN = re.compile(r"sk-or-v1-[A-Za-z0-9]+|Bearer\s+[A-Za-z0-9._-]+")


def redact_text(value: Any) -> str:
    """Remove credential-shaped tokens from text before storing or sending it."""
    return SECRET_PATTERN.sub("<redacted>", str(value))


def _utc_now() -> str:
    """Return a stable, sortable UTC timestamp."""
    return datetime.now(timezone.utc).isoformat(timespec="microseconds")


def _shorten(text: str, limit: int = 4000) -> str:
    text = str(text)
    return text if len(text) <= limit else text[: limit - 1].rstrip() + "…"


@dataclass
class Task:
    """One unit of agent work.

    ``instructions`` is the command the backend should run. A plain string is
    split with :func:`shlex.split`; a JSON-encoded list of strings is also
    accepted, which is useful for arguments containing whitespace.
    """

    id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    title: str = "Untitled task"
    instructions: str = ""
    repo_path: str = ""
    model: str = ""  # optional backend model id (for example a free OpenRouter model)
    status: str = PENDING
    attempts: int = 0
    created_at: str = field(default_factory=_utc_now)
    updated_at: str = field(default_factory=_utc_now)
    result: str = ""
    error: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Task":
        known = set(cls.__dataclass_fields__)
        clean = {key: value for key, value in data.items() if key in known}
        status = str(clean.get("status", PENDING))
        if status not in STATUSES:
            raise ValueError(f"unknown task status: {status!r}")
        clean["status"] = status
        clean["attempts"] = int(clean.get("attempts", 0))
        clean.setdefault("created_at", _utc_now())
        clean.setdefault("updated_at", clean["created_at"])
        return cls(**clean)


class TaskStore:
    """JSON-backed task store with atomic writes.

    There is no file locking: use a single writer process (or one orchestrator
    per store) to avoid lost updates.
    """

    def __init__(self, path: os.PathLike[str] | str) -> None:
        self.path = Path(path).expanduser().resolve()
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def _load(self) -> Dict[str, Dict[str, Any]]:
        if not self.path.exists():
            return {}
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise ValueError(f"corrupt task store {self.path}: {exc}") from exc
        if not isinstance(raw, dict):
            raise ValueError(f"corrupt task store {self.path}: expected an object")
        tasks: Dict[str, Dict[str, Any]] = {}
        for key, value in raw.items():
            if not isinstance(value, dict):
                raise ValueError(f"corrupt task store {self.path}: bad task {key!r}")
            task = Task.from_dict(value)
            task.id = str(key)
            for field_name in ("title", "instructions", "repo_path", "model", "result", "error"):
                setattr(task, field_name, redact_text(getattr(task, field_name, "")))
            tasks[task.id] = task.to_dict()
        return tasks

    def _save(self, tasks: Dict[str, Dict[str, Any]]) -> None:
        """Write the whole store to a temp file in the same directory, then rename."""
        for task in tasks.values():
            for field_name in ("title", "instructions", "repo_path", "model", "result", "error"):
                task[field_name] = redact_text(task.get(field_name, ""))
        payload = json.dumps(tasks, indent=2, sort_keys=True, ensure_ascii=False)
        fd, tmp_name = tempfile.mkstemp(
            prefix=".openclaw-", suffix=".json.tmp", dir=str(self.path.parent)
        )
        tmp_path = Path(tmp_name)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                handle.write(payload)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(tmp_path, self.path)
            # Best-effort directory fsync so the rename itself is durable.
            dir_fd = os.open(str(self.path.parent), os.O_RDONLY)
            try:
                os.fsync(dir_fd)
            finally:
                os.close(dir_fd)
        except BaseException:
            tmp_path.unlink(missing_ok=True)
            raise

    def add(self, task: Task) -> Task:
        tasks = self._load()
        if task.id in tasks:
            raise ValueError(f"task already exists: {task.id}")
        tasks[task.id] = task.to_dict()
        self._save(tasks)
        return task

    def get(self, task_id: str) -> Optional[Task]:
        data = self._load().get(task_id)
        return Task.from_dict(data) if data is not None else None

    def update(self, task_id: str, **changes: Any) -> Task:
        tasks = self._load()
        if task_id not in tasks:
            raise KeyError(f"unknown task: {task_id}")
        allowed = set(Task.__dataclass_fields__) - {"id"}
        unknown = set(changes) - allowed
        if unknown:
            raise ValueError(f"unknown task fields: {', '.join(sorted(unknown))}")
        current = dict(tasks[task_id])
        current.update(changes)
        current["id"] = task_id
        current["updated_at"] = _utc_now()
        updated = Task.from_dict(current)
        tasks[task_id] = updated.to_dict()
        self._save(tasks)
        return updated

    def list(self, status: Optional[str] = None) -> List[Task]:
        tasks = self._load()
        if status is not None and status not in STATUSES:
            raise ValueError(f"unknown task status: {status!r}")
        result = [Task.from_dict(data) for data in tasks.values()]
        if status is not None:
            result = [task for task in result if task.status == status]
        return sorted(result, key=lambda task: (task.created_at, task.id))

    def next_pending(self) -> Optional[Task]:
        for task in self.list(status=PENDING):
            return task
        return None


class AgentBackend(ABC):
    """Pluggable executor interface. Return a string result or raise on failure."""

    @abstractmethod
    def run(self, task: Task) -> str:
        """Execute *task* and return captured output."""


class LocalShellBackend(AgentBackend):
    """Run task instructions as an argv list (never through a shell)."""

    def __init__(
        self,
        timeout: float = 300.0,
        max_output_chars: int = 8000,
        cwd: os.PathLike[str] | str | None = None,
    ) -> None:
        if timeout <= 0:
            raise ValueError("timeout must be positive")
        self.timeout = float(timeout)
        self.max_output_chars = int(max_output_chars)
        self.cwd = str(cwd) if cwd is not None else None

    @staticmethod
    def _argv(instructions: str) -> List[str]:
        text = instructions.strip()
        if not text:
            raise ValueError("task has no instructions")
        if text.startswith("["):
            try:
                parsed = json.loads(text)
            except json.JSONDecodeError as exc:
                raise ValueError(f"invalid JSON argv in instructions: {exc}") from exc
            if not isinstance(parsed, list) or not parsed or not all(
                isinstance(item, str) for item in parsed
            ):
                raise ValueError("JSON argv must be a non-empty list of strings")
            return parsed
        argv = shlex.split(text, posix=True)
        if not argv:
            raise ValueError("task has no instructions")
        return argv

    def _working_dir(self, task: Task) -> str | None:
        if task.repo_path:
            path = Path(task.repo_path).expanduser()
            if not path.is_dir():
                raise FileNotFoundError(f"repo path is not a directory: {path}")
            return str(path)
        return self.cwd

    def run(self, task: Task) -> str:
        argv = self._argv(task.instructions)
        cwd = self._working_dir(task)
        try:
            completed = subprocess.run(
                argv,
                cwd=cwd,
                shell=False,  # explicit: OpenClaw never invokes a shell
                capture_output=True,
                text=True,
                timeout=self.timeout,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            partial = (exc.stdout or "") + (exc.stderr or "")
            if isinstance(partial, bytes):
                partial = partial.decode("utf-8", errors="replace")
            raise TimeoutError(
                f"command timed out after {self.timeout}s: {_shorten(partial)}"
            ) from exc
        except OSError as exc:
            raise RuntimeError(f"could not start {argv[0]!r}: {exc}") from exc

        output = (completed.stdout or "") + (completed.stderr or "")
        if completed.returncode != 0:
            raise RuntimeError(
                f"command exited {completed.returncode}: {_shorten(output)}"
            )
        return _shorten(output, self.max_output_chars)


class StubBackend(AgentBackend):
    """Deterministic backend for tests and demos.

    ``outcomes`` is a sequence of strings (successes) or exceptions (failures).
    When exhausted, a generic success string is returned.
    """

    def __init__(self, outcomes: Optional[Iterable[Any]] = None) -> None:
        self.outcomes: List[Any] = list(outcomes or [])
        self.calls: List[str] = []

    def run(self, task: Task) -> str:
        self.calls.append(task.id)
        outcome = self.outcomes.pop(0) if self.outcomes else f"stub result for {task.id}"
        if isinstance(outcome, BaseException):
            raise outcome
        return str(outcome)


class Orchestrator:
    """Dispatch pending tasks through a backend with bounded retries.

    Events passed to ``event_callback`` are ``"task.claimed"``,
    ``"attempt.started"``, ``"attempt.failed"``, ``"task.retry"``,
    ``"task.succeeded"``, and ``"task.failed"``. Callbacks receive
    ``(event, task)`` and are isolated from task execution.
    """

    def __init__(
        self,
        store: TaskStore,
        backend: AgentBackend,
        event_callback: Optional[EventCallback] = None,
        max_attempts: int = 3,
    ) -> None:
        if max_attempts < 1:
            raise ValueError("max_attempts must be at least 1")
        self.store = store
        self.backend = backend
        self.event_callback = event_callback
        self.max_attempts = int(max_attempts)
        self.last_event_error: Optional[BaseException] = None

    def _emit(self, event: str, task: Task) -> None:
        if self.event_callback is None:
            return
        try:
            self.event_callback(event, task)
        except Exception as exc:  # reporters must never break orchestration
            self.last_event_error = exc

    def run_one(self, task_id: Optional[str] = None) -> Optional[Task]:
        task = self.store.get(task_id) if task_id else self.store.next_pending()
        if task is None:
            return None
        if task.status != PENDING:
            raise ValueError(f"task {task.id} is {task.status}, not pending")
        self._emit("task.claimed", task)

        while True:
            task = self.store.update(
                task.id, status=RUNNING, attempts=task.attempts + 1, error=""
            )
            self._emit("attempt.started", task)
            try:
                output = self.backend.run(task)
            except Exception as exc:
                message = redact_text(_shorten(f"{type(exc).__name__}: {exc}"))
                exhausted = task.attempts >= self.max_attempts
                task = self.store.update(
                    task.id,
                    status=FAILED if exhausted else PENDING,
                    error=message,
                    result="",
                )
                self._emit("attempt.failed", task)
                if exhausted:
                    self._emit("task.failed", task)
                    return task
                self._emit("task.retry", task)
                continue

            task = self.store.update(
                task.id, status=DONE, result=redact_text(output), error=""
            )
            self._emit("task.succeeded", task)
            return task

    def run_all(self, max_tasks: Optional[int] = None) -> List[Task]:
        completed: List[Task] = []
        while max_tasks is None or len(completed) < max_tasks:
            task = self.run_one()
            if task is None:
                break
            completed.append(task)
        return completed
