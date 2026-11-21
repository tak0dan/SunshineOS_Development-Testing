# Solution — SteamOS architecture enforcement, Wave 1 deepening

- Enforced canonical phase-prefix and current-cursor validation in `WorkflowRun` construction.
- Restricted aborts to the current phase and disallowed aborting completed workflows.
- Added `STEAMOS_AB_006` to test forged phase history and out-of-order abort attempts; adjusted the shared workflow test to advance to `ValidateStaged` before aborting.
- Test evidence: `autonomy/codex/steamos-architecture-enforcement-wave1-test.log`.
