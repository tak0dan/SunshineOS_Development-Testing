# Obarun 66/s6 repair tooling — Wave 1

Date: 2026-11-21  
Scope: service repair plan representation and Obarun/66+s6 source catalogue. This is code grounded in this checkout, not an Obarun installation survey.

## Repository catalogue

| Concern | Exact path and symbol | Finding |
|---|---|---|
| PID 1/init detection | `evolution-engine/src/discovery/system.py::_detect_init_system` | Recognizes `s6` markers and normalizes `s6-*` PID 1 names to init family `s6`. Marker presence is not proof of a running service manager. |
| 66 manager detection | `evolution-engine/src/discovery/system.py::_detect_66_manager` | Looks for rooted `/usr/bin/66`, `/usr/sbin/66`, `/etc/66`; records installed confidence only. |
| Capability derivation | `evolution-engine/src/discovery/capabilities.py::derive_capabilities` | Emits `66-service-manager` only with high-confidence observation; this is capability evidence, not a service inventory. |
| Existing service repair planner | `evolution-engine/src/evolution/tools/service_supervision.py::ServiceSpec`, `ServiceSupervisor.plan`, `validate_coverage` | Previously accepted systemd only and returned executable `systemctl` argv plans. |
| Discovery regression | `evolution-engine/tests/test_discovery.py::DiscoveryTests.test_obarun_66_s6_is_detected_without_confusing_manager_and_init` | Test ID `T-OBARUN-66-001`; rooted fixture distinguishes s6 init and the 66 manager. |
| Repair regression | `evolution-engine/tests/test_evolution.py::VersionAndSchemeTests.test_66_and_s6_repairs_fail_closed_without_inventory_adapters` | Test ID `T-REPAIR-66S6-001`; verifies non-mutating plans for both runtimes and rejects traversal identifiers. |

Architecture grounding: AD-04 (capability discovery), AD-05 (observed state authoritative), AD-08 (adaptors constrained), AD-09 (argv, no shell), AD-14 (qualified support tier), AD-24 (service supervision contract). See `reports/ARCHITECTURE_DECISIONS.md`.

## Implementation

`ServiceSpec` now accepts `runtime="66"` and `runtime="s6"` with path-safe identifiers. The planner returns a declarative plan with no commands and no systemd drop-in for either runtime; its rationale calls out the missing inventory-backed adapter. `validate_coverage` rejects these empty plans as lacking a qualified repair adapter. The planner does not guess 66 bundle/tree names, s6 service directories, or invoke host tools.

This is a safe integration boundary, not yet a working 66/s6 mutator. Current code discovers manager markers but does not inventory concrete service objects or establish reversible operations. A future adapter needs rooted object inventory, capability evidence, dry-run output, checkpoint/restore semantics, and fixture captures before it can emit mutation argv.

## Verification and evidence

Command:

```sh
cd evolution-engine && python3 -m unittest tests.test_evolution tests.test_discovery
```

Result: PASS, 37 tests. Detailed output: `autonomy/codex/obarun-66-s6-repair-wave1-test.log`.

Regression IDs: `T-OBARUN-66-001` and `T-REPAIR-66S6-001`.

Changed implementation: `evolution-engine/src/evolution/tools/service_supervision.py`.  
Changed regression tests: `evolution-engine/tests/test_evolution.py`.
