# EndeavourOS architecture enforcement — Wave 1

Date: 2026-11-21

## Scope and finding

The existing lineage gate in `evolution-engine/src/target/compatibility.py::classify_source` allows EndeavourOS only when configured `system.os-release` evidence contains the exact `arch` token in `ID_LIKE`. That is a conditional source-preflight result; it does not establish full installation-specific qualification. Before this change, `evolution-engine/tests/source-matrix.toml` had no EndeavourOS fixture, so the repository's G5 matrix did not enforce that boundary across plan, apply, and repeat-apply.

This change adds a reusable EndeavourOS fixture and a source-matrix case. The fixture advertises `ID=endeavouros` and `ID_LIKE=arch`, and the matrix asserts its `arch-customized` profile remains `conditional`. Existing matrix checks then exercise discovery, common convergence operations, apply, and idempotent repeat apply. The fixture uses the existing deterministic fixture command executor; no host system is modified.

## Exact path catalogue

| Path | Symbol / test ID | Enforcement or observed role |
|---|---|---|
| `evolution-engine/fixtures/endeavouros/etc/os-release` | fixture source identity | Supplies test-only `ID=endeavouros`, `ID_LIKE=arch`; does not represent a captured installed host. |
| `evolution-engine/src/fixtures.py` | `FIXTURE_NAMES`, `FixtureExecutor.__init__` | Registers fixture and provisions a test session for apply validation. |
| `evolution-engine/src/discovery/system.py` | `_detect_distribution` | Parses `/etc/os-release` and retains fields as `system.os-release` evidence. |
| `evolution-engine/src/target/compatibility.py` | `_os_release_value`, `classify_source`, `preflight_source` | Requires configured evidence and exact Arch lineage; conditional EndeavourOS is still subject to architecture, init, pacman, database, and boot checks. |
| `evolution-engine/tests/source-matrix.toml` | `endeavouros` case | Declares lineage, conditional support level, storage and boot expectations. |
| `evolution-engine/tests/test_source_matrix.py` | `T-ENDEAVOUR-MATRIX-001` | Checks lineage evidence and conditional status; shared matrix checks discovery, plan convergence, apply, and repeat-apply idempotency. |
| `evolution-engine/tests/test_compatibility.py` | `T-ENDEAVOUR-COMP-001`–`004` | Covers lineage accepted only with configured exact-token evidence; missing, absent-status, and near-match evidence block. |
| `evolution-engine/tests/test_discovery.py` | `T-ENDEAVOUR-DISC-001` | Checks that discovery retains `ID_LIKE` evidence. |
| `evolution-engine/tests/test_integration.py` | source-matrix integration checks | Existing adjacent integration assertions remain in place. |

## Architecture alignment and evidence boundary

The enforcement follows `reports/ARCHITECTURE_DECISIONS.md` AD-04 (capability-driven source handling), AD-05 (observed installation authority), AD-14 (qualification tiers), and AD-15 (source-shape qualification matrix), plus mandate invariants M-04, M-08, and M-09. Both reports were read only; neither was modified.

The ISO survey in `autonomy/codex/endeavouros-wave1-deepening.md` records the local ISO outer-tree paths (`/arch/version`, `/arch/pkglist.x86_64.txt`, `/arch/x86_64/airootfs.sfs`, boot entries) and explicitly limits what those live-media artifacts prove. The compressed live root and installer internals remain uninspected. This patch makes no claim about EndeavourOS installer behavior, installed upgrade hooks, keyring/repository transitions, or real-host end-to-end recovery qualification.

## Regression run

Command (from `evolution-engine/`):

```sh
python3 -m unittest tests.test_source_matrix tests.test_compatibility tests.test_discovery
```

Result: **35 tests passed**. Output: `autonomy/codex/endeavouros-wave1-architecture-enforcement-test.log`.
