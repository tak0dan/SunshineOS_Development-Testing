# codex-lead / regression tests / Arch 2015 sysvinit

- Agent: codex-lead
- Model: gpt-6-luna
- Parent directive: none
- Completed: 2026-11-21 02:22

---

## Arch 2015 SysV init — Wave 1

Added a focused discovery fix: a named PID 1 now takes precedence over stale SysV configuration or installed init binaries. Added regression **T-ARCH2015-SYSV-003** and catalogued verified repository paths, while flagging prior research artifacts that are absent from this checkout.

- Survey and change record: [arch2015-sysvinit-wave1-regression.md](/home/tak_0/sunshineos-audit/SunshineOS_Development-Testing/autonomy/codex/arch2015-sysvinit-wave1-regression.md)
- Discovery change: [system.py](/home/tak_0/sunshineos-audit/SunshineOS_Development-Testing/evolution-engine/src/discovery/system.py:205)
- Regression test: [test_arch2015_sysvinit.py](/home/tak_0/sunshineos-audit/SunshineOS_Development-Testing/evolution-engine/tests/test_arch2015_sysvinit.py:17)
- Test evidence: [arch2015-sysvinit-regression-test.log](/home/tak_0/sunshineos-audit/SunshineOS_Development-Testing/autonomy/codex/arch2015-sysvinit-regression-test.log) — **10 tests passed**, including existing IDs `T-ARCH2015-SYSV-001` and `T-ARCH2015-SYSV-002`.

I could not commit: the workspace’s `.git` index is read-only, so Git rejected creating `.git/index.lock`. I left other agents’ modified files untouched.
