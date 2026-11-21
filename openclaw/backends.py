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
import subprocess
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping, Sequence

from .core import AgentBackend, Task, redact_text

DEFAULT_FREE_MODELS: tuple[str, ...] = (
    "nvidia/nemotron-3.5-super-vl:free",
    "baidu/ernie-5.5-flash-preview:free",
    "inclusionai/ling-3.2-flash:free",
    "google/gemma-4-31b-it:free",
    "nvidia/nemotron-3.5-lightning:free",
    "google/gemma-4-26b-a4b-it:free",
    "dots-studio/dots-3-note-preview:free",
    "recursive/flint-v1.0:free",
    "nvidia/nemotron-3-ultra-550b-a55b:free",
    "openrouter/free",
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
        return redact_text(text)

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
        return redact_text("\n\n".join(sections))

    def request_body(self, task: Task) -> dict[str, Any]:
        model = getattr(task, "model", "") or self.model
        if model not in DEFAULT_FREE_MODELS:
            raise RuntimeError(
                f"model is not in the free-model allowlist: {model}"
            )
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
        return _clip(redact_text(content.strip()), self.max_output_chars)


class OllamaBackend(AgentBackend):
    """Local Ollama agent that can run allowlisted read-only commands.

    No credentials or network keys are used. Tool calls are executed only
    against a strict allowlist inside the task repository, so the agent can
    inspect code, logs and VM state without mutating the host.
    """

    API_URL = "http://127.0.0.1:11434/api/chat"
    DEFAULT_MODEL = "gemma3:4b"
    ALLOWED = re.compile(
        r"^(?:ls|find|cat|sed|grep|rg|head|tail|wc|pwd|uname|df|ps|date|"
        r"git\s+(?:status|log|diff|show|ls-files)|python3\s+-c|"
        r"VBoxManage\s+(?:list|showvminfo|snapshot\s+\S+\s+list))\b"
    )
    BLOCKED = re.compile(r"(?:rm\s|sudo|curl|wget|dd\s|mkfs|mount|umount|chmod|chown|\$\(|`|[|;><])")

    def __init__(self, model: str | None = None, *, opener: Callable[..., Any] | None = None,
                 timeout: float = 600.0, max_rounds: int = 4) -> None:
        self.model = model or self.DEFAULT_MODEL
        self.opener = opener or urllib.request.urlopen
        self.timeout = float(timeout)
        self.max_rounds = int(max_rounds)
        self.calls: list[dict[str, Any]] = []

    @property
    def enabled(self) -> bool:
        return True

    def __repr__(self) -> str:
        return f"OllamaBackend(model={self.model!r})"

    def build_prompt(self, task: Task) -> str:
        root = Path(task.repo_path).expanduser().resolve() if task.repo_path else None
        prompt = task.instructions.strip()
        if root and root.is_dir():
            try:
                entries = sorted(root.iterdir(), key=lambda p: p.name)
            except OSError:
                entries = []
            prompt = (f"Repository: {root}\nTop-level: " +
                      ", ".join(e.name for e in entries[:60]) + "\n\nTASK: " + prompt)
        return redact_text(prompt)

    def _run_command(self, command: str, task: Task) -> str:
        command = str(command).strip()
        if not command or self.BLOCKED.search(command) or not self.ALLOWED.match(command):
            return "command rejected by safety allowlist"
        root = Path(task.repo_path).expanduser().resolve() if task.repo_path else None
        try:
            proc = subprocess.run(command, shell=True, cwd=str(root) if root else None,
                                  capture_output=True, text=True, timeout=30)
            return _clip((proc.stdout or "") + "\n" + (proc.stderr or ""), 6000)
        except Exception as exc:  # noqa: BLE001
            return f"command failed: {self.redact(str(exc))}"

    @staticmethod
    def redact(text: Any) -> str:
        return redact_text(text)

    def run(self, task: Task) -> str:
        # gemma3:4b has no tool-call support; use fenced read-only commands instead.
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT +
             " To inspect files, output one safe read-only command in a ```bash fenced "
             "block; its output will be returned to you. Then give the final answer."},
            {"role": "user", "content": self.build_prompt(task)},
        ]
        final = ""
        for round_no in range(self.max_rounds):
            payload = json.dumps({
                "model": getattr(task, "model", "") or self.model,
                "messages": messages,
                "stream": False,
                "options": {"temperature": 0.2},
            }, ensure_ascii=True).encode("utf-8")
            request = urllib.request.Request(
                self.API_URL, data=payload,
                headers={"Content-Type": "application/json"}, method="POST",
            )
            try:
                with self.opener(request, timeout=self.timeout) as response:
                    data = json.loads(response.read().decode("utf-8", errors="replace"))
            except Exception as exc:  # noqa: BLE001
                raise RuntimeError(f"Ollama request failed: {self.redact(str(exc))}") from None
            message = data.get("message") or {}
            content = str(message.get("content") or "")
            final = content
            commands = re.findall(r"```(?:bash|sh|shell)\n(.*?)```", content, re.S)
            if not commands or round_no == self.max_rounds - 1:
                break
            outputs = [self._run_command(cmd, task) for cmd in commands[:3]]
            messages.append({"role": "assistant", "content": content})
            messages.append({"role": "user", "content": "COMMAND OUTPUT:\n" + "\n".join(outputs)})
            self.calls.append({"task_id": task.id, "model": self.model,
                               "commands": len(outputs)})
        if not final.strip():
            raise RuntimeError("Ollama returned an empty completion")
        return _clip(redact_text(final.strip()), 20000)


