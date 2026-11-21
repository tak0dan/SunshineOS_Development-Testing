# Arch 2026 systemd architecture enforcement — Wave 1 deepening

## Change summary

Added `ServiceSupervisor.plan_checked` in `evolution-engine/src/evolution/tools/service_supervision.py`. It assesses each requested unit against a complete observed unit-file inventory before returning any service argv. It raises a reviewable `ValueError` when collection failed or was malformed, when a requested unit is masked, or when the unit is absent and needs package installation/removal outside service supervision. Existing `plan` remains a proposal renderer; callers preparing execution must use `plan_checked`.

This closes a boundary between the repository's read-only assessor and command-plan generation: previously `assess_unit_inventory` could report a blocker while `ServiceSupervisor.plan` independently emitted `systemctl enable/start` commands for the same masked or unobserved unit.

## Verified repository catalogue

| Area | Exact path and symbol | Verified behavior |
|---|---|---|
| Source baseline | `evolution-engine/evolution/docs/BASELINE_ARCH_2026.md` | Frozen Arch 2026 baseline documentation; the engine uses capability and inventory state rather than a floating release assumption. |
| Runtime/service discovery | `evolution-engine/src/discovery/services_desktop.py::_collect_systemd` | Reads systemd health and enabled/running unit lists; records low confidence when no probes answer. It is discovery, not repair authorization. |
| Unit inventory | `evolution-engine/src/evolution/tools/systemd_inventory.py::parse_unit_file_inventory` | Parses unit-file states. Failed command, malformed/unknown rows, or duplicates make the snapshot incomplete. |
| Inventory policy | `evolution-engine/src/evolution/tools/systemd_inventory.py::assess_unit_inventory` | Incomplete inventory blocks requests; masked desired enabled/present units block; missing units request package-stage review. It performs no mutation. |
| Service declarations and proposal rendering | `evolution-engine/src/evolution/tools/service_supervision.py::ServiceSpec`, `ServiceSupervisor.plan` | Validates typed service declarations and emits deterministic argv/drop-in proposals without executing them. |
| New enforcement boundary | `evolution-engine/src/evolution/tools/service_supervision.py::ServiceSupervisor.plan_checked` | Applies inventory policy before returning service argv; rejects blocked and package-stage findings. |
| Target foundation | `evolution-engine/src/target/current.toml` (`core`, profiles, component requirements) | Declares systemd as part of the Arch/Sunshine target foundation and associates service/backend choices with systemd capabilities. |
| Compatibility | `evolution-engine/src/target/compatibility.py::classify_source` | Treats a known non-systemd init as an unsupported source; unknown init remains dependent on discovery confidence/preflight. |
| Architecture decisions | `reports/ARCHITECTURE_DECISIONS.md` AD-05, AD-09, AD-14, AD-24 | Observed state authoritative; safe argv-only operations; qualified support; declarative service/profile management. Read-only context only. |

## Enforcement details and boundaries

`plan_checked` materializes the declarations once, derives their requested desired states, and calls the established fail-closed inventory assessor. It refuses to return any plans if a finding is `block`, `review-install`, or `review-remove`; a disabled existing unit can proceed to a planned enable transition. The method does not execute commands, install packages, unmask units, or claim that a unit is running/functional. This preserves the separate discovery, planning, execution, and validation responsibilities described in `evolution-engine/docs/ARCHITECTURE.md`.

The plain `plan` API still renders unapproved proposals for callers that explicitly need proposal generation. Execution-facing call sites should use `plan_checked` after fresh discovery and retain the repository's stale-plan and executor authorization checks. This change does not yet bind the checked plan to an inventory fingerprint; callers must rebuild the plan after discovery changes.

## Regression tests

Test file: `evolution-engine/tests/test_systemd_inventory.py`

- `T-ARCH2026-SYSTEMD-013`: masked requested unit blocks checked planning.
- `T-ARCH2026-SYSTEMD-014`: failed inventory blocks checked planning as unknown.
- `T-ARCH2026-SYSTEMD-015`: absent requested unit blocks service-only planning pending package installation.
- `T-ARCH2026-SYSTEMD-016`: existing disabled unit may be planned for enablement.
- Existing `T-ARCH2026-SYSTEMD-001` through `-012` continue to cover parsing, malformed/unknown/duplicate observations, masks, absent desired state, and identifier/state validation.

## Evidence

Command: `cd evolution-engine && python3 -m unittest tests/test_systemd_inventory.py -v`

Result: **16 tests passed**. Raw output: `autonomy/codex/arch2026-systemd-wave1-enforcement-test.log`.

The ISO path and read-only inventory attempt are recorded in `autonomy/codex/arch2026-systemd-wave1-integration.md`. That evidence did not expose an extracted systemd root tree, so Arch package unit/hook contents remain unverified upstream leads. No upstream implementation detail is inferred from candidate hook names.
