# Garuda repair tools — Wave 1 deepening

## Scope and source identity

Surveyed the local `garuda-toolbox` source checkout at revision
`430de5bc5356468318a5c677d8b2f6d2c4565a75`:
`/home/tak_0/.local/state/sunshine-orchestrator/iso/repos/garuda-toolbox`.
The cited source is outside the SunshineOS git tree and was inspected read-only.
The mandate and architecture context are `reports/USER_MIGRATION_MANDATE_2026-11-21.md`
and `reports/ARCHITECTURE_DECISIONS.md`; neither was modified.

## Repair surface catalogue

| Repair/tool | Exact Garuda source | Observed behavior | SunshineOS adoption/control |
|---|---|---|---|
| Remote repair actions | `packages/renderer/src/app/components/maintenance/maintenance.component.ts:164-280` | UI launches `garuda-update remote fix`, `remote keyring`, `remote fullfix`, reset actions and reinstall via terminal shell strings. | Keep repair actions discoverable; map them to typed operation IDs, capability checks, plans, journal entries and postconditions (AD-08/AD-09, M-05/M-06). |
| System update | `packages/renderer/src/app/components/maintenance/maintenance.component.ts:283-288` | Prefers `garuda-update --skip-mirrorlist`, else invokes `pacman -Syu`. | Do not silently switch transaction semantics. Resolve one available signed adapter and present its plan before execution (M-04/M-05). |
| Cache cleanup | `packages/renderer/src/app/components/maintenance/maintenance.component.ts:280-288` | Invokes `paccache -ruk 0`, which removes cached package versions. | Show the resolved deletion set and preserve rollback artifacts according to retention policy; require explicit confirmation (M-05/M-06). |
| Orphan cleanup | `packages/renderer/src/app/components/maintenance/maintenance.component.ts:290-300` | Repeats `pacman -Qtdq` then runs `pacman --noconfirm -Rns` on results. | Never auto-remove. Recompute and display the complete transaction, reverse dependencies and package DB lock status; journal approved changes (M-05/M-06/M-09). |
| Mirror/keyring maintenance | `packages/renderer/src/app/components/maintenance/maintenance.component.ts:302-368` | Refreshes Arch/Chaotic mirrors and runs `pacman-key --refresh-keys`; mirror output is copied into `/etc/pacman.d`. | Stage and preserve config, validate provenance and exact signer/revocation state; a failed refresh must not expand trust (M-02/M-05/M-07). |
| Btrfs Assistant | `packages/renderer/src/app/components/maintenance/maintenance.component.ts:370-385` | Starts the GUI tool if `btrfs-assistant` can be installed. | Gate on detected filesystem/subvolume capabilities; keep snapshots OS-scoped and exclude user data by default (M-04/M-10). |
| Pacman lock removal | `packages/renderer/src/app/components/maintenance/maintenance.component.ts:388-400` | If `/var/lib/pacman/db.lck` exists, directly removes it. No owner/process check is visible in this action. | Implemented below as a read-only assessment: a live owner blocks, inaccessible process state is unknown, and an ownerless lock is only a candidate. No deletion API is provided. |
| Health check/fix | `packages/renderer/src/app/components/maintenance/maintenance.component.ts:438-458` | Exposes `garuda-health` and `garuda-health --fix` through a terminal. | Treat `--fix` as a separate planned mutation set; capture before/after evidence and checkpoint before repair. Further source inspection of `garuda-health` internals is a follow-up. |
| Boot repair | `packages/renderer/src/app/components/boot-repair/boot-repair.service.ts:300-303, 430-470` | Builds privileged scripts for GRUB installation/update and MBR backup/restore (`dd` of 446 bytes). | Require resolved disk/ESP identity, mounted-layout validation, backup/checkpoint, explicit target confirmation and boot postcondition. Preserve original boot mode. |
| Privileged shell boundary | `packages/main/src/modules/ShellModule.ts:25,138-180`; `packages/renderer/src/app/components/maintenance/maintenance.component.ts:517-535,646-650` | Renderer maintenance definitions hand shell command strings to the main process; the boot service also submits scripts. | SunshineOS boundary must accept allowlisted operation IDs plus validated argv, not UI-authored shell fragments (AD-08/AD-09). |

`autonomy/codex/garuda-wave1-catalog.json` retains the five broader categorized
findings and their plan/journal/postcondition controls. The source-path validator
is `autonomy/codex/garuda_catalog.py`.

## Delivered code

Added `autonomy/codex/pacman_lock_repair.py`. `assess_pacman_lock()` inspects the
lock path and `/proc` process `comm` entries for known package transaction
processes. It reports `missing`, `active-owner`, `owner-unknown` or
`stale-candidate`. It never mutates the lock, and `repair_allowed` is always
false. An ownerless lock does not prove staleness: callers must recheck and use
an independently reviewed checkpointed repair procedure.

This implements a concrete control prompted by the Garuda lock-removal action
and aligns with AD-08/AD-09 plus M-05/M-06. It is a repair assessment primitive,
not yet wired into the toolbox or migration executor.

## Regression IDs and evidence

- `GARUDA_REPAIR_001` — absent lock is reported; repair remains unauthorized.
- `GARUDA_REPAIR_002` — detected `pacman` process blocks repair and lock remains.
- `GARUDA_REPAIR_003` — ownerless lock is only a candidate and remains present.
- `GARUDA_REPAIR_004` — inaccessible process table fails closed as unknown.
- Existing `GARUDA_CAT_001`–`GARUDA_CAT_011` cover catalog provenance and controls.

Run from repository root:

```sh
python3 -m unittest autonomy/codex/test_garuda_catalog.py autonomy/codex/test_pacman_lock_repair.py
python3 autonomy/codex/garuda_catalog.py
```

Evidence: `autonomy/codex/garuda-repair-wave1-test.log` — 15 tests passed;
catalog validation reported 5 findings. The regression source is
`autonomy/codex/test_pacman_lock_repair.py`.

## Next investigation

Inspect the pinned Garuda implementation behind `garuda-health --fix` and
`garuda-update remote fullfix`, recording each filesystem/package mutation,
precondition, rollback behavior and validation result. Do not treat the UI
action label as evidence of safety or completeness.
