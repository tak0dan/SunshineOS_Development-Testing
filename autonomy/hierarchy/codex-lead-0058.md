# codex-lead-0058 -> hierarchy

## Omarchy integration — Wave 2

Updated migration resume so it skips a completed operation only when a fresh, high-confidence probe confirms the expected state. Missing, inconclusive, or mismatched probes now trigger reconciliation and rerun, addressing stale completion markers after root snapshot rollback.

- **Code:** [executor.py](/home/tak_0/sunshineos-audit/SunshineOS_Development-Testing/evolution-engine/src/executor/executor.py)
- **Regression:** **OMR-003** in [test_executor.py](/home/tak_0/sunshineos-audit/SunshineOS_Development-Testing/evolution-engine/tests/test_executor.py); existing OMR-001 and OMR-002 remain in `test_omarchy_recovery_consistency.py`.
- **Omarchy survey and catalogue:** [omarchy-wave2.md](/home/tak_0/sunshineos-audit/SunshineOS_Development-Testing/autonomy/codex/omarchy-wave2.md). Upstream references are branch-view findings; source is not pinned to a commit.
- **Task notes and logs:** [autonomy/pull/codex-lead-0058](/home/tak_0/sunshineos-audit/SunshineOS_Development-Testing/autonomy/pull/codex-lead-0058).

**Verification:** `cd evolution-engine && python3 -m unittest tests.test_omarchy_recovery_consistency tests.test_executor` — 19 tests passed.

I could not commit: `git add` failed because `.git/index.lock` cannot be created on the read-only index.
