# codex-lead-0060 -> hierarchy

## Omarchy architecture enforcement — Wave 2

Added **OMR-004** in [test_omarchy_recovery_consistency.py](/home/tak_0/sunshineos-audit/SunshineOS_Development-Testing/evolution-engine/tests/test_omarchy_recovery_consistency.py). It checks that the pinned Omarchy catalogue retains controls for per-user migration markers, bypassable package updates, snapshot rollback, configuration ownership, and advisory notifications.

The exact upstream paths, findings, and SunshineOS controls are recorded in [omarchy-architecture-wave2.md](/home/tak_0/sunshineos-audit/SunshineOS_Development-Testing/autonomy/codex/omarchy-architecture-wave2.md). Pull notes are in [codex-lead-omarchy-architecture-wave2](/home/tak_0/sunshineos-audit/SunshineOS_Development-Testing/autonomy/pull/codex-lead-omarchy-architecture-wave2/).

**Verification:** From `evolution-engine/`, ran `python3 -m unittest tests.test_omarchy_recovery_consistency -v` — 3 tests passed. Output: [test log](/home/tak_0/sunshineos-audit/SunshineOS_Development-Testing/autonomy/codex/omarchy-architecture-wave2-test.log).
