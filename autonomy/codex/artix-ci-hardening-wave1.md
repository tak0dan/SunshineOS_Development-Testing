# Artix runit/OpenRC CI hardening — Wave 1

## Survey and catalogue

The checkout has no CI provider configuration: no `.github/workflows/`, `.gitlab-ci.yml`, `azure-pipelines.yml`, `Jenkinsfile`, or root `Makefile`/`tox.ini`/`pyproject.toml`. The repository-local CI policy check is `autonomy/codex/ci_policy_audit.py::main`; it inspects GitHub Actions workflows when present. Before this change, no workflows returned success, which could report a repository with no CI controls as policy-clean.

The Artix service implementation and regression inventory are:

| Area | Exact path and symbol/test | Finding |
|---|---|---|
| OpenRC/runit planner | `evolution-engine/src/evolution/tools/artix_services.py::plan_artix_service` | Produces argv-only plans from exact observed service paths; does not execute commands. |
| Public export | `evolution-engine/src/evolution/tools/__init__.py` | Exports `ArtixServicePlan` and `plan_artix_service`. |
| Artix regression suite | `evolution-engine/tests/test_artix_services.py::ArtixServicePlanTests` | Ten contracts, `ARTIX_SVC_001`–`ARTIX_SVC_010`, cover operation ordering, observed paths, package-owned definitions, argv constraints, runit persistent-activation boundary, serialization and rejection of mixed init evidence. |
| CI policy auditor | `autonomy/codex/ci_policy_audit.py::workflows`, `audit_workflow`, `main` | Audits action SHA pinning, fork-trigger review, write permissions and secret references. Missing workflow tree now fails with review-required exit status. |
| CI auditor regressions | `autonomy/codex/test_ci_policy_audit.py::CiPolicyAuditTests` | `CI_001`–`CI_004`; `CI_004` ensures absence of workflows is a failure. |

The prior catalogue `autonomy/results/surge-19-0020.md` names paths such as `autonomy/ci-artix/runit/`, `logs/ci-artix-runit-2026-11-21.log`, and `evidence/test-definitions/artix-init-schema.yaml`. Those paths are not present in this checkout; they are not treated as collected evidence or executable CI coverage.

## Change

Updated `autonomy/codex/ci_policy_audit.py::main` to fail closed when `.github/workflows` is absent. It now prints `NO_WORKFLOWS` and returns 1 instead of treating absence as success. Added regression `CI_004` in `autonomy/codex/test_ci_policy_audit.py`.

This is a local policy-auditor hardening change. Since the repository has no CI provider configuration, no automated hosted pipeline was added or claimed. The Artix suite remains directly runnable and validates plan construction only; it does not qualify migration execution, boot recovery or VM behavior for runit/OpenRC.

## Verification evidence

- `CI_001`–`CI_004`: 4 tests passed. Log: `autonomy/codex/artix-ci-policy-regression.log`.
- `ARTIX_SVC_001`–`ARTIX_SVC_010`: 10 tests passed. Log: `autonomy/codex/artix-ci-service-regression.log`.
- Running the auditor on this repository reports `FINDING: NO_WORKFLOWS` and exits 1 as intended. Log: `autonomy/codex/artix-ci-policy-current-repo.log`.

## Architecture context

This guard supports fail-closed verification under mandate M-08 and preserves the observed-state boundary in M-04. It follows `reports/ARCHITECTURE_DECISIONS.md` AD-06 (trust fails closed), AD-14 (support is qualified), and AD-30 (long support margin). The context documents were read but not modified.
