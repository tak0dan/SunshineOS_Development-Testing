# Solutions

## Arch 2026 systemd regression survey

Added six regression cases, **T-ARCH2026-SYSTEMD-007 through -012**, covering duplicate and unknown rows, enabled aliases, masked-runtime units, absent targets, and invalid desired states. The inventory remains read-only and blocks assessment when evidence is incomplete.

The suite passed: **12 tests**. The survey distinguishes verified repository behavior from upstream Arch details that remain unverified.

- [Survey and change summary](</home/tak_0/sunshineos-audit/SunshineOS_Development-Testing/autonomy/codex/arch2026-systemd-wave1-regression.md>)
- [Regression tests](</home/tak_0/sunshineos-audit/SunshineOS_Development-Testing/evolution-engine/tests/test_systemd_inventory.py>)
- [Test log](</home/tak_0/sunshineos-audit/SunshineOS_Development-Testing/autonomy/codex/arch2026-systemd-wave1-regression-test.log>)

I couldn’t commit: `.git` is read-only in this workspace, and staging failed because Git could not create `.git/index.lock`.
