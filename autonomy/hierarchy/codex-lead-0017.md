# codex-lead-0017 -> hierarchy

## Arch 2015 SysV init — Wave 1

Surveyed the repository’s Arch 2015 recovery lineage and verified the paths against the source. The existing old-Arch fixture is not a SysV snapshot, and the snapshot/restore scripts and ledger paths claimed by `autonomy/results/sub-repair-engine-0024.md` are absent. The report’s restore example also cannot extract individual files from the archive as written.

Updated [`system.py`](/home/tak_0/sunshineos-audit/SunshineOS_Development-Testing/evolution-engine/src/discovery/system.py) so SysV detection requires affirmative runtime evidence and a stale `/etc/inittab` cannot outweigh running systemd. Added regression cases in [`test_discovery.py`](/home/tak_0/sunshineos-audit/SunshineOS_Development-Testing/evolution-engine/tests/test_discovery.py):

- `T-ARCH2015-SYSV-001`: recognizes SysV when PID 1 is `init` and the rooted evidence supports it.
- `T-ARCH2015-SYSV-002`: stale `inittab` does not override systemd.

The focused discovery suite passed: **9 tests**. Output is recorded in [`arch2015-sysvinit-wave1-test.log`](/home/tak_0/sunshineos-audit/SunshineOS_Development-Testing/autonomy/codex/arch2015-sysvinit-wave1-test.log). The catalogue and audit notes are in [`arch2015-sysvinit-wave1.md`](/home/tak_0/sunshineos-audit/SunshineOS_Development-Testing/autonomy/codex/arch2015-sysvinit-wave1.md).

I did not commit: both modified code and test files contain concurrent edits from another agent, so committing those whole files risks including work outside this task. `git diff --check` passed.
