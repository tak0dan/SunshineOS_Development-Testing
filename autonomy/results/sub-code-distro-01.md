# Distro admin tool source audit

- Agent: sub-code-distro
- Model: nvidia/nemotron-3.5-super-vl:free
- Completed: 2026-11-21 00:15

---

# SunshineOS Admin-Tool Byte-Level Audit

**Context files:** `reports/USER_MIGRATION_MANDATE_2026-11-21.md`, `reports/OPENCLAW_ORDER_3_CONVERGENCE_ARCHITECTURE.md`  
**Governing invariants:** M-01, M-04, M-05, M-06, M-09, M-10  
**Target distros:** Obarun, Windows 11, EndeavourOS, GarudaOS, Artix, Arch (2015), Arch (2026), CachyOS, Omarchy, SteamOS

---

## 1. Audit scope matrix

| Distro | Package transaction wrapper | Snapshot manager | Boot repair helper | Keyring maintainer |
|--------|----------------------------|------------------|--------------------|--------------------|
| Arch (2015 / 2026) | `pacman` / libalpm | `snapper`, `timeshift` (community) | `grub-install`, `mkinitcpio`, `arch-chroot` | `pacman-key` |
| Artix | `pacman` / libalpm | `snapper` | `grub-install`, `mkinitcpio`, runit/s6 service repair | `pacman-key` |
| Obarun | `pacman` / libalpm | s6 service state snapshots | `grub-install`, `s6-rc` | `pacman-key` |
| EndeavourOS | `pacman` / libalpm | `timeshift` | `grub-install`, EndeavourOS welcome/repair routines | `pacman-key` |
| GarudaOS | `garuda-toolbox` (pacman wrapper) | `snapper`, `btrfs-assistant` | `garuda-boot-options`, `grub-install` | `pacman-key`, `garuda-keyring` |
| CachyOS | `cachy-tools` / `pacman` | `snapper` | `grub-install`, Cachy kernel hooks | `pacman-key` |
| Omarchy | `pacman` / libalpm | (dotfile/git snapshots) | `grub-install` | `pacman-key` |
| SteamOS | `pacman` (steamos variant) | btrfs read-only snapshots (`steamos-readonly`) | SteamOS recovery / `btrfs` rollback | `steamos-keyring` |
| Windows 11 | DISM / Component Store (WinSxS) | System Restore / VSS | `BCDboot`, `bcdedit`, WinRE | Windows Update trust roots / `certutil` |

---

## 2. Audit record schema

Each finding must be committed as a separate Markdown file on the **development branch**:

```
evidence/distro-audit/<distro>/<category>/<tool>.md
```

Example: `evidence/distro-audit/garudaos/package/garuda-toolbox.md`

**Required fields per record:**

| Field | Content |
|-------|---------|
| `tool` | Binary / package name |
| `distro` | Source distro |
| `category` | `package` \| `snapshot` \| `boot` \| `keyring` |
| `function_signature` | Exact C function prototype or shell function definition (byte-level, from source or `nm -D` / `readelf -s`) |
| `error_handling` | Exit codes, `errno`, `ALPM_ERR_*`, GnuPG return codes, stderr strings, log paths, rollback behavior on failure |
| `verdict` | `COPY` \| `ADAPT` \| `AVOID` |
| `rationale` | Invariant IDs (M-01…M-10) that justify the verdict |
| `source_path` | Path in `evidence/` where the binary/source was inspected |
| `sunshineos_target` | Proposed SunshineOS component or path (e.g. `evolution-engine/executor/alpm-adapter.c`) |

---

## 3. Known signatures and error paths to verify (do not trust from memory—extract from `evidence/`)

### Package transaction wrappers

**Arch family — `pacman` / libalpm**
- Functions to extract: `alpm_trans_init`, `alpm_trans_add`, `alpm_trans_remove`, `alpm_trans_upgrade`, `alpm_trans_commit`, `alpm_trans_release`
- Error codes to capture: `ALPM_ERR_NONE`, `ALPM_ERR_TRANSACTION_INIT_FAILED`, `ALPM_ERR_DUPLICATE_PKG`, `ALPM_ERR_CONFLICTING_FILE`, `ALPM_ERR_INVALID_DEP`, `ALPM_ERR_TRANSACTION_FAILED`
- **Copy:** transaction staging, progress callbacks, explicit rollback on `ALPM_ERR_TRANSACTION_FAILED`, separation of download and install phases.
- **Avoid:** non-atomic partial upgrades without explicit user opt-in; silent dependency resolution that mutates the system before user approval.

**Garuda — `garuda-toolbox`**
- Bash menu system wrapping `pacman`, `snapper`, `btrfs-assistant`.
- Error handling to capture: `dialog`/`whiptail` return codes, root-UID check, dependency presence checks before menu activation.
- **Copy:** categorized maintenance menu, one-click repair categories, clear pre-flight checks.
- **Avoid:** Garuda branding, monolithic script without modular SunshineOS boundaries, no staging journal.

**Windows 11 — DISM / SFC**
- Commands: `DISM /Online /Cleanup-Image /RestoreHealth`, `sfc /scannow`, `DISM /Online /Cleanup-Image /StartComponentCleanup`
- Error handling to capture: CBS log at `%WINDIR%\Logs\CBS\CBS.log`, exit codes, `/Source` fallback for corrupted store, offline repair via `dism /image:`.
- **Copy:** component-store corruption detection, source-aware restoration, offline repair mode.
- **Avoid:** opaque binary blobs, no user-visible plan before mutation, no rollback journal, silent replacement of system binaries.

