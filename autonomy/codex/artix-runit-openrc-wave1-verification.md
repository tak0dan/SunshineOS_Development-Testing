# Artix runit/OpenRC Wave 1 — verified catalogue

**Result:** repository survey and regression verification for the Artix service-planning increment. Findings are limited to checked-in code and local corpus metadata; an Artix runit image was not available, so this does not qualify runit as an end-to-end migration source.

## Repository catalogue

| Concern | Exact path and symbol/test | Verified role |
|---|---|---|
| Init observation | `evolution-engine/src/discovery/system.py::_detect_init_system` | Collects independent init signals. PID 1 is the basis for identifying the running init; installed markers alone do not establish that it is active. |
| Normalized state | `evolution-engine/src/core.py::ObservedState.init_system`; `evolution-engine/src/evolution/inventory.py::from_observed` | Carries observed init identity into inventory for adapter selection. |
| Source qualification | `evolution-engine/src/evolution/compatibility.py::SourceProfile`; `evolution-engine/tests/test_compatibility.py` | Artix/alternate-init compatibility is represented in source classification; compatibility is not proof that a specific service layout was exercised. |
| Existing generic plans | `evolution-engine/src/evolution/tools/service_supervision.py::ServiceSupervisor.plan` | systemd commands are rendered; 66 and s6 remain no-command/manual-qualification paths absent an inventory-backed adapter. |
| Artix planner | `evolution-engine/src/evolution/tools/artix_services.py::plan_artix_service` | Renders argv-only OpenRC and constrained runit runtime plans. It never executes commands. |
| Public tool exports | `evolution-engine/src/evolution/tools/__init__.py` | Exports `ArtixServicePlan` and `plan_artix_service`. |
| Regression tests | `evolution-engine/tests/test_artix_services.py::ArtixServicePlanTests` | Four named regressions listed below. |

## Behaviour and safety boundary

- OpenRC `enabled` emits `rc-update add <service> default`, then `rc-service <service> start`; `disabled` emits stop then runlevel removal. Only the exact observed `/etc/init.d/<service>` path is accepted.
- runit `enabled`/`disabled` require an observed `/run/runit/service/<service>` active path and render `sv up`/`sv down`. The planner does not infer persistent enablement or remove activation links.
- runit service definition `present`/`absent` emits no commands because definition lifecycle is package-owned.
- Unsupported init names, unsafe names, and paths outside the exact supported roots fail closed. Commands are tuples of argv, with no shell invocation.
- This remains a plan renderer. M-05/M-06 still require staging, journaling, validation and recovery in any executor; a rendered plan alone does not qualify an installed source (M-04/M-08).

## Local Artix evidence boundary

`/home/tak_0/.local/state/sunshine-orchestrator/iso/manifest.json` records `artix-openrc` and `artix-dinit` ISO entries. It contains no Artix runit ISO entry. The present local corpus therefore cannot substantiate runit distro-specific service layout, script dependencies, shutdown ordering or initramfs hooks. No service-level claims from older autonomy notes were treated as primary evidence.

## Regression IDs and evidence

| Test ID | Assertion |
|---|---|
| `ARTIX_SVC_001` | OpenRC runlevel enrollment precedes service start; package presence has no runtime command. |
| `ARTIX_SVC_002` | runit runtime action requires observed active path and targets that path. |
| `ARTIX_SVC_003` | Unsupported init, injected service name, and mismatched service path reject. |
| `ARTIX_SVC_004` | runit definition removal is not planned as a runtime mutation. |

Evidence: `autonomy/codex/artix-runit-openrc-wave1-verified-test.log`.

## Architecture anchors

The implementation follows mandate M-04 (observed installation authority), M-05/M-06 (staged and recoverable execution), M-08 (qualified support), and M-09 (repeatability). It aligns with `reports/ARCHITECTURE_DECISIONS.md` AD-04 (capability-based source handling), AD-08 (constrained/journaled adapters), AD-10 (fixture/live root separation), AD-14 (qualified support tier), AD-18 (preserve retired transition knowledge), and AD-30 (long support margin).

## Change summary

The repository already contains the scoped planner and four regressions at the paths above; this verification pass did not modify those shared worktree files. It adds this grounded survey and a fresh test log under `autonomy/codex/`. Before claiming Artix runit qualification, add pinned source evidence and service-layout fixtures, then route actions through the journaled executor and source qualification matrix.
