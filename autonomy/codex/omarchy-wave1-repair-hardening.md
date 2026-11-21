# Omarchy repair tooling survey — wave 1 hardening

## Survey catalogue

The pinned Omarchy checkout is commit `e4635a4eea887d5c8dbd70427386f570c37a2a61`; its six catalogued files and SHA-256 values are in `evolution-engine/fixtures/research/omarchy-update-recovery-wave1.json` (`CAT_006`). The checkout snapshot is useful for source provenance, but does not prove runtime behavior.

| Exact Omarchy path | Repair/update behavior or hazard | SunshineOS implication |
|---|---|---|
| `docs/update-process.md` | Describes locking, pacman guard, package update, migrations, and login notification. | Keep package and migration status separately observed. |
| `bin/omarchy-update` | Main update orchestration entry point. | Require journaled stage boundaries; invocation is not completion evidence. |
| `bin/omarchy-migrate` | Uses user-scoped migration markers. | Reconcile claims against journal and fresh system state. |
| `bin/omarchy-update-pacman-guard` | Blocks direct upgrades unless an explicit workflow allowance exists; bypass is possible. | Treat guards as advisory; package inventory and transaction evidence remain authoritative. |
| `manual/30-updates.md` | Describes snapshots, migrations, configuration work, and package updates; direct package updates may skip steps. | Require reviewed plans and recovery evidence. |
| `manual/47-system-snapshots.md` | Root restore may retain `/home`, leaving user markers after root effects have rolled back; documented snapshot behavior is setup-specific. | Re-probe postconditions after restore; never infer snapshot support from Omarchy documentation. |

## Change

`evolution-engine/src/evolution/markers.py::validate_user_completion_markers` already compared marker, completed-journal, and fresh-observation values but treated any equal nonempty strings as hashes. It now requires lowercase 64-character SHA-256 values at all three evidence boundaries. Malformed evidence fails closed and cannot confirm completion. This remains read-only; recovery decisions stay with the caller.

Regression IDs `OMR-009` and `OMR-010` cover malformed marker/journal hashes and malformed fresh observation. Existing `OMR-005..008` cover agreement, rollback divergence, orphan markers, and missing observations.

Grounding: mandate priorities for stability, recovery, and observed-state authority; architecture decisions AD-05, AD-11, AD-16, and AD-21.

## Verification

From `evolution-engine/`:

```sh
python3 -m unittest tests.test_omarchy_marker_reconciliation tests.test_omarchy_recovery_consistency tests.test_research_catalog -v
```

Result: **15 tests passed**. Captured output: `autonomy/codex/omarchy-wave1-repair-hardening-test.log`.
