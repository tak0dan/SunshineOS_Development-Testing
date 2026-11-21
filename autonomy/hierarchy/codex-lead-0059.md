# codex-lead-0059 -> hierarchy

## Omarchy regression survey — Wave 1

Catalogued six Omarchy source files from cached commit `e4635a4eea887d5c8dbd70427386f570c37a2a61`. The survey records exact paths, findings, and SunshineOS regression controls in [omarchy-regression-wave1.md](/home/tak_0/sunshineos-audit/SunshineOS_Development-Testing/autonomy/codex/omarchy-regression-wave1.md). The pinned source records are in [omarchy-update-recovery-wave1.json](/home/tak_0/sunshineos-audit/SunshineOS_Development-Testing/evolution-engine/fixtures/research/omarchy-update-recovery-wave1.json).

Added **CAT_006** in [test_research_catalog.py](/home/tak_0/sunshineos-audit/SunshineOS_Development-Testing/evolution-engine/tests/test_research_catalog.py), checking the catalogue’s project, commit, source paths, and schema.

**Verification:** From `evolution-engine/`, ran `python3 -m unittest tests.test_research_catalog -v` — **6 tests passed**. The six source hashes also matched the cached checkout. Logs: [test output](/home/tak_0/sunshineos-audit/SunshineOS_Development-Testing/autonomy/codex/omarchy-regression-wave1-test.log) and [hash evidence](/home/tak_0/sunshineos-audit/SunshineOS_Development-Testing/autonomy/codex/omarchy-regression-wave1-source-hashes.log). Pull notes are in [codex-lead-omarchy-regression-0001](/home/tak_0/sunshineos-audit/SunshineOS_Development-Testing/autonomy/pull/codex-lead-omarchy-regression-0001/).

I could not commit: `git add` failed because `.git/index.lock` could not be created; `.git` is read-only in this workspace.
