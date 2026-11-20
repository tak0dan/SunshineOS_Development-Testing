"""Agent backends backed by models available through OpenRouter.

Credentials are read from the environment only and are never written to the
task store, logs, reports, or this repository. The backend uses stdlib
``urllib.request`` and takes an injectable opener so tests never touch the
network. Model identifiers are public identifiers, not secrets.
"""
from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping, Sequence

from .core import AgentBackend, Task

DEFAULT_FREE_MODELS: tuple[str, ...] = (
    "nvidia/nemotron-3.5-super-vl:free",
    "baidu/ernie-5.5-flash-preview:free",
    "inclusionai/ling-3.2-flash:free",
    "google/gemma-4-31b-it:free",
    "nvidia/nemotron-3.5-lightning:free",
)

MODEL_ROLES: Mapping[str, str] = {
    "reviewer": DEFAULT_FREE_MODELS[0],
    "architect": DEFAULT_FREE_MODELS[1],
    "researcher": DEFAULT_FREE_MODELS[2],
}

SYSTEM_PROMPT = (
    "You are a SunshineOS development subagent working on an evolutionary "
    "Arch-to-SunshineOS migration engine. Return concise, actionable Markdown. "
    "Cite exact repository paths and identifiers. Never output API keys, tokens, "
    "passwords, or other credentials. Prefer knowledge that remains valid "
    "across decades: invariants, capability checks, semantic transitions, and "
    "verifiable desired state rather than release-specific scripts."
)

SECRET_PATTERN = re.compile(r"sk-or-v1-[A-Za-z0-9]+|Bearer\s+[A-Za-z0-9._-]+")
CONTEXT_DIRECTIVE = re.compile(r"^CONTEXT_FILES:\s*(.+)$", re.MULTILINE)


def _clip(text: str, limit: int) -> str:
    if limit <= 0:
        return ""
    text = str(text)
    return text if len(text) <= limit else text[: limit - 1].rstrip() + "…"


