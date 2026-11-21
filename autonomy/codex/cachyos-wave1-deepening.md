# CachyOS regression deepening — Wave 1

## Scope and architecture grounding

Read `reports/USER_MIGRATION_MANDATE_2026-11-21.md` and `reports/ARCHITECTURE_DECISIONS.md`. This increment supports the mandate's stability and qualification priorities and AD-04/05 (capability and observed-state decisions), AD-08/09 (controlled execution boundaries), AD-11 (checkpoint and restore), and AD-14 (qualified support). It only audits text; it does not run CachyOS hooks or modify the external source checkout.

## Source catalogue

Cached source root: `/home/tak_0/.local/state/sunshine-orchestrator/iso/repos/cachyos-tools`, commit `97a5553`.

| Exact source file | Directly verified behavior | SunshineOS decision / evidence limit |
|---|---|---|
| `/home/tak_0/.local/state/sunshine-orchestrator/iso/repos/cachyos-tools/cachyos-hooks/PKGBUILD` | Package recipe pins version `2026.10.23` and a SHA-512 for a Git tag. Its `package()` function lists five hook installs, two helper installs, and `update-initramfs`. | Keep artifact provenance and transaction-scoped hooks as patterns. This cached package checkout contains the recipe but not the upstream payload files it names; actual behavior of those hooks is not independently established here. |
| `/home/tak_0/.local/state/sunshine-orchestrator/iso/repos/cachyos-tools/systemd-boot-manager/sdboot-kernel-update.hook` | Path trigger for kernel image Install/Upgrade; runs `sdboot-manage autogen` after the transaction. | Useful trigger pattern. A SunshineOS transition still needs journaled execution and staged validation (AD-11, M-05/M-06). |
| `/home/tak_0/.local/state/sunshine-orchestrator/iso/repos/cachyos-tools/systemd-boot-manager/sdboot-kernel-remove.hook` | Separate Path trigger for kernel-file Remove; runs `sdboot-manage remove` after the transaction. | Treat removal as a separate operation and protect the active boot path using observed inventory; the hook alone does not establish that safety. |
| `/home/tak_0/.local/state/sunshine-orchestrator/iso/repos/cachyos-tools/systemd-boot-manager/sdboot-systemd-update.hook` | Package trigger for systemd Upgrade; runs `sdboot-manage autoupdate` after the transaction. | Keep systemd update and kernel image events distinct. Do not infer active boot state from package presence. |
| `/home/tak_0/.local/state/sunshine-orchestrator/iso/repos/cachyos-tools/systemd-boot-manager/sdboot-manage` | `set -euo pipefail` is enabled (line 4); `mkinitcpio -p "${kernel}" || true` suppresses its error (line 259), then the UKI branch fails if `EFI/Linux` is empty (lines 272–273). Regular-entry generation checks nonempty kernel/initramfs artifacts and `lsinitcpio` (lines 323–331), but the regeneration pipeline at line 324 suppresses errors. | Wrapper success cannot stand alone as proof of successful generation. Verify every expected per-kernel artifact at a staged boundary and retain failure evidence. The static audit only flags suppression lacking a recognized nearby validation pattern; it is not a shell parser or proof of runtime safety. |

The cached checkout does not provide enough evidence to validate previous `autonomy/results/sub-research-hooks-01.md` claims about specific CachyOS hook names or scheduler/microcode mutations. Those claims remain unverified and are not used here.

## Code change

Updated `autonomy/codex/cachyos_boot_hook_audit.py`: expanded its default validation window from 12 to 16 lines. The real UKI empty-directory gate is 13 lines after the suppressed generator call, so the old default reported a false positive despite the later fatal gate. The window remains bounded to avoid accepting arbitrarily distant checks.

Added cases in `autonomy/codex/test_cachyos_boot_hook_audit.py`:

- `AUDIT_005`: reproduces the cached CachyOS spacing (generator at line 259; empty-UKI gate at line 272) and expects no finding.
- `AUDIT_006`: verifies a validation beyond the configured default window does not clear the finding.

Existing IDs remain `AUDIT_001`–`AUDIT_004`; ALPM metadata cases remain `HOOK_001`–`HOOK_004` in `autonomy/codex/test_cachyos_alpm_hook.py`.

## Verification evidence

Command:

```sh
python3 -m unittest autonomy/codex/test_cachyos_boot_hook_audit.py autonomy/codex/test_cachyos_alpm_hook.py -v
```

Result: 10 tests passed. Full output: `autonomy/codex/cachyos-wave1-deepening-test.log`.

## Remaining qualification

These static checks do not establish live hook ordering, bootability, command safety, ESP availability, or rollback behavior. Before adopting a boot transition, qualify missing/read-only ESP, generation failure, stale UKI, removal of the active kernel, and GRUB separately, with checkpoint and restore evidence.
