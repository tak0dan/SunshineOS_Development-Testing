# codex-lead-0031 -> hierarchy

# Arch 2026 systemd CI hardening — Wave 1

Added [arch2026-systemd.yml](/home/tak_0/sunshineos-audit/SunshineOS_Development-Testing/.github/workflows/arch2026-systemd.yml), a push and pull request workflow with read-only repository permission. It runs the systemd inventory, repair, discovery, and compatibility suites, then audits workflow policy.

Added regression **CI_006** in [test_ci_policy_audit.py](/home/tak_0/sunshineos-audit/SunshineOS_Development-Testing/autonomy/codex/test_ci_policy_audit.py). The path catalogue, architecture grounding, and verification details are in [arch2026-systemd-ci-hardening-wave1.md](/home/tak_0/sunshineos-audit/SunshineOS_Development-Testing/autonomy/codex/arch2026-systemd-ci-hardening-wave1.md).

**Verification:** 46 focused tests passed, including T-ARCH2026-SYSTEMD-001–017 and T-ARCH2026-SYSTEMD-REPAIR-001–005. CI auditor tests CI_001–CI_006 passed. The policy audit found no issues across two workflows. Logs: [focused tests](/home/tak_0/sunshineos-audit/SunshineOS_Development-Testing/autonomy/codex/arch2026-systemd-ci-focused-test.log), [auditor tests](/home/tak_0/sunshineos-audit/SunshineOS_Development-Testing/autonomy/codex/arch2026-systemd-ci-auditor-test.log), [policy audit](/home/tak_0/sunshineos-audit/SunshineOS_Development-Testing/autonomy/codex/arch2026-systemd-ci-policy.log).

I could not commit the changes: Git reported `.git/index.lock: Read-only file system`. Hosted CI execution is also pending availability of the workflow to the provider. The existing survey records that the ISO query did not expose an extracted systemd tree, so this work makes no claims about unverified upstream Arch unit files or hooks.
