# Arch 2015 SysV CI hardening — Wave 1

## Survey and catalogue

The repository had no `.github/workflows/` tree before this change, so its
Arch 2015 SysV regression suite was not wired into hosted CI. The local
`autonomy/codex/ci_policy_audit.py::main` reports an absent workflow tree as
`REVIEW_REQUIRED` (exit 1); its `audit_workflow` checks action SHA pins,
fork-trigger use, write permissions, and visible secret references.

| Exact path and symbol | Role / observation |
|---|---|
| `.github/workflows/arch2015-sysvinit.yml` | New GitHub Actions entry point; read-only `contents` permission, `pull_request`/`push` triggers, pinned checkout action, focused regression command, then local workflow policy audit. |
| `evolution-engine/tests/test_arch2015_sysvinit.py::Arch2015SysvinitTests` | Runtime evidence precedence and refusal to send detected SysV state through ordinary Arch transformation; IDs `T-ARCH2015-SYSV-004`–`005`. |
| `evolution-engine/tests/test_sysvinit_inventory.py::SysVInitInventoryTests` | Literal-only `rc.conf` parsing and fail-closed ambiguity handling; IDs `T-ARCH2015-SYSV-006`–`009`. |
| `evolution-engine/tests/test_sysvinit_repair.py::SysVInitRepairTests` | Read-only service assessment, incomplete inventory and root-escape blocks; IDs `T-ARCH2015-SYSV-010`–`012`. |
| `evolution-engine/tests/test_discovery.py::DiscoveryTests` | Discovery regressions `T-ARCH2015-SYSV-001`–`002`; included in CI command. |
| `evolution-engine/tests/test_compatibility.py::CompatibilityTests.test_arch_2015_sysvinit_requires_recovery_bridge` | Compatibility boundary `T-ARCH2015-SYSV-003`; included in CI command. |
| `autonomy/codex/ci_policy_audit.py::audit_workflow`, `main` | Existing local trust-policy audit; workflow absence is not a clean result. |
| `autonomy/codex/test_ci_policy_audit.py::CiPolicyAuditTests.test_ci_005_arch2015_sysv_workflow_is_present_and_policy_clean` | New wiring regression `CI_005`; checks workflow presence, trust-policy cleanliness, and references to the inventory, repair, and Arch 2015 suites. |

## Context and change

`reports/USER_MIGRATION_MANDATE_2026-11-21.md` and
`reports/ARCHITECTURE_DECISIONS.md` were read and left untouched. This gate
supports AD-06 and AD-14 / M-08: CI runs the fail-closed source evidence and
repair regressions, and reports workflow-policy problems instead of silently
passing. It also exercises the AD-13 Arch 2015 recovery boundary. No historical
Arch 2015 VM or hosted-run result is claimed by this workflow change.

Added `.github/workflows/arch2015-sysvinit.yml` to run the five focused
regression modules on pushes and pull requests with read-only repository
permissions. Added `CI_005` to ensure the workflow remains present, invokes the
relevant test suites, and passes the existing policy audit.

## Verification

- Focused workflow test command: 33 tests passed. Evidence:
  `autonomy/codex/arch2015-sysvinit-ci-wave1-test.log`.
- Workflow policy audit: one workflow, no detected policy findings. Evidence:
  `autonomy/codex/arch2015-sysvinit-ci-wave1-policy.log`.
- CI auditor regressions `CI_001`–`CI_005`: 5 tests passed. Evidence:
  `autonomy/codex/arch2015-sysvinit-ci-wave1-auditor-test.log`.

Hosted execution remains pending the workflow being pushed to the provider; the
verification above ran the exact test and audit commands locally.
