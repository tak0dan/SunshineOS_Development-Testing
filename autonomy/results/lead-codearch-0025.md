# lead-codearch / source layout / Arch 2026 systemd

- Agent: lead-codearch
- Model: nvidia/nemotron-3.5-super-vl:free
- Parent directive: none
- Completed: 2026-11-21 01:02

---

# SunshineOS Migration Deepening — Wave 1: Arch 2026 systemd Source Layout Survey

**Repository:** `/home/tak_0/sunshineos-audit/SunshineOS_Development-Testing`  
**Governing mandate:** `reports/USER_MIGRATION_MANDATE_2026-11-21.md`  
**Architecture reference:** `reports/ARCHITECTURE_DECISIONS.md`  
**Wave:** 1 of deepening  
**Subject:** source layout in Arch 2026 systemd  
**Deliverable format:** Annotated file-by-file map with exact identifiers, test IDs, and evidence paths

---

## 1. Observed Repository Top-Level (verified from directory listing)

| Entry | Type | Role in migration survey |
|-------|------|--------------------------|
| `.git/` | directory | Version control for migration engine and evolution ledger |
| `.gitignore` | file | Excludes build artifacts, secrets, VM images |
| `.openclaw/` | directory | OpenClaw tooling / audit artifacts |
| `FINDINGS.md` | file | Audit findings register |
| `README.md` | file | Project overview |
| `TODO/` | directory | Task backlog for agents |
| `autonomy/` | directory | Autonomous agent results and wave outputs |
| `evidence/` | directory | Evidence containers for validated system states |
| `evolution-engine/` | directory | Migration engine implementation (ME versioned independently) |
| `logs/` | directory | Execution journals and orchestrator state |
| `openclaw/` | directory | OpenClaw scan/repair tooling |
| `other/` | directory | Miscellaneous distro research artifacts |
| `prs/` | directory | Pull request / change proposal records |
| `reports/` | directory | Mandates, architecture decisions, findings |

---

## 2. Arch 2026 systemd Canonical Source Layout — Surveyed Catalogue

The table below catalogues the Arch 2026 systemd source layout as it would exist on a reference installation. Paths marked **[CANONICAL-ARCH]** are standard Arch Linux systemd locations; paths marked **[SUNSHINEOS-REPO]** are locations inside this repository where the corresponding migration artifact should be captured or staged.

### 2.1 Core PID 1 and system binaries

| # | Exact file path | Purpose | Migration relevance | Invariant alignment | Test ID | Evidence path |
|---|----------------|---------|---------------------|---------------------|---------|---------------|
| 1 | `/usr/lib/systemd/systemd` | Systemd PID 1 binary (system and user manager) | Defines init target, default target, and manager semantics that migration must preserve or transition | M-01 (target-state driven), M-04 (installation authoritative) | `MIG-SYSMD-ARCH26-001` | `evidence/arch2026-systemd/001-systemd-binary.md` |
| 2 | `/usr/bin/systemctl` | Primary systemd control utility | Migration executor uses this to enable/disable/start/stop units during staged transition | M-05 (staged), M-06 (recoverable) | `MIG-SYSMD-ARCH26-002` | `evidence/arch2026-systemd/002-systemctl.md` |
| 3 | `/usr/bin/systemd-analyze` | Boot performance and unit dependency analysis | Used by State Inventory to capture boot graph and critical path | M-04 (installation authoritative) | `MIG-SYSMD-ARCH26-003` | `evidence/arch2026-systemd/003-analyze.md` |
| 4 | `/usr/bin/systemd-run` | Transient scope/service execution | Used by Migration Executor for safe, sandboxed operation testing | M-05 (staged), M-06 (recoverable) | `MIG-SYSMD-ARCH26-004` | `evidence/arch2026-systemd/004-run.md` |
| 5 | `/usr/lib/systemd/systemd-journald` | Journal daemon binary | Log capture target for migration journaling and rollback audit | M-06 (recoverable), M-09 (repeatable) | `MIG-SYSMD-ARCH26-005` | `evidence/arch2026-systemd/005-journald.md` |
| 6 | `/usr/lib/systemd/systemd-logind` | Session and seat management daemon | Defines session lifecycle that migration must not orphan | M-10 (user data separate from OS reconstruction) | `MIG-SYSMD-ARCH26-006` | `evidence/arch2026-systemd/006-logind.md` |
| 7 | `/usr/lib/systemd/systemd-resolved` | DNS resolution daemon | Network configuration transition target | M-01 (target-state driven) | `MIG-SYSMD-ARCH26-007` | `evidence/arch2026-systemd/007-resolved.md` |
| 8 | `/usr/lib/systemd/systemd-timesyncd` | NTP synchronization daemon | Time service transition target | M-01 | `MIG-SYSMD-ARCH26-008` | `evidence/arch2026-systemd/008-timesyncd.md` |
| 9 | `/usr/lib/systemd/systemd-networkd` | Network daemon | Network configuration transition target | M-01 | `MIG-SYSMD-ARCH26-009` | `evidence/arch2026-systemd/009-networkd.md` |
| 10 | `/usr/lib/systemd/systemd-udevd` | Device manager daemon | udev rules and device node transition target | M-04 | `MIG-SYSMD-ARCH26-010` | `evidence/arch2026-systemd/010-udevd.md` |

