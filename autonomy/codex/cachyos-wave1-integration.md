# CachyOS integration survey — Wave 1

## Scope and grounding

Reviewed `reports/USER_MIGRATION_MANDATE_2026-11-21.md` and `reports/ARCHITECTURE_DECISIONS.md` (AD-04/05 capability-based inventory; AD-08 signed and journaled adaptors; AD-09 argv-only execution; AD-11 checkpoint and restore on failure; AD-14 qualified support). The CachyOS source cited below is the local cached checkout at `/home/tak_0/.local/state/sunshine-orchestrator/iso/repos/cachyos-tools`. This is a source survey; the checker reads metadata and does not invoke any inspected hook.

## Catalogue and integration decisions

| Exact source path | Observed behavior | SunshineOS integration decision |
|---|---|---|
| `/home/tak_0/.local/state/sunshine-orchestrator/iso/repos/cachyos-tools/cachyos-hooks/PKGBUILD` | Installs five libalpm hooks under `/usr/share/libalpm/hooks`, helper scripts under `/usr/share/libalpm/scripts`, and `update-initramfs` under `/usr/bin`; source is pinned to tag `2026.10.23` with a SHA-512 source checksum. | Retain declarative, package-scoped transaction triggers as an integration pattern. Preserve source digest and provenance when importing any artifact; never import CachyOS branding as SunshineOS identity. |
| `/home/tak_0/.local/state/sunshine-orchestrator/iso/repos/cachyos-tools/systemd-boot-manager/sdboot-kernel-update.hook` | Path trigger on kernel images for Install and Upgrade; runs `/usr/bin/sdboot-manage autogen` after transaction. | Accept as a useful trigger shape. SunshineOS boot work must be journaled and validated after execution, with checkpoint/restore under AD-11. |
| `/home/tak_0/.local/state/sunshine-orchestrator/iso/repos/cachyos-tools/systemd-boot-manager/sdboot-kernel-remove.hook` | Separate path hook for kernel removal (reviewed in cached checkout). | Model removal separately from generation/update; require inventory-derived expected entries so removal cannot silently delete the active boot path. |
| `/home/tak_0/.local/state/sunshine-orchestrator/iso/repos/cachyos-tools/systemd-boot-manager/sdboot-systemd-update.hook` | Hook for systemd package updates (reviewed in cached checkout). | Treat systemd and kernel triggers as distinct transition causes; do not infer installed/active boot state from package names. |
| `/home/tak_0/.local/state/sunshine-orchestrator/iso/repos/cachyos-tools/systemd-boot-manager/sdboot-manage` | UKI branch suppresses `mkinitcpio -p "${kernel}"` errors at line 259, then checks for an empty `${ESP}/EFI/Linux` and calls `die` at lines 272–273. Regular-entry generation calls `lsinitcpio` in validation at line 329; other install operations suppress failures. | A wrapper’s exit status alone is insufficient. Keep per-kernel expected output checks and journal the failed command/result; the existing static helper `cachyos_boot_hook_audit.py` flags the suppression heuristic for human review. |
| `evolution-engine/src/discovery/kernel_boot.py` | Existing discovery distinguishes installed bootloader signals from evidence of the active firmware entry and observes kernel/initramfs state. | Extend the existing capability discovery boundary rather than adding CachyOS-specific migration branches (AD-04/05). |
| `evolution-engine/src/evolution/updater.py::EvolutionUpdater.upgrade` | Existing migration boundary checkpoints and restores on failure. | Boot artifact qualification belongs at staged validation boundaries, not in best-effort package hooks (AD-11, M-05/M-06). |

The previous research note `autonomy/results/sub-research-hooks-01.md` includes claims about particular CachyOS hook names and kernel mutations. This review did not verify those claims from the exact named source files; they remain unverified and are not used to justify the code here.

## Delivered code

Added `autonomy/codex/cachyos_alpm_hook.py::audit_alpm_hook`. It validates ALPM hook section/key structure, required trigger/action metadata, legal operation/timing values, and absolute `Exec` paths. Repeated `Operation` and `Target` entries are accepted. Unknown or malformed metadata creates findings. The checker parses text only and never runs hook commands. It is a review aid, not a replacement for libalpm's parser or runtime validation.

Regression tests in `autonomy/codex/test_cachyos_alpm_hook.py`:

- `HOOK_001`: CachyOS kernel update hook contract accepted.
- `HOOK_002`: missing target fails closed.
- `HOOK_003`: unknown key rejected.
- `HOOK_004`: relative executable rejected.

Existing static boot generation tests `AUDIT_001`–`AUDIT_004` were rerun as the adjacent regression set.

## Verification

Command: `python3 -m unittest autonomy/codex/test_cachyos_alpm_hook.py autonomy/codex/test_cachyos_boot_hook_audit.py -v`

Result: 8 tests passed. Full output: `autonomy/codex/cachyos-wave1-integration-test.log`.

## Remaining qualification

The metadata checker does not prove command safety, hook ordering, artifact correctness, or behavior on a live system. Production adoption requires signed/journaled execution and qualified EFI/systemd-boot plus GRUB cases, including missing/read-only ESP, failed generation, stale UKI, and kernel removal, with rollback evidence.
