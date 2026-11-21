# Artix runit/OpenRC migration survey — Wave 1

## Survey findings

This catalog is grounded in the checked-out engine and local corpus metadata. The engine supports an argv-only service planner; it does not yet qualify end-to-end migration from Artix runit or OpenRC.

| Area | Exact path and symbol | Finding |
|---|---|---|
| Init discovery | `evolution-engine/src/discovery/system.py::_detect_init_system` | PID 1 evidence distinguishes the running init from merely installed markers. Preserve that distinction for adapter selection. |
| Observed inventory | `evolution-engine/src/core.py::ObservedState.init_system`; `evolution-engine/src/evolution/inventory.py::from_observed` | The normalized inventory carries observed init identity; it does not establish service layout or qualify a transition. |
| Source classification | `evolution-engine/src/evolution/compatibility.py::SourceProfile`; `evolution-engine/tests/test_compatibility.py` | Artix/alternate-init source classification exists. It is not evidence that service migration is qualified. |
| Generic supervisor | `evolution-engine/src/evolution/tools/service_supervision.py::ServiceSupervisor.plan` | systemd plans concrete argv. 66/s6 have no mutation plan absent a qualified inventory adapter. |
| Artix planner | `evolution-engine/src/evolution/tools/artix_services.py::plan_artix_service`; `ArtixServicePlan.to_dict` | OpenRC uses the exact `/etc/init.d/<service>` observation and emits runlevel/runtime argv. runit requires `/etc/runit/sv/<service>`; runtime operations also require the exact `/run/runit/service/<service>` observation. Its activation boundary is serialized explicitly. |
| Public tool surface | `evolution-engine/src/evolution/tools/__init__.py` | Exports `ArtixServicePlan` and `plan_artix_service`. |
| Regression suite | `evolution-engine/tests/test_artix_services.py::ArtixServicePlanTests` | Ten `ARTIX_SVC_*` contracts cover ordering, observed paths, package ownership, argv safety, activation qualification, serialization, and init-specific evidence rejection. |

## Catalogue and adoption limits

- OpenRC enable is ordered as `rc-update add <service> default`, then `rc-service <service> start`. Disable stops before removing default runlevel membership. The plan renderer does not execute either operation.
- runit `sv up/down` is runtime state only. `activation_transition_required=True` for runtime requests signals that persistent activation still needs a separate qualified, inventory-backed and recoverable transition. The planner does not manipulate links.
- Service-definition `present/absent` is package-owned and yields no service mutation.
- `reports/USER_MIGRATION_MANDATE_2026-11-21.md` M-04/M-08 and `reports/ARCHITECTURE_DECISIONS.md` AD-04/AD-08/AD-10/AD-14/AD-18/AD-30 bound the implementation: observed state, qualification, journaled execution and recovery remain mandatory.
- `/home/tak_0/.local/state/sunshine-orchestrator/iso/manifest.json` lists Artix OpenRC and dinit media, not runit. The runit-specific on-disk layout is therefore not independently validated from an Artix runit source artifact in this workspace.
- `autonomy/results/surge-17-0018.md` contains proposed runit/OpenRC boot procedures, but several statements (including `sv enable` behavior, link locations, and forced symlink repair) are not substantiated by the local primary artifacts. Treat it as an unverified lead; do not use it as implementation evidence.

## Code change

`ArtixServicePlan.to_dict()` now provides a deterministic JSON-compatible representation and retains `activation_transition_required`; without that field, downstream plan storage could erase the distinction between runtime state and persistent activation. Regression `ARTIX_SVC_009` verifies the emitted argv and activation marker.

The OpenRC planner also rejects a supplied runit active-service path (`ARTIX_SVC_010`), preventing mixed-supervisor evidence from being silently ignored.

## Verification evidence

- `ARTIX_SVC_001`–`ARTIX_SVC_010`: targeted suite passed (10 tests).
- Full migration-engine suite: 175 tests passed.
- Captured output: `autonomy/codex/artix-runit-openrc-wave1-final-test.log` and `autonomy/codex/artix-runit-openrc-wave1-final-full-test.log`.

This is planner-level coverage, not VM qualification. No runit service filesystem, dependency conversion, journaled service execution, or rollback path was exercised.
