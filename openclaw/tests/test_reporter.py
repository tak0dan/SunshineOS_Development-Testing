"""Tests for reporter behavior without any network access."""

from __future__ import annotations

import json
import secrets
import unittest
import urllib.error
from unittest import mock

from openclaw.core import Task
from openclaw.reporter import (
    MAX_TELEGRAM_CHARS,
    CompositeReporter,
    TelegramReporter,
    format_task_event,
    truncate_markdown,
)


class TelegramReporterTests(unittest.TestCase):
    @staticmethod
    def _fake_credentials() -> dict[str, str]:
        # Generated at runtime: no credential literals live in this repository.
        return {
            "TELEGRAM_BOT_TOKEN": "test-token-" + secrets.token_hex(6),
            "TELEGRAM_CHAT_ID": "test-chat-" + secrets.token_hex(6),
        }

    def test_no_env_is_a_silent_no_op(self) -> None:
        reporter = TelegramReporter(env={})
        self.assertFalse(reporter.enabled)
        with mock.patch("openclaw.reporter.urllib.request.urlopen") as urlopen:
            reporter.send("hello")
            reporter.task_event("task.succeeded", Task(id="x", title="X", result="ok"))
        urlopen.assert_not_called()
        self.assertEqual(reporter.last_error, "")

    def test_partial_env_is_also_a_no_op(self) -> None:
        credentials = self._fake_credentials()
        reporter = TelegramReporter(env={"TELEGRAM_BOT_TOKEN": credentials["TELEGRAM_BOT_TOKEN"]})
        with mock.patch("openclaw.reporter.urllib.request.urlopen") as urlopen:
            reporter.send("hello")
        self.assertFalse(reporter.enabled)
        urlopen.assert_not_called()

    def test_enabled_reporter_posts_json_without_network(self) -> None:
        credentials = self._fake_credentials()
        reporter = TelegramReporter(env=credentials)
        self.assertTrue(reporter.enabled)
        self.assertNotIn(credentials["TELEGRAM_BOT_TOKEN"], repr(reporter))

        with mock.patch("openclaw.reporter.urllib.request.urlopen") as urlopen:
            urlopen.return_value.__enter__.return_value.read.return_value = b"{}"
            reporter.send("plain update")

        urlopen.assert_called_once()
        request = urlopen.call_args.args[0]
        self.assertEqual(request.get_method(), "POST")
        self.assertEqual(json.loads(request.data)["text"], "plain update")
        self.assertEqual(json.loads(request.data)["parse_mode"], "Markdown")
        self.assertIn(credentials["TELEGRAM_BOT_TOKEN"], request.full_url)
        self.assertEqual(reporter.last_error, "")

    def test_http_error_is_swallowed_and_redacted(self) -> None:
        credentials = self._fake_credentials()
        token = credentials["TELEGRAM_BOT_TOKEN"]
        url = "https://api.telegram.org/bot" + token + "/sendMessage"
        error = urllib.error.HTTPError(
            url, 400, f"Bad Request for {url}", {}, None
        )

        reporter = TelegramReporter(env=credentials)
        with mock.patch("openclaw.reporter.urllib.request.urlopen", side_effect=error):
            reporter.send("hello")  # must not raise

        self.assertNotIn(token, reporter.last_error)
        self.assertIn("<redacted>", reporter.last_error)

    def test_event_message_is_compact_markdown_with_fenced_block(self) -> None:
        message = format_task_event(
            "task.failed", Task(id="abc", title="Audit", status="failed", error="boom")
        )
        self.assertIn("*Audit*", message)
        self.assertIn("```\nboom\n```", message)

    def test_truncation_respects_limit_and_balances_fences(self) -> None:
        long_text = "header\n```\n" + ("x" * (MAX_TELEGRAM_CHARS * 2))
        truncated = truncate_markdown(long_text)
        self.assertLessEqual(len(truncated), MAX_TELEGRAM_CHARS)
        self.assertTrue(truncated.endswith("[truncated]"))
        self.assertEqual(truncated.count("```") % 2, 0)


class CompositeReporterTests(unittest.TestCase):
    def test_fans_out_and_isolates_failures(self) -> None:
        first = mock.Mock()
        second = mock.Mock()
        second.send.side_effect = RuntimeError("down")
        third = mock.Mock()
        composite = CompositeReporter([first, second, third])

        composite.send("hello")
        first.send.assert_called_once_with("hello")
        third.send.assert_called_once_with("hello")
        self.assertEqual(len(composite.last_errors), 1)

    def test_task_event_uses_native_handler_when_available(self) -> None:
        reporter = mock.Mock()
        reporter.task_event = mock.Mock()
        task = Task(id="t", title="T")
        CompositeReporter([reporter]).task_event("task.succeeded", task)
        reporter.task_event.assert_called_once_with("task.succeeded", task)


if __name__ == "__main__":
    unittest.main()
