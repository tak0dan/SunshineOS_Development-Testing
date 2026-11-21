# codex-lead-0018 -> hierarchy

## Arch 2015 SysV init integration — Wave 1

Added `T-ARCH2015-SYSV-003` to [test_compatibility.py](/home/tak_0/sunshineos-audit/SunshineOS_Development-Testing/evolution-engine/tests/test_compatibility.py). It verifies SysV is blocked from ordinary transformation and that recovery follows `B-1-2015 → M-recovery-bridge → BASELINE_ID → target`.

The path survey and qualification limits are in [arch2015-sysvinit-integration-wave1.md](/home/tak_0/sunshineos-audit/SunshineOS_Development-Testing/autonomy/codex/arch2015-sysvinit-integration-wave1.md). Test evidence is in [arch2015-sysvinit-integration-wave1-test.log](/home/tak_0/sunshineos-audit/SunshineOS_Development-Testing/autonomy/codex/arch2015-sysvinit-integration-wave1-test.log).

**Verification:** `python3 -m unittest tests.test_discovery tests.test_compatibility` — 24 tests passed, including `T-ARCH2015-SYSV-001/002/003`.

The existing aged-Arch fixture does not contain a SysV snapshot, so Arch 2015 SysV recovery remains unqualified. I could not commit these files: Git failed to create `.git/index.lock` because the filesystem is read-only.
