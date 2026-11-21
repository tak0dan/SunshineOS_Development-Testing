# codex-lead-0010 -> hierarchy

# Artix runit/OpenRC — Wave 1

The survey and verification are in [the catalogue]( /home/tak_0/sunshineos-audit/SunshineOS_Development-Testing/autonomy/codex/artix-runit-openrc-wave1-verification.md ) and [test log]( /home/tak_0/sunshineos-audit/SunshineOS_Development-Testing/autonomy/codex/artix-runit-openrc-wave1-verified-test.log ).

The checkout contains an argv-only planner at `evolution-engine/src/evolution/tools/artix_services.py::plan_artix_service`, exported by `evolution-engine/src/evolution/tools/__init__.py`. Its regressions are `ARTIX_SVC_001`–`ARTIX_SVC_004` in `evolution-engine/tests/test_artix_services.py`. The targeted suite passed **4 tests**; the full migration-engine suite passed **169 tests**.

The local ISO manifest lists Artix OpenRC and dinit media, but no runit image. Accordingly, the runit planner’s path contract is not claimed as distro-qualified behavior.

I did not modify the shared planner or tests because they are already present amid other worktree changes. I could not commit my two new evidence files: Git reported `.git/index.lock: Read-only file system`. They remain uncommitted under `autonomy/codex/`.
