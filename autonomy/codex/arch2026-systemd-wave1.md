# Arch 2026 systemd survey — Wave 1

## Verified repository catalogue

The repository implements systemd-aware service discovery and declarative planning. These are the concrete paths found and read in this checkout:

| Concern | Repository path and symbol | Verified behavior |
|---|---|---|
| Runtime and enabled/running unit observations | `evolution-engine/src/discovery/services_desktop.py::_collect_systemd` | Queries `systemctl is-system-running`, enabled service unit files and running services. Emits evidence-backed observations and falls back to per-unit checks for known backends. |
| Desired service declarations and argv plan | `evolution-engine/src/evolution/tools/service_supervision.py::ServiceSpec`, `ServiceSupervisor.plan` | Validates unit/state fields and renders deterministic argv. It does not execute commands. |
| Service supervision API | `evolution-engine/src/evolution/tools/__init__.py` | Re-exports the service supervisor data types. |
| New unit-file inventory assessment | `evolution-engine/src/evolution/tools/systemd_inventory.py::parse_unit_file_inventory`, `assess_unit_inventory` | Parses observed unit-file states and returns review/block findings without mutation. Failed or malformed collection stays unknown/incomplete. |
| Regression cases | `evolution-engine/tests/test_systemd_inventory.py` | T-ARCH2026-SYSTEMD-001 through -005 cover parsing, probe failure, masked services, malformed output, and invalid identifiers. |
| Architecture grounding | `reports/ARCHITECTURE_DECISIONS.md` AD-05, AD-09, AD-14, AD-24; `evolution-engine/src/evolution/invariants.py` M-04, M-08, M-09 | Observed state remains authoritative; safety and support require explicit validation and repeatability. |

## Upstream hook inventory: evidence status

`autonomy/results/sub-research-hooks-0025.md` lists candidate Arch paths such as `/usr/share/libalpm/hooks/90-systemd.hook` through `99-systemd-udev-trigger.hook`, with IDs HOOK-SUN-001..014. The referenced `evidence/wave1/hook-*.md` files are not present in this checkout, and the report does not include file contents or source package revision. Therefore those hook names and adopt/adapt/isolate decisions remain unverified leads, not established upstream facts.

Similarly, `autonomy/results/sub-code-kernel-0026.md` maps boot parameters to paths including `evolution-engine/config/kernel_cmdline.yaml` and `evolution-engine/config/power.yml`; those mapped files are not present. Its performance thresholds are proposed acceptance criteria, not measurements evidenced here.

No Arch ISO or extracted root tree was inspected in this task. This report does not claim byte-level verification of Arch 2026 package contents. The repository-level implementation deliberately avoids encoding unverified unit/hook assumptions.

## Implementation behavior

The inventory assessor accepts the output rows from `systemctl list-unit-files --no-legend`. It preserves recognized states including enabled, static, disabled, masked, generated and transient. A failed query or any malformed/unknown row marks the inventory incomplete; every requested desired-state check then blocks. For a complete inventory, absent units are distinct from failed observation, masked units block desired enabled/present states, and other mismatches are flagged for review. The module never runs systemctl or changes the machine.

## Verification

Command: `cd evolution-engine && python3 -m unittest tests/test_systemd_inventory.py -v`

Result: 5 tests passed. Raw output: `autonomy/codex/arch2026-systemd-wave1-test.log`.