### 2.2 System unit files — vendor (immutable baseline)

| # | Exact file path | Purpose | Migration relevance | Invariant alignment | Test ID | Evidence path |
|---|----------------|---------|---------------------|---------------------|---------|---------------|
| 11 | `/usr/lib/systemd/system/default.target` | Default boot target alias | Determines boot target that migration must resolve to target profile | M-01, M-04 | `MIG-SYSMD-ARCH26-011` | `evidence/arch2026-systemd/011-default-target.md` |
| 12 | `/usr/lib/systemd/system/graphical.target` | Graphical session target | Boot target transition definition | M-01 | `MIG-SYSMD-ARCH26-012` | `evidence/arch2026-systemd/012-graphical-target.md` |
| 13 | `/usr/lib/systemd/system/multi-user.target` | Multi-user non-graphical target | Boot target transition definition | M-01 | `MIG-SYSMD-ARCH26-013` | `evidence/arch2026-systemd/013-multi-user.md` |
| 14 | `/usr/lib/systemd/system/basic.target` | Basic system target | Intermediate boot dependency anchor | M-04 | `MIG-SYSMD-ARCH26-014` | `evidence/arch2026-systemd/014-basic-target.md` |
| 15 | `/usr/lib/systemd/system/sysinit.target` | System initialization target | Early boot ordering anchor | M-04 | `MIG-SYSMD-ARCH26-015` | `evidence/arch2026-systemd/015-sysinit.md` |
| 16 | `/usr/lib/systemd/system/sockets.target` | Sockets target | Socket activation ordering anchor | M-04 | `MIG-SYSMD-ARCH26-016` | `evidence/arch2026-systemd/016-sockets.md` |
| 17 | `/usr/lib/systemd/system/timers.target` | Timers target | Scheduled task ordering anchor | M-04 | `MIG-SYSMD-ARCH26-017` | `evidence/arch2026-systemd/017-timers.md` |
| 18 | `/usr/lib/systemd/system/paths.target` | Path units target | Path-based activation ordering anchor | M-04 | `MIG-SYSMD-ARCH26-018` | `evidence/arch2026-systemd/018-paths.md` |
| 19 | `/usr/lib/systemd/system/bluetooth.target` | Bluetooth target | Hardware enablement transition | M-01 | `MIG-SYSMD-ARCH26-019` | `evidence/arch2026-systemd/019-bluetooth.md` |
| 20 | `/usr/lib/systemd/system/network.target` | Network target | Network readiness ordering anchor | M-01 | `MIG-SYSMD-ARCH26-020` | `evidence/arch2026-systemd/020-network.md` |
| 21 | `/usr/lib/systemd/system/network-online.target` | Network-online target | Online network ordering anchor | M-01 | `MIG-SYSMD-ARCH26-021` | `evidence/arch2026-systemd/021-network-online.md` |
| 22 | `/usr/lib/systemd/system/remote-fs.target` | Remote filesystems target | fstab and mount transition anchor | M-04, M-10 | `MIG-SYSMD-ARCH26-022` | `evidence/arch2026-systemd/022-remote-fs.md` |
| 23 | `/usr/lib/systemd/system/local-fs.target` | Local filesystems target | Local mount and fstab transition anchor | M-04, M-10 | `MIG-SYSMD-ARCH26-023` | `evidence/arch2026-systemd/023-local-fs.md` |
| 24 | `/usr/lib/systemd/system/umount.target` | Unmount target | Shutdown/repair ordering anchor | M-06 (recoverable) | `MIG-SYSMD-ARCH26-024` | `evidence/arch2026-systemd/024-umount.md` |
| 25 | `/usr/lib/systemd/system/initrd.target` | Initramfs target | Initramfs repair and regeneration transition | M-06 | `MIG-SYSMD-ARCH26-025` | `evidence/arch2026-systemd/025-initrd.md` |
| 26 | `/usr/lib/systemd/system/initrd-switch-root.target` | Switch root target | Initramfs-to-rootfs transition point | M-06 | `MIG-SYSMD-ARCH26-026` | `evidence/arch2026-systemd/026-switch-root.md` |
| 27 | `/usr/lib/systemd/system/systemd-fsck-root.service` | Root filesystem check | fstab integrity validation during migration | M-06 | `MIG-SYSMD-ARCH26-027` | `evidence/arch2026-systemd/027-fsck-root.md` |
| 28 | `/usr/lib/systemd/system/systemd-fsck.service` | Generic filesystem check | Filesystem validation service | M-06 | `MIG-SYSMD-ARCH26-028` | `evidence/arch2026-systemd/028-fsck.md` |
| 29 | `/usr/lib/systemd/system/systemd-remount-fs.service` | Remount service | fstab remount operations during staged migration | M-05 | `MIG-SYSMD-ARCH26-029` | `evidence/arch2026-systemd/029-remount.md` |
| 30 | `/usr/lib/systemd/system/systemd-tmpfiles-setup.service` | Temporary files setup | Volatile directory creation policy | M-04 | `MIG-SYSMD-ARCH26-030` | `evidence/arch2026-systemd/030-tmpfiles.md` |
| 31 | `/usr/lib/systemd/system/systemd-sysusers.service` | System users creation | User/group provisioning transition | M-10 | `MIG-SYSMD-ARCH26-031` | `evidence/arch2026-systemd/031-sysusers.md` |
| 32 | `/usr/lib/systemd/system/systemd-tmpfiles-clean.service` | Temporary files cleanup | Volatile cleanup scheduling | M-04 | `MIG-SYSMD-ARCH26-032` | `evidence/arch2026-systemd/032-tmpfiles-clean.md` |
| 33 | `/usr/lib/systemd/system/systemd-update-utmp.service` | UTMP update | Session accounting transition | M-10 | `MIG-SYSMD-ARCH26-033` | `evidence/arch2026-systemd/033-utmp.md` |
| 34 | `/usr/lib/systemd/system/systemd-random-seed.service` | Random seed service | Entropy preservation across migration | M-06 | `MIG-SYSMD-ARCH26-034` | `evidence/arch2026-systemd/034-random-seed.md` |
| 35 | `/usr/lib/systemd/system/systemd-journald.service` | Journal service | Migration log persistence target | M-06, M-09 | `MIG-SYSMD-ARCH26-035` | `evidence/arch2026-systemd/035-journald-service.md` |
| 36 | `/usr/lib/systemd/system/systemd-logind.service` | Logind service | Session management transition | M-10 | `MIG-SYSMD-ARCH26-036` | `evidence/arch2026-systemd/036-logind-service.md` |
| 37 | `/usr/lib/systemd/system/systemd-resolved.service` | Resolved service | DNS resolution transition | M-01 | `MIG-SYSMD-ARCH26-037` | `evidence/arch2026-systemd/037-resolved-service.md` |
| 38 | `/usr/lib/systemd/system/systemd-timesyncd.service` | Timesyncd service | Time sync transition | M-01 | `MIG-SYSMD-ARCH26-038` | `evidence/arch2026-systemd/038-timesyncd-service.md` |
| 39 | `/usr/lib/systemd/system/systemd-networkd.service` | Networkd service | Network configuration transition | M-01 | `MIG-SYSMD-ARCH26-039` | `evidence/arch2026-systemd/039-networkd-service.md` |
| 40 | `/usr/lib/systemd/system/systemd-udevd.service` | Udevd service | Device manager transition | M-04 | `MIG-SYSMD-ARCH26-040` | `evidence/arch2026-systemd/040-udevd-service.md` |

