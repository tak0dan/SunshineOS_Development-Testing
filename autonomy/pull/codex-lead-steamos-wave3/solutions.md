# Solution — SteamOS regression survey, Wave 3

- Added `WorkflowRun.__post_init__` validation that rejects strategy values outside `STRATEGIES`.
- Added `STEAMOS_AB_005` in `evolution-engine/tests/test_steam_os_ab_staging.py` for invalid direct construction and aborted validation preventing activation.
- Test evidence: `autonomy/codex/steamos-development-lead-wave3-test.log`; catalogue: `autonomy/codex/steamos-development-lead-wave3.md`.
