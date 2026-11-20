# sub-repair-engine / pacman database / Obarun/66+s6

- Agent: sub-repair-engine
- Model: nvidia/nemotron-3.5-lightning:free
- Parent directive: none
- Completed: 2026-11-21 00:18

---

# Wave 1: Pacman Database Survey & Catalogue in Obarun/66+s6 Context
**Repository:** `/home/tak_0/sunshineos-audit/SunshineOS_Development-Testing`  
**Context Files:** `reports/USER_MIGRATION_MANDATE_2026-11-21.md`, `reports/ARCHITECTURE_DECISIONS.md`, `autonomy/results`  
**Test ID Scheme:** `OBARUN-PACMAN-W1-<sequence>`  
**Evidence Path Convention:** `evidence/wave1/obarun-pacman/<test-id>/`

---
## 1. Preconditions & Environment Requirements

| Requirement | Specification |
|-------------|---------------|
| **Target System** | Obarun Linux with s6-init init system (version 66+s6 lineage) |
| **Package Manager** | pacman v6.x with libalpm |
| **Database Location** | `/var/lib/pacman/` (standard Arch-compatible location, may vary with s6 overlay) |
| **Rollback Target** | Pre-survey pacman database dump at `evidence/wave1/obarun-pacman/OBARUN-PACMAN-W1-000/base-dump.tar.zst` |
| **Idempotency Guard** | Must not modify `/var/lib/pacman/sync/` or `/var/lib/pacman/local/` beyond read-only catalogue operations |
| **Required Tools** | `pacman -Q`, `pacman -Qm`, `pacman -Qq`, `tar`, `zstd`, `sha256sum`, `s6-svc` (for service state check) |

---
## 2. Idempotent Survey Primitives

### 2.1 Raw Database Inventory (Read-Only)
```bash
# Generate canonical inventory of locally installed packages
pacman -Qqe | sort > /tmp/obarun-pacman-local-$(date +%Y%m%d-%H%M%S).txt

# Generate inventory of explicitly installed packages
pacman -Qqe | grep -v '^$(pacman -Qqm | head -1)$' | sort > /tmp/obarun-pacman-explicit-$(date +%Y%m%d-%H%M%S).txt

# Generate package version map with architectures
pacman -Qi | grep -E '^(Name|Version|Arch)' > /tmp/obarun-pacman-meta-$(date +%Y%m%d-%H%M%S).txt
```

### 2.2 s6-Service-Conscious Pacman State
```bash
# Capture pacman database state while ensuring no s6 services are actively modifying it
s6-svc -t /var/run/s6/services/pacman 2>/dev/null || true
sleep 2
pacman -Qqe | sort > evidence/wave1/obarun-pacman/OBARUN-PACMAN-W1-001/local-inventory-$(date +%Y%m%d-%H%M%S).txt
```

### 2.3 Database Integrity Verification (Idempotent)
```bash
# Verify pacman database integrity without modification
pacman -Qk 2>&1 | tee evidence/wave1/obarun-pacman/OBARUN-PACMAN-W1-002/integrity-check-$(date +%Y%m%d-%H%M%S).txt || true

# Generate hash of database files for change detection
sha256sum /var/lib/pacman/db.lck /var/lib/pacman/local/*/desc 2>/dev/null | sort > evidence/wave1/obarun-pacman/OBARUN-PACMAN-W1-003/db-hashes-$(date +%Y%m%d-%H%M%S).txt
```

---
## 3. File Path Catalogue

### 3.1 Core pacman Database Directories
```
evidence/wave1/obarun-pacman/
├── OBARUN-PACMAN-W1-000/          # Base reference (pre-survey dump)
│   ├── base-dump.tar.zst          # Compressed pacman local database dump
│   └── MIGRATION-INVARIANT.md     # Invariants captured at survey time
├── OBARUN-PACMAN-W1-001/          # Local inventory (read-only catalogue)
│   └── local-inventory-*.txt
├── OBARUN-PACMAN-W1-002/          # Integrity verification
│   └── integrity-check-*.txt
├── OBARUN-PACMAN-W1-003/          # File hashes
│   └── db-hashes-*.txt
├── OBARUN-PACMAN-W1-004/          # s6-conscious state capture
│   └── service-pause-log-*.txt
└── OBARUN-PACMAN-W1-005/          # Migration-ready summary
    └── catalogue-summary.json
```

### 3.2 Key Database Files (Catalogued Paths)
| File/Path | Purpose | Evidence ID |
|-----------|---------|-------------|
| `/var/lib/pacman/local/` | Per-package installation records | `OBARUN-PACMAN-W1-001` |
| `/var/lib/pacman/local/*/desc` | Package description & dependencies | `OBARUN-PACMAN-W1-003` |
| `/var/lib/pacman/local/*/files` | Installed file map | `OBARUN-PACMAN-W1-001` |
| `/var/lib/pacman/sync/` | Sync database mirrors | `OBARUN-PACMAN-W1-003` |
| `/var/lib/pacman/db.lck` | Lock file (must be absent during survey) | `OBARUN-PACMAN-W1-003` |
| `/etc/pacman.conf` | Pacman configuration | `OBARUN-PACMAN-W1-004` |
| `/etc/pacman.d/gnupg/` | Keyring for package verification | `OBARUN-PACMAN-W1-004` |

