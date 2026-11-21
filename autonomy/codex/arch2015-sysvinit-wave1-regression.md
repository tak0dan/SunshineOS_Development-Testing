# Arch 2015 SysV init — Wave 1 regression survey

Date: 2026-11-21  
Scope: repository-grounded catalogue and one discovery regression for stale SysV remnants.

## Catalogue: verified repository state

| Path / symbol | Verified role | Qualification / evidence |
|---|---|---|
| `evolution-engine/src/evolution/recovery.py::RECOVERY_BASELINE_ID` | Names the recovery anchor `B-1-2015`; `RECOVERY_LINEAGE` routes through `M-recovery-bridge` to the Arch 2026 baseline. | This is an architectural anchor, not a captured 2015 machine image. |
| `evolution-engine/src/evolution/recovery.py::RecoveryBridge` | Describes the bridge and carries explicit qualification fields (`independent_toolchain`, artifact manifest hash, supported conditions, `qualified`). | The bridge must be qualified; the anchor alone does not qualify a source. |
| `evolution-engine/evolution/docs/BASELINE_ARCH_2026.md` | Documents the `B-1 -> M bridge -> B0 -> target` recovery path and says discovery must be repeatable/read-only, checkpointed, verified, and recoverable. | Consistent with `reports/ARCHITECTURE_DECISIONS.md` AD-13, AD-14, AD-21. |
| `evolution-engine/src/discovery/system.py::_detect_init_system` | Probes PID 1, systemd runtime signals, SysV `/etc/inittab`, and `init --version`; observations distinguish `RUNNING` from `INSTALLED`. | Wave 1 adjustment gives a named PID 1 precedence over conflicting installed init evidence. Generic `init` remains corroboration-dependent. |
| `evolution-engine/tests/test_discovery.py::DiscoveryTests` | Contains `T-ARCH2015-SYSV-001` (generic `init` + SysV marker/version) and `T-ARCH2015-SYSV-002` (stale inittab under systemd). | Existing fake-root and fake-executor tests; no host command execution. |
| `evolution-engine/tests/test_arch2015_sysvinit.py::Arch2015SysvinitTests` | Adds `T-ARCH2015-SYSV-003`: SysV marker and positive SysV version output cannot override named systemd PID 1. | New focused regression, isolated fake root. |
| `evolution-engine/tests/source-matrix.toml` (`fixture = "arch-five-year-old"`) | Includes an aged Arch source shape. | Its referenced fixture `evolution-engine/fixtures/arch-five-year-old/etc/os-release` identifies old Arch but contains no SysV init artifacts; this is not SysV qualification evidence. |
| `evolution-engine/src/evolution/qualification.py::SourceCapabilities.tier` | Classifies source support by capabilities and qualification tier. | Supports the mandate’s AD-14 principle: age or distro label alone does not imply support. |

## Arch 2015 artifact survey and evidence quality

The earlier catalogue in `autonomy/results/lead-migration-0022.md` enumerates expected source-root paths such as `/etc/inittab`, `/etc/rc.conf`, `/etc/rc.sysinit`, `/etc/rc.d/`, `/etc/conf.d/`, `/etc/fstab`, `/etc/mkinitcpio.conf`, and bootloader files. Those are useful inventory targets, but they are paths inside a hypothetical observed system, not repository files checked into this workspace. The repository has no checked-in Arch 2015 SysV snapshot or materialized `evolution-engine/catalogs/arch-2015-sysvinit/` catalogue at the paths proposed there.

Likewise, `autonomy/results/sub-research-hooks-0023.md` names `autonomy/sandbox/hooks/arch2015/sysvinit/` and `evidence/sysvinit/arch2015/` artifacts and reports VM boot evidence. Those paths are absent from this checkout, so the claimed hooks and VM evidence are not independently verifiable here. Treat its test IDs and dispositions as research claims, not qualified implementation. No unsupported historical source behavior is asserted in this deliverable.

## Change

In `evolution-engine/src/discovery/system.py::_detect_init_system`, a named PID 1 (for example `systemd`) now takes precedence over a competing installed init binary or configuration marker. This closes a scoring edge case where stale `/etc/inittab` plus a SysV `init --version` response could outweigh a directly observed, different PID 1. Generic PID 1 name `init` is not used as an unconditional winner because multiple init implementations use that name; the existing SysV marker corroboration remains required.

Regression ID: `T-ARCH2015-SYSV-003` in `evolution-engine/tests/test_arch2015_sysvinit.py`. The regression confirms status remains `RUNNING` for the directly observed PID 1. Existing test IDs `T-ARCH2015-SYSV-001` and `T-ARCH2015-SYSV-002` also pass.

## Verification and evidence

Command, run from `evolution-engine/`:

```sh
python3 -m unittest tests/test_arch2015_sysvinit.py tests/test_discovery.py
```

Result: **10 tests passed**. Captured output: `autonomy/codex/arch2015-sysvinit-regression-test.log`.

Changed code: `evolution-engine/src/discovery/system.py`  
New regression source: `evolution-engine/tests/test_arch2015_sysvinit.py`  
Survey and change record: `autonomy/codex/arch2015-sysvinit-wave1-regression.md`