class OpenRouterBackend(AgentBackend):
    """Delegate a task to a free OpenRouter coding model.

    ``task.instructions`` is treated as the user prompt. A line beginning with
    ``CONTEXT_FILES:`` lists comma-separated repository-relative paths to embed
    before the prompt. Paths are confined to ``task.repo_path``.
    """

    API_URL = "https://openrouter.ai/api/v1/chat/completions"

    def __init__(
        self,
        model: str | None = None,
        *,
        api_key_env: str = "OPENROUTER_API_KEY",
        opener: Callable[..., Any] | None = None,
        timeout: float = 300.0,
        max_context_chars: int = 12000,
        max_output_chars: int = 20000,
        referer: str = "https://github.com/tak0dan/SunshineOS_Development-Testing",
        title: str = "OpenClaw SunshineOS",
    ) -> None:
        if timeout <= 0:
            raise ValueError("timeout must be positive")
        if max_context_chars < 0 or max_output_chars <= 0:
            raise ValueError("invalid context/output limits")
        self.model = model or DEFAULT_FREE_MODELS[0]
        self.api_key_env = api_key_env
        self.opener = opener or urllib.request.urlopen
        self.timeout = float(timeout)
        self.max_context_chars = int(max_context_chars)
        self.max_output_chars = int(max_output_chars)
        self.referer = referer
        self.title = title
        self.calls: list[dict[str, Any]] = []

    @property
    def enabled(self) -> bool:
        return bool(self._key())

    def __repr__(self) -> str:
        return f"OpenRouterBackend(enabled={self.enabled}, model={self.model!r})"

    def _key(self) -> str:
        return str(os.environ.get(self.api_key_env, "")).strip()

    @staticmethod
    def redact(text: Any) -> str:
        return SECRET_PATTERN.sub("<redacted>", str(text))

    def _repo_root(self, task: Task) -> Path | None:
        if not task.repo_path:
            return None
        root = Path(task.repo_path).expanduser().resolve()
        if not root.is_dir():
            raise FileNotFoundError(f"repo path is not a directory: {root}")
        return root

    def _context_files(self, task: Task, root: Path) -> list[Path]:
        requested: list[str] = []
        match = CONTEXT_DIRECTIVE.search(task.instructions)
        if match:
            requested.extend(part.strip() for part in match.group(1).split(","))
        for candidate in re.findall(r"`([^`]+)`", task.instructions):
            if candidate.endswith((".py", ".md", ".toml", ".rs", ".sh", ".json", ".txt")):
                requested.append(candidate)
        resolved: list[Path] = []
        seen: set[Path] = set()
        for name in requested:
            if not name:
                continue
            path = Path(name).expanduser()
            if not path.is_absolute():
                path = root / path
            try:
                path = path.resolve()
                path.relative_to(root)
            except (ValueError, OSError):
                continue
            if path.is_file() and path not in seen:
                seen.add(path)
                resolved.append(path)
        return resolved

    def build_prompt(self, task: Task) -> str:
        """Assemble bounded repository context and the task prompt."""
        root = self._repo_root(task)
        if root is None:
            return task.instructions.strip()
        sections: list[str] = [f"Repository: {root}"]
        try:
            entries = sorted(root.iterdir(), key=lambda p: p.name)
        except OSError as exc:
            raise RuntimeError(f"cannot read repository: {exc}") from exc
        sections.append("Top-level entries: " + ", ".join(
            entry.name + ("/" if entry.is_dir() else "") for entry in entries[:100]
        ))
        budget = self.max_context_chars
        for path in self._context_files(task, root):
            try:
                content = path.read_text(encoding="utf-8", errors="replace")
            except OSError as exc:
                sections.append(f"FILE {path.relative_to(root)}: unreadable ({exc})")
                continue
            relative = path.relative_to(root).as_posix()
            header = f"FILE {relative}:\n"
            allowance = max(0, budget - len(header) - len("\n".join(sections)) - 2)
            if allowance <= 0:
                sections.append(f"FILE {relative}: omitted (context budget exhausted)")
                continue
            sections.append(header + _clip(content, allowance))
            budget -= min(allowance, len(content))
        sections.append("TASK: " + task.instructions.strip())
        return "\n\n".join(sections)

    def request_body(self, task: Task) -> dict[str, Any]:
        model = getattr(task, "model", "") or self.model
        return {
            "model": model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": self.build_prompt(task)},
            ],
            "temperature": 0.2,
        }

    def run(self, task: Task) -> str:
        key = self._key()
        if not key:
            raise RuntimeError(f"{self.api_key_env} is not set; OpenRouter delegation is disabled")
        body = self.request_body(task)
        payload = json.dumps(body, ensure_ascii=True).encode("utf-8")
        request = urllib.request.Request(
            self.API_URL,
            data=payload,
            headers={
                "Authorization": "Bearer " + key,
                "Content-Type": "application/json",
                "HTTP-Referer": self.referer,
                "X-Title": self.title,
            },
            method="POST",
        )
        try:
            with self.opener(request, timeout=self.timeout) as response:
                raw = response.read()
            data = json.loads(raw.decode("utf-8", errors="replace"))
        except urllib.error.HTTPError as exc:
            raise RuntimeError(
                f"OpenRouter HTTP {exc.code}: {self.redact(exc)}"
            ) from None
        except Exception as exc:
            raise RuntimeError(f"OpenRouter request failed: {self.redact(exc)}") from None

        choices = data.get("choices") if isinstance(data, dict) else None
        if not choices or not isinstance(choices, list):
            detail = self.redact(data.get("error", "no completion choices"))
            raise RuntimeError(f"OpenRouter returned no completion: {detail}")
        message = choices[0].get("message") or {}
        content = message.get("content")
        if not isinstance(content, str) or not content.strip():
            raise RuntimeError("OpenRouter returned an empty completion")
        self.calls.append({
            "task_id": task.id,
            "model": body["model"],
            "prompt_chars": len(body["messages"][1]["content"]),
        })
        return _clip(content.strip(), self.max_output_chars)
