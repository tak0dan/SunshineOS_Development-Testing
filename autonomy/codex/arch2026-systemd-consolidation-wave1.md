# Arch 2026 systemd deliverable consolidation — Wave 1

## Scope and grounding

Surveyed the repository implementation against the migration mandate and architecture decisions. This is a repository-level implementation survey; prior evidence at `autonomy/codex/arch2026-systemd-wave1-integration.md` records that the ISO query did not expose an extracted Arch 2026 systemd root tree. Consequently, this deliverable makes no byte-level claims about Arch package unit files or upstream hooks.

The governing requirements are observation-first inventory and fail-closed transitions in `reports/USER_MIGRATION_MANDATE_2026-11-21.md`; AD-05 (observed installation is authoritative), AD-09 (safe argv boundaries), AD-14 (qualified support), AD-24 (declarative service management), and AD-30 (modular engine) in `reports/ARCHITECTURE_DECISIONS.md`.

## Exact-path catalogue

| Concern | Path and symbol | Observed role |
|---|---|---|
| Frozen Arch anchor | `evolution-engine/src/evolution/baseline.py::ARCH_2026_BASELINE`; `evolution-engine/evolution/docs/BASELINE_ARCH_2026.md` | Pins a baseline epoch instead of a floating Arch release. |
| Runtime service observations | `evolution-engine/src/discovery/services_desktop.py::_collect_systemd` | Separately records enabled and running observations; these are observations rather than proof of service health. |
| Unit-file parser/policy | `evolution-engine/src/evolution/tools/systemd_inventory.py::parse_unit_file_inventory`, `assess_unit_inventory` | Failed or ambiguous probes are incomplete; masked and `bad` states block desired transitions. |
| Service proposal boundary | `evolution-engine/src/evolution/tools/service_supervision.py::ServiceSupervisor.plan_checked` | Checks inventory before emitting deterministic argv proposals. |
| Rooted file-layer assessment | `evolution-engine/src/evolution/tools/systemd_repair.py::assess_systemd_unit_files` | Catalogues vendor/admin definitions, masks and unsafe symlinks without mutation. |
| New evidence handoff | `evolution-engine/src/evolution/tools/systemd_consolidation.py::consolidate_systemd_evidence` | Joins inventory, desired policy and unit-file evidence, keeping blockers and emitting no commands. |
| Prior regression contracts | `evolution-engine/tests/test_systemd_inventory.py`, `evolution-engine/tests/test_systemd_repair.py` | Existing test IDs cover parser/policy and rooted repair evidence. |

## Change

Added `consolidate_systemd_evidence`, a single read-only assessment boundary for consumers that need both systemd's unit-file state and on-disk vendor/admin evidence. It deliberately does not equate a file's presence with a loaded or healthy service. A failed systemctl probe remains incomplete even when the expected file exists; a masked desired unit remains blocked across both evidence layers. The serialized result includes explicit blockers and an empty command list, so this layer cannot accidentally become an executor.

## Regression and evidence

- `T-ARCH2026-SYSTEMD-CONSOLIDATION-001`: joins a satisfied enabled unit with its vendor file.
- `T-ARCH2026-SYSTEMD-CONSOLIDATION-002`: failed systemctl collection remains blocked despite file presence.
- `T-ARCH2026-SYSTEMD-CONSOLIDATION-003`: preserves a mask blocker in inventory and filesystem evidence.
- Existing tests `T-ARCH2026-SYSTEMD-001` through `017` and `T-ARCH2026-SYSTEMD-REPAIR-001` through `005` also pass.
- Command: `cd evolution-engine && python3 -m unittest tests/test_systemd_consolidation.py tests/test_systemd_inventory.py tests/test_systemd_repair.py -v`
- Result: 25 tests passed. Raw output: `autonomy/codex/arch2026-systemd-consolidation-wave1-test.log`.

## Changed files

- `evolution-engine/src/evolution/tools/systemd_consolidation.py`
- `evolution-engine/tests/test_systemd_consolidation.py`
- `autonomy/codex/arch2026-systemd-consolidation-wave1.md`
- `autonomy/codex/arch2026-systemd-consolidation-wave1-test.log`

No report files were changed.
