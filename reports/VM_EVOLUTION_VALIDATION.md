# VM validation: evolutionary migration subsystem

Date: 2026-11-20
VM: `SunshineOS-Audit` (running, UEFI/OVMF, 4 CPU, 6144 MB)
Artifact under test: DevTesting commit `f3f8129`
Guest path: `/tmp/eve/evolution-engine`, state root `/tmp/eve-state`
Evidence: `reports/screenshots/vm-evolution-validation-2026-11-20.png`

## Procedure

```sh
# host
tar --exclude-vcs --exclude='__pycache__' -czf /tmp/evolution-engine.tar.gz evolution-engine
VBoxManage guestcontrol SunshineOS-Audit --username sunshine --password 111 \
  copyto /tmp/evolution-engine.tar.gz /tmp/evolution-engine.tar.gz
```

Inside the guest, `/tmp/eve` and `/tmp/eve-state` were cleaned, the tarball was
extracted, and the following checks were run.

## Results

| Check | Result |
|---|---|
| Extracted module inventory | `artifacts.py`, `baseline.py`, `compatibility.py`, `hooks.py`, `invariants.py`, `repository.py`, `updater.py`, `tools/`, etc. present |
| `python3 -m unittest discover -s tests` | `Ran 161 tests ... OK` |
| `src/milestone_cli.py --milestones` | current `0.9`; aliases `vanilla-arch`, `arch-2026-baseline-01`, `sunshine-2026.1`, `old-sunshine` |
| `src/milestone_cli.py --from 0 --upgrade-to 0.9 --dry-run` | `ok: true`, chain `["0.9"]`, full 64-char journal id, preconditions validated |
| `src/engine.py --state-root /tmp/eve-state --apply --decide desktop-profile=hyprland` | `status success`, `errors []`, `journal_status completed` |
| Immediate `--verify` | all probes passed |
| Repeat `--apply` | converged; third consecutive apply reported `status success`, `changed false`, `errors []` |
| `--verify` summary | `passed True`, `reports 18` |
| Tamper: move `migration/checkpoints` away | `passed False`; only failing capability: `recovery-checkpoints` |
| Restore checkpoints and re-verify | `passed True`, `reports 18` |
| `vm_updater_check.py` rollback injection | `rollback_ok true`, `journal_state RolledBack`, `restore_calls ["checkpoint-ref"]` |
| `vm_updater_check.py` checkpoint tamper guard | `guard_no_rollback true`; restore was not called |
| `vm_updater_check.py` digest length | `full_digest true` |

## Notes

- The live guest sudo authentication currently accepts the guest account's own
  password; an earlier note in the project history naming a different sudo
  password was stale. No credential value is recorded here.
- The first convergence pass performed mutations; a later pass still showed
  `changed true`, and the following pass showed `changed false`. Follow-up on a
  clean state root in the same VM showed `changed true` on the first apply and
  `changed false` on both the second and third applies, so the earlier two-pass
  result came from the intervening tamper/restore and rollback-injection tests,
  not from steady-state convergence. `tests/test_cli.py` now asserts three
  consecutive applies: first may change, later ones must be no-ops.
- The checkpoint-tamper guard is now demonstrated both in the unit suite and in
  the live VM via an injected `checkpoint_verify_fn`.

## Conclusion

The published evolutionary subsystem passes its full Python suite in the VM,
resolves and previews the `0 -> 0.9` milestone chain, applies with the operator
desktop decision, verifies 18 capabilities, detects checkpoint tampering,
recovers after restoration, and refuses rollback when checkpoint integrity fails.
