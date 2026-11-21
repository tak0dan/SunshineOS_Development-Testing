# EndeavourOS integration survey — Wave 1 audit

Date: 2026-11-21  
Scope: verify the existing EndeavourOS integration in this checkout, catalogue its exact paths, and rerun its regression coverage. This audit does not claim a qualified end-to-end migration from a real EndeavourOS installation.

## Source survey

The local image at `/home/tak_0/.local/state/sunshine-orchestrator/iso/endeavouros.iso` is a 3,718 MiB ArchISO live/rescue image. Read-only `xorriso -pvd_info` inspection reports volume ID `EOS_202608`, publisher `ENDEAVOUROS <HTTPS://ENDEAVOUROS.COM>`, preparer `PREPARED BY MKARCHISO`, and creation time `2026081514130800` (2026-08-15 14:13:08 UTC). The prior catalog [`endeavouros-wave1-deepening.md`](endeavouros-wave1-deepening.md) records exact outer ISO tree entries and hashes. The package list and boot files describe live media; they do not establish installer behavior or installed-system qualification. `airootfs.sfs` remains uninspected in this wave.

## Repository path catalogue

| Exact path | Symbol / behavior | Integration boundary |
|---|---|---|
| `evolution-engine/src/discovery/system.py` | `_detect_distribution` parses `/etc/os-release` and retains sorted `KEY=value` fields, including `ID_LIKE`, in `system.os-release` evidence. | The classifier can use observed lineage instead of distro branding alone. |
| `evolution-engine/src/discovery/packages.py` | `discover_packages` uses pacman queries including `pacman -Qqm` for foreign packages. | Foreign package names are inventory evidence; they are not automatically treated as all-AUR or removed. |
| `evolution-engine/src/target/compatibility.py` | `classify_source`, `_os_release_value`, `preflight_source`; EndeavourOS is conditional only with observed `ID_LIKE` containing `arch`. | Fails closed on absent lineage; ordinary core checks still require supported architecture, systemd, pacman database, and bootloader. |
| `evolution-engine/tests/test_compatibility.py` | `T-ENDEAVOUR-COMP-001`, `T-ENDEAVOUR-COMP-002`. | Covers corroborated lineage acceptance and missing-lineage rejection. |
| `evolution-engine/tests/test_discovery.py` | `T-ENDEAVOUR-DISC-001`. | Confirms raw `ID_LIKE=arch` evidence survives discovery. |
| `evolution-engine/src/evolution/compatibility.py` | `SOURCE_PROFILES` includes an EndeavourOS source profile. | This is a separate compatibility subsystem from `src/target/compatibility.py`; matching its profile is not proof that the CLI's full execution path is qualified. |
| `evolution-engine/tests/source-matrix.toml` | G5 integration matrix currently contains five Arch/Sunshine fixtures and no EndeavourOS fixture. | The distribution-specific lineage tests do not yet exercise full `--check`, `--plan`, `--apply`, and idempotency convergence on an EndeavourOS fixture. |
| `evolution-engine/tests/test_source_matrix.py` | Checks matrix discovery, plans, apply, and repeated apply. | Appropriate next integration point after an EndeavourOS fixture is added and reviewed. |

## Architecture alignment and limits

The observed-evidence gate follows `reports/USER_MIGRATION_MANDATE_2026-11-21.md` M-04 (installation authority) and M-08 (qualification, not assumption), and `reports/ARCHITECTURE_DECISIONS.md` AD-04, AD-05, and AD-14. A conditional classification is only source preflight; it is not a claim of fully tested migration. In particular, current coverage does not establish an EndeavourOS installer profile, hook behavior, repo/keyring transition, mirror behavior, package replacement policy, or end-to-end crash recovery. No claim about those behaviors is made here.

## Regression evidence

Test IDs: `T-ENDEAVOUR-COMP-001`, `T-ENDEAVOUR-COMP-002`, `T-ENDEAVOUR-DISC-001`.  
Command: `python3 -m unittest tests.test_compatibility tests.test_discovery` from `evolution-engine/`.  
Result: 27 tests passed. Full captured output: [`endeavouros-wave1-deepening-audit-test.log`](endeavouros-wave1-deepening-audit-test.log).

The existing implementation and tests were already present in this checkout at audit start. This audit adds the verification and integration-gap catalogue; it does not claim authorship of those pre-existing code changes. No source code was changed in this audit.
