# Windows servicing Wave 1

Deepened the read-only Windows servicing evidence evaluator in `evolution-engine/src/evolution/tools/windows_servicing.py`: healthy now requires an allowlisted clean-result marker, and evidence identity must match its lookup key. Added two regressions to `evolution-engine/tests/test_windows_servicing.py`. Survey scope and evidence limits are catalogued in `autonomy/codex/windows-servicing-wave1.md`.

Test IDs: `WIN-SERV-001` through `WIN-SERV-006` (the last two cover unknown successful output and mismatched evidence identity).

Exact command (from `evolution-engine/`): `python -m unittest tests/test_windows_servicing.py -v`

Evidence: `autonomy/pull/codex-lead-windows-servicing-wave1/evidence/test-windows-servicing.log` (6 passed).
