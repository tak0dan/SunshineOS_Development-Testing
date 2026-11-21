# Artix runit/OpenRC deliverable consolidation — Wave 1

## Scope and grounding

This consolidates the existing Wave 1 planner and evidence in this checkout. It follows the mandate's observed-state, qualification, recovery, and repeatability requirements (M-04 through M-09) and Architecture Decisions AD-04, AD-08, AD-10, AD-14, AD-18, and AD-30. No `reports/` files were changed.

The repository's implementation is a conservative **plan renderer**, not a live Artix service manager or end-to-end distro qualification. The local ISO manifest at `/home/tak_0/.local/state/sunshine-orchestrator/iso/manifest.json` records Artix OpenRC and dinit images, but no runit image. Consequently, runit layout and migration behavior are not independently validated against a local Artix runit source image here.

## Verified repository catalogue

| Concern | Exact path and symbol | Finding / boundary |
|---|---|---|
| Running init discovery | `evolution-engine/src/discovery/system.py::_detect_init_system` | Separates PID 1 evidence from installed markers; a marker alone does not prove the active init. |
| Observed state | `evolution-engine/src/core.py::ObservedState.init_system`; `evolution-engine/src/evolution/inventory.py::from_observed` | Carries observed init identity into normalized inventory; does not qualify an individual service layout. |
| Source classification | `evolution-engine/src/evolution/compatibility.py::SourceProfile`; `evolution-engine/tests/test_compatibility.py` | Includes alternate-init/Artix classification. Classification is not end-to-end migration qualification. |
| Generic supervisor boundary | `evolution-engine/src/evolution/tools/service_supervision.py::ServiceSupervisor.plan` | Renders systemd argv; other supervisors remain conservative without a qualified inventory adapter. |
| Artix planner | `evolution-engine/src/evolution/tools/artix_services.py::plan_artix_service`, `ArtixServicePlan.to_dict` | Emits argv data only. OpenRC requires the exact `/etc/init.d/<service>` path. runit requires `/etc/runit/sv/<service>` and, for runtime requests, the exact observed `/run/runit/service/<service>` path. |
| Public API | `evolution-engine/src/evolution/tools/__init__.py` | Exports `ArtixServicePlan` and `plan_artix_service`. |
| Regression tests | `evolution-engine/tests/test_artix_services.py::ArtixServicePlanTests` | Ten named tests protect the planner contracts (table below). |

## Planner behavior

- OpenRC `enabled` plans `rc-update add <service> default` before `rc-service <service> start`; `disabled` stops first, then removes default runlevel membership.
- runit `enabled`/`disabled` plans `sv up`/`sv down` against the exact observed active path. It sets `activation_transition_required=True`, since runtime state does not establish persistent activation policy.
- `present`/`absent` definition requests produce no commands; definition installation and removal are package-owned.
- Unsupported init names, malformed service names, mismatched paths, and cross-init evidence are rejected. Commands are argv tuples; nothing is executed by this module.
- Runit persistent activation, package changes, journaling, checkpoints, rollback, and qualification remain outside this planner. These are explicit gaps, not completed capabilities.

## Regression catalogue and evidence

| Test ID | Contract |
|---|---|
| `ARTIX_SVC_001` | OpenRC enable ordering; package-presence request emits no runtime command. |
| `ARTIX_SVC_002` | runit enable requires the observed active path. |
| `ARTIX_SVC_003` | Unknown init, injected service identifiers, and mismatched paths fail closed. |
| `ARTIX_SVC_004` | runit definition removal remains package-owned. |
| `ARTIX_SVC_005` | OpenRC disable stops before default runlevel removal. |
| `ARTIX_SVC_006` | runit disable requires and targets the observed active path. |
| `ARTIX_SVC_007` | Out-of-tree active paths reject; command representation remains argv. |
| `ARTIX_SVC_008` | runit runtime requests expose unresolved persistent activation. |
| `ARTIX_SVC_009` | Stable serialization preserves that unresolved-transition flag. |
| `ARTIX_SVC_010` | OpenRC rejects runit active-path evidence. |

Evidence captured during this consolidation:

- `autonomy/codex/artix-runit-openrc-consolidated-regression.log` — targeted `python3 -m unittest tests.test_artix_services -v`, 10 tests passed.
- `autonomy/codex/artix-runit-openrc-consolidated-full.log` — full `python3 -m unittest discover -s tests`, 175 tests passed.

Existing corroborating records are `autonomy/codex/artix-runit-openrc-wave1-final.md`, `autonomy/codex/artix-runit-openrc-wave1-final-test.log`, and `autonomy/codex/artix-runit-openrc-wave1-final-full-test.log`.

## Corpus claim audit

Several older Artix result notes describe hypothetical paths as if they were present or tested. In particular, `autonomy/results/surge-17-0018.md` proposes `sv enable`, `_active` symlink repair, and boot-recovery evidence under `evidence/`; these are not supported by the actual planner or the local Artix runit source evidence. `autonomy/results/surge-20-0020.md` and `autonomy/results/surge-03-0020.md` similarly list proposed CI/evidence paths. Treat these as leads, not test results or source-backed Artix behavior. No such claims are used to justify the implementation above.

## Next qualification work

Pin an authentic Artix runit source artifact and extract its service definitions and activation metadata with provenance. Add fixture-driven discovery and migration tests, then qualify persistent activation only through an inventory-backed, journaled adapter with checkpoint/recovery behavior. Until those steps pass, supported behavior is limited to the argv planning contracts above.
