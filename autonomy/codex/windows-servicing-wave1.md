# Windows 11 servicing survey and implementation — Wave 1

## Catalogue reviewed

| Repository path | What it establishes | Wave 1 use |
|---|---|---|
| `reports/USER_MIGRATION_MANDATE_2026-11-21.md` §4, §6 | Sustainability, recoverability, and repair requirements; Windows 11 is a comparison target. | Apply fail-closed, staged assessment. |
| `reports/ARCHITECTURE_DECISIONS.md` AD-03–AD-09 and M-04–M-06 | Observed state drives planning; trust and recovery gates; staged operations. | Evidence model refuses healthy on missing/uncertain checks. |
| `autonomy/results/sub-code-distro-01.md` §1, §3, §4 | Team audit lists DISM/SFC and BCDboot/bcdedit/WinRE, plus proposed error/log surfaces and copy/avoid rules. It is a survey lead, not byte-level source evidence. | Retain explicit limits; do not treat its command notes as verified Windows behavior. |
| `autonomy/results/sub-research-vuln-02.md` L-01–L-05 | Research proposes immutable repair artifacts, provenance, component transitions, staged validation, and OS/data separation. | Map only design lessons to M-05/M-06/M-07/M-10; Windows-specific failure claims remain unverified. |
| `evolution-engine/src/evolution/invariants.py` | Implements M-01–M-10 checks. | This adapter remains an evidence assessor; executor and validation policy own mutation and recovery. |
| `evolution-engine/src/evolution/tools/windows_servicing.py::assess_windows_servicing` | Classifies exact read-only probe commands, captured output, and reboot state. | Only recognized clean-result text can be healthy; unknown/localized output fails closed. |
| `evolution-engine/src/evolution/tools/package_health.py` | Read-only health report pattern with healthy/degraded/unknown outcomes. | Mirrored for platform-neutral report output. |
| `evolution-engine/tests/test_package_health.py` | Existing regression style for degraded and unknown checks. | Followed in test structure. |

## Delivered behavior

Added `evolution-engine/src/evolution/tools/windows_servicing.py`. It evaluates captured output for the exact read-only DISM `/CheckHealth`, DISM `/ScanHealth`, and SFC `/verifyonly` probes, plus an independently observed pending-reboot state. Missing results and unrecognized output (including locale variants without a parser) are `unknown`; command or identity mismatch and pending reboot are `blocked`; probe failure or reported corruption is `degraded`. Healthy requires a recognized clean-result marker. The evaluator never executes repair operations; mutation planning, staging, journal, authorization, and rollback remain responsibilities of the migration executor (AD-07/AD-08).

The catalogue's high-level DISM/SFC statements have not been validated against a Windows VM in this wave. This code tests conservative output classification using captured evidence, not live Windows servicing behavior. A later Windows VM qualification should archive raw command outputs and reboot-state provenance before any repair adapter is implemented.

## Regression tests and evidence

- Test IDs: `WIN-SERV-001` clean required probes; `WIN-SERV-002` missing probes/unknown reboot fail closed; `WIN-SERV-003` corruption and pending reboot block healthy; `WIN-SERV-004` unexpected command blocked; `WIN-SERV-005` unrecognized success output remains unknown; `WIN-SERV-006` evidence identity mismatch blocked. Test methods are in `evolution-engine/tests/test_windows_servicing.py::WindowsServicingTests`.
- Test file: `evolution-engine/tests/test_windows_servicing.py`.
- Exact command (run from `evolution-engine/`): `python -m unittest tests/test_windows_servicing.py -v`
- Result: 6 tests passed. Full captured output: `autonomy/pull/codex-lead-windows-servicing-wave1/evidence/test-windows-servicing.log`.
