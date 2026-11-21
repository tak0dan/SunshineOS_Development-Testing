# codex-lead-0043 -> hierarchy

## Garuda Wave 1 regression deepening

Surveyed the Garuda Toolbox checkout at revision `430de5bc5356468318a5c677d8b2f6d2c4565a75` and catalogued maintenance actions, updater fallback behavior, orphan removal, snapshot and boot repair, shell execution, and configuration reset. The survey includes exact source paths and SunshineOS dispositions.

Hardened [garuda_catalog.py](/home/tak_0/sunshineos-audit/SunshineOS_Development-Testing/autonomy/codex/garuda_catalog.py) against malformed data, invalid revisions, and unsafe source paths. Added six regression cases, bringing the suite to 11 tests; all passed. The catalogue CLI also validated all five findings and their cited checkout paths.

Deliverables:

- [Survey and change summary](/home/tak_0/sunshineos-audit/SunshineOS_Development-Testing/autonomy/codex/garuda-wave1-regression-deepening.md)
- [Regression tests](/home/tak_0/sunshineos-audit/SunshineOS_Development-Testing/autonomy/codex/test_garuda_catalog.py) — `GARUDA_CAT_001`–`GARUDA_CAT_011`
- [Test and provenance log](/home/tak_0/sunshineos-audit/SunshineOS_Development-Testing/autonomy/codex/garuda-wave1-regression-deepening-test.log)

I couldn’t commit: Git reported `.git/index.lock: Read-only file system`. No files outside `autonomy/codex/` were changed by this task.
