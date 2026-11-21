# CachyOS repair tool survey and code change — Wave 1

## Source catalogue

Cached research checkout: `/home/tak_0/.local/state/sunshine-orchestrator/iso/repos/cachyos-tools` (CachyOS-PKGBUILDS, commit `97a55536e5f756d22199f043de4aa1a0d8eebc8a`). The following files were inspected directly:

| Exact source path | Verified behavior | SunshineOS repair decision |
|---|---|---|
| `systemd-boot-manager/sdboot-kernel-update.hook` | Path triggers cover kernel images on Install/Upgrade and invoke `sdboot-manage autogen` PostTransaction. | Keep this artifact-trigger pattern; trigger success is not proof generated images are valid. |
| `systemd-boot-manager/sdboot-manage` lines 258–260 | `mkinitcpio -p` failure is ignored with `|| true` in the UKI path. | Never use wrapper exit status alone as health evidence. |
| `systemd-boot-manager/sdboot-manage` lines 272–274 | The UKI path fails if `EFI/Linux` is empty, but only checks directory population. | Add expected-artifact inspection; directory non-emptiness alone does not establish completeness. |
| `systemd-boot-manager/sdboot-manage` lines 323–331 | The regular-entry path suppresses the generator failure, then separately checks nonempty kernel/initramfs and runs `lsinitcpio`; failure prints and continues. | Adopt explicit per-artifact postcondition checks. The checker reports missing/empty evidence and blocks escaped paths; validation still needs a qualified image parser/runtime boot check. |

## Architecture fit

The mandate prioritizes repair and fail-closed verification. This change supports AD-05 (observed installation is authoritative), AD-11 (checkpoint and restore on failure), and AD-14 (qualification is explicit). It is assessment-only: it does not run generation commands or modify boot files. Any future executor must stage regeneration, checkpoint the prior boot state, and validate all requested artifacts before activation.

## Implementation

Added `evolution-engine/src/evolution/tools/boot_artifact_repair.py::assess_boot_artifacts`. It accepts explicit root-relative expected paths, rejects empty requests and traversal, refuses symlinks escaping the observed root, and distinguishes present, missing, empty, and unsafe artifacts. No mutation commands are emitted.

Regression cases in `evolution-engine/tests/test_boot_artifact_repair.py`:

- `T_CACHYOS_BOOT_REPAIR_001`: all expected artifacts are required.
- `T_CACHYOS_BOOT_REPAIR_002`: empty generated image is degraded.
- `T_CACHYOS_BOOT_REPAIR_003`: external symlink fails closed.
- `T_CACHYOS_BOOT_REPAIR_004`: traversal and empty request rejected.

## Verification

Command: `python3 -m unittest tests/test_boot_artifact_repair.py -v` (from `evolution-engine/`)

Result: **4 tests passed**. Full output: `autonomy/codex/cachyos-repair-wave1-test.log`.
