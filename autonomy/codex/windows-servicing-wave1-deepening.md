# Windows 11 servicing — Wave 1 deepening

## Survey and repository catalogue

- `reports/USER_MIGRATION_MANDATE_2026-11-21.md` defines M-04/M-05/M-06 and §4's servicing/recovery requirements; `reports/ARCHITECTURE_DECISIONS.md` maps AD-03–AD-09 to resolver, trust, staging, and adapter boundaries.
- `autonomy/results/sub-code-distro-01.md` §1 and §3 lists DISM/SFC, component-store checks, CBS logs, BCDboot/bcdedit, and WinRE. This is a team lead catalogue, not inspected Windows source or captured VM behavior.
- `autonomy/results/sub-research-vuln-02.md` L-01–L-05 describes proposed immutable artifacts, provenance, component-level changes, staged validation, and data separation. Windows-specific comparative claims are not independently evidenced here.
- `evolution-engine/src/evolution/tools/package_health.py` and `evolution-engine/tests/test_package_health.py` provide the existing platform-neutral report and fail-closed test pattern.
- `evolution-engine/src/evolution/tools/windows_servicing.py::assess_windows_servicing` accepts only exact read-only probe argv and recognized clean output markers. It does not execute DISM, SFC, or repairs.

## Change and limits

Healthy requires an explicit clean-result phrase. A zero exit with generic or unrecognized output is `unknown`; a mismatched evidence key/name or command is `blocked`. Captured corruption is `degraded`; unknown/pending reboot state cannot be healthy. Localized clean output needs separately reviewed locale fixtures before it can be accepted. No Windows VM or servicing operation was run, so this validates classifier behavior, not platform command semantics.

## Regression evidence

- `WIN-SERV-001` clean probe output and settled reboot.
- `WIN-SERV-002` missing probes and unknown reboot state.
- `WIN-SERV-003` corruption output and pending reboot.
- `WIN-SERV-004` unexpected command.
- `WIN-SERV-005` unrecognized successful output remains unknown.
- `WIN-SERV-006` evidence identity mismatch is blocked.

Test file: `evolution-engine/tests/test_windows_servicing.py::WindowsServicingTests`.

Exact command (run in `evolution-engine/`): `python -m unittest tests/test_windows_servicing.py -v`

Result: **6 tests passed**. Captured output: `autonomy/pull/codex-lead-windows-servicing-wave1/evidence/test-windows-servicing.log`.
