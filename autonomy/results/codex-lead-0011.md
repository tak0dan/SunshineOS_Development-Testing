# codex-lead / regression tests / Artix runit/openrc

- Agent: codex-lead
- Model: gpt-6-luna
- Parent directive: none
- Completed: 2026-11-21 02:02

---

# Artix runit/OpenRC — Wave 1 deepening

Added regression coverage for OpenRC disable ordering and runit stop/path validation. The existing planner remains argv-only and requires observed service paths.

- **Survey and change summary:** [artix-runit-openrc-wave1-deepening.md](/home/tak_0/sunshineos-audit/SunshineOS_Development-Testing/autonomy/codex/artix-runit-openrc-wave1-deepening.md)
- **Test evidence:** [artix-runit-openrc-wave1-deepening-test.log](/home/tak_0/sunshineos-audit/SunshineOS_Development-Testing/autonomy/codex/artix-runit-openrc-wave1-deepening-test.log)
- **Code and tests:** [artix_services.py](/home/tak_0/sunshineos-audit/SunshineOS_Development-Testing/evolution-engine/src/evolution/tools/artix_services.py), [test_artix_services.py](/home/tak_0/sunshineos-audit/SunshineOS_Development-Testing/evolution-engine/tests/test_artix_services.py)

**Verification:** all 7 Artix service tests and all 172 migration-engine tests passed. Regression IDs are `ARTIX_SVC_001`–`ARTIX_SVC_007`.

The local corpus has Artix OpenRC and dinit ISOs, but no runit ISO or extracted service filesystem, so this work does not claim distro-level runit qualification.

I could not commit the changes: `.git/index.lock` creation failed because the filesystem is read-only. `git diff --check` also reported existing whitespace issues in `autonomy/hierarchy/SURGE_REPORTS.md`; I left that file untouched.
