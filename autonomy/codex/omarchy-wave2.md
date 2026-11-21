# Omarchy integration — Wave 2

Date: 2026-11-21
Scope: connect the snapshot rollback finding from `omarchy-wave1.md` to the real migration resume path.

## Survey and catalogue

These are exact upstream paths from the `basecamp/omarchy` `quattro` branch view. The snapshot remains unpinned, so the references are useful research leads rather than immutable/hash-verified source evidence.

| Upstream path | Finding | Integration point |
|---|---|---|
| `manual/47-system-snapshots.md` | Root snapshot rollback does not restore `/home`; user-resident completion markers can therefore survive rollback. Snapshot support is tied to the documented Limine flow. | `evolution-engine/src/executor/executor.py::execute_plan`, resume reconciliation block. A journal marker is not sufficient to skip an operation. |
| `manual/30-updates.md` | The supported update workflow includes snapshot, migrations, configuration work, and package updates; direct package updates can bypass that workflow. | Resume must verify observed operation postconditions independently of how a marker was written. |
| `docs/update-process.md` | Per-user markers are used in migration/update flows, while direct package transactions can bypass the wrapper. | Unknown or unavailable postcondition probes must not be interpreted as successful completion. |
| `manual/31-dotfiles.md` | User hooks and system configuration have distinct ownership; a documented resync can overwrite changes. | Preserve explicit reconcile/re-execution behavior; do not overwrite configuration based on a stale marker. |
| `docs/file-layout.md` | System defaults, per-user seeding, provisioning, and migrations have separate locations and deferred work can be queued. | Recovery decisions must account for split state and remain safe to retry. |

Wave 1 additionally catalogued `docs/update-process.md` and `manual/30-updates.md` at `autonomy/codex/omarchy-wave1.md`. The references there and here remain branch-view findings pending a pinned upstream commit and archived source snapshot.

## Implementation

In `evolution-engine/src/executor/executor.py::execute_plan`, resume now skips a journal-completed operation only if a fresh probe exists, has `high` confidence, and matches the recorded expected state. Missing probes, unknown/low-confidence probes, or mismatches are journaled as `Reconcile` evidence and the operation is executed again. This closes the stale user-marker/root-rollback case at the actual resume decision point.

Regression test **OMR-003**, `evolution-engine/tests/test_executor.py::ExecutorTests.test_OMR_003_resume_does_not_skip_completed_marker_without_probe`, simulates a completed legacy operation for which no current-state probe exists and verifies that resume reconciles and reruns it. Existing OMR-001/002 cover matching, mismatch, absent observation, and absent output hash in `evolution-engine/tests/test_omarchy_recovery_consistency.py`.

## Verification

Exact command, run from `evolution-engine/`:

```text
python3 -m unittest tests.test_omarchy_recovery_consistency tests.test_executor
...................
Ran 19 tests in 0.146s
OK
```

## Evidence and limits

- Source: `evolution-engine/src/executor/executor.py`
- Tests: `evolution-engine/tests/test_executor.py` (OMR-003); `evolution-engine/tests/test_omarchy_recovery_consistency.py` (OMR-001, OMR-002)
- Prior survey: `autonomy/codex/omarchy-wave1.md`
- Relevant architecture grounding: AD-04/05/10/11/16/21/22 and M-04/06/09/10.
- This does not claim Omarchy snapshot compatibility or implement snapshot discovery. Existing capability qualification remains responsible for deciding whether snapshot-specific recovery is available. Upstream provenance remains unpinned.
