# codex-lead-0039 -> hierarchy

## EndeavourOS CI hardening — Wave 1

Added a read-only GitHub Actions workflow at [.github/workflows/endeavouros.yml](/home/tak_0/sunshineos-audit/SunshineOS_Development-Testing/.github/workflows/endeavouros.yml). It runs on pushes and pull requests, pins checkout to a full commit SHA, and runs the compatibility, discovery, and source-matrix suites.

Added `CI_007` coverage in [test_ci_policy_audit.py](/home/tak_0/sunshineos-audit/SunshineOS_Development-Testing/autonomy/codex/test_ci_policy_audit.py). The survey, exact path catalogue, test IDs, and evidence links are in [endeavouros-ci-hardening-wave1.md](/home/tak_0/sunshineos-audit/SunshineOS_Development-Testing/autonomy/codex/endeavouros-ci-hardening-wave1.md).

**Verification:** auditor tests passed (7); EndeavourOS suites passed (37); policy audit reported 3 workflows and no detected findings. Logs are in `autonomy/codex/endeavouros-ci-hardening-*.log`.

I could not commit the changes: the workspace’s `.git/index` is read-only, so `git add` failed. No `reports/` files were modified.
