# OpenClaw delegation report

Date: 2026-11-20
Framework: `openclaw/` (stdlib-only orchestrator, env-only OpenRouter backend)
Credential policy: key loaded from the local OpenCode auth store into the process
environment only; no key value was written to a file, commit, task store, report,
or chat output. Outputs were redacted before display and storage.

## Tasks dispatched

| Task | Model role | Outcome |
|---|---|---|
| `review-evolution` | free reviewer | Completed |
| `draft-architecture` | free architect | Completed; output too generic to adopt verbatim |
| `draft-baseline` | free researcher | Failed with HTTP 429 (rate limit) |
| `review-openclaw` | free reviewer | Completed |

## Findings and disposition

### Evolution updater

The reviewer claimed the pipeline had no rollback handler. Verification against
`evolution-engine/src/evolution/updater.py` showed the `try/except` rollback path
already exists and is covered by
`tests/test_evolution.py::HookRepositoryUpdaterTests::test_updater_success_dry_run_and_rollback`.
The model's context was truncated, so the critical finding was a false positive.

Valid improvements were implemented anyway:

- `journal_id` now uses the full 64-character content digest instead of 12
  characters, removing a long-term collision risk.
- Both programmatic dry runs and real upgrades validate `apply_fn`, `verify_fn`
  and required hook commands before work starts. A CLI chain preview uses
  explicit no-op placeholders because it has no live transformation.
- An optional `checkpoint_verify_fn` now runs before any restore; a tampered
  checkpoint refuses rollback and records the reason in the report/journal.
- The journal has a terminal `RolledBack` state, so a crash/rollback is
  distinguishable from an incomplete `Failed` journal.

Tests were extended for the full digest, dry-run precondition failure, checkpoint
verification refusal, and the `RolledBack` terminal state.

### Architecture decision mapping

The architect could not infer AD-01..AD-30 from code alone and produced a
repetitive mapping derived only from the ten M-invariants. A repository search
confirmed no prior AD register existed. `reports/ARCHITECTURE_DECISIONS.md` now
establishes canonical AD-01..AD-30 meanings from the actual shipped decisions and
links each to implementing code. The exact M-01..M-10 labels are preserved from
`evolution-engine/src/evolution/invariants.py`.

### Baseline document

The researcher task hit HTTP 429. The backstop document
`evolution-engine/evolution/docs/BASELINE_ARCH_2026.md` was written directly. It
records the frozen epoch identity, evidence requirements, ISO digest fail-closed
policy, freeze procedure, and the independent
`B-1 -> M bridge -> B0 -> target` recovery lineage.

### OpenClaw security

The reviewer found no credential leakage or unsafe shell use in
`openclaw/backends.py`; credentials are read only from the environment and
outputs are redacted. It could not see `reporter.py` due context truncation.
That module was already covered by
`openclaw/tests/test_reporter.py`, including no-op behavior when Telegram
environment variables are absent and redaction of HTTP errors. No code change
was required.

## Verification after delegation

- `evolution-engine`: 161 Python tests OK.
- `openclaw`: 24 tests OK.
- Rust Stage A / rotation shell tests: OK.
- Source matrix and post-migration verification shell suites: OK.
- `cargo test --offline --locked`: 5 tests OK.

## Standing constraint

Telegram reporting remains a silent no-op until a bot token and chat ID are
provided. No credential value is stored in this report or the repository.
