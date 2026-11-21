# Garuda integration — Wave 1 deepening

## Scope and grounding

The source survey in [`garuda-wave1.md`](garuda-wave1.md) is pinned to the local
Garuda Toolbox checkout at `430de5bc5356468318a5c677d8b2f6d2c4565a75`. It
catalogues maintenance actions, update flow, cleanup, snapshots/boot repair,
repository/keyring repair, and the UI-to-shell boundary. The machine-readable
records are in [`garuda-wave1-catalog.json`](garuda-wave1-catalog.json).

The mandate requires source-state qualification (M-08), actual-installation
authority (M-04), and staged/recoverable changes (M-05/M-06). AD-04 and AD-14
map these to capability discovery and conditional qualification. In the active
engine, `evolution-engine/src/target/compatibility.py::classify_source` is the
classifier and `_os_release_value` only trusts `system.os-release` evidence
when its status is `CONFIGURED`.

## Integration change

`evolution-engine/src/target/compatibility.py` now recognizes the `garuda`
distribution ID as an Arch-family candidate and requires corroborating
`ID_LIKE=arch` evidence from a successful os-release probe. A corroborated
Garuda source is **conditional**, then still passes through the common
architecture, init, pacman database/ownership, bootloader, filesystem, and
package checks. Missing, stale, or lookalike lineage evidence blocks
transformation. This does not declare Garuda generally qualified: it provides
conditional preflight classification, and M-08 still requires source-matrix
qualification for supported configurations.

Regression coverage in `evolution-engine/tests/test_compatibility.py`:

- `T-GARUDA-COMP-001` — configured `ID_LIKE=arch` yields conditional support.
- `T-GARUDA-COMP-002` — no lineage evidence blocks.
- `T-GARUDA-COMP-003` — stale evidence from an absent probe blocks.
- `T-GARUDA-COMP-004` — `archlinux` is not accepted as the exact `arch` token.
- `T-GARUDA-COMP-005` — strict preflight rejects the conditional Garuda profile.

Existing derivative safeguards are also covered by `T-ENDEAVOUR-COMP-001`
through `T-ENDEAVOUR-COMP-004`; package ownership discovery failure is covered
by `T-ENDEAVOUR-PKG-002`.

## Verification evidence

Run from repository root:

```sh
(cd evolution-engine && python3 -m unittest tests.test_compatibility)
python3 -m unittest autonomy/codex/test_garuda_catalog.py
python3 autonomy/codex/garuda_catalog.py
```

Captured output: [`garuda-wave1-integration-test.log`](garuda-wave1-integration-test.log).
The focused compatibility suite passed 25 tests, catalog regression suite
passed 5 tests, and validator reported `validated 5 Garuda findings`.

## Scope limit

This is source-checkout and fixture-based evidence. It does not execute Garuda
Toolbox actions, inspect a running Garuda installation, or qualify a full
Garuda-to-Sunshine migration. The engine files already had unrelated pending
changes in the shared worktree; only the Garuda lineage branch and its four
tests are part of this integration task.
