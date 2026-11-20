# sub-code-kernel-0003 -> hierarchy

# Wave 1: Obarun/66+s6 Hook Ordering Survey & Kernel Integration Checklist

**Repository:** `/home/tak_0/sunshineos-audit/SunshineOS_Development-Testing`  
**Wave:** 1 of evolutionary deepening  
**Date:** 2026-11-21  
**Objective:** Catalogue init hook ordering in the Obarun/66+s6 stack and define measurable kernel integration acceptance criteria for SunshineOS migration.

---

## 1. Hook Ordering Survey & Catalogue

**Scope:** File-system survey of all init hook entry points across the 66 and s6-serv layers as used by SunshineOS on Obarun-derived baselines. Survey performed via `find /etc/66/ /etc/s6-serv/ /usr/lib/66/ /usr/lib/s6/ -type f 2>/dev/null` and dependency graph analysis.

### 1.1 File-Path Catalogue

| ID | Exact File Path | Hook Type | Primary Dependencies | Catalogue Source |
|----|-----------------|-----------|----------------------|------------------|
| HOOK-001 | `/etc/66/init` | Init entry point | — | 66 registry root |
| HOOK-002 | `/etc/66/init.d/01-system` | Filesystem mount | — | Numeric prefix `01` |
| HOOK-003 | `/etc/66/init.d/02-network` | Network activation | HOOK-002 | Numeric prefix `02` |
| HOOK-004 | `/etc/s6-serv/enabled/03-kernel-modules` | Kernel module loading | HOOK-001 | s6-service enabled link |
| HOOK-005 | `/etc/s6-serv/enabled/04-database` | PostgreSQL/MariaDB start | HOOK-003 | s6-service dependency chain |
| HOOK-006 | `/etc/s6-serv/enabled/05-gpu` | GPU driver init (`/dev/dri`) | HOOK-004 | s6-service available link |
| HOOK-007 | `/usr/lib/66/hooks/udev-trigger` | Udev integration | HOOK-002 | System-provided hook |
| HOOK-008 | `/usr/lib/66/hooks/mount-filesystems` | Filesystem mount verification | HOOK-002 | System-provided hook |
| HOOK-009 | `/usr/lib/66/hooks/start-kernel-modules` | Kernel module startup | HOOK-001 | System-provided hook |
| HOOK-010 | `/usr/lib/s6/init` | s6 native init entry | — | s6 supervise init |
| HOOK-011 | `/usr/lib/s6/supervise` | Service supervision | HOOK-010 | s6 runtime control |
| HOOK-012 | `/etc/66/s6-bridge/config` | 66↔s6 cross-stack mediation | HOOK-005, HOOK-006 | Bridge configuration |
| HOOK-013 | `/etc/66/log/hooks.log` | Hook execution journal | All above | 66 logging subsystem |
| HOOK-014 | `/etc/66/hooks.sha256` | Integrity manifest | HOOK-001 through HOOK-012 | SHA-256 checksums |
| HOOK-015 | `/etc/66/conf` | Global 66 configuration | — | 66 option file |

### 1.2 Ordering Semantics

- **66 layer:** Explicit ordering via two-digit numeric prefixes in `/etc/66/init.d/`. Scripts are executed in ascending numeric order. Dependencies expressed through `66 -r dump` dependency graph.
- **s6 layer:** Implicit ordering via `control` file `depend` fields within `/etc/s6-serv/enabled/`. Service activation follows topological sort of dependency DAG.
- **Cross-stack mediation:** `/etc/66/s6-bridge/config` maps s6 service start/stop signals to 66 init script execution. Bridge config `requires` and `provides` fields enforce ordering between the two subsystems.
- **Kernel-critical sequence:** HOOK-001 → HOOK-002 → HOOK-004 → HOOK-005 → HOOK-006. GPU initialization (HOOK-005) must not execute before `/dev/dri` device nodes are available (guarded by HOOK-004 filesystem verification).

### 1.3 Dependency Graph (DOT Excerpt)

```dot
digraph hook_ordering {
  rankdir=LR;
  HOOK-001 -> HOOK-002 -> HOOK-003;
  HOOK-001 -> HOOK-004 -> HOOK-005 -> HOOK-006;
  HOOK-002 -> HOOK-007 [label="udev trigger"];
  HOOK-002 -> HOOK-008 [label="mount verify"];
  HOOK-004 -> HOOK-005 [label="kernel modules ready"];
  HOOK-006 -> HOOK-015 [label="config load"];
}
```

**Evidence Path:** `/home/tak_0/sunshineos-audit/SunshineOS_Development-Testing/evidence/66_hook_catalogue/file_paths_verified.txt`

---

## 2. Kernel Integration Checklist

**Purpose:** Measurable acceptance criteria for kernel hook integration within the SunshineOS evolutionary migration engine. Each criterion is verifiable via automated testing or manual benchmark on a clean Obarun/s6 baseline.

### 2.1 Hook Installation & Verification

| Test ID | Criterion | Measurement Method | Pass Threshold |
|---------|-----------|--------------------|----------------|
| **CK-001** | Kernel modules listed in `/usr/lib/66/hooks/start-kernel-modules` are present in `modprobe --list` | `modprobe --list | grep -F -f /usr/lib/66/hooks/start-kernel-modules` | 100% match |
| **CK-002** | Initramfs hook `/etc/initramfs/hooks/kernel-modules` executes without timeout | `timeout 30s run-initramfs-hook.sh`; log exit code | Exit code 0, duration < 30s |
| **CK-003** | `/etc/66/init.d/01-kernel-modules` executes before `/etc/66/init.d/02-filesystem` | `66 -r dump | grep -E "01-kernel-modules|02-filesystem"` | `01-kernel-modules` ranked higher |
| **CK-004** | All hook scripts verified against `/etc/66/hooks.sha256` | `sha256sum -c /etc/66/hooks.sha256` | All checksums pass |
| **CK-005** | No hook script has `setuid` or unnecessary elevated privileges | `find /etc/66/init.d/ /usr/lib/66/hooks/ -perm /u+s -type f` | Empty result set |

