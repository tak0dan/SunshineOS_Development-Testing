# codex-lead-0038 -> hierarchy

# EndeavourOS repair-tool survey — Wave 1

I surveyed EndeavourOS repair-related tools and added a read-only SunshineOS assessment for pending pacman configuration files.

## Survey

The upstream [`eos-bash-shared` README](https://github.com/endeavouros-team/eos-bash-shared) lists:

- `eos-pacdiff`, which wraps `pacdiff` to review configuration candidates. Its [source](https://github.com/endeavouros-team/eos-bash-shared/blob/main/eos-pacdiff#L629) includes a warning about sensitive account files; it also supports backups and invokes `pacdiff -s` ([source](https://github.com/endeavouros-team/eos-bash-shared/blob/main/eos-pacdiff#L699)).
- `eos-update`, a pacman updater with optional yay support.
- `paccache-service-manager`, which manages the package-cache service.

The ISO’s compressed live root, `/arch/x86_64/airootfs.sfs`, was not extracted. The survey therefore does not establish which tools are present in that image or qualify repair on an installed EndeavourOS system.

## Changes and regression evidence

Added [config_drift.py](/home/tak_0/sunshineos-audit/SunshineOS_Development-Testing/evolution-engine/src/evolution/tools/config_drift.py), which inventories regular `.pacnew` and `.pacsave` files under `/etc`, flags sensitive configuration for manual review, and reports missing configuration roots as incomplete. It does not modify files or follow symlinks.

Added [test_config_drift.py](/home/tak_0/sunshineos-audit/SunshineOS_Development-Testing/evolution-engine/tests/test_config_drift.py) with:

- `T-EOS-REPAIR-001`: classifies candidates without modifying configuration.
- `T-EOS-REPAIR-002`: treats an absent configuration root as incomplete.
- `T-EOS-REPAIR-003`: does not follow symlinks.

Command: `python3 -m unittest tests.test_config_drift tests.test_package_health` from `evolution-engine/`  
Result: **6 tests passed**. Log: [endeavouros-wave1-repair-test.log](/home/tak_0/sunshineos-audit/SunshineOS_Development-Testing/autonomy/codex/endeavouros-wave1-repair-test.log).

The full survey and change record is in [endeavouros-wave1-repair.md](/home/tak_0/sunshineos-audit/SunshineOS_Development-Testing/autonomy/codex/endeavouros-wave1-repair.md).

I could not commit: Git could not create `.git/index.lock` because the index is read-only. The four task files remain in the worktree.
