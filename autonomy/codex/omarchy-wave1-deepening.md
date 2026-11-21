# Omarchy migration engine survey — wave 1 deepening

## Survey scope and provenance

Surveyed the local Omarchy source checkout at commit `e4635a4eea887d5c8dbd70427386f570c37a2a61` (`/home/tak_0/.local/state/sunshine-orchestrator/iso/repos/omarchy`). The six exact source paths below were SHA-256 checked against `evolution-engine/fixtures/research/omarchy-update-recovery-wave1.json`; all matched. This confirms the pinned local snapshot, not runtime behavior on a live Omarchy installation.

| Source path | Finding | SunshineOS control and limit |
|---|---|---|
| `docs/update-process.md` | Update orchestration includes locking, pacman guard, package updates, migration execution, and login notification. | Keep package transaction completion and migration completion as separately observed state; a queued notification does not prove either. |
| `bin/omarchy-update` | User-facing update orchestrator. | Use an explicit, journaled workflow boundary; do not infer operation completion from the entry point returning or a notification. |
| `bin/omarchy-migrate` | Migration scripts are selected by absence of per-user files under `$HOME/.local/state/omarchy/migrations`; pending state is user-scoped. | Treat these files as claims. Reconcile them against the authoritative journal and freshly observed root effects. Marker presence alone is insufficient. |
| `bin/omarchy-update-pacman-guard` | ALPM guard restricts direct system upgrades unless the update workflow grants an allowance. | Detect package-manager bypasses and require a complete planned transaction before accepting package state. Guards remain bypassable, so inventory and transaction evidence are still required. |
| `manual/30-updates.md` | Supported update sequence includes snapshot, migrations, configuration updates, and package updates; direct pacman use can skip steps. | Require transaction plans, explicit configuration ownership, and recovery evidence. Documentation is not proof of runtime qualification. |
| `manual/47-system-snapshots.md` | Restore rolls back root but retains `/home`; per-user migration records can claim a migration is complete after its root changes have been reverted. The described snapshot feature is Limine-specific. | Re-probe postconditions during recovery and fail closed on missing or mismatched evidence. Do not generalize Limine snapshot behavior to other boot setups. |

Catalogue path: [omarchy-update-recovery-wave1.json](/home/tak_0/sunshineos-audit/SunshineOS_Development-Testing/evolution-engine/fixtures/research/omarchy-update-recovery-wave1.json). The fixture records all six hashes and source limitations. Research validation is covered by `CAT_006` in `evolution-engine/tests/test_research_catalog.py`.

## Repository grounding

The migration mandate prioritizes installation-state authority, staged/recoverable migration, and separation of migration knowledge from execution (mandate §§1–5; see [mandate](/home/tak_0/sunshineos-audit/SunshineOS_Development-Testing/reports/USER_MIGRATION_MANDATE_2026-11-21.md)). Applicable decisions are AD-05 (observed installation authoritative), AD-11/12 (checkpoint and staged/recoverable transition), AD-17 (integrity-tracked ledger), and AD-21 (user data separate) in [architecture decisions](/home/tak_0/sunshineos-audit/SunshineOS_Development-Testing/reports/ARCHITECTURE_DECISIONS.md). Existing code in `evolution-engine/src/evolution/journal_state.py::MigrationJournal.verify_completed_outputs` checks journal completion claims against observed output hashes; existing `evolution-engine/tests/test_omarchy_recovery_consistency.py` covers OMR-001/002 and catalogue controls OMR-004.

## Implementation

Added `evolution-engine/src/evolution/markers.py::validate_user_completion_markers`. It accepts user-marker hashes, hashes for journaled completed operations, and hashes from fresh system discovery. It rejects orphan markers, missing evidence, marker/journal disagreement, and root/journal disagreement. It is read-only: callers decide recovery action only after validation. This closes the specific snapshot rollback inconsistency without treating another system's per-user marker format as a SunshineOS execution mechanism.

Regression coverage: `evolution-engine/tests/test_omarchy_marker_reconciliation.py` — OMR-005 accepts consistent evidence; OMR-006 rejects a rolled-back root effect; OMR-007 rejects an orphan marker; OMR-008 fails closed when current state was not observed.

## Verification

Command (from `evolution-engine/`):

```text
python3 -m unittest tests/test_omarchy_marker_reconciliation.py tests/test_omarchy_recovery_consistency.py tests/test_research_catalog.py -v
```

Result: **Ran 13 tests in 0.006s — OK**. Full output is preserved at [test log](/home/tak_0/sunshineos-audit/SunshineOS_Development-Testing/autonomy/codex/omarchy-wave1-deepening-test.log).

## Change summary

- New production source: `evolution-engine/src/evolution/markers.py`.
- New regression tests: `evolution-engine/tests/test_omarchy_marker_reconciliation.py`.
- Survey, provenance, limitations, and rationale: this file.
- Pull notes and command evidence: `autonomy/pull/codex-lead-omarchy-wave1-deepening/`.
- Commit could not be created: `.git` is read-only here and `git add` failed while creating `.git/index.lock`; details are in the test log.
