# Solutions

# Omarchy migration survey — wave 1 deepening

Surveyed the pinned Omarchy checkout at commit `e4635a4eea887d5c8dbd70427386f570c37a2a61`. All six source hashes recorded in the research catalogue match the local checkout.

| Omarchy source path | Finding and SunshineOS lesson |
|---|---|
| `docs/update-process.md` | Updates coordinate package operations, migrations, and notifications. Track transaction and migration completion separately. |
| `bin/omarchy-update` | Provides an explicit update entry point. Journal workflow steps; the entry point alone does not prove completion. |
| `bin/omarchy-migrate` | Uses per-user marker files under `$HOME/.local/state/omarchy/migrations`. Treat markers as claims and reconcile them with journal and system state. |
| `bin/omarchy-update-pacman-guard` | Restricts direct upgrades unless the workflow allows them. Detect bypasses; still verify package state and transaction evidence. |
| `manual/30-updates.md` | The documented update sequence includes snapshots, migrations, configuration, and packages. Preserve transaction plans and configuration ownership evidence. |
| `manual/47-system-snapshots.md` | Root restore leaves `/home` intact, so markers can outlive reverted root changes. The described snapshot support is Limine-specific. |

Implemented [`validate_user_completion_markers`](</home/tak_0/sunshineos-audit/SunshineOS_Development-Testing/evolution-engine/src/evolution/markers.py>) to reject orphaned markers, missing observations, and marker/journal/root hash mismatches. Regression cases OMR-005 through OMR-008 are in [test_omarchy_marker_reconciliation.py](/home/tak_0/sunshineos-audit/SunshineOS_Development-Testing/evolution-engine/tests/test_omarchy_marker_reconciliation.py).

Verification from `evolution-engine/`:

```text
python3 -m unittest tests/test_omarchy_marker_reconciliation.py tests/test_omarchy_recovery_consistency.py tests/test_research_catalog.py -v

Ran 13 tests in 0.006s

OK
```

The complete survey and test output are in [the deliverable](/home/tak_0/sunshineos-audit/SunshineOS_Development-Testing/autonomy/codex/omarchy-wave1-deepening.md) and [test log](/home/tak_0/sunshineos-audit/SunshineOS_Development-Testing/autonomy/codex/omarchy-wave1-deepening-test.log). Pull notes are under `autonomy/pull/codex-lead-omarchy-wave1-deepening/`.

The change remains uncommitted: `.git` is read-only in this workspace, and `git add` failed while creating `.git/index.lock`.
