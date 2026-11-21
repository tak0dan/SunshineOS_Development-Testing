# Artix runit/OpenRC regression deepening — Wave 1

## Scope and evidence boundary

This pass rechecked the local implementation and source corpus, then extended regression coverage. It does not claim end-to-end qualification for Artix runit or OpenRC: the local corpus manifest has an `artix-openrc` ISO and an `artix-dinit` ISO, but no runit ISO or extracted service filesystem. The exact local manifest is `/home/tak_0/.local/state/sunshine-orchestrator/iso/manifest.json`.

The primary implementation is `evolution-engine/src/evolution/tools/artix_services.py::plan_artix_service`. It emits argv tuples and does not execute commands. OpenRC requires the exact `/etc/init.d/<service>` observation; runit requires `/etc/runit/sv/<service>`, and runtime changes additionally require `/run/runit/service/<service>`. Runit definition presence/removal remains package-owned and yields no runtime command.

## Repository catalogue

| Concern | Exact path and symbol | Verified contract |
|---|---|---|
| Running init discovery | `evolution-engine/src/discovery/system.py::_detect_init_system` | Reads PID 1 and gathers independent marker/CLI signals. Marker evidence can classify an init as installed; `Status.RUNNING` requires PID-1 identity (with a dedicated systemd runtime marker case). |
| Normalized observed identity | `evolution-engine/src/core.py::ObservedState.init_system`; `evolution-engine/src/evolution/inventory.py::from_observed` | Carries observed init identity into inventory, without making a service policy/removal decision. |
| Source profile qualification | `evolution-engine/src/evolution/compatibility.py::SourceProfile`; `evolution-engine/tests/test_compatibility.py` | Source profiles include Artix/alternate-init handling. This is source classification, not proof a particular service layout has been qualified. |
| Generic service adapter boundary | `evolution-engine/src/evolution/tools/service_supervision.py::ServiceSupervisor.plan` | Renders systemd argv. For 66/s6 it emits no mutations absent an inventory-backed layout adapter. |
| Artix service plan | `evolution-engine/src/evolution/tools/artix_services.py::plan_artix_service` | Narrow OpenRC/runit path contracts; commands are data, not executed. |
| Public API | `evolution-engine/src/evolution/tools/__init__.py` | Exports `ArtixServicePlan` and `plan_artix_service`. |
| Regression suite | `evolution-engine/tests/test_artix_services.py::ArtixServicePlanTests` | Seven named cases, listed below. |

## Regression catalogue

| Test ID | Regression protected |
|---|---|
| `ARTIX_SVC_001` | OpenRC enable adds default runlevel membership before starting; package presence has no runtime command. |
| `ARTIX_SVC_002` | runit enable requires the observed active service path. |
| `ARTIX_SVC_003` | Unknown init, injected service identifier, and mismatched service path fail closed. |
| `ARTIX_SVC_004` | Removing a runit service definition is package-owned and creates no runtime mutation. |
| `ARTIX_SVC_005` | OpenRC disable stops the service before removing default runlevel membership. |
| `ARTIX_SVC_006` | runit disable requires and targets the observed active service path. |
| `ARTIX_SVC_007` | Out-of-tree runit active paths reject; emitted commands remain argv tuples without shell metacharacters. |

## Architecture relationship

This scope follows mandate M-04 (the observed installation is authoritative), M-05/M-06 (mutations need staged/recoverable execution), M-08 (support must be qualified), and M-09 (repeatable plans). It is consistent with `reports/ARCHITECTURE_DECISIONS.md` AD-04 (capability discovery), AD-08 (constrained and journaled adapters), AD-10 (fixture/live root separation), AD-14 (qualified support tier), AD-18 (retain transition knowledge), and AD-30 (long support margin). The planner alone does not provide staging, journaling, recovery, or source qualification.

## Verification and evidence

- Targeted: `cd evolution-engine && python3 -m unittest tests.test_artix_services -v` — **7 passed**.
- Full suite: `cd evolution-engine && python3 -m unittest discover -s tests` — **172 passed**.
- Captured evidence: `autonomy/codex/artix-runit-openrc-wave1-deepening-test.log`.

Before declaring distro qualification, pin and verify Artix runit/OpenRC source artifacts, extract service definitions and activation metadata with provenance, and test discovery plus execution/recovery through qualified fixtures.
