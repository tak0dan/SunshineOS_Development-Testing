# Solutions

# Garuda CI hardening — Wave 1

Added a read-only Garuda workflow at [.github/workflows/garuda.yml](/home/tak_0/sunshineos-audit/SunshineOS_Development-Testing/.github/workflows/garuda.yml). It validates the five-finding catalogue, runs portable package-lock and catalogue regressions on pushes and pull requests, and audits workflow policy. `CI_008` protects the workflow wiring.

The source survey and exact Garuda Toolbox paths are catalogued in [garuda-ci-hardening-wave1.md](/home/tak_0/sunshineos-audit/SunshineOS_Development-Testing/autonomy/codex/garuda-ci-hardening-wave1.md). The pinned upstream checkout is local, so hosted CI omits its checkout-dependent provenance test; that test passed in local verification.

**Verification:** 23 tests passed (`CI_001`–`CI_008`, `GARUDA_CAT_001`–`011`, `GARUDA_REPAIR_001`–`004`). The workflow policy audit found no detected issues across four workflows. Logs are under `autonomy/codex/garuda-ci-*.log`.

I could not commit these files: Git could not create `.git/index.lock` because `.git` is read-only. No reports or unrelated files were changed.
