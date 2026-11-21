# Solutions

# Omarchy CI hardening — Wave 1

Added `CI_DOCKER_IMAGE_MUTABLE` to [ci_policy.py](/home/tak_0/sunshineos-audit/SunshineOS_Development-Testing/evolution-engine/src/evolution/tools/ci_policy.py). It flags untagged or `:latest` images in `docker run` commands, including shell continuations. Regression tests **CI_OMARCHY_001** and **CI_OMARCHY_002** cover mutable, version-tagged, and digest-pinned images in [test_ci_policy.py](/home/tak_0/sunshineos-audit/SunshineOS_Development-Testing/evolution-engine/tests/test_ci_policy.py).

The survey catalogues five Omarchy CI files with SHA-256 hashes and findings in [omarchy-ci-hardening-wave1.md](/home/tak_0/sunshineos-audit/SunshineOS_Development-Testing/autonomy/codex/omarchy-ci-hardening-wave1.md). It identifies the mutable `ghcr.io/archlinux/archlinux:latest` image in `.github/workflows/test.yml`; the workflow verifies the VM disk hash but not the downloaded kernel, initrd, or cmdline individually.

**Verification:** From `evolution-engine/`, ran `python3 -m unittest tests.test_ci_policy -v` — **5 tests passed**. Log: [omarchy-ci-wave1-test.log](/home/tak_0/sunshineos-audit/SunshineOS_Development-Testing/autonomy/codex/omarchy-ci-wave1-test.log). Pull notes: [codex-lead-omarchy-ci-wave1](/home/tak_0/sunshineos-audit/SunshineOS_Development-Testing/autonomy/pull/codex-lead-omarchy-ci-wave1/).

I did not commit: the auditor and test files were already untracked in the shared worktree, so committing them would also include pre-existing work.
