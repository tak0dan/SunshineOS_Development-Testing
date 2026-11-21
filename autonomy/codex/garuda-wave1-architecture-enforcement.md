# Garuda architecture enforcement — Wave 1 deepening

## Scope and grounding

This source survey uses the local Garuda Toolbox checkout at revision
`430de5bc5356468318a5c677d8b2f6d2c4565a75`. The governing policy is the user
migration mandate and `reports/ARCHITECTURE_DECISIONS.md`: the observed system is
authoritative (M-04), changes are staged and recoverable (M-05/M-06), repeated
execution is controlled (M-09), and user data is separate (M-10). Relevant
decisions include AD-08/AD-09 (signed, constrained adapters and argv/no shell),
AD-11 (checkpoint and restore), AD-16 (verification), and AD-22 (deterministic
resolution).

The prior catalog at `autonomy/codex/garuda-wave1-catalog.json` describes five
findings. This deepening adds a read-only source audit so those findings are
checked against the actual pinned checkout rather than accepted as prose alone.

## Architecture survey and enforcement mapping

| Audit ID | Exact Garuda source | Verified behavior | SunshineOS architecture enforcement |
|---|---|---|---|
| `GARUDA-ARCH-001` | `packages/renderer/src/app/components/maintenance/maintenance.component.ts:272` | Update action selects `garuda-update` when available and falls back to `pacman -Syu`. | Resolve updater capability and transaction through the planner; require the chosen operation and trust path to be explicit (M-01/M-04/M-05). |
| `GARUDA-ARCH-002` | `packages/renderer/src/app/components/maintenance/maintenance.component.ts:299` | Orphan cleanup includes `pacman --noconfirm -Rns` in a loop. | Do not auto-confirm removal. Inventory and display the package set, acquire transaction ownership, journal, and verify package state (M-04/M-06/M-09). |
| `GARUDA-ARCH-003` | `packages/renderer/src/app/components/maintenance/maintenance.component.ts:174` | Renderer maintenance action invokes a shell-command API. | User interface should submit an allowlisted operation ID and typed arguments to a narrow adapter, never shell text (AD-08/AD-09). |
| `GARUDA-ARCH-004` | `packages/renderer/src/app/components/maintenance/maintenance.component.ts:526` | Config reset interpolates paths into a `cp -r` command. | Use structured filesystem APIs; constrain paths, preserve current config as a checkpoint, reconcile ownership and verify postconditions (M-05/M-06/M-10). |
| `GARUDA-ARCH-005` | `packages/renderer/src/app/components/boot-repair/boot-repair.service.ts:469` | MBR restore builds a raw-device write with `dd`. | Require observed boot mode/device identity, validated target, checkpoint, explicit plan, and post-write validation. A device mismatch must block (M-04/M-05/M-06). |
| `GARUDA-ARCH-006` | `packages/main/src/modules/ShellModule.ts:16-26` | Shell IPC receives `command` and `args` and passes them to `spawn`. | Keep argv execution, but authorize the operation at a privileged boundary; validate operation identity/arguments and do not allow renderer-supplied executables or options (AD-08/AD-09). |

Line-level machine evidence is generated in
`autonomy/codex/garuda-wave1-architecture-audit.json`. This is a source checkout
survey, not a runtime, ISO, exploitability or complete security audit. Findings
describe inspected implementation, not whether Garuda behavior is currently
exploitable.

## Working code and regression coverage

Added `autonomy/codex/garuda_architecture_audit.py`. It reads the existing source
pin, checks the Git revision before inspection, requires all six expected source
behaviors, and emits source path, line number, and evidence excerpt. It is
read-only and grants no privileges. Revision drift, missing files, or absent
behavior fail closed.

Regression IDs in `autonomy/codex/test_garuda_architecture_audit.py`:

- `GARUDA_ARCH_001` — all six source behaviors exist at the pinned revision and
  each returns line/evidence.
- `GARUDA_ARCH_002` — revision mismatch is rejected.
- `GARUDA_ARCH_003` — missing expected safety evidence is rejected.

The prior catalog validator was also rerun: `GARUDA_CAT_001` through
`GARUDA_CAT_011`.

## Verification evidence

Commands run from repository root:

```sh
python3 -m unittest autonomy/codex/test_garuda_catalog.py autonomy/codex/test_garuda_architecture_audit.py
python3 autonomy/codex/garuda_catalog.py
python3 autonomy/codex/garuda_architecture_audit.py
```

Results: 14 tests passed; the catalog validator validated five findings; source
audit emitted six checks at the pinned revision. Full command output is in
`autonomy/codex/garuda-wave1-architecture-enforcement-test.log`; structured
source evidence is in `autonomy/codex/garuda-wave1-architecture-audit.json`.