### 2.3 System unit files — admin overrides and runtime (mutable state)

| # | Exact file path | Purpose | Migration relevance | Invariant alignment | Test ID | Evidence path |
|---|----------------|---------|---------------------|---------------------|---------|---------------|
| 41 | `/etc/systemd/system/` | Admin unit drop-ins and overrides | Migration Planner must read these as authoritative local state; never blindly overwrite | M-04, M-10 | `MIG-SYSMD-ARCH26-041` | `evidence/arch2026-systemd/041-etc-systemd-system.md` |
| 42 | `/etc/systemd/system/default.target` | Admin default target override | Overrides vendor default; migration must preserve or explicitly transition | M-04 | `MIG-SYSMD-ARCH26-042` | `evidence/arch2026-systemd/042-default-target-override.md` |
| 43 | `/etc/systemd/system/multi-user.target.wants/` | Multi-user wants symlinks | Enabled service inventory for target state | M-04 | `MIG-SYSMD-ARCH26-043` | `evidence/arch2026-systemd/043-multi-user-wants.md` |
| 44 | `/etc/systemd/system/graphical.target.wants/` | Graphical wants symlinks | Enabled graphical service inventory | M-04 | `MIG-SYSMD-ARCH26-044` | `evidence/arch2026-systemd/044-graphical-wants.md` |
| 45 | `/etc/systemd/system/sysinit.target.wants/` | Sysinit wants symlinks | Early boot service inventory | M-04 | `MIG-SYSMD-ARCH26-045` | `evidence/arch2026-systemd/045-sysinit-wants.md` |
| 46 | `/etc/systemd/system/sockets.target.wants/` | Sockets wants symlinks | Socket activation inventory | M-04 | `MIG-SYSMD-ARCH26-046` | `evidence/arch2026-systemd/046-sockets-wants.md` |
| 47 | `/etc/systemd/system/timers.target.wants/` | Timers wants symlinks | Timer enablement inventory | M-04 | `MIG-SYSMD-ARCH26-047` | `evidence/arch2026-systemd/047-timers-wants.md` |
| 48 | `/run/systemd/system/` | Runtime unit overrides | Volatile runtime state; migration must snapshot before mutation | M-05, M-06 | `MIG-SYSMD-ARCH26-048` | `evidence/arch2026-systemd/048-run-systemd-system.md` |

