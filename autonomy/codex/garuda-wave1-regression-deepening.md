# Garuda Toolbox survey and regression deepening — Wave 1

## Scope and source provenance

Reviewed the local source checkout at `/home/tak_0/.local/state/sunshine-orchestrator/iso/repos/garuda-toolbox`, pinned to `430de5bc5356468318a5c677d8b2f6d2c4565a75`. This is a source-code survey and catalogue validation, not a runtime or ISO test. The checkout revision and every catalogued source path are checked by `GARUDA_CAT_011`.

The migration mandate establishes M-01..M-10; relevant policy is target-driven planning, observed-state authority, checkpoint/recovery and repeatability. Their implementation mapping is listed in `reports/ARCHITECTURE_DECISIONS.md` (AD-01..AD-30 and M-01..M-10 table). Existing Garuda classification coverage is in `evolution-engine/tests/test_compatibility.py` (`T-GARUDA-COMP-001` through `T-GARUDA-COMP-005`); this change stays inside `autonomy/codex/` and does not alter that in-flight engine work.

## Survey catalogue

| Pattern / risk | Exact Garuda source | Observation | SunshineOS disposition |
|---|---|---|---|
| Maintenance action grouping | `packages/renderer/src/app/components/maintenance/maintenance.component.ts:162-220,260-301` | Actions include remote repair/keyring/fullfix and system update/cache/orphan cleanup operations with UI metadata. | Adapt the discoverable grouping; bind each operation to a typed plan, journal and postcondition before mutation (M-01/M-05/M-06/M-09). |
| Updater fallback semantics | `packages/renderer/src/app/components/maintenance/maintenance.component.ts:260-274`; `packages/renderer/src/app/components/system-status/system-status.component.ts:112-124` | `garuda-update` falls back to `pacman -Syu`; system-status also constructs an update command. Fallback must not cross transaction/trust semantics silently. | Use capability-selected package adapters and show resolved transaction before action. |
| Orphan deletion | `packages/renderer/src/app/components/maintenance/maintenance.component.ts:290-300` | `pacman -Qtdq` is reevaluated in a loop and removed with `--noconfirm -Rns`; package set/dependency context can change. | Avoid unattended deletion; resolve/display the set and reverse dependencies and require explicit approval plus journal/postcondition. |
| Snapshot and boot repair | `packages/renderer/src/app/components/maintenance/maintenance.component.ts:370-383`; `packages/renderer/src/app/components/boot-repair/boot-repair.service.ts:463-470` | Btrfs Assistant action assumes a capability; MBR backup/restore emits `dd` commands targeting a device. | Adapt only after filesystem/boot inventory, validated target and checkpoint; verify restore result and preserve user data. |
| Shell/process boundary | `packages/main/src/modules/ShellModule.ts:15-30,134-183`; maintenance source above | IPC handlers call `spawn(command,args)`; UI maintenance actions also return shell command strings, including interpolation and fallback commands. | SunshineOS UI should submit allowlisted operation IDs and typed arguments to a least-privilege adapter; no UI-provided shell text (AD-08/AD-09). |
| Config reset | `packages/renderer/src/app/components/maintenance/maintenance.component.ts:518-540` | Reset builds `cp -r ${file} ${destination}` command strings and reports per-file result. | Use structured filesystem operations, validate paths and ownership, checkpoint existing content, and verify the resulting config. |

Machine-readable findings with source paths, invariant links, verdicts and required controls: `autonomy/codex/garuda-wave1-catalog.json` (five findings). Source observations above are tied to the pinned checkout; they are not claims that these behaviors are unique to Garuda or suitable to copy as-is.

## Code and tests

Hardened `autonomy/codex/garuda_catalog.py` to validate JSON object/list types, full lowercase hexadecimal commit IDs, safe relative paths, and string-list controls/invariant references. The CLI checks that cited paths exist in the recorded checkout when it is available. This remains a recording/provenance guard; it does not execute maintenance actions or grant privileges.

`autonomy/codex/test_garuda_catalog.py` contains these regression IDs:

- `GARUDA_CAT_001` catalog/revision load.
- `GARUDA_CAT_002` plan/journal/postcondition controls for adopted findings.
- `GARUDA_CAT_003` duplicate finding IDs fail closed.
- `GARUDA_CAT_004` missing journal control rejected.
- `GARUDA_CAT_005` unknown invariant rejected.
- `GARUDA_CAT_006` non-object catalog shapes rejected.
- `GARUDA_CAT_007` malformed full revision rejected.
- `GARUDA_CAT_008` non-object finding rejected.
- `GARUDA_CAT_009` source path traversal rejected.
- `GARUDA_CAT_010` malformed control shape rejected.
- `GARUDA_CAT_011` checkout revision and cited source paths verified.

## Verification evidence

Commands run from repository root:

```sh
python3 -m unittest autonomy/codex/test_garuda_catalog.py
python3 autonomy/codex/garuda_catalog.py
```

Both passed; 11 tests ran and the CLI validated all five findings. Detailed output and the exact revision/path verification are in `autonomy/codex/garuda-wave1-regression-deepening-test.log`.