### 2.2 Boot Timing & Ordering

| Test ID | Criterion | Measurement Method | Pass Threshold |
|---------|-----------|--------------------|----------------|
| **CK-006** | Total hook sequence duration from init start to multi-user target | `systemd-analyze boot` equivalent for 66+s6; measure `clock_gettime` around HOOK-001 through HOOK-006 | < 8 seconds |
| **CK-007** | No dependency cycles in `66 -r dump` or `s6-svc -d` analysis | `66 -r dump | cypher -c`; `s6-svc -d` cycle detection | Zero cycles reported |
| **CK-008** | GPU hook (`/etc/s6-serv/enabled/05-gpu`) only activates after `/dev/dri` availability | Monitor `/dev/dri` mknod timing relative to HOOK-005 start | GPU hook start time > `/dev/dri` creation time |
| **CK-009** | Interruptible hooks support `s6-svc -t` timeout signaling | Send `SIGTERM` via `s6-svc -t 5s` during HOOK-004 execution; verify no filesystem corruption | Clean exit, no fsck required |

### 2.3 Failure Recovery

| Test ID | Criterion | Measurement Method | Pass Threshold |
|---------|-----------|--------------------|----------------|
| **CK-010** | Failed hook rollback via `/usr/lib/66/hooks/rollback` completes within 5 seconds | Execute rollback script; measure duration with `date +%s` | Duration ≤ 5s |
| **CK-011** | Journal entry created in `/var/log/sunshineos/hooks.log` for each hook outcome | `grep -c "HOOK-.*:.*PASSED\|FAILED" /var/log/sunshineos/hooks.log` | Entry count = number of hooks executed |
| **CK-012** | Kernel module signing policy enforced via `s6-key` or equivalent | `s6-key list --trusted` includes all modules loaded by HOOK-009 | 100% modules trusted |

### 2.4 Security & Integrity

| Test ID | Criterion | Measurement Method | Pass Threshold |
|---------|-----------|--------------------|----------------|
| **CK-013** | All hook scripts execute under unprivileged user where possible | `stat -c %U /usr/lib/66/hooks/*` | No hook runs as root unless mandated |
| **CK-014** | No hook contains hardcoded credentials, API keys, or token strings | `grep -Ri "KEY\|SECRET\|TOKEN" /etc/66/init.d/ /usr/lib/66/hooks/` | Zero matches (excluding comments) |
| **CK-015** | Hook execution environment is sandboxed via `unshare` or `seccomp` | `cat /proc/<pid>/status | grep Seccomp` | Seccomp filter present for hook processes |

---

## 3. Evidence Paths & Test Identifiers

**Repository-Relative Structure:**

```
/home/tak_0/sunshineos-audit/SunshineOS_Development-Testing/
├── autonomy/
│   └── results/
│       ├── hook_ordering_survey_2026-11-21.md          (this deliverable)
│       └── kernel_integration_checklist_2026-11-21.md
├── evidence/
│   ├── 66_hook_catalogue/
│   │   ├── file_paths_verified.txt
│   │   └── dependency_graph.dot
│   └── kernel_hooks/
│       ├── sha256_checksums.txt
│       └── boot_timing_measurements.log
├── reports/
│   ├── USER_MIGRATION_MANDATE_2026-11-21.md
│   └── ARCHITECTURE_DECISIONS.md
└── evolution-engine/
    └── (migration engine implementation)
```

**Associated Test ID Prefixes:**
- `HOOK-SURVEY-WAVE1` — Hook ordering survey completion (Wave 1)
- `CK-001` through `CK-015` — Kernel integration acceptance criteria
- `EVI-66PATH-20261121` — File path evidence package (evidence/66_hook_catalogue/)
- `EVI-KERN-HASH-20261121` — SHA-256 integrity evidence (evidence/kernel_hooks/sha256_checksums.txt)
- `EVI-BOOT-TIMING-20261121` — Boot timing measurements (evidence/kernel_hooks/boot_timing_measurements.log)

---

## 4. Wave 1 Deliverable Summary

- **Catalogued** 15 critical hook entry points across `/etc/66/`, `/etc/s6-serv/`, `/usr/lib/66/`, `/usr/lib/s6/`
- **Defined** ordering semantics: numeric prefixing in 66, dependency DAGs in s6, cross-bridge mediation via `/etc/66/s6-bridge/config`
- **Established** 15 measurable acceptance criteria (CK-001 through CK-015) for kernel hook integration
- **Mapped** evidence paths and test identifiers for reproducibility across evolutionary milestones
- **All file paths** consistent with `/home/tak_0/sunshineos-audit/SunshineOS_Development-Testing` repository structure
- **No credentials, tokens, or key material** included in this deliverable
- **Next wave** (Wave 2): Implement hook ordering validation within the migration engine's state inventory component, integrate with Evolutionary Ledger E010→E011 transition

---

**Generated:** 2026-11-21T00:00:00Z  
**Context:** SunshineOS evolutionary migration — Obarun/66+s6 deepening, Wave 1 of 40+ planned milestones  
**Governed by:** Migration Mandate invariants M-01 through M-09 (target-state driven, staged, recoverable, repeatable)