### 3.3 s6-Overlay Specific Paths
```
# Obarun/s6 may redirect or augment pacman behavior via service files
/etc/s6/services/ Pacman-related hooks (if present)
/var/lib/s6/pacman/  s6-managed pacman state (if applicable)
/run/s6/services/   Active service state snapshots
```

---
## 4. Rollback / Recovery Primitives

### 4.1 Database Restoration from Base Dump
```bash
# Stop any s6-managed pacman processes
s6-svc -o /var/run/s6/services/pacman 2>/dev/null || true

# Remove current local database
rm -rf /var/lib/pacman/local/*

# Restore from base dump (Wave 1 reference)
tar -xJf evidence/wave1/obarun-pacman/OBARUN-PACMAN-W1-000/base-dump.tar.zst -C /var/lib/pacman/

# Verify restoration
pacman -Qqe > /tmp/obarun-post-restore.txt
diff /tmp/obarun-pacman-local-base.txt /tmp/obarun-post-restore.txt && echo "ROLLBACK SUCCESSFUL" || echo "ROLLBACK DISCREPANCIES DETECTED"
```

### 4.2 Integrity Re-establishment
```bash
# Refresh package databases (safe, non-destructive)
pacman -Sy

# Fix any detected corruption
pacman -K /var/lib/pacman/local/*/desc

# Re-sign if keyring requires (document in evidence)
```

---
## 5. Migration Invariants Alignment

| Invariant | Survey Alignment |
|-----------|-----------------|
| **M-04**: The actual installation is authoritative | Catalogue reflects live `/var/lib/pacman/` state, not assumed release numbers |
| **M-07**: Historical artifacts are archived | Base dump `base-dump.tar.zst` serves as immutable historical anchor |
| **M-09**: Migration must be repeatable | Idempotent commands produce identical catalogue outputs when run on identical state |
| **M-01**: Migration is target-state driven | Catalogue informs target-profile `TP` definition for pacman database migration |
| **M-06**: Migration operations must be recoverable | Rollback primitives restore pre-survey state from archived base dump |

---
## 6. Test ID & Evidence Index

| Test ID | Description | Command Source | Evidence Path |
|---------|-------------|----------------|---------------|
| `OBARUN-PACMAN-W1-000` | Base pre-survey dump | `tar -cJf /home/tak_0/sunshineos-audit/SunshineOS_Development-Testing/evidence/wave1/obarun-pacman/OBARUN-PACMAN-W1-000/base-dump.tar.zst /var/lib/pacman/local/` | `evidence/wave1/obarun-pacman/OBARUN-PACMAN-W1-000/base-dump.tar.zst` |
| `OBARUN-PACMAN-W1-001` | Local package inventory | `pacman -Qqe | sort` | `evidence/wave1/obarun-pacman/OBARUN-PACMAN-W1-001/local-inventory-*.txt` |
| `OBARUN-PACMAN-W1-002` | Integrity check | `pacman -Qk` | `evidence/wave1/obarun-pacman/OBARUN-PACMAN-W1-002/integrity-check-*.txt` |
| `OBARUN-PACMAN-W1-003` | Database file hashes | `sha256sum /var/lib/pacman/*` | `evidence/wave1/obarun-pacman/OBARUN-PACMAN-W1-003/db-hashes-*.txt` |
| `OBARUN-PACMAN-W1-004` | s6-conscious state | `s6-svc -t /var/run/s6/services/pacman && sleep 2` | `evidence/wave1/obarun-pacman/OBARUN-PACMAN-W1-004/service-pause-log-*.txt` |
| `OBARUN-PACMAN-W1-005` | Migration summary | `cat evidence/wave1/obarun-pacman/OBARUN-PACMAN-W1-001/*.txt | sha256sum > catalogue-summary.json` | `evidence/wave1/obarun-pacman/OBARUN-PACMAN-W1-005/catalogue-summary.json` |

---
## 7. Wave 1 Deliverable Checklist

- [ ] Execute all idempotent survey primitives on target Obarun/66+s6 system
- [ ] Archive base dump to `evidence/wave1/obarun-pacman/OBARUN-PACMAN-W1-000/`
- [ ] Populate all test ID evidence directories with command output
- [ ] Verify `sha256sum` consistency across repeat runs (idempotency guard)
- [ ] Document any deviations from standard Arch pacman paths (s6 overlays)
- [ ] Store rollback primitives in `evidence/wave1/obarun-pacman/ROLLBACK-PRIMITIVES.md`
- [ ] Align findings with migration invariants M-01, M-04, M-06, M-07, M-09
- [ ] Publish results to corresponding development branch per mandate M-10

---
*End of Wave 1 Deepening. Subsequent waves will deepen catalogue granularity, incorporate version schema integration (INV7/TC18), and transition to evolutionary state reconstruction.*
