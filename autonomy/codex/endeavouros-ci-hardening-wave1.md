# EndeavourOS CI hardening — Wave 1

Date: 2026-11-21  
Scope: repository-backed CI survey, exact path catalogue, a focused GitHub Actions gate, and regression coverage. The source matrix is fixture-based; hosted CI and real EndeavourOS host migration are not qualified by this change.

## CI survey and catalogue

Before this change, `.github/workflows/` contained `arch2015-sysvinit.yml` and `arch2026-systemd.yml` but no EndeavourOS-specific gate. Both existing workflows use `pull_request` and `push`, grant `contents: read`, pin checkout by full commit SHA, run focused unittest suites, and invoke `autonomy/codex/ci_policy_audit.py`.

| Exact path and symbol | Role and finding |
|---|---|
| `.github/workflows/arch2015-sysvinit.yml` | Existing historical SysV focused CI; policy-audited. |
| `.github/workflows/arch2026-systemd.yml` | Existing systemd inventory/repair CI; policy-audited. |
| `.github/workflows/endeavouros.yml` | Added push and pull request gate; read-only permissions, SHA-pinned checkout; executes EndeavourOS relevant lineage, discovery, package ownership and source-matrix suites; then runs workflow trust audit. |
| `autonomy/codex/ci_policy_audit.py::audit_workflow`, `workflows`, `main` | Checks mutable action references, `pull_request_target`, write permissions and visible secret references. Missing workflow tree fails closed. It is a focused text auditor, not a full YAML parser or hosted CI validator. |
| `autonomy/codex/test_ci_policy_audit.py::CiPolicyAuditTests.test_ci_007_endeavouros_regressions_are_wired_and_policy_clean` | Added `CI_007`, protecting workflow presence, policy cleanliness, triggers, read-only permission and suite wiring. |
| `evolution-engine/tests/test_compatibility.py::CompatibilityTests` | EndeavourOS lineage and incomplete package ownership blockers (`T-ENDEAVOUR-COMP-001`–`004`, `T-ENDEAVOUR-PKG-002`). |
| `evolution-engine/tests/test_discovery.py::DiscoveryTests` | Retained `ID_LIKE` and fail-closed incomplete ownership probe (`T-ENDEAVOUR-DISC-001`, `T-ENDEAVOUR-PKG-001`). |
| `evolution-engine/tests/test_source_matrix.py::SourceMatrixTests` | Conditional EndeavourOS source matrix and common apply/idempotency path (`T-ENDEAVOUR-MATRIX-001`). |
| `evolution-engine/tests/source-matrix.toml` and `evolution-engine/fixtures/endeavouros/etc/os-release` | Test fixture/matrix only; they do not stand in for a captured installed system. |

The gate makes the existing conditional-source boundary continuously visible in CI. It does not promote EndeavourOS to fully qualified support. This follows `reports/ARCHITECTURE_DECISIONS.md` AD-04, AD-05, AD-14 and AD-15, and mandate invariants M-04, M-08 and M-09. The context reports were read only.

## Regression evidence

- `CI_007`: new workflow is present, read-only, policy-clean, and invokes all three focused test modules.
- Existing EndeavourOS test IDs run through the workflow: `T-ENDEAVOUR-COMP-001`–`004`, `T-ENDEAVOUR-PKG-001`–`002`, `T-ENDEAVOUR-DISC-001`, `T-ENDEAVOUR-MATRIX-001`.
- Auditor command: `python3 -m unittest -v test_ci_policy_audit` from `autonomy/codex/` — **7 passed**. Evidence: `autonomy/codex/endeavouros-ci-hardening-auditor-test.log`.
- Workflow suites: `python3 -m unittest -v tests.test_compatibility tests.test_discovery tests.test_source_matrix` from `evolution-engine/` — **37 passed**. Evidence: `autonomy/codex/endeavouros-ci-hardening-regression.log`.
- Repository policy audit: `python3 autonomy/codex/ci_policy_audit.py .` — **3 workflows, no detected policy findings**. Evidence: `autonomy/codex/endeavouros-ci-hardening-policy.log`.

Hosted execution requires the workflow to be published to the CI provider. The policy auditor checks a limited set of textual trust properties; passing it is not a substitute for provider-side workflow review.
