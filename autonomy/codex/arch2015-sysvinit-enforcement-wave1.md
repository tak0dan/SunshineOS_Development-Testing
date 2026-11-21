# Arch 2015 SysV init: architecture enforcement, wave 1

Date: 2026-11-21  
Scope: repository-grounded survey and regression coverage for the SysV-to-Sunshine architecture boundary. The task-specific change adds an end-to-end test from rooted system discovery to ordinary transformation refusal. No historical ISO or machine capture was assumed.

## Catalogue

| Exact path / symbol | Verified role and enforcement |
|---|---|
| `reports/USER_MIGRATION_MANDATE_2026-11-21.md` | User's long-term target-state migration and old-state qualification mandate (context only; not modified). |
| `reports/ARCHITECTURE_DECISIONS.md` AD-05, AD-13, AD-14; M-04, M-06, M-08 | Observed installation is authoritative; Arch 2015 uses independent recovery lineage; support is qualified, and operations require recovery. (Context only; not modified.) |
| `evolution-engine/src/discovery/system.py::_detect_init_system` | Collects PID 1, systemd runtime, root-scoped init markers and init CLI evidence. SysV is identified through `init --version` or generic PID 1 `init` corroborated by `/etc/inittab`; the file alone cannot establish active SysV. Named PID 1 runtime evidence takes priority over installed remnants. |
| `evolution-engine/src/target/compatibility.py::classify_source` | Hard-blocks any identified init other than `systemd` for the ordinary Arch transformer, returning an unsupported report with a specific init blocker. |
| `evolution-engine/src/evolution/recovery.py::RECOVERY_BASELINE_ID`, `BRIDGE_ID`, `recovery_path` | Encodes separate `B-1-2015 -> M-recovery-bridge -> B0 -> target` lineage. This route is architecture, not empirical proof that an arbitrary 2015 installation has been qualified. |
| `evolution-engine/src/evolution/recovery.py::RECONSTRUCTION_SPEC` | Names semantic reconstruction concerns across package manager/trust, repositories, package DB, kernel/initramfs, boot, filesystem, services, config, identity and validation. |
| `evolution-engine/src/evolution/qualification.py::SourceCapabilities`, `CompatibilityEngine.classify` | Capabilities determine qualification; age or lineage alone does not grant support. |
| `evolution-engine/tests/source-matrix.toml` (`arch-five-year-old`) | Existing old-Arch row is not a SysV qualification row. |
| `evolution-engine/fixtures/arch-five-year-old/etc/os-release` | Only identifies Arch; does not capture `/etc/inittab`, `/etc/rc.conf`, `DAEMONS`, `rc.local`, SysV package state, or mkinitcpio. |

## Code and regression coverage

Added `test_detected_sysv_source_is_blocked_from_ordinary_transformation` to `evolution-engine/tests/test_arch2015_sysvinit.py`. It uses a fake root and fake command runner, confirms discovery identifies `sysvinit`, and asserts `classify_source()` refuses the ordinary transformer with an init blocker. Test ID: `T-ARCH2015-SYSV-005`.

The adjacent stale-marker regression was assigned unique ID `T-ARCH2015-SYSV-004`. The compatibility boundary test already present in `evolution-engine/tests/test_compatibility.py::CompatibilityTests.test_arch_2015_sysvinit_requires_recovery_bridge` uses `T-ARCH2015-SYSV-003`; discovery cases in `evolution-engine/tests/test_discovery.py` use `T-ARCH2015-SYSV-001` and `T-ARCH2015-SYSV-002`.

Inherited claim audit: `autonomy/results/sub-repair-engine-0024.md` refers to snapshot/restore artifacts and `B0-2015.yaml`; the listed paths `evidence/sysvinit/`, `autonomy/primitives/snapshot-sysvinit.sh`, `autonomy/primitives/restore-sysvinit.sh`, and `evolution-engine/ledger/B0-2015.yaml` are absent in this checkout. They are not counted as working controls. The available fixture and matrix do not prove historical SysV recovery. Continue to block generic SysV state from the ordinary transformer until a provenance-recorded fixture and separately qualified recovery path exist.

## Verification

From `evolution-engine/`:

```sh
python3 -m unittest tests.test_arch2015_sysvinit tests.test_compatibility tests.test_discovery
```

Result: **26 tests passed**. Evidence log: `autonomy/codex/arch2015-sysvinit-enforcement-wave1-test.log`.

## Changed paths

- `evolution-engine/tests/test_arch2015_sysvinit.py`
- `autonomy/codex/arch2015-sysvinit-enforcement-wave1.md`
- `autonomy/codex/arch2015-sysvinit-enforcement-wave1-test.log`

No credentials or key material were used or recorded. `reports/` was not modified.
