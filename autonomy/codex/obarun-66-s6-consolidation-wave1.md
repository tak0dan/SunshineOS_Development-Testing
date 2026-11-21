# Obarun / 66 / s6 deliverable consolidation — Wave 1

Date: 2026-11-21  
Scope: consolidate the repository-grounded discovery and repair boundary, catalogue exact paths, and separate verified source evidence from inherited claims.

## Findings and evidence boundary

The local source corpus contains an s6 checkout at `/home/tak_0/.local/state/sunshine-orchestrator/iso/repos/s6`, revision `c7c24531c294e2573e79380de8c2d21849cb39ad`. The Obarun distribution and an independent 66 source checkout were not present in the inspected corpus. The project task therefore has no captured Obarun filesystem, service database, or live service output to support a byte-level claim about Obarun's installed layout. Earlier `autonomy/results/lead-research-0002.md` and `autonomy/results/sub-migration-ledger-0003.md` contain hypothetical paths and test/evidence identifiers; these are not observed artifacts and must not be consumed as transition evidence.

The s6 source's `Makefile:136-139` defines `check` by looping over test binaries through `tools/run-test.sh`. That runner (`tools/run-test.sh:3-21`) assembles a shell command string and invokes it unquoted, then removes the expected-output file only after a successful diff. This is a source-level test harness observation, not an executed upstream test result. There is no tracked CI workflow in that checkout. The prior CI audit is recorded in `autonomy/codex/obarun-66-s6-ci-wave1.md` and `autonomy/codex/obarun-66-s6-ci-wave1-audit.log`.

## Exact repository catalogue

| Path and symbol | Current behavior | Qualification |
|---|---|---|
| `evolution-engine/src/discovery/system.py::_detect_init_system` | Uses rooted markers and PID 1 evidence; maps `s6-*` PID 1 names to init family `s6`. | A rooted fixture verifies behavior; no Obarun host was observed. |
| `evolution-engine/src/discovery/system.py::_detect_66_manager` | Records `/usr/bin/66`, `/usr/sbin/66`, `/etc/66` presence as installed evidence; one marker is medium confidence, two or more high. | Does not claim manager responsiveness or inventory services. |
| `evolution-engine/src/discovery/capabilities.py::derive_capabilities` | Exposes `66-service-manager` only with high-confidence marker evidence. | Capability signal only; not authorization to mutate. |
| `evolution-engine/src/evolution/tools/service_supervision.py::ServiceSpec`, `ServiceSupervisor.plan`, `ServiceSupervisor.validate_coverage` | Accepts 66/s6 identifiers but emits no mutation command/drop-in for them; coverage validation rejects plans without a qualified adapter. | Fail-closed planning boundary pending inventory and recovery adapters. |
| `evolution-engine/tests/test_discovery.py::DiscoveryTests.test_obarun_66_s6_is_detected_without_confusing_manager_and_init` | Fake-root regression for PID 1 `s6-svscan` plus independent 66 markers. | ID `T-OBARUN-66-001`. |
| `evolution-engine/tests/test_evolution.py::StabilityToolsTests.test_66_and_s6_repairs_fail_closed_without_inventory_adapters` | Checks empty mutation plans and traversal rejection for 66/s6. | ID `T-REPAIR-66S6-001`. |
| `autonomy/codex/obarun-66-s6-wave1.md` | Prior discovery change summary and limits. | Existing project artifact. |
| `autonomy/codex/obarun-66-s6-repair-wave1.md` | Prior service repair boundary summary. | Existing project artifact. |
| `autonomy/codex/obarun-66-s6-ci-wave1.md` | s6 harness/CI source catalogue. | Existing project artifact. |

Architecture alignment: AD-04/05/08/09/14 and M-04/06/08/09 constrain discovery to observed capabilities and require qualified, recoverable execution. This wave preserves those constraints: 66 presence never implies a safe bundle mapping, and s6 presence never implies a service path.

## Regression evidence

Command: `cd evolution-engine && python3 -m unittest -v tests.test_discovery tests.test_evolution`  
Result: PASS, 37 tests.  
Evidence log: `autonomy/codex/obarun-66-s6-consolidation-wave1-test.log`  
Regression IDs: `T-OBARUN-66-001`, `T-REPAIR-66S6-001`.

## Next evidence needed before enabling a repair adapter

Capture a versioned Obarun image or source checkout and record package ownership, exact 66 service-object inventory, dependency/order representation, state query output, and reversible operation semantics. Store source hashes and fixture captures under an owned evidence directory. Until then, 66/s6 service repair remains deliberately non-mutating.
