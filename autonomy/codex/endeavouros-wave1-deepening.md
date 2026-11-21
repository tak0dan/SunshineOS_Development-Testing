# EndeavourOS migration deepening — Wave 1

Date: 2026-11-21  
Scope: local EndeavourOS ISO survey, repository path catalogue, and source qualification in the SunshineOS evolution engine.

## Findings grounded in repository and ISO evidence

The local source image is `/home/tak_0/.local/state/sunshine-orchestrator/iso/endeavouros.iso` (3.7 GiB; SHA-256 `0487f46fe29e0ab2ed153ba874568cc542a0507fb6029f29ad552b36ba447393`). Read-only `xorriso` inspection reports volume ID `EOS_202608`, publisher `ENDEAVOUROS <https://endeavouros.com>`, preparer `PREPARED BY MKARCHISO`, and image creation time 2026-08-15 14:13:08 UTC. Its outer ISO tree exposes:

| Exact ISO path | Observed role | Migration relevance |
|---|---|---|
| `/arch/version` | Live image version marker | Candidate inventory input; do not use alone as source-state authority. |
| `/arch/pkglist.x86_64.txt` | 23,024-byte x86_64 live image package list | Package baseline evidence, not installed-system inventory. SHA-256 of extracted copy: `d2f0036ace8a3c83a71d6221fe84884ca0d1de1c0e5269d9f06b137924179a22`. |
| `/arch/x86_64/airootfs.sfs` | 3,352,948,736-byte compressed live root filesystem | Contains the live environment; not unpacked or inspected in this wave. |
| `/arch/x86_64/airootfs.sha512` | Live root integrity metadata | Image integrity evidence; does not itself establish a trusted signer. |
| `/boot/grub/` and `/loader/entries/` | GRUB and systemd-boot live-media boot entries | ISO boot configuration, not evidence of an installed user's bootloader. |
| `/boot/syslinux/` | Syslinux live-media boot configuration and modules | PXE/legacy media support inventory; not an installed target configuration. |
| `/EFI/BOOT/BOOTx64.EFI` and `/EFI/BOOT/BOOTIA32.EFI` | UEFI boot executables | Boot-media capability only. |

The image is identified as an ArchISO-built live/rescue medium. Its package list is a dated media snapshot. It does not prove installation defaults, installer transaction behavior, upgrade policy, package hooks, or installed-system configuration. Those require extraction/inspection of `airootfs.sfs` and installer artifacts in a subsequent wave. No claim is made here about EndeavourOS upstream source file paths.

## Repository catalogue (paths verified in this checkout)

| Repository path and symbol | Observed behavior | Relevance / treatment |
|---|---|---|
| `evolution-engine/src/discovery/system.py::_detect_distribution` | Parses `/etc/os-release`; preserves parsed fields, including `ID_LIKE`, in `system.os-release` observation evidence. | Retain provenance for derivative recognition. |
| `evolution-engine/src/discovery/packages.py::discover_packages` | Combines `pacman -Q`, `pacman -Qqdt`, and `pacman -Qqm`; treats foreign ownership conservatively and never equates all foreign packages with AUR. | Appropriate for EndeavourOS-derived sources; preserve unknown/foreign packages for review. |
| `evolution-engine/src/target/compatibility.py::classify_source` | Checks distribution lineage, architecture, init, pacman health, bootloader, storage and customizations before qualification. | Changed to permit EndeavourOS only with observed `ID_LIKE=arch`; it is classified conditional and still subject to foundation blockers. |
| `evolution-engine/tests/test_compatibility.py::CompatibilityTests` | Existing qualification regression suite. | Added `T-ENDEAVOUR-COMP-001` and `T-ENDEAVOUR-COMP-002`. |
| `evolution-engine/tests/test_discovery.py::DiscoveryTests` | Fixture-backed host discovery tests. | Added `T-ENDEAVOUR-DISC-001` for retaining `ID_LIKE` evidence. |
| `reports/ARCHITECTURE_DECISIONS.md` AD-04, AD-05, AD-14; M-04, M-08 | One capability-driven engine, observed installation authority, qualified support. | Compatibility change follows these decisions; the report was read only and not modified. |

## Change delivered

`evolution-engine/src/target/compatibility.py` now recognizes `endeavouros` as a candidate Arch-derived source only when the retained `system.os-release` evidence includes `ID_LIKE=arch`. It adds an explicit conditional-support warning and records the lineage evidence. The existing checks still reject unsupported architecture, non-systemd init, non-pacman package manager, unreadable/broken package database, and missing bootloader. Foreign/AUR package inventories remain conditional and preserved under the existing logic.

A missing `ID_LIKE=arch` signal blocks EndeavourOS classification. This prevents distribution branding alone from authorizing migration. The qualification change does not claim a complete EndeavourOS installation matrix; it is a narrowly scoped lineage gate.

## Regression tests and evidence

- `T-ENDEAVOUR-COMP-001`: EndeavourOS with observed Arch lineage is supported conditionally.
- `T-ENDEAVOUR-COMP-002`: EndeavourOS without observed Arch lineage is blocked.
- `T-ENDEAVOUR-DISC-001`: discovery retains `ID_LIKE=arch` as `system.os-release` evidence.
- Existing compatibility and discovery tests also ran in the same invocation.
- Result: `python3 -m unittest tests.test_compatibility tests.test_discovery` — 27 tests passed.
- Test log: `autonomy/codex/endeavouros-wave1-test.log`.
- ISO tree inspection: `xorriso -indev …/endeavouros.iso -find / -maxdepth 3 -type f -exec lsdl`.
- ISO metadata inspection: `xorriso -indev …/endeavouros.iso -pvd_info`.
- Package list was extracted to `/tmp/endeavouros-pkglist-wave1.txt`; it is outside the repository and is not a migration authority.
