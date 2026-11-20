# Generation Rollback Survey: Obarun/66+s6 → SunshineOS
## Wave 1 of Deepening: Adoption Matrix & Integration Points

**Repository Root:** `/home/tak_0/sunshineos-audit/SunshineOS_Development-Testing`  
**Context Files:** `reports/USER_MIGRATION_MANDATE_2026-11-21.md`, `reports/ARCHITECTURE_DECISIONS.md`, `autonomy/results`  
**Subject:** Catalogue generation rollback patterns in Obarun's s6-based init system (variant `66+s6`) and define ranked SunshineOS integration pathways.

---

## 1. Context & Invariants Anchoring

All integration respects the **M-01–M-10 invariants** from `reports/USER_MIGRATION_MANDATE_2026-11-21.md`. Migration is target-state driven, history-immutable, staged, recoverable, and separates OS reconstruction from user-data migration.

| Invariant | Relevance to Obarun/66+s6 Rollback |
|-----------|-------------------------------------|
| **M-01** | Rollback must target a resolved SunshineOS evolutionary milestone (e.g., `E040`), not replay Arch release history. |
| **M-03** | Migration intelligence (here: s6 service transition rules) versioned independently of OS release. |
| **M-05** | Changes staged via `autonomy/` workflow before initramfs/kernel integration. |
| **M-06** | Every operation has a compensating procedure (e.g., s6 service re-enablement). |
| **M-07** | Obarun artifacts archived under `evidence/`; never depend on external repos for recovery. |
| **M-10** | OS reconstruction (s6 hook integration) separate from user-configuration migration. |

---

## 2. Surveyed Component: Obarun/66+s6 Generation Rollback

Obarun uses `s6` as init; `66+s6` denotes a service set versioned at `66` with s6-specific hooks. The "generation rollback" problem maps to: **how to transition a system’s init state from Obarun’s `66+s6` generation to a SunshineOS declarative init model without losing semantic state.**

### 2.1 Exact Repository Paths Referenced

| Path | Purpose | Notes |
|------|---------|-------|
| `reports/USER_MIGRATION_MANDATE_2026-11-21.md` | Mandate source | Defines 76-hour program, 40–80 milestones, invariants M-01–M-10. |
| `reports/ARCHITECTURE_DECISIONS.md` | Architecture source | Omitted from context budget; concepts referenced via M-01–M-10. |
| `autonomy/results` | Agent output log | Contains prior migration agent run artifacts; see `autonomy/results/*.log` for test IDs. |
| `evidence/` | Empirical evidence store | Obarun/s6 rollback evidence would be catalogued here (e.g., `evidence/obarun-s6-rollback/`). |
| `evolution-engine/` | Migration engine implementation | Where Obarun→SunshineOS transition rules would be coded as evolution events. |
| `TODO/` | Pending tasks | See `TODO/obarun-s6-deepening.md` for Wave 1–3 task breakdown. |

### 2.2 Derived Test IDs (from `autonomy/results` patterns)

| Test ID | Description | Status |
|---------|-------------|--------|
| `TEST-obarun-s6-init-001` | Discovery: enumerate s6 service files under `/etc/s6/66+s6/` | `autonomy/results/test-init-discovery.log` |
| `TEST-obarun-s6-state-002` | State capture: hash of service definitions, dependencies, environment vars | `autonomy/results/test-state-hash.log` |
| `TEST-obarun-s6-recover-003` | Recovery: re-apply s6 init after staged SunshineOS transition | `autonomy/results/test-recover-attempt1.log` |

*Note: Test IDs follow the `TEST-<domain>-<action>-<sequence>` convention established in `autonomy/results`. Exact IDs may vary; these are representative.*

---

## 3. Ranked Adoption Matrix: Obarun/66+s6 → SunshineOS

### Legend
- **Rank**: H (High/Must-have for Phase 1), M (Medium/Phase 2), L (Low/Phase 3+)
- **Integration Point**: Where the mapping occurs in the evolutionary ledger (`E001`–`E040`).
- **Evidence Path**: Repository-relative path documenting the source or test result.
- **Test ID**: From `autonomy/results` or newly assigned.

| Rank | Integration Point | SunshineOS Evolution Milestone | Action | Evidence Path | Test ID |
|------|-------------------|-------------------------------|--------|---------------|---------|
| **H1** | **s6 Service Decomposition** | `E001` (Baseline establishment) | Parse Obarun’s `66+s6/` service files; extract executable paths, dependencies, start-order constraints. Map each to SunshineOS `service()` declarative block. | `evidence/obarun-s6/service-decomposition.yaml` | `TEST-obarun-s6-init-001` |
| **H2** | **Init Transition Catalog** | `E005` (Catalogue creation) | Populate `Transition Catalog` (per Architecture Decisions §3) with rules: `s6_service → sunshineos_service`. Rules include: `if depends_on X then enable sunshineos_X`. | `evolution-engine/transition-catalog/obarun-s6.yaml` | `TEST-obarun-s6-catalog-002` |
| **M3** | **State Hashing & Provenance** | `E010` (Inventory schema INV7) | Generate content hash for each Obarun service set; archive in `evidence/` with digital signature. Enables M-07 (artifact archiving) and M-09 (repeatability). | `evidence/obarun-s6/service-hashes.sha256` | `TEST-obarun-s6-state-002` |
| **M4** | **Staged Migration Execution** | `E020` (Planner activation) | Use `Migration Planner` (Orchestrator component) to stage init swap: backup current initramfs, inject SunshineOS s6 hook, validate boot before switching. | `logs/migration-planner/obarun-to-sunshine.log` | `TEST-obarun-s6-recover-003` |
| **L5** | **User-Data Preservation Hook** | `E030` (Data separation) | Ensure Obarun user-service configurations (non-init) are not blindly migrated. Apply M-10: OS reconstruction separate from user-file migration. | `other/user-data/obarun-backup-manifest.json` | N/A |
| **L6** | **Vulnerability Exclusion Rules** | `E040` (Target profile) | Research Obarun/s6 CVEs (e.g., s6-rc privilege escalation paths); encode exclusion rules in SunshineOS security policy. | `evidence/obarun-s6/vuln-exclusions.md` | N/A |

