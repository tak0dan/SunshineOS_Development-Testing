# CachyOS CI hardening — Wave 1

## Scope and grounding

Read `reports/USER_MIGRATION_MANDATE_2026-11-21.md` and `reports/ARCHITECTURE_DECISIONS.md`. This work applies AD-04/05 (capability and observed-state reasoning), AD-09 (safe command boundaries), and AD-14 (qualification over assumption). The cached source is `/home/tak_0/.local/state/sunshine-orchestrator/iso/repos/cachyos-tools`, commit `97a55536e5f756d22199f043de4aa1a0d8eebc8a`. The checkout was read only; no CI job or package build was run.

## Exact CI catalogue and findings

| Cached source path | Verified CI behavior | Hardening consequence |
|---|---|---|
| `/home/tak_0/.local/state/sunshine-orchestrator/iso/repos/cachyos-tools/.github/workflows/check-pkg-ver.yml:5-15` | Scheduled/manual workflow grants `secrets.GITHUB_TOKEN` to the job and runs `.github/scripts/checker.sh --ci`; checkout is referenced as `actions/checkout@v6`, with no explicit permissions block. | Scope token permissions to the minimum required issue operations and pin the checkout action to a reviewed commit SHA. |
| `/home/tak_0/.local/state/sunshine-orchestrator/iso/repos/cachyos-tools/.github/scripts/checker.sh:10-23,139-150` | Bash enables `nounset`, `errexit`, and `pipefail`, reads token and repository from environment, and constructs the API URL from `GITHUB_REPO`. CI discovers `.nvchecker.toml` files with `find` and unquoted word splitting. | Constrain repository identity and use null-delimited file traversal/arrays; retain the existing required-environment checks. The workflow itself does not expose a token value in this report. |
| `/home/tak_0/.local/state/sunshine-orchestrator/iso/repos/cachyos-tools/.github/workflows/makepkg.yml:16-26,55-84` | PR-only build uses two `actions/checkout@v4` references; the build image is `cachyos/cachyos:latest`; it adds `builder ALL=(ALL) NOPASSWD: ALL`; `makepkg` uses `--skippgpcheck`. No explicit permissions block is declared. | Pin actions and image; set read-only token permissions; avoid unrestricted sudo and do not bypass PGP checks in CI. If signatures cannot be checked, fail with an explicit qualification gap. |
| `/home/tak_0/.local/state/sunshine-orchestrator/iso/repos/cachyos-tools/.github/workflows/validate-pkgbuilds.yml:1-29` | Push/PR/manual validation uses `actions/checkout@v6`, mutable `cachyos/cachyos:latest`, installs `namcap` and `bun`, and has no explicit permissions block. | Pin executable inputs and minimize token permissions for the validation job. |
| `/home/tak_0/.local/state/sunshine-orchestrator/iso/repos/cachyos-tools/.github/scripts/validate-pkgbuilds.js:10-17,46-53` | Changed paths are passed to `git diff` via Bun's tagged command template; `namcap` is invoked with an argument array through the same API. | Keep structured argv invocation and retain command failures as CI failures. Validate paths derived from event SHAs before using them. |

The dependency-free audit implemented in `evolution-engine/src/evolution/tools/ci_policy.py` reports the current workflow-level findings at exact line numbers in [the audit evidence](cachyos-ci-hardening-audit.log). It checks for absent permissions, mutable action refs, mutable/unpinned containers, privileged `pull_request_target`, unrestricted passwordless sudo, and disabled PGP checks. It is a bounded text audit, not a complete YAML or shell parser.

## SunshineOS implementation

Added a read-only policy helper and three regression cases:

- `CI_CACHYOS_001`: mutable action/image and package-build bypass conditions are detected.
- `CI_CACHYOS_002`: privileged PR trigger is reported.
- `CI_CACHYOS_003`: a full action SHA and image digest pass the policy.

Source: `evolution-engine/src/evolution/tools/ci_policy.py`  
Tests: `evolution-engine/tests/test_ci_policy.py`  
Test output: `autonomy/codex/cachyos-ci-hardening-test.log`

## Verification

Command, run from `evolution-engine/`:

```sh
python3 -m unittest tests/test_ci_policy.py -v
```

Result: **Ran 3 tests — OK.** The cached workflows were separately passed through the same audit; its full output is `autonomy/codex/cachyos-ci-hardening-audit.log`.

## Qualification boundary

The audit identifies review conditions, not exploitability. It does not validate effective GitHub token permissions, action contents, container provenance, YAML semantics, package signature keyrings, or runtime behavior. Remediation must be made and exercised in the CachyOS upstream repository by its maintainers; this increment changes only SunshineOS code and documentation.
