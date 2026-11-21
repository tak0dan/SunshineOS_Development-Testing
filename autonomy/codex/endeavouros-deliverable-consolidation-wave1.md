# EndeavourOS deliverable consolidation — Wave 1

Date: 2026-11-21  
Scope: consolidate the verified EndeavourOS source survey, repository integration, regression evidence, and qualification limits. This document does not claim real-machine migration qualification.

## Source survey and evidence boundary

The local image survey in [`endeavouros-wave1-deepening.md`](endeavouros-wave1-deepening.md) records `/home/tak_0/.local/state/sunshine-orchestrator/iso/endeavouros.iso` as ArchISO live/rescue media, with outer paths `/arch/version`, `/arch/pkglist.x86_64.txt`, `/arch/x86_64/airootfs.sfs`, `/arch/x86_64/airootfs.sha512`, `/boot/grub/`, `/loader/entries/`, `/boot/syslinux/`, `/EFI/BOOT/BOOTx64.EFI`, and `/EFI/BOOT/BOOTIA32.EFI`. This is media inventory, not evidence of installed-system defaults. The compressed root and installer internals were not inspected, so no installer, hook, update, mirror, keyring, or upgrade behavior is inferred from the ISO.

Additional existing source-level surveys cover package ownership and safe repair patterns in [`endeavouros-wave1-package-ownership.md`](endeavouros-wave1-package-ownership.md) and [`endeavouros-wave1-repair.md`](endeavouros-wave1-repair.md). EndeavourOS tools are treated as research leads; their presence does not authorize destructive reconciliation.

## Consolidated repository catalogue

| Exact path | Symbol / test ID | Verified behavior and boundary |
|---|---|---|
| `evolution-engine/src/discovery/system.py` | `_detect_distribution` | Captures parsed `/etc/os-release`, retaining `ID_LIKE` as observation evidence. |
| `evolution-engine/src/discovery/packages.py` | `discover_packages` | Collects pacman installed, orphan, and foreign package evidence. Ownership uncertainty is preserved; foreign packages are not automatically replaced or called AUR solely from foreign status. |
| `evolution-engine/src/target/compatibility.py` | `_os_release_value`, `classify_source`, `preflight_source` | EndeavourOS conditional support requires configured `ID_LIKE` evidence with exact `arch` token and still passes the common capability checks. |
| `evolution-engine/fixtures/endeavouros/etc/os-release` | EndeavourOS fixture | Provides `ID=endeavouros`, `ID_LIKE=arch`; simulation only. |
| `evolution-engine/src/fixtures.py` | `FIXTURE_NAMES`, fixture executor | Routes the fixture through shared discovery/planning/apply logic with isolated state. |
| `evolution-engine/tests/source-matrix.toml` | `endeavouros` case | Declares source shape, conditional level, observed lineage, Btrfs, and GRUB expectations. |
| `evolution-engine/tests/test_compatibility.py` | `T-ENDEAVOUR-COMP-001`–`004` | Tests positive lineage, missing lineage, unconfigured provenance, and exact-token matching. |
| `evolution-engine/tests/test_discovery.py` | `T-ENDEAVOUR-DISC-001` and package ownership cases | Tests preservation of lineage evidence and fail-closed incomplete package ownership observations. |
| `evolution-engine/tests/test_source_matrix.py` | `T-ENDEAVOUR-MATRIX-001`, matrix convergence and idempotency tests | Exercises fixture `--check`, `--plan`, `--apply`, and repeat apply through the same engine. It is offline fixture qualification, not real hardware or host qualification. |
| `evolution-engine/src/evolution/tools/config_drift.py` | `assess_config_drift` | Read-only `.pacnew`/`.pacsave` candidate inventory; sensitive files require manual review. |
| `evolution-engine/src/evolution/tools/package_health.py` | `assess_package_health` | Read-only package-health findings; results are advisory, not automatic repair authorization. |
| `evolution-engine/tests/test_config_drift.py` | `T-EOS-REPAIR-001`–`003` | Tests candidate classification, incomplete evidence, and symlink boundaries. |

The integration follows mandate M-04/M-06/M-08 and architecture decisions AD-04/AD-05/AD-14: observed state controls qualification, repair must be recoverable, and support is qualified rather than assumed. The referenced reports were read only; no `reports/` file was changed by this deliverable.

## Working regression path

The EndeavourOS case now participates in the generic source matrix. It checks lineage and conditional status, verifies a plan contains the shared convergence operations without replacing foreign packages, and applies twice in a temporary state root to require idempotent convergence. The focused test run executed from `evolution-engine/`:

```text
python3 -m unittest tests.test_source_matrix tests.test_compatibility tests.test_discovery
Ran 37 tests — OK
```

Evidence log: [`endeavouros-deliverable-consolidation-wave1-test.log`](endeavouros-deliverable-consolidation-wave1-test.log).

## Qualification limits

The tests exercise a synthetic rooted fixture and injected command responses. They do not prove migration safety on a real EndeavourOS installation, installer behavior, upstream package hooks, repository/keyring transitions, live mirrors, hardware-specific boot behavior, or crash recovery on physical storage. The source remains conditional; broadening support requires the historical/source qualification matrix and fault-injection evidence required by AD-14/AD-15/AD-27/AD-28.
