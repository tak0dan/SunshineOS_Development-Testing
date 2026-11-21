# Garuda CI hardening — Wave 1

## Survey and catalogue

The pinned upstream source is the local read-only checkout
`/home/tak_0/.local/state/sunshine-orchestrator/iso/repos/garuda-toolbox`, revision
`430de5bc5356468318a5c677d8b2f6d2c4565a75`. The survey in
`autonomy/codex/garuda-repair-wave1.md` and source audit in
`autonomy/codex/garuda_architecture_audit.py` catalogue these CI-relevant behaviors:

| Exact source path / audit ID | Observed behavior | CI and SunshineOS consequence |
|---|---|---|
| `packages/renderer/src/app/components/maintenance/maintenance.component.ts` / `GARUDA-ARCH-001` | Update can use `garuda-update --skip-mirrorlist` or fall back to `pacman -Syu`. | Exercise catalogued controls; don't silently equate package transaction paths. |
| Same maintenance component / `GARUDA-ARCH-002` | Orphan cleanup uses `pacman --noconfirm -Rns`. | Test SunshineOS package-lock assessment and maintain explicit transaction controls. |
| Same maintenance component / `GARUDA-ARCH-003` | Renderer calls a shell execution API. | Keep shell boundary in the risk catalogue; hosted CI audits this repo's workflow trust properties. |
| `packages/renderer/src/app/components/boot-repair/boot-repair.service.ts` / `GARUDA-ARCH-005` | Boot repair constructs raw-device writes using `dd`. | Source-level finding requires target verification/checkpointing; hosted jobs do not run boot repair. |
| `packages/main/src/modules/ShellModule.ts` / `GARUDA-ARCH-006` | Shell IPC spawns caller-provided command and argv. | Preserve typed/allowlisted command boundary as a SunshineOS control. |
| `packages/main/src/modules/AutoUpdater.ts` / `GARUDA-ARCH-007..008`; system status component / `GARUDA-ARCH-009` | Application self-update and OS package update are separate flows; updater errors are logged and suppressed. | Keep the distinction explicit in the catalogue; don't claim an upstream Garuda CI run. |
| `autonomy/codex/garuda-wave1-catalog.json` | Five findings bind source paths to verdicts, invariants, and controls. | `garuda_catalog.py` validates schema, provenance shape, path safety, and required controls. |
| `autonomy/codex/pacman_lock_repair.py::assess_pacman_lock` | Read-only pacman lock ownership assessment; never authorizes deletion. | Regression suite checks absent, active, candidate, and unknown-owner states. |

The repository had no Garuda workflow before this change. Its existing workflow
policy auditor is `autonomy/codex/ci_policy_audit.py::audit_workflow` and rejects
mutable action references, risky `pull_request_target`, visible broad write
permissions, and selected secret-use patterns. This text auditor is not a full
YAML parser or hosted workflow validator. It fails closed when the repository
has no workflows.

## Change

Added `.github/workflows/garuda.yml` with `push` and `pull_request` triggers,
repository-level `contents: read`, and checkout pinned to a full commit SHA. It
validates the Garuda catalogue, runs the portable package-lock regressions and
catalogue tests `GARUDA_CAT_001`–`010`, then runs the workflow policy audit.
`GARUDA_CAT_011` checks a machine-local upstream checkout and is intentionally
not part of hosted CI; it is included in local verification below.

Added `CI_008` in `autonomy/codex/test_ci_policy_audit.py` to protect workflow
presence, triggers, read-only permission, portable suite wiring, and policy
audit inclusion. No Garuda upstream CI workflow was observed or asserted: this
gate tests SunshineOS controls derived from the survey.

## Regression IDs and evidence

- `CI_001`–`CI_008`, `GARUDA_CAT_001`–`011`, and `GARUDA_REPAIR_001`–`004`: **23 passed**.
- Hosted-workflow command (14 portable tests): `python3 -m unittest -v autonomy.codex.test_pacman_lock_repair` plus catalogue cases `GARUDA_CAT_001`–`010`. Log: `autonomy/codex/garuda-ci-focused-test.log`.
- Full local regression command: `python3 -m unittest -v test_ci_policy_audit test_garuda_catalog test_pacman_lock_repair` from `autonomy/codex/`. Log: `autonomy/codex/garuda-ci-regression-test.log`.
- Auditor regressions `CI_001`–`CI_008` (8 passed). Log: `autonomy/codex/garuda-ci-auditor-test.log`.
- Catalogue validation: `validated 5 Garuda findings`. Log: `autonomy/codex/garuda-ci-catalog-validation.log`.
- Repository policy audit: `WORKFLOWS: 4`, `NO_DETECTED_POLICY_FINDINGS`. Log: `autonomy/codex/garuda-ci-policy-audit.log`.

Context read: `reports/USER_MIGRATION_MANDATE_2026-11-21.md` and
`reports/ARCHITECTURE_DECISIONS.md` (AD-06, AD-08, AD-09, AD-14; mandate
M-04/M-05/M-06). Neither context file was modified. This is local evidence;
hosted execution is not claimed until the workflow runs in the provider.
