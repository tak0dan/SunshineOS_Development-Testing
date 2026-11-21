# Solutions — SteamOS CI hardening, Wave 1

- Added `.github/workflows/steamos-regressions.yml`, with read-only contents permissions, SHA-pinned checkout, staging/activation and repair test execution, and trust-policy audit.
- Added `evolution-engine/tests/test_steamos_ci.py`, IDs `STEAMOS_CI_001`–`003`, to guard required CI coverage and trust settings.
- Survey and evidence: `autonomy/codex/steamos-ci-hardening-wave1.md`; exact test transcript: `autonomy/codex/steamos-ci-hardening-wave1-test.log`.
