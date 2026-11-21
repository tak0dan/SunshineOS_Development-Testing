# Obarun / 66 / s6 CI hardening — Wave 1

Date: 2026-11-21  
Scope: survey available source and CI surfaces, then add a reusable local CI policy audit with regression coverage. No upstream checkout was modified.

## Evidence boundary

The local research corpus contains the `s6` source checkout at
`/home/tak_0/.local/state/sunshine-orchestrator/iso/repos/s6`, revision
`c7c24531c294e2573e79380de8c2d21849cb39ad`. The checkout has no tracked CI
workflow/configuration paths and no `.github/workflows/` directory. The corpus
does not contain an Obarun distribution source checkout or an independent `66`
source checkout. Therefore upstream Obarun/66 workflow behavior cannot be
catalogued as inspected evidence in this wave. Existing Obarun/66 marker-path
observations in `autonomy/codex/obarun-66-s6-wave1.md` are host discovery
candidates, not source-tree evidence.

## Exact source catalogue

| File and symbol | Observed behavior | CI/security implication |
|---|---|---|
| Cached s6 `Makefile:136-139`, `tests` and `check` | `check` builds test binaries and loops over `TEST_BINS`, invoking `./tools/run-test.sh` for each. | A CI job can use `make check` as the project test entry point, but this checkout does not wire it to a hosted CI workflow. |
| Cached s6 `tools/run-test.sh:3-9` | Takes `$1` as `prog`, chooses a wrapper or executable, then builds an unquoted `cmd` string. | Test names and wrapper arguments undergo shell word splitting and pathname expansion at `$cmd`; invoke a fixed executable/argument vector instead. |
| Cached s6 `tools/run-test.sh:11-21` | Copies or generates expected output in the checkout root, pipes the test through `diff`, then removes the temporary expected file only on success. | Run tests in an isolated temporary build directory or use a trap for cleanup. Failed comparisons can leave generated files in the source tree. |
| Cached s6 `Makefile:198` | Declares `.DELETE_ON_ERROR`. | This make-level cleanup does not clean the manually written `*.expected` output after a failing runner comparison. |
| Cached s6 repository tracked paths | `git ls-files` reports no `.github/workflows`, `.gitlab-ci.yml`, `.builds`, or `Jenkinsfile`. | No upstream workflow permission model, action pinning, secret exposure, or CI trigger policy is available for review. |

The external checkout was inspected read-only. No Obarun VM/image was booted and
no upstream build or `make check` was run; the current host may not have its
dependency set, and the requested scope is CI hardening. Avoid treating this as
a pass/fail result for s6's test suite.

## Change delivered

Added `autonomy/codex/ci_policy_audit.py`, a dependency-free command-line audit
for GitHub Actions workflows. It flags mutable action references (anything not
pinned to a 40-character commit SHA), write permissions, `pull_request_target`,
and visible secret references combined with pull-request event context. It
reports workflow absence explicitly and returns nonzero when a policy finding
exists. This is a review aid rather than a complete YAML parser or security
proof; the flags require human context, especially for privileged workflows.

Added `autonomy/codex/test_ci_policy_audit.py` with regression IDs:

- `CI-001`: catches mutable action, write permission, and `pull_request_target`.
- `CI-002`: accepts a SHA-pinned action and read-only permission.
- `CI-003`: handles a missing workflow directory distinctly.

The auditor is not installed into the external s6 repository and does not
claim to harden a nonexistent upstream pipeline. It can be used as a gate when
a relevant workflow checkout is available. Recommended next upstream change,
after obtaining the intended Obarun/66 repository and build constraints:
workflow `permissions: {contents: read}` by default, scoped write grants only
on release jobs, full-SHA action pins, fork-safe `pull_request` triggers,
secret-free test jobs, and isolated build/test directories. For s6 itself,
replace the `run-test.sh` command string with direct quoted argv execution and
ensure expected-output cleanup occurs on every exit path.

## Verification

Command: `cd autonomy/codex && python3 -m unittest -v test_ci_policy_audit.py`  
Result: PASS, 3 tests. Output: `autonomy/codex/obarun-66-s6-ci-wave1-test.log`.

Command: `python3 autonomy/codex/ci_policy_audit.py /home/tak_0/.local/state/sunshine-orchestrator/iso/repos/s6`  
Result: `NO_WORKFLOWS`; output: `autonomy/codex/obarun-66-s6-ci-wave1-audit.log`.

Code paths: `autonomy/codex/ci_policy_audit.py`,
`autonomy/codex/test_ci_policy_audit.py`. Source evidence: cached s6
`Makefile:136-139`, `Makefile:198`, and `tools/run-test.sh:3-21`.

Architecture alignment: this records a qualified evidence boundary and leaves
the actual external source unchanged, consistent with AD-04 capability-based
claims, AD-05 observed-state authority, AD-09 constrained execution, and the
mandate's sustainability/reliability priorities.
