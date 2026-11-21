# Arch 2026 systemd CI hardening — Wave 1

## Scope and grounding

This change wires the repository's existing systemd evidence and migration regressions into GitHub Actions. It follows the observed-state and qualification policies in `reports/ARCHITECTURE_DECISIONS.md` AD-05, AD-14, and AD-24, and the user's fail-closed stability mandate. The context reports were read only.

The prior survey `autonomy/codex/arch2026-systemd-wave1-integration.md` records that a read-only query of the local Arch 2026 ISO did not expose an extracted systemd root tree. This CI gate therefore tests verified SunshineOS code and does not claim to validate upstream Arch unit files, hooks, or hosted workflow execution.

## Verified path catalogue

| Exact path and symbol | CI role / observed contract |
|---|---|
| `.github/workflows/arch2026-systemd.yml` | New push and pull request workflow. Grants `contents: read`, pins `actions/checkout` to a full commit SHA, runs the four focused suites, then audits workflow policy. |
| `evolution-engine/src/evolution/tools/systemd_inventory.py::parse_unit_file_inventory` | Parses unit-file inventory; failed, malformed, duplicate, or unknown observations remain incomplete. |
| `evolution-engine/src/evolution/tools/systemd_inventory.py::assess_unit_inventory` | Assesses desired states without mutation; incomplete observations and broken/masked states block checked planning. |
| `evolution-engine/src/evolution/tools/service_supervision.py::ServiceSupervisor.plan_checked` | Uses inventory assessment before returning service command proposals; it does not execute them. |
| `evolution-engine/src/evolution/tools/systemd_repair.py` | Read-only unit repair assessment; identifies vendor/admin definitions, masks, unsafe links, empty files, and missing units. |
| `evolution-engine/tests/test_systemd_inventory.py::SystemdUnitInventoryTests` | T-ARCH2026-SYSTEMD-001..017 cover parser, ambiguity, state assessment and checked-plan boundaries. |
| `evolution-engine/tests/test_systemd_repair.py::SystemdRepairAssessmentTests` | T-ARCH2026-SYSTEMD-REPAIR-001..005 cover read-only repair assessment and fail-closed path handling. |
| `evolution-engine/tests/test_discovery.py::DiscoveryTests` | Runs runtime discovery regressions, including systemd observations and init-system identification. |
| `evolution-engine/tests/test_compatibility.py::CompatibilityTests` | Runs source qualification and ensures unsupported init/package/system states are blocked or conditional. |
| `autonomy/codex/ci_policy_audit.py::audit_workflow`, `main` | Checks workflow action SHA pinning, risky pull request triggers, write permissions, and visible secret references; no-workflow state fails closed. |
| `autonomy/codex/test_ci_policy_audit.py::CiPolicyAuditTests.test_ci_006_arch2026_systemd_workflow_is_present_and_policy_clean` | CI_006 protects workflow presence, policy cleanliness, both triggers, and all four focused suites. |

## Change and regression IDs

Added `.github/workflows/arch2026-systemd.yml` to run `tests.test_systemd_inventory`, `tests.test_systemd_repair`, `tests.test_discovery`, and `tests.test_compatibility` on pushes and pull requests with read-only repository permission. Added `CI_006` in `autonomy/codex/test_ci_policy_audit.py` to ensure that workflow remains wired and clean under the local policy auditor.

The focused suite retains IDs T-ARCH2026-SYSTEMD-001..017 and T-ARCH2026-SYSTEMD-REPAIR-001..005. These tests exercise code paths governed by observation-first, capability-qualified migration decisions; the workflow does not turn discovery into mutation authorization.

## Verification and evidence

- Command from `evolution-engine/`: `python3 -m unittest -v tests.test_systemd_inventory tests.test_systemd_repair tests.test_discovery tests.test_compatibility` — **46 passed**. Raw output: `autonomy/codex/arch2026-systemd-ci-focused-test.log`.
- Command from `autonomy/codex/`: `python3 -m unittest -v test_ci_policy_audit` — **6 passed**, including CI_001..CI_006. Raw output: `autonomy/codex/arch2026-systemd-ci-auditor-test.log`.
- Command from repository root: `python3 autonomy/codex/ci_policy_audit.py .` — **2 workflows**, no detected policy findings. Raw output: `autonomy/codex/arch2026-systemd-ci-policy.log`.

Hosted execution awaits the workflow being available to the CI provider. No report-owned files were changed.
