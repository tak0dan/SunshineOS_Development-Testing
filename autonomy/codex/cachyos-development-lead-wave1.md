# CachyOS development leadership — Wave 1

## Scope and source basis

Reviewed the user migration mandate and canonical decisions, then grounded this increment in the locally cached CachyOS source at `/home/tak_0/.local/state/sunshine-orchestrator/iso/repos/cachyos-tools` (outside the SunshineOS repository). The cached ISO is `/home/tak_0/.local/state/sunshine-orchestrator/iso/cachyos.iso`; its manifest is `.../iso/manifest.json`. No claims below depend on unverified inherited CachyOS summaries.

## Catalogue

| Source path | Observed behavior | SunshineOS treatment |
|---|---|---|
| `cachyos-hooks/PKGBUILD` | `cachyos-hooks` installs libalpm hooks for branding, Plymouth initramfs, reboot-required, LSB and os-release work; package metadata pins source and SHA-512. | Adopt the useful pattern of package-scoped, declarative ALPM triggers and explicit artifact provenance. Do not copy distro branding or assume its hooks are suitable migration transitions. |
| `systemd-boot-manager/sdboot-kernel-update.hook` | Post-transaction hook watches kernel image paths and invokes `/usr/bin/sdboot-manage autogen`. | A package transaction trigger is a useful integration point. SunshineOS should journal, validate generated boot artifacts, and fail the migration gate when required generation fails (AD-08, AD-11; M-05/M-06). |
| `systemd-boot-manager/sdboot-manage` | UKI generation contains `mkinitcpio -p "${kernel}" || true`; subsequent flow checks for an empty `EFI/Linux` directory and calls `die`. Regular-entry generation checks image file sizes and `lsinitcpio`, but some install calls also suppress errors. | Do not treat a zero exit from the wrapper as proof of success. Require per-kernel artifact validation and preserve failure details in the migration journal. This is the inspiration for the auditor below, not a claim that all CachyOS paths lack validation. |
| `evolution-engine/src/discovery/kernel_boot.py` | Existing discovery already distinguishes installed bootloader signals from evidence of the active firmware entry and records kernel/initramfs observations. | Extend only with a tested capability/validation layer when integrated; avoid a duplicate discovery model or decisions based on distro/release name (AD-04/05, M-04). |
| `evolution-engine/src/evolution/updater.py` | The shipped updater checkpoints, runs hooks, and restores on failure. | New boot artifact checks belong at staged validation boundaries, not in unjournaled best-effort package scripts (AD-11, M-05/M-06). |

The prior notes in `autonomy/results/sub-research-hooks-01.md` assert that particular CachyOS hooks mutate kernel state and should be rejected. This wave verified the cached repository's `cachyos-hooks/PKGBUILD` but did not find evidence there for those specific hook names or claims; consider those statements unverified until matched to exact source files.

## Implementation

Added `autonomy/codex/cachyos_boot_hook_audit.py`, a static review helper that flags a suppressed `mkinitcpio`, `dracut`, or `kernel-install` command when no artifact validation appears within a bounded line window. It never invokes inspected content. This is intentionally a heuristic and is not a substitute for shell parsing or migration-time validation.

Regression test IDs in `autonomy/codex/test_cachyos_boot_hook_audit.py`:

- `AUDIT_001`: suppressed generation without validation is flagged.
- `AUDIT_002`: nearby file validation clears the finding.
- `AUDIT_003`: fail-fast generation is not flagged.
- `AUDIT_004`: nearby empty-UKI fatal check is recognized.

## Verification evidence

Command: `python3 -m unittest autonomy/codex/test_cachyos_boot_hook_audit.py -v`

Result: 4 tests passed. Full output: `autonomy/codex/cachyos-wave1-test.log`.

## Follow-up

For the production evolution engine, connect boot artifact verification to an explicit staged operation with per-kernel expected outputs, journal evidence, and rollback coverage. Qualify EFI/systemd-boot and GRUB paths separately, including missing ESP, read-only ESP, failed initramfs generation, and stale UKI scenarios before claiming support.
