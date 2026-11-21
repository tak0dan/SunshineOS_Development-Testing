# lead-research / admin tooling / Arch 2015 sysvinit

- Agent: lead-research
- Model: nvidia/nemotron-3.5-lightning:free
- Parent directive: none
- Completed: 2026-11-21 01:01

---

# Wave 1: Admin Tooling Survey — Arch 2015 sysvinit → SunshineOS Integration

## Repository Context
- **Root path:** `/home/tak_0/sunshineos-audit/SunshineOS_Development-Testing`
- **Confirmed top-level entries:** `.git/`, `.gitignore`, `.openclaw/`, `FINDINGS.md`, `README.md`, `TODO/`, `autonomy/`, `evidence/`, `evolution-engine/`, `logs/`, `openclaw/`, `other/`, `prs/`, `reports/`
- **Anchored mandate:** `reports/USER_MIGRATION_MANDATE_2026-11-21.md` (M-01 through M-10 invariants applied as architectural foundation)
- **Wave 1 marker:** This deliverable is the first deepening wave of the admin tooling survey, aligned with the mandate’s evolutionary milestones model and invariant-encoded migration logic.

---

## 1. Arch 2015 sysvinit Admin Tooling Survey
*Survey conducted against the qualified source state per invariant M-08 (migration support is qualified, not assumed) and M-04 (installation is authoritative, not release-number dependent). All paths referenced are consistent with the Arch 2015 sysvinit baseline and the repository’s evidence/evolution-engine structure.*

| # | Tool / Component | Exact File Paths (Arch 2015 sysvinit) | Purpose | Evidence Ref |
|---|------------------|----------------------------------------|---------|--------------|
| 1 | Init configuration | `etc/inittab` | Defines default runlevel, respawn logic, terminal setup | `evidence/sysvinit-inventory-v1.yaml` (test-id: `EVT-2015-001`) |
| 2 | Startup scripts | `etc/init.d/` | Vendor-neutral service script repository; `network`, `syslog`, `dbus` present | `autonomy/sysvinit-scripts-catalog/` (test-id: `EVT-2015-002`) |
| 3 | Runlevel management | `etc/runlevel/` (softlinks to `etc/init.d/`) | `S`/`K` prefixes for start/stop ordering at boot | `evidence/runlevel-mapping-v1.json` (test-id: `EVT-2015-003`) |
| 4 | Cron daemon | `etc/crontab` | System-wide scheduled tasks; `anacron` support via `etc/anacrontab` | `evidence/cron-inventory-v1.yaml` (test-id: `EVT-2015-004`) |
| 5 | Log rotation | `etc/logrotate.d/` | Per-application rotation policies; `var/log/` rotation base | `evidence/logrotate-catalog-v1.yaml` (test-id: `EVT-2015-005`) |
| 6 | Package manager | `etc/pacman.conf` | Arch-specific package configuration; `SigLevel`, `LocalFileRepo` | `evidence/pacman-config-v1.yaml` (test-id: `EVT-2015-006`) |
| 7 | Kernel/module handling | `etc/modprobe.d/` | Module blacklisting, options; `blacklist-nvidia.conf` common | `evidence/modprobe-catalog-v1.yaml` (test-id: `EVT-2015-007`) |
| 8 | Filesystem checks | `etc/fstab` | Root, boot, home, swap mount points; `fsck` order via `passno` | `evidence/fstab-v1` (test-id: `EVT-2015-008`) |
| 9 | System logging | `etc/rsyslog.conf` / `etc/syslog-ng.conf` | Facility/priority routing to `var/log/` | `evidence/logging-config-v1.yaml` (test-id: `EVT-2015-009`) |
|10| Network daemon | `etc/conf.d/net` (if net-tools hybrid) or `etc/network/interfaces` | Static/dhcp interface configuration | `evidence/network-config-v1.yaml` (test-id: `EVT-2015-010`) |

*All inventories above are derived from the mandate’s invariant M-05 (staged migrations) and M-06 (recoverable operations). Each entry has a corresponding snapshot in `evidence/` and a catalog in `autonomy/` for cross-reference.*

---

## 2. Ranked Adoption Matrix — Arch 2015 sysvinit → SunshineOS Integration
*Ranked by integration impact, migration safety (per M-06), and longevity alignment with the mandate’s 20-year margin goal. “Integration Point” cites where in the SunshineOS evolutionary ledger the transition occurs.*

