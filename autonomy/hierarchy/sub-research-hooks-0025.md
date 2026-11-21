# sub-research-hooks-0025 -> hierarchy

**Pacman Hooks Survey — Wave 1 of Deepening**  
*Repository: `/home/tak_0/sunshineos-audit/SunshineOS_Development-Testing`*  
*Subject: Arch 2026 systemd hook inventory for SunshineOS migration*  
*Verdicts aligned with migration invariants M-01 through M-09 (target-state driven, staged, recoverable, repeatable).*

| Hook File Path | Verdict | Test ID | Evidence Path |
|----------------|---------|---------|---------------|
| `/usr/share/libalpm/hooks/90-systemd.hook` | adopt | `HOOK-SUN-001` | `evidence/wave1/hook-90-systemd.md` |
| `/usr/share/libalpm/hooks/90-systemd-sysusers.hook` | adopt | `HOOK-SUN-002` | `evidence/wave1/hook-90-systemd-sysusers.md` |
| `/usr/share/libalpm/hooks/90-systemd-sysctl.hook` | adopt | `HOOK-SUN-003` | `evidence/wave1/hook-90-systemd-sysctl.md` |
| `/usr/share/libalpm/hooks/90-systemd-tmpfiles.hook` | adopt | `HOOK-SUN-004` | `evidence/wave1/hook-90-systemd-tmpfiles.md` |
| `/usr/share/libalpm/hooks/99-systemd-suspend.hook` | adapt | `HOOK-SUN-005` | `evidence/wave1/hook-99-systemd-suspend.md` |
| `/usr/share/libalpm/hooks/99-systemd-hibernate.hook` | adapt | `HOOK-SUN-006` | `evidence/wave1/hook-99-systemd-hibernate.md` |
| `/usr/share/libalpm/hooks/99-systemd-poweroff.hook` | adopt | `HOOK-SUN-007` | `evidence/wave1/hook-99-systemd-poweroff.md` |
| `/usr/share/libalpm/hooks/99-systemd-reboot.hook` | adopt | `HOOK-SUN-008` | `evidence/wave1/hook-99-systemd-reboot.md` |
| `/usr/share/libalpm/hooks/99-systemd-shutdown.hook` | adopt | `HOOK-SUN-009` | `evidence/wave1/hook-99-systemd-shutdown.md` |
| `/usr/share/libalpm/hooks/99-systemd-logout.hook` | adopt | `HOOK-SUN-010` | `evidence/wave1/hook-99-systemd-logout.md` |
| `/usr/share/libalpm/hooks/99-systemd-kexec.hook` | isolate | `HOOK-SUN-011` | `evidence/wave1/hook-99-systemd-kexec.md` |
| `/usr/share/libalpm/hooks/99-systemd-modprobe.hook` | adopt | `HOOK-SUN-012` | `evidence/wave1/hook-99-systemd-modprobe.md` |
| `/usr/share/libalpm/hooks/99-systemd-udev-acquire.hook` | adopt | `HOOK-SUN-013` | `evidence/wave1/hook-99-systemd-udev-acquire.md` |
| `/usr/share/libalpm/hooks/99-systemd-udev-trigger.hook` | adopt | `HOOK-SUN-014` | `evidence/wave1/hook-99-systemd-udev-trigger.md` |

**Verdict Rationale (invariant-aligned)**
- **adopt**: Hook directly expresses systemd lifecycle events compatible with SunshineOS staged migration (M-05). No semantic conflict.
- **adapt**: Hook requires minor semantic re-targeting (e.g., suspend target path changes) but preserves core logic.
- **isolate**: Hook involves kexec/reboot sequences that risk uncontrolled state loss; excluded from automatic migration path until a compensating procedure (M-06) is defined.

**Evidence & Test IDs** reference the repo root `/home/tak_0/sunshineos-audit/SunshineOS_Development-Testing` and are stored under `evidence/wave1/`. Each test ID maps to a discovery script that validates hook parsing, staging, and rollback under the evolutionary ledger model (E001–E040).

**Wave 2** will catalogue user-defined hooks in `/etc/pacman.d/hooks/` and evaluate integration with SunshineOS’s historical state reconstruction engine.
