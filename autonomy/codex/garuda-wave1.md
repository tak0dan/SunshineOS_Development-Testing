# Garuda development leadership — Wave 1

**Scope:** survey the locally available Garuda Toolbox source, catalogue actionable patterns, and provide a machine-checkable guard for recording adapted patterns. Source inspected at `/home/tak_0/.local/state/sunshine-orchestrator/iso/repos/garuda-toolbox`, revision `430de5bc5356468318a5c677d8b2f6d2c4565a75`. This is a source checkout review, not a runtime or ISO audit.

## Repository grounding

The governing migration invariants are M-01 through M-10 in `reports/USER_MIGRATION_MANDATE_2026-11-21.md` and the implementing map in `reports/ARCHITECTURE_DECISIONS.md`. Relevant existing code includes `evolution-engine/src/evolution/compatibility.py::SOURCE_PROFILES` (Garuda markers and repository hints), `evolution-engine/src/target/compatibility.py::classify_source` (active source classification), and `evolution-engine/tests/test_compatibility.py`. The latter engine files are already modified in the shared worktree, so this wave records the integration contract without touching them.

## Survey and catalogue

| Finding | Exact source | Observation | SunshineOS disposition |
|---|---|---|---|
| Categorized maintenance surface | `packages/renderer/src/app/components/maintenance/maintenance.component.ts:164` onward | Named actions cover repository/keyring repair, package reinstall, updates, cleanup, snapshots and diagnostics. This is a useful discoverability model. | **Adapt** categories and status UX. Resolve each action to a plan, journal, postcondition and recovery path before enabling mutation (M-01/M-05/M-06/M-09). |
| Update orchestration | `packages/renderer/src/app/components/system-status/system-status.component.ts:120-122`; maintenance component `:269-274` | Calls the distro updater when present, otherwise falls back to `pacman -Syu`. A fallback can change transaction semantics and must be explicit in SunshineOS. | **Adapt** only behind a capability-selected package adapter and a displayed transaction plan; no silent fallback across trust or transaction boundaries (M-04/M-05/M-06). |
| Orphan cleanup | `packages/renderer/src/app/components/maintenance/maintenance.component.ts:290-300` | The loop repeats `pacman -Qtdq` and removes with `--noconfirm -Rns`. Orphan status may change and dependency removal can be consequential. | **Avoid** automatic deletion. Show the resolved package set and reverse dependencies, require explicit approval, journal and verify (M-01/M-05/M-06/M-09). |
| Snapshot and boot repair | `packages/renderer/src/app/components/maintenance/maintenance.component.ts:228-240,370-383`; `packages/renderer/src/app/components/boot-repair/boot-repair.service.ts:463-468` | Snapper reset / Btrfs Assistant and MBR backup/restore functionality are exposed. Their safety depends on detected filesystem, mount and boot layout. | **Adapt** after inventory capability checks; checkpoint before writes; default snapshots to OS state and exclude user data; verify boot target (M-04/M-05/M-06/M-10). |
| Privileged shell boundary | `packages/main/src/modules/ShellModule.ts:25,138-180`; maintenance component `:517-535` | Main process spawns commands, while UI action definitions supply shell command text. | **Adapt** the UI-to-main-process separation, but SunshineOS actions should use typed operation IDs and argv with a narrow privileged helper, never UI-provided shell strings (M-04/M-06; AD-08/AD-09). |
| Repository and signing repair | `packages/renderer/src/app/components/maintenance/maintenance.component.ts:164-210,303-368` | Distinct actions exist for repository “fix”, mirror refresh, keyring refresh and reset flows. Repair can alter trust/configuration. | **Adapt** only with preserved configuration, exact signer and revocation validation, and fail-closed behavior on refresh errors (M-02/M-05/M-06/M-07). |

The exact, reviewable records are in [`garuda-wave1-catalog.json`](garuda-wave1-catalog.json). The source checkout's README identifies `pacman-contrib`, `garuda-libs`, `garuda-update`, and `paru` as dependencies (`README.md:7-12`); this is useful packaging context, not proof that every installation has those capabilities.

## Implementation and regression evidence

Added `garuda_catalog.py`, a stdlib-only validator. It rejects records without a pinned full source revision, source paths, unique stable IDs, valid invariant references, and mandatory plan/journal/postcondition controls for `ADAPT` or `COPY` findings. The catalog validator is deliberately a recording guard, not an executor and grants no package or root privileges.

Regression test IDs:

- `GARUDA_CAT_001` — source revision and catalog load.
- `GARUDA_CAT_002` — adapted/copied findings carry safety controls.
- `GARUDA_CAT_003` — duplicate finding IDs fail closed.
- `GARUDA_CAT_004` — adopted pattern without journaling fails closed.
- `GARUDA_CAT_005` — invalid invariant reference fails closed.

Run from repository root:

```sh
python3 -m unittest autonomy/codex/test_garuda_catalog.py
python3 autonomy/codex/garuda_catalog.py
```

Evidence log: `autonomy/codex/garuda-wave1-test.log`.

## Follow-up integration

Feed the catalog dispositions into the active `src/target/compatibility.py` only after the current in-flight compatibility changes settle. A future GUI can adopt Garuda's task grouping and progress presentation, while its engine-facing contract stays with the existing planner/executor, signed-adapter, journaling and recovery boundaries. No runtime behavior was changed in this wave.
