"""Reporters for OpenClaw progress updates.

The Telegram reporter uses only :mod:`urllib.request`, reads credentials from
the environment, is a no-op until both are configured, and never lets an HTTP
failure propagate into the orchestrator.
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import TYPE_CHECKING, Any, Iterable, Mapping, Protocol, runtime_checkable

if TYPE_CHECKING:  # type-only import; avoids a runtime dependency on core
    from .core import Task

MAX_TELEGRAM_CHARS = 4096


@runtime_checkable
class Reporter(Protocol):
    """Minimal interface every reporter implements."""

    def send(self, message: str) -> None:
        """Deliver an already-formatted message."""

    def task_event(self, event: str, task: "Task") -> None:
        """Deliver a task lifecycle event."""


def escape_markdown(text: Any) -> str:
    """Escape characters meaningful in Telegram's legacy ``Markdown`` mode."""
    out = str(text)
    for char in ("_", "*", "`", "["):
        out = out.replace(char, "\\" + char)
    return out


def truncate_markdown(text: str, limit: int = MAX_TELEGRAM_CHARS) -> str:
    """Truncate while keeping fenced code blocks balanced."""
    if len(text) <= limit:
        return text
    marker = "\n… [truncated]"
    if limit <= len(marker):
        return marker[:limit]
    cut = text[: limit - len(marker)]

    # Drop a dangling fence opener rather than leaving an unclosed code block.
    if cut.count("```") % 2:
        index = cut.rfind("```")
        if index >= 0:
            cut = cut[:index]

    # Remove a partially-captured fence token (one or two backticks).
    trailing_backticks = len(cut) - len(cut.rstrip("`"))
    if trailing_backticks in (1, 2) and not cut.endswith("```"):
        cut = cut[: -trailing_backticks]
    return cut.rstrip() + marker


def format_task_event(event: str, task: "Task") -> str:
    """Render a compact Markdown progress update."""
    lines = [
        f"*OpenClaw* · `{escape_markdown(event)}`",
        f"*{escape_markdown(task.title)}*",
        f"id `{escape_markdown(task.id)}` · "
        f"status `{escape_markdown(task.status)}` · "
        f"attempts `{task.attempts}`",
    ]
    if task.repo_path:
        lines.append(f"repo `{escape_markdown(task.repo_path)}`")
    detail = task.result or task.error
    if detail:
        lines.append("```\n" + detail + "\n```")
    return "\n".join(lines)


class TelegramReporter:
    """Send updates via the Telegram Bot API ``sendMessage`` method.

    Credentials are read from ``TELEGRAM_BOT_TOKEN`` and ``TELEGRAM_CHAT_ID``.
    If either is empty, all methods return immediately without network I/O.
    """

    def __init__(
        self,
        *,
        token_env: str = "TELEGRAM_BOT_TOKEN",
        chat_id_env: str = "TELEGRAM_CHAT_ID",
        env: Mapping[str, str] | None = None,
        timeout: float = 5.0,
        api_base: str = "https://api.telegram.org",
    ) -> None:
        environ = os.environ if env is None else env
        self._token = str(environ.get(token_env, "")).strip()
        self._chat_id = str(environ.get(chat_id_env, "")).strip()
        self.enabled = bool(self._token and self._chat_id)
        self.timeout = float(timeout)
        self.api_base = api_base.rstrip("/")
        self.last_error: str = ""

    def __repr__(self) -> str:
        return f"TelegramReporter(enabled={self.enabled})"

    def _redact(self, text: Any) -> str:
        """Remove credentials from any diagnostic text before storing it."""
        result = str(text)
        for secret in (self._token, self._chat_id):
            if secret:
                result = result.replace(secret, "<redacted>")
        return result

    def send(self, message: str) -> None:
        if not self.enabled:
            return
        text = truncate_markdown(str(message))
        payload = json.dumps(
            {
                "chat_id": self._chat_id,
                "text": text,
                "parse_mode": "Markdown",
                "disable_web_page_preview": True,
            }
        ).encode("utf-8")
        url = f"{self.api_base}/bot{self._token}/sendMessage"
        request = urllib.request.Request(
            url,
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                response.read()
            self.last_error = ""
        except Exception as exc:  # network/HTTP failures are non-fatal
            self.last_error = self._redact(exc)

    def task_event(self, event: str, task: "Task") -> None:
        self.send(format_task_event(event, task))


class CompositeReporter:
    """Fan out messages to several reporters, isolating their failures."""

    def __init__(self, reporters: Iterable[Reporter] = ()) -> None:
        self.reporters: list[Reporter] = list(reporters)
        self.last_errors: list[str] = []

    def add(self, reporter: Reporter) -> None:
        self.reporters.append(reporter)

    def send(self, message: str) -> None:
        for reporter in self.reporters:
            try:
                reporter.send(message)
            except Exception as exc:
                self.last_errors.append(f"{type(reporter).__name__}: {exc}")

    def task_event(self, event: str, task: "Task") -> None:
        for reporter in self.reporters:
            try:
                handler = getattr(reporter, "task_event", None)
                if callable(handler):
                    handler(event, task)
                else:
                    reporter.send(format_task_event(event, task))
            except Exception as exc:
                self.last_errors.append(f"{type(reporter).__name__}: {exc}")
