# Arch 2026 systemd regression survey — Wave 1

## Scope and grounding

This wave surveys the systemd inventory and service regression surface already present in the repository, then adds regression coverage for inventory ambiguity and desired-state semantics. The architecture basis is `reports/ARCHITECTURE_DECISIONS.md` AD-05 (observed installation is authoritative), AD-09 (safe argv-based operations), AD-14 (qualified support), and AD-24 (declarative profile service management); the corresponding migration invariants include M-04, M-08, and M-09 in `evolution-engine/src/evolution/invariants.py`.

The repository records an Arch 2026 ISO candidate in earlier work, but this wave does not claim byte-level upstream verification. The earlier read-only ISO query did not expose an extracted root tree. Thus upstream hook names and exact Arch package contents remain unverified leads; findings below concern repository code and its tests.

## Verified catalogue

| Area | Exact path and symbol | Regression IDs / evidence | Finding |
|---|---|---|---|
| Runtime/system service discovery | `evolution-engine/src/discovery/services_desktop.py::_collect_systemd` | `evolution-engine/tests/test_discovery.py`; whole-module output not captured in this wave | Queries systemd runtime, enabled and running service state. Discovery records observations; it does not establish support solely from an assumed release label. |
| Declarative service plan | `evolution-engine/src/evolution/tools/service_supervision.py::ServiceSpec`, `ServiceSupervisor.plan` | service coverage resides under `evolution-engine/tests/`; no test ID asserted here because this survey did not execute those modules | Validates desired service declarations and produces deterministic argv/drop-in planning; the planner itself does not execute service changes. |
| Unit-file parsing | `evolution-engine/src/evolution/tools/systemd_inventory.py::parse_unit_file_inventory`, `UNIT_NAME`, `KNOWN_STATES` | T-ARCH2026-SYSTEMD-001, -004, -006, -007, -008; `autonomy/codex/arch2026-systemd-wave1-regression-test.log` | Parses unit/state rows, accepts legacy busname/snapshot unit types, and treats malformed, duplicate, or unknown-state rows as incomplete evidence. |
| Desired-state assessment | `evolution-engine/src/evolution/tools/systemd_inventory.py::assess_unit_inventory` | T-ARCH2026-SYSTEMD-002, -003, -005, -009..-012; same evidence log | Incomplete inventory blocks all requested checks; masked units block desired enable/present states; absent and mismatching states request review; already absent targets are satisfied. No mutation occurs. |
| Architecture/invariants | `reports/ARCHITECTURE_DECISIONS.md` AD-05, AD-09, AD-14, AD-24; `evolution-engine/src/evolution/invariants.py` M-04, M-08, M-09 | Documentation source; see exact test IDs above for exercised inventory invariants | Supports observation-first, fail-closed inventory, qualified capability decisions, and repeatable planning. |

## Regression cases added

The new tests in `evolution-engine/tests/test_systemd_inventory.py` extend the original T-ARCH2026-SYSTEMD-001..006 suite:

- **T-ARCH2026-SYSTEMD-007:** duplicate unit rows invalidate the snapshot and block assessment.
- **T-ARCH2026-SYSTEMD-008:** an unknown future state invalidates the snapshot and prevents partial evidence from satisfying a request.
- **T-ARCH2026-SYSTEMD-009:** enabled, enabled-runtime, linked, linked-runtime, and alias states satisfy an enabled target.
- **T-ARCH2026-SYSTEMD-010:** masked-runtime blocks a desired present state.
- **T-ARCH2026-SYSTEMD-011:** an already absent target is satisfied; an observed unit targeted for absence is marked review-remove.
- **T-ARCH2026-SYSTEMD-012:** invalid desired-state vocabulary is rejected.

No mutation or live systemd command is exercised. This keeps tests hermetic and safe.

## Verification evidence

Command: `cd evolution-engine && python3 -m unittest tests.test_systemd_inventory -v`

Result: **12 tests passed**. Full output: `autonomy/codex/arch2026-systemd-wave1-regression-test.log`.

## Change summary

Only `evolution-engine/tests/test_systemd_inventory.py` was extended in code. This survey and the raw test log are under `autonomy/codex/`. No files under `reports/` or other agents' directories were changed.