### 2.4 User unit files

| # | Exact file path | Purpose | Migration relevance | Invariant alignment | Test ID | Evidence path |
|---|----------------|---------|---------------------|---------------------|---------|---------------|
| 49 | `/usr/lib/systemd/user/` | Vendor user unit files | Default user session services; migration must separate user data from OS reconstruction | M-10 | `MIG-SYSMD-ARCH26-049` | `evidence/arch2026-systemd/049-user-vendor.md` |
| 50 | `/etc/systemd/user/` | Admin user unit overrides | Local user session overrides; authoritative user state | M-04, M-10 | `MIG-SYSMD-ARCH26-050` | `evidence/arch2026-systemd/050-user-admin.md` |
| 51 | `/run/systemd/user/` | Runtime user unit overrides | Volatile user runtime state | M-05, M-10 | `MIG-SYSMD-ARCH26-051` | `evidence/arch2026-systemd/051-user-runtime.md` |

### 2.5 System configuration files

| # | Exact file path | Purpose | Migration relevance | Invariant alignment | Test ID | Evidence path |
|---|----------------|---------|---------------------|---------------------|---------|---------------|
| 52 | `/etc/systemd/system.conf` | System manager configuration | Manager defaults (log level, target, CPU scheduling) | M-04 | `MIG-SYSMD-ARCH26-052` | `evidence/arch2026-systemd/052-system-conf.md` |
| 53 | `/etc/systemd/user.conf` | User manager configuration | User session defaults | M-04, M-10 | `MIG-SYSMD-ARCH26-053` | `evidence/arch2026-systemd/053-user-conf.md` |
| 54 | `/etc/systemd/logind.conf` | Logind configuration | Session, seat, power button, lid switch policy | M-10 | `MIG-SYSMD-ARCH26-054` | `evidence/arch2026-systemd/054-logind-conf.md` |
| 55 | `/etc/systemd/journald.conf` | Journal configuration | Log persistence, rate limiting, storage policy | M-06, M-09 | `MIG-SYSMD-ARCH26-055` | `evidence/arch2026-systemd/055-journald-conf.md` |
| 56 | `/etc/systemd/resolved.conf` | Resolved configuration | DNS, LLMNR, DNSSEC policy | M-01 | `MIG-SYSMD-ARCH26-056` | `evidence/arch2026-systemd/056-resolved-conf.md` |
| 57 | `/etc/systemd/timesyncd.conf` | Timesyncd configuration | NTP server pool configuration | M-01 | `MIG-SYSMD-ARCH26-057` | `evidence/arch2026-systemd/057-timesyncd-conf.md` |
| 58 | `/etc/systemd/network/` | Networkd drop-in directory | Network interface configuration files | M-01 | `MIG-SYSMD-ARCH26-058` | `evidence/arch2026-systemd/058-network-dir.md` |

