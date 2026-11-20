"""OpenRouter backend tests: no real network calls and no credential literals."""

from __future__ import annotations

import json
import os
import secrets
import tempfile
import unittest
import urllib.error
import urllib.request
from pathlib import Path
from unittest import mock

from openclaw.backends import (
    DEFAULT_FREE_MODELS,
    MODEL_ROLES,
    OpenRouterBackend,
)
from openclaw.core import Task


class FakeResponse:
    def __init__(self, payload: dict) -> None:
        self.payload = payload

    def read(self) -> bytes:
        return json.dumps(self.payload).encode("utf-8")

    def __enter__(self) -> "FakeResponse":
        return self

    def __exit__(self, *_args: object) -> bool:
        return False


class OpenRouterBackendTests(unittest.TestCase):
    def setUp(self) -> None:
        self.key = "sk-or-v1-" + secrets.token_hex(24)

    def _backend(self, opener) -> OpenRouterBackend:
        return OpenRouterBackend(
            DEFAULT_FREE_MODELS[0],
            opener=opener,
            api_key_env="OPENCLAW_TEST_API_KEY",
            max_context_chars=4000,
        )

    def test_disabled_without_credentials(self) -> None:
        backend = self._backend(mock.Mock())
        with mock.patch.dict(os.environ, {"OPENCLAW_TEST_API_KEY": ""}):
            self.assertFalse(backend.enabled)
            with self.assertRaisesRegex(RuntimeError, "not set"):
                backend.run(Task(instructions="hello"))

    def test_request_and_response_without_network(self) -> None:
        opener = mock.Mock(return_value=FakeResponse({
            "choices": [{"message": {"content": "Finding: fail closed on missing signatures."}}]
        }))
        backend = self._backend(opener)
        task = Task(id="rev", title="Review", instructions="Audit signer validation", model=DEFAULT_FREE_MODELS[1])

        with mock.patch.dict(os.environ, {"OPENCLAW_TEST_API_KEY": self.key}):
            result = backend.run(task)

        self.assertEqual(result, "Finding: fail closed on missing signatures.")
        request = opener.call_args.args[0]
        self.assertEqual(request.get_header("Authorization"), "Bearer " + self.key)
        self.assertEqual(request.get_header("X-title"), "OpenClaw SunshineOS")
        body = json.loads(request.data)
        self.assertEqual(body["model"], DEFAULT_FREE_MODELS[1])
        self.assertIn("Audit signer validation", body["messages"][1]["content"])
        self.assertEqual(backend.calls[0]["task_id"], "rev")

    def test_repo_context_is_bounded_and_confined(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "repo"
            root.mkdir()
            (root / "notes.md").write_text("CONTEXT_MARKER: migration invariant", encoding="utf-8")
            outside = Path(tmp) / "secret.md"
            outside.write_text("OUTSIDE_MARKER: must not appear", encoding="utf-8")

            opener = mock.Mock(return_value=FakeResponse({
                "choices": [{"message": {"content": "ok"}}]
            }))
            backend = self._backend(opener)
            task = Task(
                instructions=(
                    "CONTEXT_FILES: notes.md, ../secret.md\n"
                    "Explain the migration invariant"
                ),
                repo_path=str(root),
            )
            with mock.patch.dict(os.environ, {"OPENCLAW_TEST_API_KEY": self.key}):
                backend.run(task)

            prompt = json.loads(opener.call_args.args[0].data)["messages"][1]["content"]
            self.assertIn("CONTEXT_MARKER: migration invariant", prompt)
            self.assertNotIn("OUTSIDE_MARKER", prompt)

    def test_http_error_is_redacted_and_raised(self) -> None:
        request = urllib.request.Request(OpenRouterBackend.API_URL, data=b"{}")
        error = urllib.error.HTTPError(
            OpenRouterBackend.API_URL, 401,
            f"Unauthorized Bearer {self.key}", {}, None,
        )
        error.request = request
        backend = self._backend(mock.Mock(side_effect=error))
        with mock.patch.dict(os.environ, {"OPENCLAW_TEST_API_KEY": self.key}):
            with self.assertRaises(RuntimeError) as caught:
                backend.run(Task(instructions="hello"))
        self.assertNotIn(self.key, str(caught.exception))
        self.assertIn("<redacted>", str(caught.exception))

    def test_model_roles_are_public_and_free(self) -> None:
        self.assertEqual(set(MODEL_ROLES), {"reviewer", "architect", "researcher"})
        for model in MODEL_ROLES.values():
            self.assertIn(model, DEFAULT_FREE_MODELS)
            self.assertTrue(model.endswith(":free"))


if __name__ == "__main__":
    unittest.main()
