# CachyOS architecture enforcement — Wave 1

## Survey and source catalogue

Inspected the cached `CachyOS/CachyOS-PKGBUILDS` checkout at commit `97a55536e5f756d22199f043de4aa1a0d8eebc8a` under `/home/tak_0/.local/state/sunshine-orchestrator/iso/repos/cachyos-tools` (outside the SunshineOS repository). This survey records source behavior; it does not execute any CachyOS hook.

| Exact source path | Verified behavior | SunshineOS architecture enforcement |
|---|---|---|
| `systemd-boot-manager/sdboot-kernel-update.hook` | Path triggers watch `usr/lib/modules/*/vmlinuz` and `boot/vmlinuz*` for Install and Upgrade. `sdboot-manage autogen` runs PostTransaction. | Accept as a useful artifact-trigger pattern. SunshineOS gate checks path scope and post-transaction timing; it still needs staged artifact verification (AD-07, AD-08, AD-11). |
| `systemd-boot-manager/sdboot-kernel-remove.hook` | Path trigger watches `boot/linux*.kver` for Remove; invokes `sdboot-manage remove` PostTransaction. | Removal is a distinct lifecycle event. A valid hook declaration alone cannot establish that the selected kernel is inactive or that cleanup is recoverable (AD-05, AD-11). |
| `systemd-boot-manager/sdboot-systemd-update.hook` | Package trigger watches Upgrade of `systemd`; invokes `sdboot-manage autoupdate` PostTransaction. | Keep systemd package updates distinct from kernel artifact transitions. The new boot-transition policy intentionally rejects package-only triggers for boot artifact work. |
| `systemd-boot-manager/PKGBUILD` | Pins five local source files with SHA-512 values and installs three ALPM hooks under `/usr/share/libalpm/hooks/`. | Preserve explicit source provenance and package-to-hook installation mapping when adopting a pattern. |
| `systemd-boot-manager/sdboot-manage` | Uses `set -euo pipefail`; suppresses selected initramfs/regeneration failures with `|| true`. The UKI branch later rejects an empty `EFI/Linux`; regular-entry flow checks kernel/initramfs artifacts and `lsinitcpio`, while the regeneration pipeline also suppresses errors. | Do not equate wrapper exit status with successful boot artifact generation. Existing static audit in `cachyos_boot_hook_audit.py` flags suppressed generation without nearby recognized validation; runtime qualification remains required. |
| `cachyos-hooks/PKGBUILD` | Pins the upstream `cachyos-hooks` tag with SHA-512 and lists five hook files plus three helper installs. Those payload files are absent from this package recipe checkout. | Record declared packaging inputs only; payload behavior is unverified in this cache and is not used to infer runtime semantics. |

Architecture mapping is grounded in `reports/ARCHITECTURE_DECISIONS.md`: AD-05 observed installation is authoritative, AD-07 declarative scheme data owns hooks, AD-08 adaptors are controlled and rechecked, AD-09 invocation boundaries, and AD-11 checkpoint/restore on failure. The mandate prioritizes fail-closed verification and 20-year support; hook metadata checks are a small input control, not a migration guarantee.

## Change

Updated `autonomy/codex/cachyos_alpm_hook.py`:

- Removed an accidental non-schema trigger key allowance.
- Reject empty metadata values (`HOOK_VALUE_EMPTY`).
- Added `audit_boot_transition_hook`, requiring path triggers and PostTransaction timing for boot artifact transitions. It does not execute commands or prove their effects.

Added tests `HOOK_005`–`HOOK_009` in `autonomy/codex/test_cachyos_alpm_hook.py`: current kernel update shape passes; empty values, package-only boot triggers, and pre-transaction boot work are rejected; a path-based post-transaction removal shape passes.

## Verification evidence

Command: `python3 -m unittest autonomy/codex/test_cachyos_alpm_hook.py autonomy/codex/test_cachyos_boot_hook_audit.py -v`

Result: 15 tests passed (9 hook policy tests and 6 boot-generation audit tests). Full log: `autonomy/codex/cachyos-architecture-enforcement-test.log`.

## Limits

Static checks cannot establish ALPM ordering in a live transaction, hook command behavior, active-kernel safety, artifact correctness, bootability, or rollback. These require capability-based inventory, checkpoints, staged validation, and qualified EFI/systemd-boot plus GRUB scenarios before production adoption.
