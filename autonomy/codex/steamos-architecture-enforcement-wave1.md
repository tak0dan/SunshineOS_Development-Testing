# SteamOS architecture enforcement — Wave 1 deepening

## Survey catalogue

| Evidence / code path | Verified point | SunshineOS enforcement |
|---|---|---|
| `reports/cross-distro-stability.md:19` | SteamOS updates are catalogued as image-based A/B with inactive-slot preparation and retained previous state. | Keep the previous slot identifiable and require observed candidate and switching capabilities before selecting `ab_slot`; implementation: `evolution-engine/src/evolution/staging.py::StagingCapability.ab_slot_possible` and `assess_staging`. |
| `reports/cross-distro-stability.md:106` (`S13`) | Collabora's SteamOS 3.6 account is the strongest cited source for RAUC/Casync and seed validation. | Use only the general safety invariant; don't couple SunshineOS to SteamOS-specific updater internals. |
| `reports/cross-distro-stability.md:110` (`S17`) | Branch-selection details cite a man-page mirror. | Treat channel mechanics as secondary evidence, not an implementation contract. |
| `reports/cross-distro-stability.md:147` | The report explicitly notes some SteamOS details are secondary-source claims. | Preserve this evidence-quality caveat; broad claims elsewhere in `autonomy/results/lead-research-01.md` (OSTree) and `autonomy/results/lead-research-02.md` (firmware switching) are not adopted as facts. |
| `evolution-engine/src/evolution/inventory.py::Inventory` | Inventory stores boot observations as domain facts. | A SteamOS label alone must never imply slot layout or activation support. |
| `evolution-engine/src/evolution/staging.py::WorkflowRun` | Workflow is a 14-phase sequence, with `ValidateStaged` before `Activate`. | Validate constructor history and abort location so forged history cannot skip validation. |
| `evolution-engine/tests/test_steam_os_ab_staging.py` | Existing test IDs `STEAMOS_AB_001`–`005` cover observed slot capability, ambiguous evidence, recovery priority, forced staged root, and strategy/abort checks. | Added `STEAMOS_AB_006` for forged workflow history and aborting outside the current phase. |

## Mandate and architecture mapping

This work enforces M-05 (stage and validate before switching), M-06 (recoverable workflow), M-08 (qualified capability, not assumptions), and M-09 (repeatable state transitions) from `reports/USER_MIGRATION_MANDATE_2026-11-21.md`. It maps to AD-05, AD-11, AD-12, AD-14, AD-16, and AD-30 in `reports/ARCHITECTURE_DECISIONS.md`. No files under `reports/` were changed.

## Change

`WorkflowRun.__post_init__` now requires `completed` to be an exact prefix of the canonical phase sequence and requires `current` to match that prefix. `abort()` only accepts the current phase. Thus a caller cannot construct a workflow with `Build` in its history and jump directly to `Activate`, nor record an abort at a phase that was never reached. The existing evolution regression was adjusted to walk to `ValidateStaged` before simulating an interruption.

Regression IDs: `STEAMOS_AB_001`–`STEAMOS_AB_006`; shared workflow regression: `ArtifactRecoveryQualificationTests.test_staging_and_workflow_phases`.

## Verification

From `evolution-engine/`, ran exactly:

```sh
python3 -m unittest discover -s tests -p 'test_steam_os_ab_staging.py' && python3 -m unittest discover -s tests -p 'test_evolution.py'
```

Result: SteamOS suite — 6 tests, OK; evolution suite — 30 tests, OK. Captured transcript: `autonomy/codex/steamos-architecture-enforcement-wave1-test.log`.
