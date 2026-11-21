# Arch 2026 systemd repair: Wave 1

## Scope and grounding

This change extends the repository's systemd inventory into a filesystem-level,
read-only repair assessment. The Arch-specific reports in
`autonomy/results/sub-repair-engine-0025.md` and
`autonomy/codex/arch2026-systemd-wave1-catalogue.md` provide candidate unit and
layout references. Their claimed Arch 2026 package contents were not validated
against an extracted Arch ISO in this task; this implementation relies on the
repository baseline contract and explicitly probes the observed root instead
of assuming a unit is installed.

## Repository catalogue

| Concern | Exact path and symbol | Role |
|---|---|---|
| Frozen baseline identity | `evolution-engine/evolution/docs/BASELINE_ARCH_2026.md`; `evolution-engine/src/evolution/baseline.py::ARCH_2026_BASELINE` | Declares Arch/systemd baseline assumptions; ISO digest/signature are intentionally unset, so baseline verification fails closed. |
| Runtime service discovery | `evolution-engine/src/discovery/services_desktop.py::_collect_systemd` | Collects systemd runtime and enabled/running observations. |
| Unit-file state inventory | `evolution-engine/src/evolution/tools/systemd_inventory.py::parse_unit_file_inventory`, `assess_unit_inventory` | Parses `systemctl list-unit-files` observations; failed or malformed collection remains incomplete. |
| Service plan generation | `evolution-engine/src/evolution/tools/service_supervision.py::ServiceSupervisor.plan_checked` | Checks inventory before returning declarative argv; does not execute it. |
| New unit-file repair assessment | `evolution-engine/src/evolution/tools/systemd_repair.py::assess_systemd_unit_files` | Checks vendor/admin unit-file layers under a supplied root and returns findings without mutation. |
| Existing coverage | `evolution-engine/tests/test_systemd_inventory.py`; `evolution-engine/tests/test_sysvinit_repair.py` | Prior systemd state and Arch 2015 service repair regressions. |

The filesystem layers probed are `/usr/lib/systemd/system/<unit>` (vendor) and
`/etc/systemd/system/<unit>` (administrator). An `/etc` symlink to `/dev/null` is
reported as a mask. Missing, empty vendor, empty admin, vendor-only, admin-only,
and override cases remain distinct. Invalid names and paths resolving outside
the observed root fail closed. The assessment has no proposed commands: restoring
vendor files requires package ownership/integrity evidence, and changing an
administrator override requires reconciliation with its owner.

This follows `reports/ARCHITECTURE_DECISIONS.md` AD-05 (observed installation is
authoritative), AD-09 (argv/no shell execution) and AD-11 (checkpoint before
mutation). It also follows `evolution-engine/src/evolution/baseline.py`'s
fail-closed baseline verification and the mandate's recovery and data/OS
separation principles.

## Regression IDs and evidence

| Test ID | Assertion |
|---|---|
| `T-ARCH2026-SYSTEMD-REPAIR-001` | Vendor definition plus admin override are catalogued; no commands emitted. |
| `T-ARCH2026-SYSTEMD-REPAIR-002` | `/dev/null` mask is recognized without following it outside the root. |
| `T-ARCH2026-SYSTEMD-REPAIR-003` | External symlink blocks assessment. |
| `T-ARCH2026-SYSTEMD-REPAIR-004` | Empty vendor file and absent unit are distinguished. |
| `T-ARCH2026-SYSTEMD-REPAIR-005` | Invalid unit identifier produces an incomplete result with no findings. |
| `T-ARCH2026-SYSTEMD-001`–`017` | Existing unit inventory and checked-plan regressions remain green. |

Command: `cd evolution-engine && python3 -m unittest tests/test_systemd_repair.py tests/test_systemd_inventory.py -v`

Result: 22 tests passed. Raw output:
`autonomy/codex/arch2026-systemd-repair-wave1-test.log`.

## Change summary

- Added `evolution-engine/src/evolution/tools/systemd_repair.py` with immutable
  findings/assessment records and root-confined inspection.
- Added `evolution-engine/tests/test_systemd_repair.py` with five regression
  cases and stable test IDs.
- Wrote the run log and this survey/change record under `autonomy/codex/`.