class CodexBackend(AgentBackend):
    """Senior developer lead: local authenticated Codex CLI agent.

    Codex runs non-interactively in workspace-write mode. It is instructed to
    confine its edits to autonomy/codex so its commits never sweep in work
    belonging to other agents or the other OpenCode session.
    """

    def __init__(self, model: str = "gpt-6-luna", *, timeout: float = 1800.0,
                 binary: str = "codex") -> None:
        self.model = model
        self.timeout = float(timeout)
        self.binary = binary
        self.calls: list[dict[str, Any]] = []

    @property
    def enabled(self) -> bool:
        return True

    def __repr__(self) -> str:
        return f"CodexBackend(model={self.model!r})"

    @staticmethod
    def redact(text: Any) -> str:
        return redact_text(text)

    def build_prompt(self, task: Task) -> str:
        root = Path(task.repo_path).expanduser().resolve() if task.repo_path else None
        brief = ""
        if root:
            brief_path = root / "autonomy" / "CODEX_BRIEF.md"
            if brief_path.is_file():
                brief = brief_path.read_text(encoding="utf-8", errors="replace")[:8000]
        return redact_text(
            (brief + "\n\n---\n\n" if brief else "") +
            f"You are the Senior Developer and lead of the development team.\n"
            f"TASK: {task.instructions.strip()}\n\n"
            "Write your findings, code, logs and solutions under autonomy/codex/. "
            "Do not modify reports/ or files owned by other agents. "
            "Never include API keys, tokens or credentials in any output. "
            "Return a concise Markdown summary of what you did and where you wrote it."
        )

    def run(self, task: Task) -> str:
        root = Path(task.repo_path).expanduser().resolve() if task.repo_path else Path.cwd()
        out = Path("/home/tak_0/.local/state/sunshine-orchestrator/codex") / f"{task.id}.md"
        out.parent.mkdir(parents=True, exist_ok=True)
        if out.exists():
            out.unlink()
        prompt = self.build_prompt(task)
        cmd = [self.binary, "exec", "-C", str(root), "--sandbox", "workspace-write",
               "--color", "never", "-m", self.model,
               "--output-last-message", str(out), "-"]
        try:
            proc = subprocess.run(cmd, input=prompt, capture_output=True, text=True,
                                  timeout=self.timeout, cwd=str(root))
        except subprocess.TimeoutExpired:
            raise RuntimeError("Codex timed out") from None
        except FileNotFoundError:
            raise RuntimeError("codex binary not found") from None
        if not out.exists():
            raise RuntimeError(f"Codex produced no final message (rc={proc.returncode}): "
                               + self.redact((proc.stderr or "")[-500:]))
        result = out.read_text(encoding="utf-8", errors="replace").strip()
        if not result:
            raise RuntimeError("Codex returned an empty completion")
        self.calls.append({"task_id": task.id, "model": self.model,
                           "prompt_chars": len(prompt)})
        return _clip(redact_text(result), 20000)
