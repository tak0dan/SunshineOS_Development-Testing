# Arch 2026 systemd migration engine catalogue — Wave 1

## Scope and grounding

This is a repository-level survey of the migration engine's systemd service path. It does not assert byte-level facts about the Arch 2026 ISO: the existing inventory in `autonomy/codex/arch2026-systemd-wave1-integration.md` says the read-only ISO query did not expose an extracted systemd root tree. Arch package unit files and hook behavior therefore remain unverified upstream.

The design is grounded in `reports/USER_MIGRATION_MANDATE_2026-11-21.md`'s observation-first inventory and fail-closed migration requirements, and `reports/ARCHITECTURE_DECISIONS.md` AD-05 (observed installation is authoritative), AD-09 (safe argv operations), AD-14 (qualified support), and AD-24 (declarative service management). These reports were read only.

## Verified file and symbol catalogue

| Concern | Exact path and symbol | Behavior verified in repository |
|---|---|---|
| Frozen baseline | `evolution-engine/evolution/docs/BASELINE_ARCH_2026.md`; `evolution-engine/src/evolution/baseline.py::ARCH_2026_BASELINE` | Establishes a fixed baseline epoch rather than floating current Arch. |
| Runtime discovery | `evolution-engine/src/discovery/services_desktop.py::_collect_systemd` | Reads systemd health, enabled unit files and running services; failed probes reduce confidence. Discovery is observational. |
| Unit inventory parser | `evolution-engine/src/evolution/tools/systemd_inventory.py::parse_unit_file_inventory` | Parses `systemctl list-unit-files --no-legend`; command failure, malformed rows, unknown states and duplicates make inventory incomplete. Legacy `busname` and `snapshot` types remain parseable. |
| Desired-state policy | `evolution-engine/src/evolution/tools/systemd_inventory.py::assess_unit_inventory` | Compares enabled/disabled/present/absent without mutation; incomplete evidence blocks, missing units require package-stage review, and masked or broken (`bad`) units block. |
| Service contract/planner | `evolution-engine/src/evolution/tools/service_supervision.py::ServiceSpec`, `ServiceSupervisor.plan` | Validates declarations and renders deterministic argv and drop-ins; it does not execute. |
| Checked service boundary | `evolution-engine/src/evolution/tools/service_supervision.py::ServiceSupervisor.plan_checked` | Calls inventory policy before planning, refusing incomplete, masked/bad, install, or removal cases. |
| Discovery/capability coverage | `evolution-engine/tests/test_discovery.py`, `evolution-engine/tests/test_compatibility.py` | Existing suites exercise discovery observations and source compatibility. |
| Inventory/planner regressions | `evolution-engine/tests/test_systemd_inventory.py` | T-ARCH2026-SYSTEMD-001..017 exercise parse, ambiguity, desired-state, and checked-plan behavior. |

## Wave 1 code change

The state `bad` was already accepted by the parser, but policy treated it as an ordinary mismatch (`review-enable` for a desired enabled unit). `ServiceSupervisor.plan_checked` blocks `block`, `review-install`, and `review-remove`; it therefore could emit an enable/start proposal for a unit systemd had explicitly marked broken. `assess_unit_inventory` now returns `block` for `bad` regardless of requested state, so checked planning refuses to produce service argv until the unit definition is repaired and freshly inventoried.

The inventory and planner remain read-only proposal mechanisms. This change does not authorize package operations or claim that a unit's runtime is healthy.

## Regression and evidence

- `T-ARCH2026-SYSTEMD-017`: a `bad` unit is assessed as blocked and `plan_checked` raises instead of returning an enable/start plan.
- Existing regression IDs T-ARCH2026-SYSTEMD-001..016 continue to pass.
- Command: `cd evolution-engine && python3 -m unittest tests/test_systemd_inventory.py -v`
- Result: 17 tests passed.
- Raw output: `autonomy/codex/arch2026-systemd-wave1-final-test.log`.

## Change summary

Implementation and regression coverage are in `evolution-engine/src/evolution/tools/systemd_inventory.py`, `evolution-engine/src/evolution/tools/service_supervision.py`, and `evolution-engine/tests/test_systemd_inventory.py`. This catalogue and raw test evidence are in `autonomy/codex/`. No files under `reports/` were modified.
