# EndeavourOS migration survey and package ownership hardening — Wave 1

Date: 2026-11-21  
Scope: repository-backed survey, exact-path catalogue, and a fail-closed package inventory correction. This work builds on the existing EndeavourOS ISO and conditional-source survey; it does not claim real-host or installer qualification.

## Survey evidence

The prior read-only outer-tree inspection recorded the local image `/home/tak_0/.local/state/sunshine-orchestrator/iso/endeavouros.iso` as an ArchISO live/rescue image (`EOS_202608`, created 2026-08-15). Exact paths observed in that image include `/arch/version`, `/arch/pkglist.x86_64.txt`, `/arch/x86_64/airootfs.sfs`, `/arch/x86_64/airootfs.sha512`, `/boot/grub/`, `/loader/entries/`, `/boot/syslinux/`, `/EFI/BOOT/BOOTx64.EFI`, and `/EFI/BOOT/BOOTIA32.EFI`. The live package list and boot entries describe media, not an installed system. The compressed root and installer internals were not inspected; this survey makes no claim about EndeavourOS upgrade hooks, repository/keyring transitions, or installer behavior.

Evidence and previous catalogues: [`endeavouros-wave1-deepening.md`](endeavouros-wave1-deepening.md), [`endeavouros-wave1-deepening-audit.md`](endeavouros-wave1-deepening-audit.md), and [`endeavouros-wave1-architecture-enforcement.md`](endeavouros-wave1-architecture-enforcement.md).

## Exact repository path catalogue

| Path and symbol | Observed behavior | Migration treatment |
|---|---|---|
| `evolution-engine/src/discovery/system.py::_detect_distribution` | Reads `/etc/os-release` and retains fields such as `ID_LIKE` in the `system.os-release` observation. | Classification uses configured, observed lineage; distro naming alone does not qualify a source. |
| `evolution-engine/src/discovery/packages.py::discover_packages` | Queries `pacman -Q`, `pacman -Qqdt`, `pacman -Qqm`, `/etc/pacman.conf`, and pacman sync database presence; distinguishes official, foreign, uncertain and AUR candidates. | Now records completeness of all three package ownership queries. If any query fails, official membership is withheld and the inventory is LOW confidence. |
| `evolution-engine/src/target/compatibility.py::classify_source` | Requires corroborating Arch lineage for EndeavourOS, checks the package database and other system capabilities, and reports customizations conditionally. | Now blocks transformation when `packages.ownership-inventory` is absent, requiring successful rediscovery before planning/apply. |
| `evolution-engine/fixtures/endeavouros/etc/os-release` | Test fixture advertises `ID=endeavouros`, `ID_LIKE=arch`. | Simulation evidence only; not an installed-host snapshot. |
| `evolution-engine/src/fixtures.py::FIXTURE_NAMES`, `FixtureExecutor` | Supplies deterministic offline command responses and a state sandbox for fixture tests. | EndeavourOS uses the common discovery/planning/apply path and repeat-apply convergence check. |
| `evolution-engine/tests/source-matrix.toml` (`endeavouros` case) | Declares EndeavourOS conditional, with Btrfs and GRUB expectations. | Exercises conditional source compatibility and shared plan/apply convergence. |
| `evolution-engine/tests/test_source_matrix.py::test_endeavouros_source_matrix_stays_conditional`, `test_each_source_shape_has_expected_convergence_plan`, `test_every_source_shape_applies_and_is_idempotent` | Checks conditional classification, required/forbidden operations, preservation of foreign packages, successful fixture apply, and idempotent repeat apply. | Fixture-based integration coverage; not real-host qualification. |
| `evolution-engine/tests/test_compatibility.py::CompatibilityTests` | Exercises source lineage and capability blockers. | Adds `T-ENDEAVOUR-PKG-002` for blocking an incomplete ownership inventory. |
| `evolution-engine/tests/test_discovery.py::DiscoveryTests` | Exercises rooted discovery and injected command behavior. | Adds `T-ENDEAVOUR-PKG-001` for withholding official claims after `pacman -Qqm` failure. |

The change follows migration mandate M-04/M-08 and architecture decisions AD-04, AD-05, AD-14: observed state is authoritative and support must be qualified. The read-only context files are `reports/USER_MIGRATION_MANDATE_2026-11-21.md` and `reports/ARCHITECTURE_DECISIONS.md`; neither was modified.

## Code change

Previously, a failed foreign/orphan query was treated as an empty result. Packages returned by `pacman -Q` could consequently remain in the `packages.official` observation despite ownership uncertainty. `discover_packages` now emits `packages.ownership-inventory`, marked `FUNCTIONAL`/HIGH only when all three pacman inventory queries succeed. On partial failure it leaves the observed installed and foreign lists available for diagnosis, sets official membership to empty/LOW with an explicit withheld explanation, and marks the inventory `ABSENT`/LOW. `classify_source` makes that incomplete inventory a blocker.

The adjustment is conservative across Arch-derived sources and therefore applies to EndeavourOS without distro-specific package assumptions. Foreign/AUR packages remain preserved and are not translated into target package removal operations.

## Regression IDs and results

- `T-ENDEAVOUR-PKG-001`: a failed `pacman -Qqm` query produces LOW/ABSENT ownership inventory and does not allow an official-package claim.
- `T-ENDEAVOUR-PKG-002`: incomplete ownership inventory blocks source compatibility.
- Existing coverage also passed, including `T-ENDEAVOUR-COMP-001`–`004`, `T-ENDEAVOUR-DISC-001`, `T-ENDEAVOUR-MATRIX-001`, and source-matrix apply/idempotency checks.

Commands and results:

```text
cd evolution-engine && python3 -m unittest tests.test_discovery tests.test_compatibility tests.test_source_matrix
Ran 37 tests in 3.216s — OK

cd evolution-engine && python3 -m unittest discover -s tests
Ran 234 tests in 14.544s — OK
```

Captured summary: [`endeavouros-wave1-package-ownership-test.log`](endeavouros-wave1-package-ownership-test.log).

## Qualification limits

The local fixture proves deterministic source preflight and simulated convergence only. The available ISO survey does not establish installed EndeavourOS hooks, keyring/repository update behavior, package transaction policy, or crash recovery on actual hardware. EndeavourOS remains **conditional**, and incomplete pacman ownership discovery now fails closed.