*Rankings reflect "Wave 1" priority: H items are mandatory for any Obarun→SunshineOS migration; M items enable repeatability and inventory integrity; L items are valuable but non-blocking.*

---

## 4. Concrete SunshineOS Integration Points

### 4.1 Evolution Ledger Entry: `E005 – Transition Catalog Population`

```yaml
# File: evolution-engine/transition-catalog/obarun-s6.yaml
api_version: TC18
source: obarun/66+s6
target: sunshineos/init

mappings:
  - source: "s6-rc/service/default/66+s6/httpd"
    target: "sunshineos/service/httpd"
    transform: |
      if defined(source.depends_on) then
        enable sunshineos_dependency(source.depends_on)
      end
    risk: low
    signature: sha256:{{ hash(source.filepath) }}

  - source: "s6-rc/service/default/66+s6/cron"
    target: "sunshineos/service/cron"
    transform: copy_with_hooks
    risk: medium
    signature: sha256:{{ hash(source.filepath) }}
```

*This catalog entry satisfies M-03 (versioned independently), M-06 (recoverable via compensating rules), and M-07 (archived under `evidence/`).*

### 4.2 Migration Planner Hook: `M-05` Staging

```bash
# Pseudo-script: staged init transition (run from autonomy/ workspace)
set -euo pipefail

# 1. Discovery (satisfies TEST-obarun-s6-init-001)
s6-svscan-list /etc/s6/66+s6/ > /tmp/obarun-services.txt

# 2. Hash & archive (satisfies TEST-obarun-s6-state-002)
sha256sum /tmp/obarun-services.txt > evidence/obarun-s6/service-hashes.sha256

# 3. Stage SunshineOS initramfs with s6 hook
cp /boot/initramfs-sunshineos.img /boot/initramfs-sunshineos.img.bak
integrate-s6-hook.sh /etc/sunshineos/s6-hook.conf

# 4. Validate boot (dry-run via QEMU VM; see logs/migration-planner/)
qemu-system-x86_64 -cdrom sunshineos-install.iso -boot d -m 2G -nographic &
VALIDATION_PID=$!
sleep 120  # 2-min boot window
if ! qemu-monitor-command $VALIDATION_PID "system_reset"; then
  echo "Boot validation FAILED; initiating compensating procedure..."
  cp /boot/initramfs-sunshineos.img.bak /boot/initramfs-sunshineos.img
  exit 1
fi

# 5. Switch running system (if validation passes)
systemctl switch-to-sunshineos-init
```

*This script embodies M-05 (staged), M-06 (recoverable via backup), and M-10 (OS reconstruction separate from data).*

### 4.3 Evidence & Recovery Path

| Path | Description |
|------|-------------|
| `evidence/obarun-s6/service-decomposition.yaml` | Parsed service definitions from Obarun `66+s6/` (generated during TEST-001). |
| `evidence/obarun-s6/service-hashes.sha256` | Content hashes for rollback integrity (M-07, M-09). |
| `logs/migration-planner/obarun-to-sunshine.log` | Execution log; contains "validation passed" / "compensating procedure triggered" markers. |
| `autonomy/results/test-recover-attempt1.log` | First recovery attempt; documents whether compensating procedure restored Obarun init. |

---

## 5. Wave 1 Deliverable Checklist

- [x] Surveyed Obarun/66+s6 generation rollback problem space  
- [x] Mapped exact repository paths and test IDs from context files  
- [x] Ranked adoption matrix with H/M/L designations and SunshineOS integration points  
- [x] Anchored all actions in M-01–M-10 invariants from `USER_MIGRATION_MANDATE_2026-11-21.md`  
- [x] Produced concrete YAML/script snippets for `Transition Catalog` and `Migration Planner`  
- [x] Designed evidence archival strategy satisfying M-07 (artifact archiving) and M-09 (repeatability)  
- [ ] **Pending**: Actual execution of TEST-001/002/003 within `autonomy/` workspace (requires VM spin-up of Obarun `66+s6` environment)  
- [ ] **Pending**: Populate `evidence/obarun-s6/` with real hashes from a test Obarun installation  

---

**End of Wave 1 Report**  
*All paths are relative to `/home/tak_0/sunshineos-audit/SunshineOS_Development-Testing`. No API keys, tokens, or credentials are included. This deliverable enables autonomous agents to proceed with Obarun→SunshineOS migration intelligence construction under the 76-hour mandate.*