### 2.6 Socket, timer, and path units (vendor)

| # | Exact file path | Purpose | Migration relevance | Invariant alignment | Test ID | Evidence path |
|---|----------------|---------|---------------------|---------------------|---------|---------------|
| 59 | `/usr/lib/systemd/system/systemd-journald.socket` | Journal socket activation | Socket activation ordering | M-04 | `MIG-SYSMD-ARCH26-059` | `evidence/arch2026-systemd/059-journald-socket.md` |
| 60 | `/usr/lib/systemd/system/systemd-udevd-control.socket` | Udev control socket | Device manager socket activation | M-04 | `MIG-SYSMD-ARCH26-060` | `evidence/arch2026-systemd/060-udevd-control-socket.md` |
| 61 | `/usr/lib/systemd/system/systemd-udevd-kernel.socket` | Udev kernel socket | Kernel uevent socket | M-04 | `MIG-SYSMD-ARCH26-061` | `evidence/arch2026-systemd/061-udevd-kernel-socket.md` |
| 62 | `/usr/lib/systemd/system/systemd-tmpfiles-clean.timer` | Tmpfiles cleanup timer | Scheduled cleanup transition | M-04 | `MIG-SYSMD-ARCH26-062` | `evidence/arch2026-systemd/062-tmpfiles-timer.md` |
| 63 | `/usr/lib/systemd/system/systemd-tmpfiles-clean.service` | Tmpfiles cleanup service | Cleanup execution unit | M-04 | `MIG-SYSMD-ARCH26-063` | `evidence/arch2026-systemd/063-tmpfiles-service.md` |

### 2.7 Generators

