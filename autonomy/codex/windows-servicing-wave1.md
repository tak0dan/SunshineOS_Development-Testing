# Windows 11 servicing survey and implementation — Wave 1

## Catalogue reviewed

| Repository path | What it establishes | Wave 1 use |
|---|---|---|
| `reports/USER_MIGRATION_MANDATE_2026-11-21.md` §4, §6 | Sustainability, recoverability, and repair requirements; Windows 11 is a comparison target. | Apply fail-closed, staged assessment. |
| `reports/ARCHITECTURE_DECISIONS.md` AD-03–AD-09 and M-04–M-06 | Observed state drives planning; trust and recovery gates; staged operations. | Evidence model refuses healthy on missing/uncertain checks. |
| `autonomy/results/sub-code-distro-01.md` “Windows 11 — DISM / SFC” and “BCDboot / bcdedit / WinRE” | Existing team catalogue identifies DISM/SFC, BCDboot, bcdedit and WinRE as Windows servicing/recovery surfaces and calls out opaque mutation and absent journals as risks. | Treat as a lead catalogue, not as independently verified command semantics. |
| `evolution-engine/src/evolution/tools/package_health.py` | Read-only health report pattern with healthy/degraded/unknown outcomes. | Mirrored for platform-neutral report output. |
| `evolution-engine/tests/test_package_health.py` | Existing regression style for degraded and unknown checks. | Followed in test structure. |

## Delivered behavior

Added `evolution-engine/src/evolution/tools/windows_servicing.py`. It evaluates captured output for the exact read-only DISM `/CheckHealth`, DISM `/ScanHealth`, and SFC `/verifyonly` probes, plus an independently observed pending-reboot state. Missing results and unknown reboot state are `unknown`; command mismatch and pending reboot are `blocked`; probe failure or reported corruption is `degraded`. The evaluator never executes repair operations and reports healthy only when all evidence is clean. Mutation planning, staging, journal, authorization, and rollback remain responsibilities of the migration executor (AD-07/AD-08).

The catalogue's high-level DISM/SFC statements have not been validated against a Windows VM in this wave. This code tests conservative output classification using captured evidence, not live Windows servicing behavior. A later Windows VM qualification should archive raw command outputs and reboot-state provenance before any repair adapter is implemented.

## Regression tests and evidence

- Test IDs: `WIN-SERV-001` clean required probes; `WIN-SERV-002` missing probes/unknown reboot fail closed; `WIN-SERV-003` corruption and pending reboot block healthy; `WIN-SERV-004` unexpected command blocked.
- Test file: `evolution-engine/tests/test_windows_servicing.py`.
- Exact command: `cd evolution-engine && python -m unittest tests/test_windows_servicing.py -v`
- Result: 4 tests passed. Full captured output: `autonomy/pull/codex-lead-windows-servicing-wave1/evidence/test-windows-servicing.log`.
