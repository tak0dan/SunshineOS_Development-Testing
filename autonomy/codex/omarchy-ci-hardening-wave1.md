# Omarchy CI hardening — Wave 1

Date: 2026-11-21  
Upstream snapshot: `basecamp/omarchy`, commit `e4635a4eea887d5c8dbd70427386f570c37a2a61`, clean cached checkout at `/home/tak_0/.local/state/sunshine-orchestrator/iso/repos/omarchy`.

## CI source catalogue

SHA-256 digests below were computed from the cached checkout at the pinned commit.

| Exact upstream path | SHA-256 | Observation | SunshineOS control |
|---|---|---|---|
| `.github/workflows/test.yml` | `44c59b45a74ed968ba6e47c9533bf66f3165f6a1228f91ac68486c9185f9f39b` | Read-only workflow permissions; checkout actions pinned to full commit; checkout credentials disabled. The downloaded VM disk is checked against its metadata digest. `docker run` uses `ghcr.io/archlinux/archlinux:latest` (line 71), which can change between runs. Kernel, initrd and cmdline downloads are not checked against per-file hashes in this workflow. | Pin execution images to a version or digest; verify each boot artifact independently before using it. Avoid treating the VM disk checksum as verification of the other downloaded files. |
| `.github/workflows/i18n-sync.yml` | `954d642565a17ff1c525b76f092bcefdb7e21ec30d31d59974b42ad3db8704e0` | Splits preparation/translation/validation/publication; the comments explicitly keep validation credential-free and separate the publishing job. The Muse launcher is downloaded then checked against a literal SHA-256 before execution. | Separate untrusted/generated content validation from privileged publication. Pin downloaded executable bytes and keep credentials out of validation jobs. |
| `.github/workflows/i18n-check.yml` | `f0de2f9a5a606353fa47359c7c57a32b2121bee8feba62d2f6ebe3fcf8f9ef73` | Pull request structural checks use read-only permissions and bounded execution time. It is path-filtered and documents why it must not be made a required status check in that form. | Ensure required checks cannot be skipped by path filters; use a job condition when checks must remain required. |
| `.github/workflows/visual-evidence.yml` | `052fda5b08401b31917780ec47026dd475eac1fc750dec054a5f0f2aa002866a` | Non-required review aid with read-only permissions; only reads the pull request body and has a short timeout. | Keep advisory review automation non-privileged and keep it separate from merge-critical checks. |
| `test/ci-vm` | `272662dab9ffcf651a85697447c6edcf0ff886cde8646191635c9f15991e20ad` | VM test runner invoked by `test.yml`; workflow runs it inside the downloaded Omarchy image and retains test output on failures. | Treat externally sourced VM inputs and guest state as test data; require explicit validation before they can affect trusted build or release state. |

## Implemented control

Added `CI_DOCKER_IMAGE_MUTABLE` to `evolution-engine/src/evolution/tools/ci_policy.py::audit_workflow`. It checks `docker run` commands after joining shell line continuations and reports an untagged image or `:latest`; version tags and content digests pass. The check is scoped to docker execution commands so unrelated image references do not trigger it.

Regression tests:

- `CI_OMARCHY_001` — mutable image on a continued `docker run` command is reported at the command's first line.
- `CI_OMARCHY_002` — version-tagged and digest-pinned images are accepted.

These controls align with mandate priorities for stable, verifiable evolution and architecture AD-06 (fail-closed verification), AD-09 (reproducible and constrained execution), and AD-19/20 (qualified releases and durable artifacts). The auditor remains a narrow text scanner, not a complete GitHub Actions YAML or shell parser; findings require review in workflow context.

## Verification

Exact command from `evolution-engine/`:

```text
python3 -m unittest tests.test_ci_policy -v
```

Exact result: 5 tests passed (`CI_CACHYOS_001`–`003`, `CI_OMARCHY_001`–`002`). Captured evidence: `autonomy/codex/omarchy-ci-wave1-test.log`.
