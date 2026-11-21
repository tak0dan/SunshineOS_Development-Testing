# Arch 2015 SysV repair tooling — Wave 1

Date: 2026-11-21  
Scope: repository-grounded catalogue and a fail-closed, read-only repair assessment for historical Arch SysV service scripts.

## Exact path catalogue

| Path / symbol | Role and evidence |
|---|---|
| `evolution-engine/src/evolution/tools/sysvinit_repair.py::assess_sysv_services` | New read-only repair assessment. Compares complete historical `DAEMONS` observations and explicitly required services with regular files below the supplied root's `etc/rc.d`; blocks incomplete inventory and root escapes; always returns an empty command list. |
| `evolution-engine/src/discovery/sysvinit.py::parse_rc_conf`, `SysVServiceInventory` | Literal-only parser for Arch `/etc/rc.conf` `DAEMONS`; preserves enabled, disabled, and background markers and rejects ambiguous input. |
| `evolution-engine/src/evolution/tools/service_supervision.py::ServiceSupervisor.plan` | Existing planner supports systemd command plans; 66/s6 (and SysV) must not be inferred into executable behavior from service names. `validate_coverage` rejects plans lacking a qualified adapter. |
| `evolution-engine/src/evolution/recovery.py::RECONSTRUCTION_SPEC`, `RecoveryBridge` | Recovery requirements and bridge qualification checks; these model required reconstruction checks, not proof of a qualified Arch 2015 recovery run. |
| `evolution-engine/src/discovery/system.py::_detect_init_system`, `evolution-engine/src/target/compatibility.py::classify_source` | Runtime init detection and ordinary-transform compatibility boundary; detected SysV does not qualify for the ordinary Arch migration transform. |
| `evolution-engine/tests/test_sysvinit_repair.py::SysVInitRepairTests` | New regressions `T-ARCH2015-SYSV-010` through `T-ARCH2015-SYSV-012`. |
| `evolution-engine/tests/test_sysvinit_inventory.py::SysVInitInventoryTests` | Inventory regressions `T-ARCH2015-SYSV-006` through `T-ARCH2015-SYSV-009`. |
| `evolution-engine/tests/test_arch2015_sysvinit.py::Arch2015SysvinitTests` | Regression coverage `T-ARCH2015-SYSV-004` and `T-ARCH2015-SYSV-005` for runtime evidence and compatibility blocking. |
| `evolution-engine/fixtures/arch-five-year-old/etc/os-release` | Old-Arch identity fixture only. It has no captured SysV configuration, service scripts, package database, or boot state. |

Historical paths expected inside an actual installation include `/etc/rc.conf`, `/etc/inittab`, `/etc/rc.d/`, `/etc/conf.d/`, `/etc/rc.local`, `/etc/fstab`, `/etc/mkinitcpio.conf`, `/var/lib/pacman/local/`, and `/var/log/pacman.log`. This checkout does not contain an Arch 2015 SysV machine capture. These paths describe source-system inputs; they are not present repository artifacts or empirical evidence.

## Repair behavior

`assess_sysv_services` reports required or enabled service script files that are absent. It does not execute legacy scripts, write configuration, or invent replacements. Incomplete `DAEMONS` data yields a blocker without probing. Symlinks resolving outside the observed root are blocked. A clean result means only that expected script files exist; it does not verify their content, dependencies, runtime health, package ownership, or boot behavior, and it does not qualify the recovery bridge. A mutation-capable repair adapter still requires a checkpoint, a provenance-backed source capture, semantic transition rules, and independent qualification.

This remains aligned with the mandate and `reports/ARCHITECTURE_DECISIONS.md`: AD-05/M-04 observed state is authoritative; AD-11/M-06 operations need recovery; AD-13 routes Arch 2015 through a bridge; AD-14/M-08 support is qualified, not presumed.

## Verification

From `evolution-engine/`:

```sh
python3 -m unittest tests/test_sysvinit_repair.py tests/test_sysvinit_inventory.py tests/test_arch2015_sysvinit.py
```

Result: **9 tests passed**. Evidence: `autonomy/codex/arch2015-sysvinit-repair-wave1-test.log`.

New test IDs:

- `T-ARCH2015-SYSV-010`: reports missing required scripts without proposing commands.
- `T-ARCH2015-SYSV-011`: incomplete service inventory blocks assessment.
- `T-ARCH2015-SYSV-012`: service symlink outside the observed root is blocked.

## Changed files

- `evolution-engine/src/evolution/tools/sysvinit_repair.py`
- `evolution-engine/tests/test_sysvinit_repair.py`
- `autonomy/codex/arch2015-sysvinit-repair-wave1.md`
- `autonomy/codex/arch2015-sysvinit-repair-wave1-test.log`
