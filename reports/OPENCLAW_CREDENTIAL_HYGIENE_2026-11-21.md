# OpenClaw credential hygiene review — 2026-11-21

## Source

OpenClaw task `openclaw-hygiene` was delegated with the reviewer role but all supplied credentials
returned `HTTP 429` during completion calls. This report is the manual backstop and records the
review and fixes applied directly to `openclaw/`.

No credential values, tokens, or key material were written to this report, the task store, tests,
or commits.

## Findings and fixes

### H1 — credential-shaped text could be sent to the model

`OpenRouterBackend.build_prompt()` embedded repository context files verbatim. If a context file
contained a credential-shaped token, that token would be sent to the remote model and could be
 echoed back into the task result.

**Fix:** `build_prompt()` now returns `redact_text(prompt)`, using the shared scrubber in
`openclaw/core.py`. Completion content is also redacted before it is returned.

### H2 — failed or shell-backed agents could persist raw output

The orchestrator persisted backend output and error strings directly. A backend other than
`OpenRouterBackend` (for example `LocalShellBackend`) could emit a credential into `result` or
`error`, which would then be written to the task store and forwarded to reporters.

**Fix:** `Orchestrator.run_one()` redacts both success output and error text before updating the
store. `TaskStore._load()` and `TaskStore._save()` also redact string fields defensively, so an
older store containing a credential cannot propagate it to an agent or a new write.

### H3 — `--model` could bypass the free-model role allowlist

`OpenRouterBackend.request_body()` accepted any model id from the CLI `--model` flag or the task's
`model` field. Only the role helper was constrained to `DEFAULT_FREE_MODELS`.

**Fix:** `request_body()` now rejects any model not in `DEFAULT_FREE_MODELS`. There is no paid-model
escape hatch and no credential is required in the repository to check the allowlist.

### H4 — reporter fan-out kept unredacted failures

`CompositeReporter.last_errors` stored exception text from reporters without scrubbing. Reporter
exceptions normally contain only local messages, but a URL-bearing transport error could include a
token.

**Fix:** the shared `redact_text()` helper is now the single scrubber used by the backend,
orchestrator, store, and reporters through their existing redaction paths. No reporter stores raw
exception text with a credential shape.

## Regression evidence

| Test | Result |
|---|---|
| `python3 -m unittest discover -s openclaw/tests` | 28 tests, OK (was 24; +4 hygiene tests) |
| `test_non_free_model_is_rejected` | paid model override fails closed |
| `test_prompt_and_completion_are_redacted` | context and echoed tokens become `<redacted>` |
| `test_orchestrator_redacts_backend_output_before_persistence` | backend output is scrubbed before store write |
| `test_loaded_secrets_are_redacted` | an existing store cannot re-emit a token |

Telegram remains a no-op until a bot token and chat ID are supplied through the environment; none
are present in this work.
