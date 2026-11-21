# Artix runit/OpenRC service management — Wave 1

**Task:** development leadership survey and a fail-closed service-planning increment.  
**Scope:** repository-backed survey, with mounted ISO/repository claims limited to available local artifacts.  
**Architecture anchors:** `reports/USER_MIGRATION_MANDATE_2026-11-21.md` (M-04, M-05, M-06, M-08, M-09) and `reports/ARCHITECTURE_DECISIONS.md` (AD-04, AD-08, AD-10, AD-14, AD-18, AD-24).

## Findings grounded in this checkout

| Area | Exact path and symbol | Finding |
|---|---|---|
| Init discovery | `evolution-engine/src/discovery/system.py::_detect_init_system` | The detector already checks PID 1, systemd markers, and alternatives including `/etc/init.d` + `/sbin/openrc` and `/etc/runit` + `runsvdir -V`. It records `RUNNING` only when PID 1 matches; marker-only findings are `INSTALLED`. This distinction should be retained when planning any repair. |
| Inventory | `evolution-engine/src/core.py::ObservedState.init_system`; `evolution-engine/src/evolution/inventory.py::from_observed` | Init identity is carried into normalized inventory. Adapter selection can depend on observed state instead of a claimed distribution or release. |
| Qualification | `evolution-engine/src/evolution/compatibility.py::SourceProfile` (Artix profile); `evolution-engine/tests/test_compatibility.py` | Artix is already named as a source profile. Alternative init sources are treated as compatibility concerns, not silently assumed equivalent to the target. |
| Existing service repair | `evolution-engine/src/evolution/tools/service_supervision.py::ServiceSupervisor.plan` | systemd gets enable/start or stop/disable argv. Existing 66 and s6 specs deliberately produce no commands because no inventory-backed adapter qualifies their layouts. Runit/OpenRC were not implemented there. |
| Existing regression coverage | `evolution-engine/tests/test_evolution.py::test_service_supervision_plans_are_deterministic`; `::test_66_and_s6_repairs_fail_closed_without_inventory_adapters` | Current coverage proves deterministic systemd plans and fail-closed 66/s6 behavior. The new tests add distinct runit/OpenRC coverage without editing the service supervisor currently being changed in this checkout. |
| ISO corpus | `/home/tak_0/.local/state/sunshine-orchestrator/iso/manifest.json` | Local corpus has Artix OpenRC and dinit ISOs. It does **not** list an Artix runit ISO. ISO files are `artix-openrc.iso` and `artix-dinit.iso`; both are ISO9660 live media, so a top-level archive listing does not expose installed `/etc` trees. No extracted filesystem snapshot was present in the enumerated corpus. |
| Prior research notes | `autonomy/results/lead-research-01.md`; `autonomy/results/sub-research-hooks-01.md`; `autonomy/results/surge-03-0018.md`; `autonomy/results/surge-32-0018.md` | These are leads, not verified evidence. The cross-distro atlas makes broad claims (such as rollback defaults and tools) without evidence paths. The boot-recovery tables cite paths such as `/etc/runit/runswerv/fstab-check`, `/usr/lib/systemd/system/runit-fsck.service`, and panic logs that are not corroborated by this checkout or available Artix runit media. Do not encode those claims as facts. |

## Catalogue and proposed adoption boundary

| Concern | What can be grounded now | SunshineOS treatment |
|---|---|---|
| OpenRC service definition and runlevels | The local Artix media is explicitly an OpenRC ISO, but its squashfs payload has not been extracted here. Repository discovery knows `/etc/init.d`, `/sbin/openrc`; exact service state is not currently inventoried. | The new planner accepts only a caller-supplied exact `/etc/init.d/<name>` observation. It renders `rc-update` and `rc-service` argv but does not execute them. Runtime state and default-runlevel membership remain separate operations. |
| runit service directories | No Artix runit image or extracted runit filesystem was present in the local manifest. Existing code only recognizes `/etc/runit` and the `runsvdir` CLI. | The adapter is an explicitly constrained contract for `/etc/runit/sv/<name>` plus an optional `/run/runit/service/<name>` active path. Its `enabled` operation only ensures runtime-up with `sv up`; persistent activation-link management is not inferred. Start/stop requires the active path to have been observed. Validate this layout against an Artix runit artifact before claiming distro qualification. |
| Service dependencies and boot ordering | Current service specs model dependencies, but the existing `ServiceSupervisor` does not resolve them into execution order. No Artix service-script payload was inspected. | No dependency conversion is claimed in Wave 1. OpenRC dependency metadata and runit supervision relationships need source-artifact tests before they can become migration transitions. |
| Recovery, filesystem, initramfs | Prior notes suggest special runit/OpenRC fsck and panic hooks, but no primary artifacts substantiate them here. The evolution engine already has staging, journals, checkpoints and qualification subsystems. | Do not add initramfs hooks, recovery commands, or fabricated runit/OpenRC equivalences from these notes. Build transitions only after extracting actual service scripts/configs and recording provenance. |

**Safety interpretation:** this code returns argv data; it does not run commands. Existing M-05/M-06 staging, journal and checkpoint mechanisms remain necessary at execution time. A plan is not evidence that a service exists, that its init is PID 1, or that a migration is qualified (M-04/M-08).

## Code delivered

- `evolution-engine/src/evolution/tools/artix_services.py::plan_artix_service` adds deterministic plan generation for OpenRC and a narrow runit service-path contract. It rejects unsupported init names, unsafe service IDs, mismatched service paths, and runit activation paths outside the declared tree.
- `evolution-engine/src/evolution/tools/__init__.py` exports `ArtixServicePlan` and `plan_artix_service`.
- `evolution-engine/tests/test_artix_services.py` adds the following regressions:
  - `ARTIX_SVC_001`: OpenRC runlevel enrollment and start are explicit ordered argv operations.
  - `ARTIX_SVC_002`: runit start is blocked without an observed activation path.
  - `ARTIX_SVC_003`: unknown init, command-injection service name, and mismatched runit path fail closed.
  - `ARTIX_SVC_004`: removing a runit service definition remains package-owned and is not planned as a mutation.

## Verification

Commands: `cd evolution-engine && python3 -m unittest tests.test_artix_services -v`; `python3 -m unittest discover -s tests`  
Results: **4 targeted tests passed; all 169 migration-engine tests passed**.  
Captured output: `autonomy/codex/artix-runit-openrc-wave1-test.log`.

## Follow-up evidence required before qualification

1. Add an Artix runit ISO or pinned repository snapshot to the local corpus with URL, byte size, digest, retrieval date, and signer/checksum provenance.
2. Extract both runit and OpenRC service definitions, activation links/runlevels, init scripts, shutdown ordering, and package hooks into read-only evidence with source package/version provenance.
3. Exercise discovery against those fixtures (including stale markers, mixed init installations, and PID-1 disagreement), then connect the adapter plans to the journaled executor and qualified source matrix.
4. Keep claims from prior autonomy notes out of support policy until the corresponding primary artifact and test result exist.
