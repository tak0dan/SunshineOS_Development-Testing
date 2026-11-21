# Arch 2015 SysV init — Wave 1 survey and code

Date: 2026-11-21  
Scope: repository-grounded survey of the Arch 2015 SysV init recovery lineage, exact paths, and a focused discovery correction.

## Verified repository catalogue

| Repository path | Verified role / finding |
|---|---|
| `evolution-engine/src/evolution/recovery.py::RECOVERY_BASELINE_ID` | Defines the `B-1-2015` recovery anchor and lineage model. |
| `evolution-engine/evolution/docs/BASELINE_ARCH_2026.md` | Documents `B-1 (Arch 2015) -> M bridge -> B0 (Arch 2026) -> target`; the bridge is the supported semantic boundary. |
| `evolution-engine/src/discovery/system.py::_detect_init_system` | Root-scoped init discovery; now recognizes SysV runtime evidence without letting a stale `/etc/inittab` defeat stronger runtime evidence. |
| `evolution-engine/tests/test_discovery.py::DiscoveryTests` | Fake-root/fake-executor regression coverage; test IDs `T-ARCH2015-SYSV-001` and `T-ARCH2015-SYSV-002` added. |
| `evolution-engine/tests/source-matrix.toml` | Source-state qualification matrix includes `arch-five-year-old`, but its fixture is not a SysV snapshot. |
| `evolution-engine/fixtures/arch-five-year-old/etc/os-release` | Existing old-Arch fixture identifies an old Arch state only; it does not contain `etc/inittab`, `rc.conf`, package DB, or captured SysV service state. |
| `evolution-engine/src/evolution/qualification.py::SourceCapabilities` | Qualification tier is capability-based; age alone does not establish support. |
| `reports/USER_MIGRATION_MANDATE_2026-11-21.md` | User architecture mandate: long-term target-state migration, qualify old states, and preserve recovery. |
| `reports/ARCHITECTURE_DECISIONS.md` AD-13 / AD-14, M-04 / M-06 / M-08 | Arch 2015 recovery goes through a qualified bridge; observed state is authoritative; operations recoverable; support must be qualified. |

## Audit of inherited catalogue

`autonomy/results/sub-repair-engine-0024.md` claims a repository snapshot and restore primitive are ready. That claim is not supported by checked-in files. The referenced `evidence/sysvinit/`, `autonomy/primitives/snapshot-sysvinit.sh`, `autonomy/primitives/restore-sysvinit.sh`, and `evolution-engine/ledger/B0-2015.yaml` paths are absent. The report's restore pseudocode also treats a compressed tar archive as an individual file source, so it cannot implement the described restore. I did not execute it or create those paths.

Arch 2015 here is represented as a recovery anchor and transition lineage, not as a complete captured image of `/etc/inittab`, `/etc/rc.conf`, `DAEMONS`, `rc.local`, package database, or mkinitcpio configuration. Consequently this work does not claim that such historical state has been empirically qualified.

## Change

`_detect_init_system` in `evolution-engine/src/discovery/system.py` previously scored `/etc/inittab` as SysV evidence by itself, and only recognized an init CLI when the process name included the init-system name. A stale inittab could pollute migrated state; the generic SysV PID 1 name `init` did not convey runtime status. Discovery now gives SysV positive weight when `init --version` identifies `sysvinit`, or when PID 1 is `init` and the rooted `/etc/inittab` exists. A marker alone remains weak and cannot override the running systemd signals.

Regression cases:

- `T-ARCH2015-SYSV-001`: generic `init` PID 1 plus inittab and positive SysV version output is reported as running `sysvinit`.
- `T-ARCH2015-SYSV-002`: stale inittab on a systemd system does not override runtime systemd.

## Verification and evidence

Command (from `evolution-engine/`): `python3 -m unittest tests/test_discovery.py`

Result: **9 tests passed**. Captured output: `autonomy/codex/arch2015-sysvinit-wave1-test.log`.

Changed implementation: `evolution-engine/src/discovery/system.py`  
Regression source: `evolution-engine/tests/test_discovery.py`  
This survey: `autonomy/codex/arch2015-sysvinit-wave1.md`
