"""OpenClaw -- a small, dependency-free agent orchestration framework.

OpenClaw coordinates multiple development and audit agents contributing to the
SunshineOS evolutionary migration. Tasks are persisted atomically to a JSON
file, dispatched through a pluggable :class:`~openclaw.core.AgentBackend`, and
their progress is broadcast to reporters (for example, a Telegram bot) through
an event callback. The framework deliberately uses only the Python standard
library and never executes commands through a shell.
"""

from .backends import DEFAULT_FREE_MODELS, MODEL_ROLES, OpenRouterBackend
from .core import (
    AgentBackend,
    LocalShellBackend,
    Orchestrator,
    StubBackend,
    Task,
    TaskStore,
)

__all__ = [
    "AgentBackend",
    "DEFAULT_FREE_MODELS",
    "LocalShellBackend",
    "MODEL_ROLES",
    "OpenRouterBackend",
    "Orchestrator",
    "StubBackend",
    "Task",
    "TaskStore",
]

__version__ = "0.1.0"
