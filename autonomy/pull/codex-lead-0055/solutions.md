# Solutions

## CachyOS CI hardening — Wave 1

Added a read-only CI policy auditor at [ci_policy.py](/home/tak_0/sunshineos-audit/SunshineOS_Development-Testing/evolution-engine/src/evolution/tools/ci_policy.py) and regression tests `CI_CACHYOS_001`–`003` in [test_ci_policy.py](/home/tak_0/sunshineos-audit/SunshineOS_Development-Testing/evolution-engine/tests/test_ci_policy.py).

The survey catalogs exact CachyOS workflow and script paths, observed risks, and qualification limits in [cachyos-ci-hardening-wave1.md](/home/tak_0/sunshineos-audit/SunshineOS_Development-Testing/autonomy/codex/cachyos-ci-hardening-wave1.md). The audit flagged unpinned actions and missing permissions declarations across all three workflows; it also flagged `:latest`, unrestricted builder sudo, and `--skippgpcheck` in `.github/workflows/makepkg.yml`. Detailed findings are in [cachyos-ci-hardening-audit.log](/home/tak_0/sunshineos-audit/SunshineOS_Development-Testing/autonomy/codex/cachyos-ci-hardening-audit.log).

**Verification** from `evolution-engine/`:

```sh
python3 -m unittest tests/test_ci_policy.py -v
```

Result: **Ran 3 tests — OK.** Output: [cachyos-ci-hardening-test.log](/home/tak_0/sunshineos-audit/SunshineOS_Development-Testing/autonomy/codex/cachyos-ci-hardening-test.log).

Task notes are in [autonomy/pull/codex-lead-0055](/home/tak_0/sunshineos-audit/SunshineOS_Development-Testing/autonomy/pull/codex-lead-0055). The cached CachyOS checkout and `reports/` were left unchanged. I could not commit: Git could not create `.git/index.lock` because `.git` is read-only in this workspace.
