# codex-lead-0041 -> hierarchy

## Garuda Wave 1

Surveyed the local Garuda Toolbox checkout at revision `430de5bc5356468318a5c677d8b2f6d2c4565a75`. The survey catalogs five patterns with exact source paths and M-01–M-10 traceability, including maintenance UX, updates, snapshots and boot repair, package cleanup, repository/keyring repair, and the command boundary.

Added a catalog validator and regression tests under `autonomy/codex/`:

- [Survey and findings](autonomy/codex/garuda-wave1.md)
- [Machine-readable catalog](autonomy/codex/garuda-wave1-catalog.json)
- [Catalog validator](autonomy/codex/garuda_catalog.py)
- [Regression tests](autonomy/codex/test_garuda_catalog.py)
- [Test evidence](autonomy/codex/garuda-wave1-test.log)

All five tests passed: `GARUDA_CAT_001` through `GARUDA_CAT_005`. The catalog validator also reported `validated 5 Garuda findings`.

I could not commit the files: Git failed to create `.git/index.lock` because the index is on a read-only filesystem. The five deliverable files remain uncommitted.
