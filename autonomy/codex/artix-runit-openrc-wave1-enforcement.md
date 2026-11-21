# Artix runit/OpenRC architecture enforcement — Wave 1 deepening

## Change

The Artix service planner now exposes `ArtixServicePlan.activation_transition_required`. For runit runtime requests (`enabled` and `disabled`) this is `True`: the emitted `sv up`/`sv down` only changes current runtime state, while persistent supervision activation remains a separate transition requiring inventory-backed, qualified, recoverable handling. Package-definition requests (`present`/`absent`) set it to `False`. OpenRC remains modeled with runlevel membership and runtime commands in the same plan, in their required order.

This field makes the partial nature of a runit runtime plan machine-readable, so callers cannot mistake a start/stop command for a persistent enable/disable transition. No runit activation link is modified by this planner.

## Repository survey

| Concern | Exact path and symbol | Finding |
|---|---|---|
| Init discovery | `evolution-engine/src/discovery/system.py::_detect_init_system` | Gathers PID 1, marker, and CLI signals. PID 1 identity determines `RUNNING`; files alone indicate installation. |
| Observed init field | `evolution-engine/src/core.py::ObservedState.init_system` | Holds normalized init identity from discovery. |
| Inventory transfer | `evolution-engine/src/evolution/inventory.py::from_observed` | Copies init identity into `identity.init_system`; inventory remains observational. |
| Source classification | `evolution-engine/src/evolution/compatibility.py::SourceProfile` | Represents alternate-init/Artix source handling; classification is not service-layout qualification. |
| Generic service adapter | `evolution-engine/src/evolution/tools/service_supervision.py::ServiceSupervisor.plan` | systemd gets concrete argv; s6/66 paths remain conservative without a qualified inventory adapter. |
| Artix service planner | `evolution-engine/src/evolution/tools/artix_services.py::plan_artix_service` | Emits argv tuples only; OpenRC requires exact `/etc/init.d/<name>`, runit requires exact `/etc/runit/sv/<name>` and an observed `/run/runit/service/<name>` path for runtime operations. |
| Public export | `evolution-engine/src/evolution/tools/__init__.py` | Exports `ArtixServicePlan` and `plan_artix_service`. |
| Regression suite | `evolution-engine/tests/test_artix_services.py::ArtixServicePlanTests` | Eight named contract cases, including the new activation boundary assertion. |

## Regression IDs

`ARTIX_SVC_001` OpenRC enable ordering; `002` runit active-path requirement; `003` reject unsupported/injected/mismatched inputs; `004` package-owned definition lifecycle; `005` OpenRC disable ordering; `006` runit stop target; `007` argv/path constraints; `008` report persistent activation as unresolved for runit runtime requests.

## Architecture and evidence boundary

The change enforces the observed-state authority and qualification constraints in mandate M-04/M-08 and supports M-05/M-06 by keeping unqualified persistent link changes outside this non-executing planner. It aligns with AD-04, AD-08, AD-10, AD-14, AD-18, and AD-30 in `reports/ARCHITECTURE_DECISIONS.md`.

The local corpus manifest `/home/tak_0/.local/state/sunshine-orchestrator/iso/manifest.json` has `artix-openrc` and `artix-dinit` ISO entries, but no Artix runit entry. The planner is not end-to-end Artix qualification: pinned runit source artifacts, service-layout fixtures, journaled execution, recovery, and qualification matrix coverage are still needed before runit persistent activation can be managed.

## Verification

- Targeted: `cd evolution-engine && python3 -m unittest tests.test_artix_services -v` — 8 passed.
- Full suite: `cd evolution-engine && python3 -m unittest discover -s tests` — 173 passed.
- Captured output: `autonomy/codex/artix-runit-openrc-wave1-enforcement-test.log`.
