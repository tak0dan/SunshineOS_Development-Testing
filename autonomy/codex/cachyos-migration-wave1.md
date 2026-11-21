# CachyOS migration engine survey — Wave 1 deepening

## Survey scope and provenance

Inspected the cached `CachyOS/CachyOS-PKGBUILDS` checkout at commit
`97a55536e5f756d22199f043de4aa1a0d8eebc8a` in
`/home/tak_0/.local/state/sunshine-orchestrator/iso/repos/cachyos-tools`.
The checkout is outside this repository; no CachyOS command or hook was run.
The architectural mapping uses the migration mandate's M-04 (installation
state is authoritative), M-05 (stage changes), M-06 (recoverability), and
M-08 (qualify support), plus `reports/ARCHITECTURE_DECISIONS.md` AD-05,
AD-08, and AD-11.

| Exact CachyOS checkout path | Verified from cached source | Migration implication |
|---|---|---|
| `cachyos-kernel-manager/PKGBUILD` | Package `cachyos-kernel-manager` version 1.19.0; source uses signed tag `v${pkgver}`, declares a PGP signer, and applies `fix-installed-db.patch`. Build exports LLVM/Clang and Rust optimization flags. | Kernel-manager presence alone does not prove which kernel is installed or bootable. Preserve observed kernel package identities; do not equate manager presence with migration capability. |
| `cachyos-kernel-manager/fix-installed-db.patch` | Local patch is shipped as a separate source and applied in `prepare()`. | Cache records a local compatibility delta. A migration must not assume upstream and packaged behavior are identical. |
| `cachy-update/PKGBUILD` | Declares `cachy-update` 4.4.7; pins source to commit `22c569d44b5cf87becc4b60dd2b9a8e9ec34ea23` with SHA-256; check phase runs `make test`; package installs the update notifier/applier. | Treat update-helper presence as a UI/workflow signal only. This recipe does not prove the behavior of the upstream payload, nor that a user's updates are fully applied. |
| `systemd-boot-manager/sdboot-kernel-update.hook` | Watches kernel image paths for Install/Upgrade and runs `sdboot-manage autogen` PostTransaction. | Artifact-triggered post-transaction work is useful, but staged generation and boot validation remain required. Earlier hook contract and generation audit are recorded in `cachyos-architecture-enforcement-wave1.md`. |
| `systemd-boot-manager/sdboot-kernel-remove.hook` | Watches `boot/linux*.kver` for Remove and invokes `sdboot-manage remove` PostTransaction. | Removal is an independent transition; do not infer that it is safe for the active kernel or recoverable from hook metadata. |
| `systemd-boot-manager/sdboot-manage` | Contains UKI and regular-entry branches; it suppresses some regeneration failures with `|| true`, with later artifact checks in the observed paths. | Process success is insufficient evidence of a good boot artifact. Require explicit staged artifact checks and boot validation before retiring fallback kernels. |
| `systemd-boot-manager/PKGBUILD` | Pins local source files using SHA-512 and installs hook files into `/usr/share/libalpm/hooks/`. | Preserve recipe-to-hook provenance and hashes as source evidence; installation does not establish runtime hook success. |

The package cache does not include the upstream `cachy-update` or kernel-manager
payload source trees. Behavior claims above are limited to the checked-in
recipes, patch, and boot-manager files. No migration qualification is inferred
from package metadata.

## Code delivered

Added `cachyos_kernel_migration.py`, a pure review policy over observed package
identities. It identifies CachyOS kernel variants, requires an explicit target
mapping, requires an installed fallback or retained source kernel before
replacement planning, and blocks retirement of the active kernel pending target
boot validation. It emits review blockers and never executes package operations
or authorizes removal. The literal package identities and non-mutating contract
implement the inventory-authority and staged/recoverable transition direction
of M-04/M-05/M-06 and AD-05/AD-11.

### Regression tests

| Test ID | Contract |
|---|---|
| `CKM_001` | CachyOS kernel variant without explicit target mapping blocks. |
| `CKM_002` | Replacing the only installed kernel without an installed fallback blocks. |
| `CKM_003` | Explicit mapping with installed fallback and non-retiring active fallback is reviewable. |
| `CKM_004` | Active CachyOS kernel retirement remains blocked pending boot validation. |
| `CKM_005` | Existing non-Cachy kernel is preserved when no replacement is requested. |
| `CKM_006` | Blank target package identity fails closed. |

Command: `python3 -m unittest autonomy.codex.test_cachyos_kernel_migration -v`

Result: 6 tests passed. Full output: `autonomy/codex/cachyos-migration-wave1-test.log`.

## Files written

- `autonomy/codex/cachyos_kernel_migration.py`
- `autonomy/codex/test_cachyos_kernel_migration.py`
- `autonomy/codex/cachyos-migration-wave1.md`
- `autonomy/codex/cachyos-migration-wave1-test.log`

The engine implementation remains a policy component for planning integration;
production migration support still requires qualified inventory mapping,
staged initramfs/boot artifact validation, and successful target boot evidence.