### Snapshot managers

**Snapper (Arch/Garuda/Cachy/Artix/Obarun)**
- Extract: pre/post snapshot DBus API, config file parsing (`/etc/snapper/configs/*`), `snapper create --type pre/post`.
- Error handling: failed snapshot on non-btrfs/subvolume, missing `.snapshots` directory, cleanup algorithm failures.
- **Copy:** pre/post atomic pairing, timeline cleanup, mount-point isolation.
- **Avoid:** snapshots that include `/home` or user data by default (violates M-10).

**SteamOS btrfs read-only snapshots**
- Extract: `steamos-readonly` rollback mechanism, bootloader entry selection for snapshot boot.
- Error handling: failed rollback when default subvolume is corrupt, read-only remount failures.
- **Copy:** bootloader-aware snapshot selection, immutable root with rollback at boot menu.
- **Avoid:** tying rollback to a single vendor partition layout without abstraction.

### Boot repair helpers

**`grub-install` / `grub-mkimage` (all Linux distros)**
- Extract: `--target`, `--boot-directory`, `--efi-directory`, `--removable`, probe modules.
- Error handling: exit 1 on missing EFI system partition, probe failure on software RAID, missing `grub.cfg` fallback.
- **Copy:** staged bootloader install, `--removable` fallback, backup of existing boot entries before overwrite.
- **Avoid:** overwriting boot sector without backup, no validation that the new image boots before switching default entry.

**`mkinitcpio` (Arch/Artix/Obarun)**
- Extract: hook-based `build()`, `run_earlyhook()`, `run_hook()`, `run_latehook()`, `die()`.
- Error handling: missing module abort, missing firmware abort, `set -e` propagation.
- **Copy:** modular hook system, deterministic image generation, explicit `MODULES`/`BINARIES`/`FILES` declarations.
- **Avoid:** silent initramfs regeneration without bootloader config validation afterward.

**Windows 11 — `BCDboot` / `bcdedit` / WinRE**
- Extract: `bcdboot C:\Windows /s C: /f ALL`, `bcdedit /set {default} ...`, WinRE `reagentc /enable`.
- Error handling: missing system partition, BCD store corruption, inaccessible boot device.
- **Copy:** separate system partition from OS partition, boot configuration store abstraction, recovery environment isolation.
- **Avoid:** undocumented binary store formats, no export/import of BCD before mutation.

### Keyring maintainers

**`pacman-key` (Arch family)**
- Extract: `pacman_key_init`, `pacman_key_populate`, `pacman_key_refresh`, `pacman_key_delete`.
- Error handling: GnuPG exit codes, missing keyring directory abort, trustdb rebuild failure, keyserver unreachable.
- **Copy:** separate keyring from package transaction, explicit trust verification, local keyring population before package install.
- **Avoid:** silent key import without user confirmation, keyring updates bundled inside package transactions without isolation.

**Windows trust roots**
- Extract: certificate store manipulation via `certutil`, Windows Update root trust propagation.
- Error handling: revocation check failure, untrusted root blocking install.
- **Copy:** separate trust store from package/component store, explicit revocation checking.
- **Avoid:** automatic trust of vendor-signed binaries without user-administered policy.

---

## 4. Copy vs Avoid rules (tied to invariants)

| Invariant | Copy pattern | Avoid pattern |
|-----------|--------------|---------------|
| **M-01** Target-state driven | Resolve target state before any transaction; planner computes delta from actual inventory | Sequential replay of release history |
| **M-04** Authoritative installation | Query actual filesystem, `/var/lib/pacman/local`, bootloader state | Trusting `/etc/os-release` or release number alone |
| **M-05** Staged whenever possible | Prepare in staging root / snapshot, validate, then atomic switch | In-place mutation without dry-run or validation |
| **M-06** Recoverable | Compensating transaction, journal, snapshot before every operation | Non-recoverable `rm -rf`, format, or bootloader overwrite |
| **M-09** Repeatable | Idempotent discovery and planning; re-run after interruption produces same plan | Duplication of packages/services on re-run |
| **M-10** User data separate | OS reconstruction does not migrate `/home` or user dotfiles blindly | Blind migration of all old files during OS rebuild |

---

## 5. Required publication paths

Agents must publish audit records to the **development branch**:

- `evidence/distro-audit/<distro>/package/<tool>.md`
- `evidence/distro-audit/<distro>/snapshot/<tool>.md`
- `evidence/distro-audit/<distro>/boot/<tool>.md`
- `evidence/distro-audit/<distro>/keyring/<tool>.md`
- Aggregated verdicts: `evolution-engine/migration/tool-catalog.md`
- Engine integration: `evolution-engine/executor/`, `evolution-engine/validator/`

---

## 6. Immediate tasks for subordinate agents

1. **Stage sources:** Download distro source packages / ISOs into `evidence/distro-source/<distro>/`.
2. **Extract byte-level signatures:** Run `nm -D`, `readelf -s`, `objdump -T` on binaries; extract shell function definitions from installed scripts.
3. **Inject failures:** Test each tool under missing disk, missing EFI partition, missing keyring, and corrupt snapshot conditions; record exact stderr and exit codes.
4. **Write audit records:** One file per tool at the paths in Section 4.
5. **Aggregate:** Merge all verdicts into `evolution-engine/migration/tool-catalog.md` with invariant traceability.
6. **Feed engine:** Transfer approved patterns into `evolution-engine/` executor, planner, and validator components.

**Stop condition:** No agent stops until every tool in the matrix above has a completed audit record and the catalog is published to the development branch.
