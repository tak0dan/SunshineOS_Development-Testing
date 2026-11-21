# Arch 2015 SysV init deliverable consolidation — Wave 1

Date: 2026-11-21

## Scope and evidence boundary

This consolidates the repository-backed implementation and prior Wave 1 findings for the Arch 2015 SysV migration source. It does not claim qualification against a real Arch 2015 VM: this checkout has no such captured source tree. `evolution-engine/fixtures/arch-five-year-old/etc/os-release` supplies old-Arch identity only and has no SysV configuration or service scripts. Historical paths below are expected paths inside an observed legacy installation, not paths present in this checkout.

## Exact-path catalogue

| Repository path / symbol | Verified behavior or meaning |
|---|---|
| `evolution-engine/src/discovery/system.py::_detect_init_system` | Detects init using runtime PID 1 and corroborating installed evidence; a generic `init` name alone is insufficient. |
| `evolution-engine/src/discovery/sysvinit.py::parse_rc_conf` | Parses only a single-line literal `DAEMONS=(...)` declaration; records enabled, disabled (`!`) and background (`@`) service names. It does not source shell. Dynamic or ambiguous input is incomplete. |
| `evolution-engine/src/evolution/tools/sysvinit_repair.py::assess_sysv_services` | Read-only check of enabled/explicitly required service script files under the supplied root's `etc/rc.d`. Incomplete inventory and root escapes block; no commands are proposed or run. |
| `evolution-engine/src/target/compatibility.py::classify_source` | Keeps detected SysV outside the ordinary supported Arch transformation path absent a qualified adapter. |
| `evolution-engine/src/evolution/recovery.py::RECOVERY_BASELINE_ID`, `RECOVERY_LINEAGE`, `RECONSTRUCTION_SPEC` | Models the `B-1-2015 -> M recovery bridge -> B0 -> target` recovery lineage and reconstruction requirements. This is a specification, not a successful legacy recovery run. |
| `evolution-engine/src/evolution/invariants.py::check_invariants` | Machine-checkable M-01..M-10 constraints; observed-state authority, recoverability, qualification, repeatability and user-data separation apply here. |
| `evolution-engine/tests/test_discovery.py` | Includes `T-ARCH2015-SYSV-001` detection coverage. |
| `evolution-engine/tests/test_arch2015_sysvinit.py::Arch2015SysvinitTests` | `T-ARCH2015-SYSV-004` stale SysV remnants cannot override named systemd PID 1; `T-ARCH2015-SYSV-005` detected SysV is blocked from ordinary transformation. |
| `evolution-engine/tests/test_sysvinit_inventory.py::SysVInitInventoryTests` | `T-ARCH2015-SYSV-006` marker normalization; `-007` shell expansion rejected; `-008` missing/duplicate assignments incomplete; `-009` duplicate services rejected. |
| `evolution-engine/tests/test_sysvinit_repair.py::SysVInitRepairTests` | `T-ARCH2015-SYSV-010` missing script is reported without commands; `-011` incomplete inventory blocks probes; `-012` symlink escape is blocked. |
| `evolution-engine/fixtures/arch-five-year-old/etc/os-release` | Existing old-Arch identity fixture; not a SysV qualification fixture. |

Expected source-installation paths surveyed by the parser and repair design: `/etc/rc.conf`, `/etc/inittab`, `/etc/rc.d/`, `/etc/conf.d/`, `/etc/rc.local`, `/etc/fstab`, `/etc/mkinitcpio.conf`, `/var/lib/pacman/local/`, and `/var/log/pacman.log`. The current parser consumes only the `DAEMONS` assignment. Other paths require their own format-aware, rooted inventory before they can drive planning.

## Consolidated behavior

The implementation treats historical service declarations as observations only. It rejects shell execution semantics, keeps background/disabled intent distinct, and blocks repair assessment when parsing is incomplete. A present regular script is only file-presence evidence: it does not establish package ownership, dependencies, script correctness, or service health. No repair mutation or recovery-bridge qualification is implied. These boundaries follow AD-05/M-04, AD-11, AD-13 and AD-14/M-08 in `reports/ARCHITECTURE_DECISIONS.md`; the mandate's 20-year objective requires preserving this knowledge without treating a historical release label as sufficient proof.

## Regression run

Command from `evolution-engine/`:

```sh
python3 -m unittest tests/test_sysvinit_inventory.py tests/test_sysvinit_repair.py tests/test_arch2015_sysvinit.py tests/test_discovery.py
```

Result: **18 tests passed**. Exact output is recorded in `autonomy/codex/arch2015-sysvinit-consolidation-wave1-test.log`.

## Prior evidence audit

Earlier deliverables `autonomy/codex/arch2015-sysvinit-wave1-deepening.md` and `autonomy/codex/arch2015-sysvinit-repair-wave1.md` correctly identify the absent source capture and limit claims to repository behavior. Referenced non-existent VM captures and speculative source artifacts in older result notes are not treated as evidence here.

## Changed deliverable files

- `evolution-engine/src/discovery/sysvinit.py` and `evolution-engine/src/evolution/tools/sysvinit_repair.py` — implementation already present in the working tree and verified; not modified in this consolidation.
- `evolution-engine/tests/test_sysvinit_inventory.py`, `test_sysvinit_repair.py`, `test_arch2015_sysvinit.py` — existing regressions verified; not modified here.
- `autonomy/codex/arch2015-sysvinit-consolidation-wave1.md` — this catalogue and summary.
- `autonomy/codex/arch2015-sysvinit-consolidation-wave1-test.log` — regression evidence.
