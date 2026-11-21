# Solutions

## Omarchy wave 1 repair hardening

Hardened `validate_user_completion_markers` in [markers.py](/home/tak_0/sunshineos-audit/SunshineOS_Development-Testing/evolution-engine/src/evolution/markers.py:13) to reject malformed SHA-256 evidence from markers, the completed journal, or fresh system observations. Added regressions **OMR-009** and **OMR-010** in [test_omarchy_marker_reconciliation.py](/home/tak_0/sunshineos-audit/SunshineOS_Development-Testing/evolution-engine/tests/test_omarchy_marker_reconciliation.py:47).

The survey records six exact Omarchy source paths from the pinned catalogue in [omarchy-wave1-repair-hardening.md](/home/tak_0/sunshineos-audit/SunshineOS_Development-Testing/autonomy/codex/omarchy-wave1-repair-hardening.md). Notes are in `autonomy/pull/codex-lead-omarchy-wave1-repair-hardening/`.

**Verification:** From `evolution-engine/`, ran:

```text
python3 -m unittest tests.test_omarchy_marker_reconciliation tests.test_omarchy_recovery_consistency tests.test_research_catalog -v
```

Result: **15 tests passed**. Evidence: [test log](/home/tak_0/sunshineos-audit/SunshineOS_Development-Testing/autonomy/codex/omarchy-wave1-repair-hardening-test.log).

I couldn’t stage or commit: `.git/index.lock` creation failed because `.git` is read-only in this workspace.
