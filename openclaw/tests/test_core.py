"""Tests for task persistence, backends, and orchestration transitions."""

from __future__ import annotations

import json
import os
import shlex
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from openclaw.core import (
    DONE,
    FAILED,
    PENDING,
    RUNNING,
    LocalShellBackend,
    Orchestrator,
    StubBackend,
    Task,
    TaskStore,
)


class TaskStoreTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name) / "nested" / "tasks.json"
        self.store = TaskStore(self.path)

    def _task(self, task_id: str = "task-1") -> Task:
        return Task(
            id=task_id,
            title="Audit migration notes",
            instructions="python3 --version",
            repo_path=self.tmp.name,
        )

    def test_add_persists_and_reloads(self) -> None:
        task = self.store.add(self._task())
        self.assertTrue(self.path.exists())
        self.assertIn(task.id, json.loads(self.path.read_text(encoding="utf-8")))

        fresh = TaskStore(self.path)
        self.assertEqual(fresh.get(task.id).title, task.title)
        self.assertEqual(fresh.get(task.id).repo_path, self.tmp.name)
        self.assertEqual(fresh.next_pending().id, task.id)
        self.assertEqual(len(fresh.list()), 1)

    def test_update_and_status_filter(self) -> None:
        task = self.store.add(self._task())
        updated = self.store.update(task.id, status=DONE, result="all good", attempts=2)
        self.assertEqual(updated.status, DONE)
        self.assertEqual(updated.attempts, 2)
        self.assertNotEqual(updated.updated_at, task.updated_at)

        fresh = TaskStore(self.path)
        self.assertEqual(fresh.get(task.id).result, "all good")
        self.assertEqual([item.id for item in fresh.list(status=DONE)], [task.id])
        self.assertEqual(fresh.list(status=PENDING), [])
        self.assertIsNone(fresh.next_pending())

    def test_duplicate_id_and_unknown_fields_are_rejected(self) -> None:
        self.store.add(self._task())
        with self.assertRaises(ValueError):
            self.store.add(self._task())
        with self.assertRaises(ValueError):
            self.store.update("task-1", bogus="x")
        with self.assertRaises(KeyError):
            self.store.update("missing", status=DONE)

    def test_write_is_atomic_via_os_replace(self) -> None:
        with mock.patch("openclaw.core.os.replace", wraps=os.replace) as replace:
            self.store.add(self._task())
        self.assertEqual(replace.call_count, 1)
        self.assertEqual(Path(replace.call_args.args[1]), self.path)
        self.assertEqual(list(self.path.parent.glob(".*.json.tmp")), [])

    def test_corrupt_store_raises(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text("{not json", encoding="utf-8")
        with self.assertRaises(ValueError):
            TaskStore(self.path).list()


class OrchestratorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.store = TaskStore(Path(self.tmp.name) / "tasks.json")
        self.task = self.store.add(
            Task(id="a", title="Task A", instructions="noop", repo_path=self.tmp.name)
        )

    def test_retry_then_success_with_event_and_status_transitions(self) -> None:
        events: list[tuple[str, str, int]] = []
        backend = StubBackend(
            [RuntimeError("first"), RuntimeError("second"), "final result"]
        )
        seen_statuses: list[str] = []
        original_update = self.store.update

        def tracking(task_id: str, **changes: object) -> Task:
            seen_statuses.append(changes["status"])
            return original_update(task_id, **changes)

        with mock.patch.object(self.store, "update", side_effect=tracking):
            orchestrator = Orchestrator(
                self.store,
                backend,
                event_callback=lambda event, task: events.append(
                    (event, task.status, task.attempts)
                ),
                max_attempts=3,
            )
            final = orchestrator.run_one()

        self.assertEqual(final.status, DONE)
        self.assertEqual(final.attempts, 3)
        self.assertEqual(final.result, "final result")
        self.assertEqual(final.error, "")
        self.assertEqual(backend.calls, ["a", "a", "a"])
        self.assertEqual(
            seen_statuses, [RUNNING, PENDING, RUNNING, PENDING, RUNNING, DONE]
        )
        self.assertEqual(
            [event for event, _, _ in events],
            [
                "task.claimed",
                "attempt.started",
                "attempt.failed",
                "task.retry",
                "attempt.started",
                "attempt.failed",
                "task.retry",
                "attempt.started",
                "task.succeeded",
            ],
        )
        persisted = TaskStore(self.store.path).get("a")
        self.assertEqual(persisted.status, DONE)
        self.assertEqual(persisted.attempts, 3)

    def test_permanent_failure_stops_at_bounded_attempts(self) -> None:
        backend = StubBackend(
            [RuntimeError("still broken"), RuntimeError("still broken")]
        )
        orchestrator = Orchestrator(self.store, backend, max_attempts=2)
        final = orchestrator.run_one()

        self.assertEqual(final.status, FAILED)
        self.assertEqual(final.attempts, 2)
        self.assertIn("RuntimeError: still broken", final.error)
        self.assertEqual(len(backend.calls), 2)
        self.assertIsNone(self.store.next_pending())
        self.assertEqual(TaskStore(self.store.path).get("a").status, FAILED)

    def test_event_callback_errors_do_not_abort_tasks(self) -> None:
        def broken_callback(event: str, task: Task) -> None:
            raise RuntimeError("reporter offline")

        orchestrator = Orchestrator(
            self.store, StubBackend(["ok"]), event_callback=broken_callback
        )
        final = orchestrator.run_one()
        self.assertEqual(final.status, DONE)
        self.assertIsNotNone(orchestrator.last_event_error)

    def test_run_all_drains_pending_tasks(self) -> None:
        self.store.add(Task(id="b", title="Task B", instructions="noop"))
        orchestrator = Orchestrator(self.store, StubBackend(), max_attempts=1)
        results = orchestrator.run_all()
        self.assertEqual([task.id for task in results], ["a", "b"])
        self.assertTrue(all(task.status == DONE for task in results))
        self.assertIsNone(self.store.next_pending())


class LocalShellBackendTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)

    def test_command_runs_without_shell_interpretation(self) -> None:
        backend = LocalShellBackend(timeout=10)
        marker = Path(self.tmp.name) / "should-not-exist"
        task = Task(
            instructions=(
                f"{shlex.quote(sys.executable)} -c 'print(4)' ; "
                f"touch {shlex.quote(str(marker))}"
            )
        )
        result = backend.run(task)
        self.assertEqual(result.strip(), "4")
        self.assertFalse(marker.exists())

    def test_nonzero_exit_and_timeout_are_errors(self) -> None:
        backend = LocalShellBackend(timeout=10)
        failing = Task(instructions=f"{shlex.quote(sys.executable)} -c 'exit 7'")
        with self.assertRaises(RuntimeError):
            backend.run(failing)

        slow_backend = LocalShellBackend(timeout=0.2)
        slow = Task(
            instructions=f"{shlex.quote(sys.executable)} -c 'import time; time.sleep(5)'"
        )
        with self.assertRaises(TimeoutError):
            slow_backend.run(slow)


if __name__ == "__main__":
    unittest.main()
