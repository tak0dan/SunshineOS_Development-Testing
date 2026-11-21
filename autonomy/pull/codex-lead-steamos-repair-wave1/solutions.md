# Solution — SteamOS repair tool, Wave 1

- Added `evolution-engine/src/evolution/tools/steamos_repair.py::assess_steamos_repair`, a pure, read-only, fail-closed assessment for readonly/devmode state.
- Added regressions `T_STEAMOS_REPAIR_001`–`008` in `evolution-engine/tests/test_steamos_repair.py`.
- No rootfs mutation, package command, RAUC command or live probe is implemented. Contradictory/partial state is directed to verified vendor recovery or retained-slot recovery.
- Survey and evidence caveats: `autonomy/codex/steamos-repair-wave1.md`. Test transcript: `autonomy/codex/steamos-repair-wave1-test.log`.
