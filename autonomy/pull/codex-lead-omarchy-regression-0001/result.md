# codex-lead / Omarchy regression survey / Wave 1

Pinned a hash-checked Omarchy update/recovery source catalogue at commit `e4635a4eea887d5c8dbd70427386f570c37a2a61` in `evolution-engine/fixtures/research/omarchy-update-recovery-wave1.json`. Added regression `CAT_006` in `evolution-engine/tests/test_research_catalog.py` for source set completeness, path identity, commit identity, and schema validity.

Survey and implementation summary: `autonomy/codex/omarchy-regression-wave1.md`. Evidence: `autonomy/codex/omarchy-regression-wave1-test.log` and `autonomy/codex/omarchy-regression-wave1-source-hashes.log`.

Verification command from `evolution-engine/`: `python3 -m unittest tests.test_research_catalog -v` — 6 tests passed.
