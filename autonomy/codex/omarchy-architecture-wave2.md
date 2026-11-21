# Omarchy architecture enforcement — Wave 2

Survey anchor: `basecamp/omarchy` commit `e4635a4eea887d5c8dbd70427386f570c37a2a61`, recorded in `evolution-engine/fixtures/research/omarchy-update-recovery-wave1.json`. The pinned catalogue records SHA-256 and exact upstream paths; prior hash evidence is `autonomy/codex/omarchy-regression-wave1-source-hashes.log`.

## Catalogue findings and SunshineOS controls

| Exact Omarchy path | Observed architecture concern | Enforced SunshineOS implication |
|---|---|---|
| `docs/update-process.md` | Update lock and staged package/migration ordering; user notification is not migration execution. | Track package transaction and migration as separate observed state; notifications remain advisory. |
| `bin/omarchy-update` | User-facing update orchestration. | Use a journaled orchestration boundary and explicit failure state. |
| `bin/omarchy-migrate` | Per-user migration markers can outlive root state. | Reconcile per-user claims against freshly observed system postconditions. |
| `bin/omarchy-update-pacman-guard` | ALPM guard can be bypassed explicitly. | Treat transaction provenance as evidence, not inventory; detect bypass and require planned reconciliation. |
| `manual/30-updates.md` | Direct package updates can omit snapshot, migration, and config steps. | Require transaction plans and preserve config ownership/recovery evidence. |
| `manual/47-system-snapshots.md` | Root restore can leave `/home` markers intact. | Re-probe operation postconditions; a completion marker is not proof after recovery. |

## Code and regression

Added `OMR_004` to `evolution-engine/tests/test_omarchy_recovery_consistency.py`. It loads the pinned fixture and asserts that five high-risk source records continue to carry their enforcement implications. This couples the source survey to the policy controls, while keeping the research catalogue declarative. Runtime recovery enforcement remains `MigrationJournal.verify_completed_outputs` in `evolution-engine/src/evolution/journal_state.py`; `OMR_001` and `OMR_002` already verify matching and missing observed hashes.

Architecture grounding: `reports/ARCHITECTURE_DECISIONS.md` AD-05 (observed installation authoritative), AD-10 (journal/state separation), AD-11 (checkpoint and restore), AD-16 (verification), and AD-21 (user data separate). The matching mandate invariants are M-04, M-06, M-09, and M-10.

## Verification

From `evolution-engine/`:

```text
python3 -m unittest tests.test_omarchy_recovery_consistency -v
Ran 3 tests in 0.001s
OK
```

Full captured output: `autonomy/codex/omarchy-architecture-wave2-test.log`.
