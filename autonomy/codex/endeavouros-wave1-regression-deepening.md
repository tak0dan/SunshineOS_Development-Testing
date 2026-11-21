# EndeavourOS regression deepening — Wave 1

Date: 2026-11-21  
Scope: verify the EndeavourOS survey and compatibility boundary, then close a stale-evidence qualification gap. This is source preflight coverage, not an end-to-end migration qualification.

## Survey catalogue

The read-only source image survey is recorded in [`endeavouros-wave1-deepening.md`](endeavouros-wave1-deepening.md). It identifies `/home/tak_0/.local/state/sunshine-orchestrator/iso/endeavouros.iso` as an ArchISO live/rescue image and catalogs `/arch/version`, `/arch/pkglist.x86_64.txt`, `/arch/x86_64/airootfs.sfs`, `/arch/x86_64/airootfs.sha512`, and media boot paths. The compressed live root and installer internals were not inspected; the ISO therefore does not establish installed-system upgrade or hook behavior.

| Exact repository path | Symbols / test IDs | Observed behavior and boundary |
|---|---|---|
| `evolution-engine/src/discovery/system.py` | `_detect_distribution` | Parses `/etc/os-release`, retaining raw parsed fields such as `ID_LIKE` in the `system.os-release` observation. |
| `evolution-engine/src/discovery/packages.py` | `discover_packages` | Queries pacman package ownership and foreign packages. Foreign ownership is preserved as inventory evidence, not treated as proof that every such package is AUR. |
| `evolution-engine/src/target/compatibility.py` | `_os_release_value`, `classify_source`, `preflight_source` | EndeavourOS is conditional only with observed `ID_LIKE` containing the exact `arch` token. Existing architecture, init, package database, and bootloader blockers remain in force. |
| `evolution-engine/tests/test_compatibility.py` | `T-ENDEAVOUR-COMP-001`–`004` | Exercises qualified lineage, missing lineage, unusable observation provenance, and exact-token matching. |
| `evolution-engine/tests/test_discovery.py` | `T-ENDEAVOUR-DISC-001` | Confirms discovery retains `ID_LIKE=arch` for downstream qualification. |
| `evolution-engine/src/evolution/compatibility.py` | `SOURCE_PROFILES` | Separate compatibility profile registry includes EndeavourOS; that entry alone does not qualify the CLI execution path. |
| `evolution-engine/tests/source-matrix.toml` | source qualification matrix | Current matrix does not include an EndeavourOS fixture; full check/plan/apply/repeatability qualification remains outstanding. |
| `evolution-engine/tests/test_source_matrix.py` | matrix execution tests | Existing test harness is the integration point for a future EndeavourOS fixture. |

## Change

`_os_release_value` now refuses to consume `system.os-release` evidence unless that observation has `Status.CONFIGURED`. This prevents stale values attached to absent or failed observations from authorizing the conditional EndeavourOS profile. Token matching remains exact (`arch`), so `archlinux` does not satisfy the lineage gate.

This follows mandate invariants M-04 (the observed installation is authoritative) and M-08 (support requires qualification), and architecture decisions AD-04, AD-05, and AD-14. The mandate and decisions were read only; no `reports/` files were changed.

## Regression evidence

- `T-ENDEAVOUR-COMP-001`: configured `ID_LIKE=arch` permits conditional classification.
- `T-ENDEAVOUR-COMP-002`: absent lineage blocks classification.
- `T-ENDEAVOUR-COMP-003`: `ID_LIKE=arch` on an `ABSENT` observation is rejected.
- `T-ENDEAVOUR-COMP-004`: `ID_LIKE=archlinux` does not match the exact `arch` token.
- `T-ENDEAVOUR-DISC-001`: discovery retains lineage evidence.
- Command: `python3 -m unittest tests.test_compatibility tests.test_discovery` from `evolution-engine/`.
- Result: 29 tests passed. Captured output: [`endeavouros-wave1-regression-deepening-test.log`](endeavouros-wave1-regression-deepening-test.log).

Remaining qualification gap: add an EndeavourOS source-matrix fixture and exercise full CLI check, planning, apply, and repeat-apply behavior before claiming end-to-end migration support.
