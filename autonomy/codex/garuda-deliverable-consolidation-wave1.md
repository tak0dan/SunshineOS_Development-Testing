# Garuda deliverable consolidation — Wave 1 deepening

## Grounded scope

This index consolidates the existing Garuda Toolbox work; it does not claim that
Garuda itself is qualified as a migration source or that its maintenance actions
were executed. The reviewed upstream source checkout is
`/home/tak_0/.local/state/sunshine-orchestrator/iso/repos/garuda-toolbox` at
`430de5bc5356468318a5c677d8b2f6d2c4565a75`. The catalogue and architecture
audit pin that revision and name exact relative source paths.

## Deliverable map

| Concern | SunshineOS artifact | Source/evidence |
|---|---|---|
| Survey and disposition catalogue | `autonomy/codex/garuda-wave1.md`, `autonomy/codex/garuda-wave1-catalog.json` | Maintenance, updater, cleanup, snapshot/boot, shell boundary, and config reset findings. |
| Catalog provenance enforcement | `autonomy/codex/garuda_catalog.py`, `autonomy/codex/test_garuda_catalog.py` | `GARUDA_CAT_001–GARUDA_CAT_011`; evidence: `autonomy/codex/garuda-wave1-regression-deepening-test.log`. |
| Architecture/source audit | `autonomy/codex/garuda_architecture_audit.py`, `autonomy/codex/test_garuda_architecture_audit.py` | The checked-in snapshot `autonomy/codex/garuda-wave1-architecture-audit.json` contains six findings (IDs `GARUDA-ARCH-001–GARUDA-ARCH-006`); the live audit tests cover nine source checks. Source behaviors include `packages/renderer/src/app/components/maintenance/maintenance.component.ts`, `packages/renderer/src/app/components/boot-repair/boot-repair.service.ts`, and `packages/main/src/modules/ShellModule.ts`. |
| Migration source classification | `evolution-engine/src/target/compatibility.py::classify_source`; `evolution-engine/tests/test_compatibility.py` | `T-GARUDA-COMP-001–T-GARUDA-COMP-005`; evidence: `autonomy/codex/garuda-wave1-integration-test.log`. Conditional preflight does not imply migration qualification. |
| Pacman lock repair safety | `autonomy/codex/pacman_lock_repair.py`, `autonomy/codex/test_pacman_lock_repair.py` | `GARUDA_REPAIR_001–GARUDA_REPAIR_004`; evidence: `autonomy/codex/garuda-repair-wave1-test.log`. Assessment is read-only and an ownerless lock is not authorization to delete it. |
| CI portability and policy | `.github/workflows/garuda.yml`, `autonomy/codex/test_ci_policy_audit.py` | Evidence: `autonomy/codex/garuda-ci-auditor-test.log`, `autonomy/codex/garuda-ci-policy-audit.log`, and `autonomy/codex/garuda-ci-regression-test.log`. |

## Architectural application

The adapted controls follow migration mandate invariants M-01 through M-10 and
the AD-01 through AD-30 mapping in `reports/ARCHITECTURE_DECISIONS.md`: discover
capabilities from the observed machine, resolve a typed plan, preserve package
transaction/trust semantics, checkpoint before mutation, journal work, and
verify postconditions. In particular, never turn a renderer-provided command
string, an automatically selected orphan set, or a device path into privileged
authority. The migration integration is conditional and must remain subject to
source-matrix qualification (M-08).

## Consolidation regression

Regression ID range: `GARUDA_CONSOL_001–GARUDA_CONSOL_003`.

`autonomy/codex/test_garuda_deliverable_consolidation.py` adds:

- `GARUDA_CONSOL_001` — pinned revision and every catalogued upstream file exist.
- `GARUDA_CONSOL_002` — audit, code, tests, and prior evidence artifacts are present.
- `GARUDA_CONSOL_003` — this index names the regression IDs and evidence log.

Run from the repository root:

```sh
python3 -m unittest autonomy/codex/test_garuda_deliverable_consolidation.py
```

Captured output: `autonomy/codex/garuda-deliverable-consolidation-wave1-test.log`.
