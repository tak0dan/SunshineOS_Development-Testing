# Garuda migration engine survey — Wave 1 deepening

## Scope and evidence boundary

Inspected the local Garuda Toolbox checkout at `/home/tak_0/.local/state/sunshine-orchestrator/iso/repos/garuda-toolbox`, pinned to `430de5bc5356468318a5c677d8b2f6d2c4565a75`. The checkout is an Electron/Angular maintenance application. Within this checkout, I found no OS migration engine, historical state resolver, transition catalog, migration journal, or staged OS root switch. The findings below therefore describe update and repair UI flows, not a native Garuda OS migration subsystem. This distinction is important for applying the repository mandate's M-01 through M-10 and AD-01 through AD-30 without treating app update behavior as qualified OS migration behavior.

Governing records: `reports/USER_MIGRATION_MANDATE_2026-11-21.md` (M-01..M-10) and `reports/ARCHITECTURE_DECISIONS.md` (AD-01..AD-30). In particular, target resolution, authoritative inventory, staging, recovery, repeatability, and data separation remain SunshineOS requirements; they are not demonstrated by the surveyed UI code.

## Catalogue

| Concern | Exact Garuda source | Verified behavior | SunshineOS application |
|---|---|---|---|
| Desktop application update | `packages/main/src/modules/AutoUpdater.ts:24-46` | `electron-updater` checks the Toolbox application's distribution channel and invokes `checkForUpdatesAndNotify`. | Keep application self-update separate from OS evolution and package transactions. |
| App updater failure policy | `packages/main/src/modules/AutoUpdater.ts:47-63` | Several expected publication/network errors are warnings; other errors are logged and converted to `null`, allowing the app to continue. | Suitable for optional UI self-update availability, not for migration qualification or OS update success reporting. |
| OS package update flow | `packages/renderer/src/app/components/system-status/system-status.component.ts:112-125`; `packages/renderer/src/app/components/maintenance/maintenance.component.ts:260-274` | A task invokes `garuda-update --skip-mirrorlist` when available and falls back to `pacman -Syu`. | Treat each backend as a distinct capability and transaction contract. Resolve and display a plan before execution; do not silently bridge incompatible trust/transaction behavior (M-04/M-05). |
| Orphan package cleanup | `packages/renderer/src/app/components/maintenance/maintenance.component.ts:290-300` | Repeatedly queries `pacman -Qtdq`, then uses `pacman --noconfirm -Rns`. The selected set is recomputed during the loop. | Do not copy unattended removal. Freeze the proposed package set, show consequences, require approval, journal, and verify (M-01/M-06/M-09). |
| Package dependencies | `README.md:7-13` | Toolbox documents `garuda-update` for system updates and `pacman-contrib` / `paru` for package-related features. | Treat these as optional capabilities discovered from the host; README dependency declarations are not proof of installed availability. |

## Working code and regression checks

Extended `autonomy/codex/garuda_architecture_audit.py` with source checks `GARUDA-ARCH-007` through `GARUDA-ARCH-009` to verify the app self-updater, its failure handling, and the distinct system-update path in the pinned checkout. Added regression `GARUDA_ARCH_004` to assert that app update and OS update evidence point to different source modules. Existing checks `GARUDA-ARCH-001` through `GARUDA-ARCH-006` cover updater fallback, automatic orphan removal, shell execution, interpolated config reset, raw-device `dd`, and shell IPC.

Catalog validation IDs are `GARUDA_CAT_001` through `GARUDA_CAT_011`; source audit test IDs are `GARUDA_ARCH_001` through `GARUDA_ARCH_004`. The catalog validator in `autonomy/codex/garuda_catalog.py` requires provenance, safe source paths, invariant links, and plan/journal/postcondition controls for adopted patterns.

Command run from repository root:

```sh
python3 -m unittest autonomy/codex/test_garuda_catalog.py autonomy/codex/test_garuda_architecture_audit.py
python3 autonomy/codex/garuda_catalog.py
python3 autonomy/codex/garuda_architecture_audit.py > autonomy/codex/garuda-wave1-migration-audit.json
```

Result: 15 tests passed; catalog validated five findings. The JSON audit evidence records the pinned source revision, exact relative paths, line numbers, descriptions, and matched source excerpts at `autonomy/codex/garuda-wave1-migration-audit.json`. The test log is `autonomy/codex/garuda-wave1-migration-test.log`.
