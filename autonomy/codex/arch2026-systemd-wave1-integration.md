# Arch 2026 systemd integration — Wave 1

## Survey and verified repository catalogue

The Arch 2026 ISO is present at `/home/tak_0/.local/state/sunshine-orchestrator/iso/arch-2026.iso` (ISO label `ARCH_202611`). The ISO inventory was queried read-only with `xorriso -find / -name '*systemd*' -print`; it did not expose an extracted systemd root tree. The file-level upstream table in [the earlier survey](arch2026-systemd-wave1.md) therefore remains a candidate path catalogue, not byte-verified evidence about the ISO. No upstream hook file contents or package revision are asserted here.

| Concern | Exact repository path and symbol | Verified contract | Regression/evidence |
|---|---|---|---|
| Service/runtime discovery | `evolution-engine/src/discovery/services_desktop.py::_collect_systemd` | Observes system state, enabled service unit names and running units; records low confidence when commands fail. Discovery does not claim end-to-end functionality. | `evolution-engine/tests/test_discovery.py`; existing fixture suite |
| Desired service plan | `evolution-engine/src/evolution/tools/service_supervision.py::ServiceSpec`, `ServiceSupervisor.plan` | Validates declarative service specs and emits deterministic argv/drop-in plans; does not execute. | `evolution-engine/tests/test_artifacts.py` and service supervision coverage in `evolution-engine/tests/` |
| Full unit-file inventory | `evolution-engine/src/evolution/tools/systemd_inventory.py::parse_unit_file_inventory` | Parses unit-file state rows; command failure, malformed rows, unknown states, or duplicate names make the snapshot incomplete. | `evolution-engine/tests/test_systemd_inventory.py`, T-ARCH2026-SYSTEMD-001..006 |
| Desired-state assessment | `evolution-engine/src/evolution/tools/systemd_inventory.py::assess_unit_inventory` | Incomplete observation blocks every requested assessment; masked units block desired enabled/present; absent units request review/install; no mutation is performed. | Same test module, T-ARCH2026-SYSTEMD-002..005 |
| Safety policy | `reports/ARCHITECTURE_DECISIONS.md` AD-05, AD-09, AD-14; `evolution-engine/src/evolution/invariants.py` M-04, M-08, M-09 | Installation state is authoritative; code avoids shell execution; migration support and repeatability are checked as explicit invariants. | `evolution-engine/tests/test_evolution.py::VersionAndSchemeTests` |

## Wave 1 code change

The inventory name validator in `evolution-engine/src/evolution/tools/systemd_inventory.py::UNIT_NAME` now accepts the legacy `busname` unit type and the `snapshot` type as well as the existing types. Rejecting a valid row previously made an otherwise usable system inventory incomplete and caused desired-state checks to block. This does not enable mutations or treat failed collection as absence.

Test `T-ARCH2026-SYSTEMD-006` verifies both types parse without reducing completeness. Tests `T-ARCH2026-SYSTEMD-001..005` retain coverage for normal rows, failed probes, masks, malformed rows, and invalid desired identifiers.

## Grounding and open evidence

The ISO was identified by `file` as ISO 9660, volume label `ARCH_202611`. The read-only `xorriso` path query did not expose unit files. As a result, `/usr/lib/systemd/system/*.service`, `/etc/systemd/system/`, generator directories, udev rules, and PAM integration paths remain a layout survey to verify against an extracted ISO/package tree. Arch hook names cited by `autonomy/results/sub-research-hooks-0025.md` likewise lack accompanying evidence files in this checkout. Do not treat those names as verified upstream facts.

The architecture mapping follows AD-05 (observed state), AD-09 (safe command execution), AD-14 (qualified support), and invariants M-04/M-08/M-09. It preserves fail-closed behavior: incomplete data blocks assessment and systemd inventory remains read-only.

## Verification

Command: `cd evolution-engine && python3 -m unittest tests/test_systemd_inventory.py -v`

Result: 6 tests passed. Full raw output: [arch2026-systemd-wave1-integration-test.log](arch2026-systemd-wave1-integration-test.log).
