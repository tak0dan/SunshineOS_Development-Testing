# Arch 2015 SysV init integration — Wave 1

Date: 2026-11-21  
Scope: repository-grounded path survey and integration boundary tests for the Arch 2015 recovery anchor. No historical ISO or machine snapshot was treated as captured evidence.

## Path catalogue

| Exact repository path / symbol | Role and verified status |
|---|---|
| `evolution-engine/src/discovery/system.py::_detect_init_system` | Discovers actual init using PID 1, runtime systemd signals, root-scoped markers, and `init --version`. SysV recognition is explicit; `/etc/inittab` alone cannot claim running SysV. |
| `evolution-engine/tests/test_discovery.py::DiscoveryTests.test_arch_2015_sysvinit_pid1_is_identified_from_runtime_and_marker` | `T-ARCH2015-SYSV-001`; fake-root runtime SysV identification. |
| `evolution-engine/tests/test_discovery.py::DiscoveryTests.test_stale_inittab_does_not_override_running_systemd` | `T-ARCH2015-SYSV-002`; stale legacy marker does not defeat active systemd. |
| `evolution-engine/src/target/compatibility.py::classify_source` | Ordinary Arch transformation blocks any non-systemd init, including SysV. This preserves fail-closed behavior; a positive discovery result does not authorize the ordinary systemd-target transformer. |
| `evolution-engine/tests/test_compatibility.py::CompatibilityTests.test_arch_2015_sysvinit_requires_recovery_bridge` | `T-ARCH2015-SYSV-003`; checks SysV is blocked in ordinary transformation and points the recovery lineage through the bridge to the actual `BASELINE_ID`. |
| `evolution-engine/src/evolution/recovery.py::RECOVERY_BASELINE_ID`, `BRIDGE_ID`, `recovery_path` | Recovery lineage: `B-1-2015 -> M-recovery-bridge -> BASELINE_ID -> target`. The bridge is an architecture boundary, not evidence that an Arch 2015 SysV image has been empirically qualified. |
| `evolution-engine/src/evolution/recovery.py::RECONSTRUCTION_SPEC` | Lists semantic reconstruction requirements for package management, trust, repositories, package DB, kernel, initramfs, boot, filesystem, services, configuration, identity and validation. |
| `evolution-engine/tests/source-matrix.toml` (`fixture = "arch-five-year-old"`) | Existing aged Arch qualification row. It claims btrfs/GRUB and does not declare SysV; it is not a SysV fixture. |
| `evolution-engine/fixtures/arch-five-year-old/etc/os-release` | Identifies Arch only. No `/etc/inittab`, `/etc/rc.conf`, `DAEMONS`, `rc.local`, SysV package database, or mkinitcpio capture exists in this fixture. |
| `evolution-engine/src/evolution/qualification.py::SourceCapabilities` | Support is capability-qualified; baseline age alone cannot establish support. |

## Integration change

Added `T-ARCH2015-SYSV-003` in `evolution-engine/tests/test_compatibility.py`. It asserts the SysV state is refused by `classify_source` and that recovery uses the engine's canonical `BASELINE_ID` after the recovery bridge. The test intentionally guards the boundary; it does not imply the bridge is implemented or qualified for every 2015 machine.

Existing discovery tests `T-ARCH2015-SYSV-001/002` and the implementation in `system.py` were verified against the current working tree. The source file also contains unrelated concurrent Obarun discovery edits; those are not represented as part of this change.

## Inherited claim audit and qualification limit

`autonomy/results/sub-repair-engine-0024.md` describes snapshot, restore, and `B0-2015.yaml` artifacts. The named paths `evidence/sysvinit/`, `autonomy/primitives/snapshot-sysvinit.sh`, `autonomy/primitives/restore-sysvinit.sh`, and `evolution-engine/ledger/B0-2015.yaml` are absent from this repository. The existing fixture and matrix therefore do not support a claim of empirical SysV recovery qualification. Keep Arch 2015 SysV blocked from ordinary migration until a real, provenance-recorded fixture and separately qualified recovery bridge exist.

## Verification and evidence

Command: `cd evolution-engine && python3 -m unittest tests.test_discovery tests.test_compatibility`  
Result: **24 tests passed**.  
Evidence: `autonomy/codex/arch2015-sysvinit-integration-wave1-test.log`.
