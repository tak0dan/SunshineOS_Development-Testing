# Arch 2015 SysV init — Wave 1 deepening

Date: 2026-11-21  
Scope: repository-backed path catalogue and conservative read-only inventory parsing.

## Path catalogue

All paths below are relative to the development repository unless identified as
paths inside a source installation.

| Exact path / symbol | Verified content and relevance | Evidence status |
|---|---|---|
| `evolution-engine/src/evolution/recovery.py::RECOVERY_BASELINE_ID` | Defines `B-1-2015`; `RECOVERY_LINEAGE` routes through `M-recovery-bridge` and the canonical baseline. | Checked-in recovery model; does not contain a historical disk image. |
| `evolution-engine/src/evolution/recovery.py::RECONSTRUCTION_SPEC` | Defines recovery checks for package management, trust, repositories, package DB, kernel, initramfs, boot, filesystem, services, configuration, OS identity, and final validation. | Checked-in requirements; these are not claims that an Arch 2015 VM passed them. |
| `evolution-engine/evolution/docs/BASELINE_ARCH_2026.md` | Documents `B-1 -> M bridge -> B0 -> target` and recovery constraints. | Checked-in architecture description. |
| `evolution-engine/src/discovery/system.py::_detect_init_system` | Uses PID 1, systemd runtime, init binaries, and marker evidence; SysV needs positive version identification or corroborated generic `init`. | Checked-in observational discovery. |
| `evolution-engine/src/target/compatibility.py::classify_source` | Blocks unsupported init systems from the ordinary Arch transform; the focused test confirms detected SysV is not treated as supported. | Checked-in compatibility path. |
| `evolution-engine/src/discovery/sysvinit.py::parse_rc_conf` | New literal-only parser for `/etc/rc.conf`'s `DAEMONS` array. Records enabled, disabled (`!`), and background (`@`) service intent. It executes no shell and marks dynamic/ambiguous data incomplete. | New implementation in this wave. |
| `evolution-engine/tests/test_sysvinit_inventory.py::SysVInitInventoryTests` | Regression tests for literal markers, shell expansion, absent/duplicate declarations, and duplicate services. | New tests `T-ARCH2015-SYSV-006` through `T-ARCH2015-SYSV-009`. |
| `evolution-engine/tests/test_arch2015_sysvinit.py::Arch2015SysvinitTests` | Tests stale SysV remnants against named PID 1 and blocks SysV from the ordinary transform. | Existing tests `T-ARCH2015-SYSV-004` and `T-ARCH2015-SYSV-005`. |
| `evolution-engine/fixtures/arch-five-year-old/etc/os-release` | Contains old-Arch identity only. | It has no `/etc/inittab`, `/etc/rc.conf`, `/etc/rc.d/`, `/etc/conf.d/`, local package DB, or boot capture; it cannot qualify a SysV source. |

### Historical source paths inventoried by the parser

These are paths expected *inside an observed Arch 2015 installation*, not
files present in this repository: `/etc/rc.conf` (legacy `DAEMONS` declaration),
`/etc/inittab` (SysV init configuration), `/etc/rc.d/` (service scripts),
`/etc/conf.d/` (service configuration), `/etc/rc.local` (local startup hook),
`/etc/fstab` (mount configuration), `/etc/mkinitcpio.conf` (initramfs inputs),
`/var/lib/pacman/local/` (local package database), and `/var/log/pacman.log`
(package history). The parser currently consumes only the literal service list
from `/etc/rc.conf`; it does not infer service behavior from script names.

## Evidence audit

The repository contains no checked-in Arch 2015 SysV image or VM capture. The
paths claimed in `autonomy/results/sub-repair-engine-0024.md`—including
`evidence/sysvinit/`, `autonomy/primitives/snapshot-sysvinit.sh`,
`autonomy/primitives/restore-sysvinit.sh`, and
`evolution-engine/ledger/B0-2015.yaml`—are absent from this checkout. Their
claimed snapshots, hashes, and test results therefore are not source evidence
and are not used to qualify the recovery bridge. The source is still assessment
only pending a real fixture/capture plus bridge and recovery qualification.

## Change and verification

The parser returns data only. It rejects shell expansion, command substitution,
unsupported syntax, duplicate declarations, and duplicate service names as
incomplete observations. This maintains the observed-state boundary from
AD-05/M-04 and does not turn a historical `DAEMONS` list into an execution
plan.

Command, run from `evolution-engine/`:

```sh
python3 -m unittest tests/test_sysvinit_inventory.py tests/test_arch2015_sysvinit.py tests/test_discovery.py
```

Result: **15 tests passed**. Output: `autonomy/codex/arch2015-sysvinit-wave1-deepening-test.log`.

Test IDs: `T-ARCH2015-SYSV-006`–`T-ARCH2015-SYSV-009`, alongside existing
`T-ARCH2015-SYSV-004` and `T-ARCH2015-SYSV-005`.