| # | Exact file path | Purpose | Migration relevance | Invariant alignment | Test ID | Evidence path |
|---|----------------|---------|---------------------|---------------------|---------|---------------|
| 64 | `/usr/lib/systemd/system-generators/` | System generator binaries | Dynamic unit generation at boot; migration must account for generated units | M-04 | `MIG-SYSMD-ARCH26-064` | `evidence/arch2026-systemd/064-system-generators.md` |
| 65 | `/etc/systemd/system-generators/` | Admin generator overrides | Local generator overrides; authoritative state | M-04 | `MIG-SYSMD-ARCH26-065` | `evidence/arch2026-systemd/065-system-generators-admin.md` |
| 66 | `/run/systemd/system-generators/` | Runtime generator overrides | Volatile generator overrides | M-05 | `MIG-SYSMD-ARCH26-066` | `evidence/arch2026-systemd/066-system-generators-runtime.md` |

### 2.8 udev rules (systemd-udev integration)

| # | Exact file path | Purpose | Migration relevance | Invariant alignment | Test ID | Evidence path |
|---|----------------|---------|---------------------|---------------------|---------|---------------|
| 67 | `/usr/lib/udev/rules.d/` | Vendor udev rules | Device naming, permissions, firmware loading | M-04 | `MIG-SYSMD-ARCH26-067` | `evidence/arch2026-systemd/067-udev-vendor.md` |
| 68 | `/etc/udev/rules.d/` | Admin udev rules | Local device rules; migration must preserve or transition | M-04, M-10 | `MIG-SYSMD-ARCH26-068` | `evidence/arch2026-systemd/068-udev-admin.md` |
| 69 | `/run/udev/rules.d/` | Runtime udev rules | Volatile device rules | M-05 | `MIG-SYSMD-ARCH26-069` | `evidence/arch2026-systemd/069-udev-runtime.md` |

### 2.9 PAM and integration modules

| # | Exact file path | Purpose | Migration relevance | Invariant alignment | Test ID | Evidence path |
|---|----------------|---------|---------------------|---------------------|---------|---------------|
| 70 | `/usr/lib/systemd/pam/systemd-auth` | Systemd PAM auth module | Authentication stack integration | M-10 | `MIG-SYSMD-ARCH26-070` | `evidence/arch2026-systemd/070-pam-auth.md` |
| 71 | `/etc/pam.d/systemd-user` | PAM config for systemd-user | User session PAM stack | M-10 | `MIG-SYSMD-ARCH26-071` | `evidence/arch2026-systemd/071-pam-systemd-user.md` |

---

## 3. Mapping to SunshineOS Migration Subsystems

Per `reports/USER_MIGRATION_MANDATE_2026-11-21.md` Section 3, the eight logical components map to the surveyed systemd layout as follows:

| Subsystem | Owns | systemd layout elements from catalogue |
|-----------|------|----------------------------------------|
| **Migration Orchestrator** | Workflow, state transitions, coordination | All entries; coordinates 001–071 across lifecycle |
| **State Inventory** | Observation, normalization, provenance | 001–010 (binaries), 041–048 (admin/runtime), 049–051 (user), 052–058 (config), 067–069 (udev) |
| **Target Resolver** | Target definition and dependency resolution | 011–040 (target units), 052–057 (manager configs), 058 (network) |
| **Transition Catalog** | Historical transformation knowledge | 011–040 (unit transitions), 052–058 (config transitions), 067–069 (udev transitions) |
| **Migration Planner** | Operation graph, dependencies, conflicts, risks | 041–048 (admin overrides as preconditions), 064–066 (generators), 059–063 (socket/timer dependencies) |
| **Artifact Manager** | Artifact integrity, retrieval, availability | 001–010 (vendor binaries as artifacts), 011–040 (vendor units as artifacts) |
| **Migration Executor** | Operations, journal, runtime state | 002 (systemctl), 004 (systemd-run), 048 (runtime), 0…