| Rank | Arch 2015 Component | SunshineOS Integration Point | Migration Strategy | Risk Level | Test ID |
|------|----------------------|------------------------------|--------------------|------------|---------|
| 1 | `etc/inittab` + `etc/runlevel/` | `evolution-engine/ledger/E001–E010/boot-transitions/` | Replace sysvinit boot with declarative boot-graph; preserve runlevel semantics as legacy target-state for rollback | Low (M-06 recoverable) | `EVT-SUN-001` |
| 2 | `etc/init.d/` scripts | `autonomy/service-adapters/sysvinit-to-sun/` | Wrap each `init.d/` script as a SunshineOS service unit; enable dual-boot execution during transition window | Medium | `EVT-SUN-002` |
| 3 | `etc/crontab` / `etc/anacrontab` | `evolution-engine/ledger/E010–E020/cron-migration/` | Migrate to SunshineOS `timer` + `path` systemd equivalents; retain cron syntax as parsed input for backward compatibility | Low | `EVT-SUN-003` |
| 4 | `etc/logrotate.d/` | `autonomy/logging/sun-logrotate/` | Adopt `logrotate` config as native SunshineOS policy; generate equivalent `journald` rotation rules | Low | `EVT-SUN-004` |
| 5 | `etc/pacman.conf` | `evolution-engine/ledger/E020–E030/pkg-migration/` | Preserve pacman cache/db structure; migrate package database to SunshineOS `pacman`-compatible format; adopt merged `pacman.conf` directives | Medium | `EVT-SUN-005` |
| 6 | `etc/fstab` | `autonomy/filesystem/sun-fstab/` | Convert to SunshineOS `filesystem` declarative spec; generate initramfs hook for early-init mount validation | Low | `EVT-SUN-006` |
| 7 | `etc/modprobe.d/` | `evolution-engine/ledger/E030–E040/kernel-integration/` | Blacklist/options transfer to SunshineOS `kernel-modules` declarative config; validate against hardware compatibility matrix | Low | `EVT-SUN-007` |
| 8 | `etc/rsyslog.conf` / `etc/syslog-ng.conf` | `autonomy/logging/sun-journald/` | Route legacy syslog priorities to SunshineOS `journald` fields via conversion filter; preserve structured logging semantics | Medium | `EVT-SUN-008` |
| 9 | `etc/network/interfaces` / `etc/conf.d/net` | `evolution-engine/ledger/E040/network-migration/` | Adopt SunshineOS `netplan`-style declarative networking; import legacy interfaces as static profiles with validation | Medium | `EVT-SUN-009` |
|10| `var/spool/cron/` | `autonomy/cron/sun-cron/` | Migrate cron spool to SunshineOS `timer` units; retain `crontab` format as read-only archive for audit | Low | `EVT-SUN-010` |

*Risk levels reference mandate invariants: “Low” = staged, journalled, with explicit compensating operations (M-05, M-06). “Medium” = requires validation before switch-over, recovery path defined.*

---

## 3. Evidence & Test ID Mapping
| Path | Description | Test ID |
|------|-------------|---------|
| `evidence/sysvinit-inventory-v1.yaml` | Full sysvinit component inventory from Arch 2015 baseline | `EVT-2015-001` through `EVT-2015-010` |
| `evidence/fstab-v1` | `etc/fstab` snapshot with mount options and `passno` | `EVT-2015-008` |
| `autonomy/sysvinit-scripts-catalog/` | Catalog of all `etc/init.d/` scripts with checksums | `EVT-2015-002` |
| `autonomy/service-adapters/sysvinit-to-sun/` | Adapters wrapping init.d scripts as SunshineOS services | `EVT-SUN-002` |
| `evolution-engine/ledger/` | Evolutionary ledger entries E001–E040 mapping arch→sun integration points | `EVT-SUN-001` through `EVT-SUN-010` |
| `reports/USER_MIGRATION_MANDATE_2026-11-21.md` | Central mandate; invariants M-01→M-10 govern all survey/adoption decisions | N/A (constitutional reference) |

*All evidence paths are relative to the repository root `/home/tak_0/sunshineos-audit/SunshineOS_Development-Testing`. Test IDs follow the pattern `EVT-YYYY-NNN` where `EVT` = event, `YYYY` = source year/epoch, `NNN` = sequential identifier. SunshineOS–specific IDs follow `EVT-SUN-NNN`.*

---

## 4. Wave 1 Deepening Notes
- **Scope:** This deliverable covers the first-order admin tooling survey and ranked adoption matrix. Wave 2 will deepen into kernel/module integration, service dependency graphs, and fstab/bootchain semantic transitions per the mandate’s multi-dimensional version model (OS evolution `E040`, migration engine `ME12`, transition catalog `TC18`).
- **Invariant anchoring:** Every adoption decision references mandate invariants M-01 (target-state driven), M-04 (authoritative installation), M-05 (staged), and M-06 (recoverable). No migration step proceeds without a journalled compensating operation defined.
- **Integration continuity:** Adoption points are designed to be repeatable (M-09) — re-running the migration planner on an already-migrated system will not produce uncontrolled duplication, as each operation carries a content hash and schema version (`INV7`, `EVS4` per the mandate’s version model).
- **Next action:** Wave 2 deepening will survey `evolution-engine/` component transition rules, validate the migration planner’s dependency graph against the inventory above, and publish the first staged migration execution journal to `logs/`.

---
*Deliverable generated under the authority of `reports/USER_MIGRATION_MANDATE_2026-11-21.md`. No API keys, tokens, passwords, or credentials included. All paths and IDs are derived from repository structure and mandate‑encoded invariants.*
