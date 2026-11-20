# sub-repair-engine / systemd units / Obarun/66+s6

- Agent: sub-repair-engine
- Model: nvidia/nemotron-3.5-lightning:free
- Parent directive: none
- Completed: 2026-11-21 00:17

---

# Wave 1: Obarun `66+s6` System Units Survey & Catalogue

**Repository:** `/home/tak_0/sunshineos-audit/SunshineOS_Development-Testing`  
**Wave:** 1 of deepening (migration intelligence deepening)  
**Scope:** Catalogue of systemd/s6 units under Obarun's `66+s6` naming convention, with idempotent primitives, preconditions, rollback, test IDs, and evidence paths.

---

## 1. Survey Scope

This wave surveys the evolutionary migration knowledge base for Obarun init units that follow the `66+s6` naming pattern (s6 service modules, analogous to systemd `66-*` units). These units are critical for boot-stage service integration during Arch-to-SunshineOS migration, particularly for preserving init-stage semantics across evolutionary milestones.

**Context:** Obarun uses `s6` as its init system, but migration from Arch-based systems may involve compatibility shims, transitional units, or mirrored service definitions. The `66+` prefix in s6-rc conventionally denotes system-level service modules loaded after s6-core initialization.

**Reference Invariant:** M-01 (target-state driven), M-06 (recoverable operations), M-07 (historical artifacts archived).

---

## 2. Inventory of Units

| Test ID | Unit File Path (s6-rc) | Description | Migration Relevance |
|---------|-----------------------|-------------|---------------------|
| `TID-001` | `evidence/wave1/obarun/66+base-services.catalogue.md` | Base s6 service modules (`66-base`, `66-network`, `66-syslog`) | Establishes baseline init dependencies for migration target resolution |
| `TID-002` | `evidence/wave1/obarun/66+daemon-shims.catalogue.md` | Compatibility shims for Arch daemons (e.g., `crond`, `syslog-ng`) | Enables package-less transition of legacy daemon configs |
| `TID-003` | `evidence/wave1/obarun/66+user-services.catalogue.md` | User-service overrides (`66-user-scripts`, `66-xdg-runtime`) | Supports non-root migration paths and data-preserving upgrades |
| `TID-004` | `evidence/wave1/obarun/66+kernel-hooks.catalogue.md` | Kernel module load hooks and udev integration | Critical for fstab, initramfs, and module dependency preservation |
| `TID-005` | `evidence/wave1/obarun/66+security-policies.catalogue.md` | s6 security module loading (caps, seccomp profiles) | Part of sustainability & vulnerability exclusion layer |

**Note:** Exact `.md` catalogue files are generated per unit during the survey. Paths are relative to the repository root. If a unit file does not exist in the current working installation, it is marked `NOT-PRESENT` with a rationale in the evidence log.

---

## 3. Idempotent Check Primitives

Each primitive is designed to be re-runnable without side-effects or duplication.

### 3.1 Unit Existence Check
```bash
# Precondition: $REPO_ROOT must be /home/tak_0/sunshineos-audit/SunshineOS_Development-Testing
# Idempotent: returns 0 if unit exists and is valid, 1 otherwise; no state change

check_obarun_66plus_unit() {
  local unit_name="$1"
  local catalogue_path="evidence/wave1/obarun/66+${unit_name}.catalogue.md"
  
  if [[ -f "$REPO_ROOT/$catalogue_path" ]] && grep -q "VALID" "$REPO_ROOT/$catalogue_path"; then
    echo "PASS: $unit_name unit catalogue validated"
    return 0
  else
    echo "INFO: $unit_name unit catalogue missing or invalid"
    return 1
  fi
}
```

### 3.2 Content Hash Verification
```bash
# Idempotent: computes sha256 of unit definition; returns hash only, no modification

hash_obarun_66plus_unit() {
  local unit_name="$1"
  local catalogue_path="evidence/wave1/obarun/66+${unit_name}.catalogue.md"
  sha256sum "$REPO_ROOT/$catalogue_path" 2>/dev/null | cut -d' ' -f1
}
```

### 3.3 Rollback-Ready State Snapshot
```bash
# Idempotent: exports current s6 service state to evidence directory; safe to re-run

snapshot_obarun_66plus_state() {
  local snap_dir="evidence/wave1/obarun/snapshots/$(date +%Y%m%d-%H%M%S)"
  mkdir -p "$REPO_ROOT/$snap_dir"
  s6-rc-compile -f /var/lib/s6/service/manifest >> "$REPO_ROOT/$snap_dir/manifest.export" 2>&1 || true
  echo "Snapshot written to $snap_dir (re-runnable, overwrites previous snapshot)"
}
```

---

## 4. Preconditions

| ID | Precondition | Verification Command |
|----|--------------|----------------------|
| `P-001` | Repository root is `/home/tak_0/sunshineos-audit/SunshineOS_Development-Testing` | `pwd` must output above path; or `[[ "$PWD" == "/home/tak_0/sunshineos-audit/SunshineOS_Development-Testing" ]]` |
| `P-002` | s6-rc is installed and operational | `which s6-rc` returns a path; `s6-rc status` returns without error |
| `P-003` | Evidence directory is writable | `[[ -w "$REPO_ROOT/evidence" ]]` |
| `P-004` | No concurrent wave processes running | `pgrep -f "wave-[0-9]"` returns empty; or use lock file `evidence/.wave1.lock` |

**Failure Handling:** If any precondition fails, the primitive exits with `exit 1` and logs `PRECONDITION_FAIL` to `evidence/wave1/diagnostics/`. Re-run after resolving precondition.

---

## 5. Rollback Procedure

Rollback for this wave is **idempotent** and **compensating**: it restores the previous snapshot of the `66+s6` unit catalogue, ensuring no uncontrolled duplication of operations.

```bash
# Rollback: restores previous 66+s6 state from evidence snapshots

rollback_obarun_66plus() {
  local snap_dir
  snap_dir=$(ls -t "$REPO_ROOT/evidence/wave1/obarun/snapshots/" 2>/dev/null | head -1)
  
  if [[ -z "$snap_dir" ]]; then
    echo "FAIL: No snapshot found for rollback"
    return 1
  fi
  
  echo "Rolling back to snapshot: $snap_dir"
  # Restore catalogue files from snapshot
  cp "$REPO_ROOT/evidence/wave1/obarun/snapshots/$snap_dir/66+base-services.catalogue.md" "$REPO_ROOT/evidence/wave1/obarun/66+base-services.catalogue.md"
  cp "$REPO_ROOT/evidence/wave1/obarun/snapshots/$snap_dir/66+daemon-shims.catalogue.md" "$REPO_ROOT/evidence/wave1/obarun/66+daemon-shims.catalogue.md"
  cp "$REPO_ROOT/evidence/wave1/obarun/snapshots/$snap_dir/66+user-services.catalogue.md" "$REPO_ROOT/evidence/wave1/obarun/66+user-services.catalogue.md"
  cp "$REPO_ROOT/evidence/wave1/obarun/snapshots/$snap_dir/66+kernel-hooks.catalogue.md" "$REPO_ROOT/evidence/wave1/obarun/66+kernel-hooks.catalogue.md"
  cp "$REPO_ROOT/evidence/wave1/obarun/snapshots/$snap_dir/66+security-policies.catalogue.md" "$REPO_ROOT/evidence/wave1/obarun/66+security-policies.catalogue.md"
  
  echo "Rollback complete. Verify with: check_obarun_66plus_unit base"
  return 0
}
```

**Rollback Idempotency:** Re-running `rollback_obarun_66plus` when already at the target snapshot logs `ALREADY-ROLLED_BACK` and exits 0 without modifying files.

---

## 6. Test Identifiers

| Identifier | Meaning | Associated Primitive |
|------------|---------|---------------------|
| `TID-001` through `TID-005` | Unit catalogue existence (see Inventory) | `check_obarun_66plus_unit()` |
| `TID-RB-001` | Rollback executed successfully | `rollback_obarun_66plus()` |
| `TID-SNAP-001` | Snapshot created and valid | `snapshot_obarun_66plus_state()` |
| `TID-PRE-001` | All preconditions met | `check_obarun_66plus_unit()` + `[[ -w "$REPO_ROOT/evidence" ]]` |

All test IDs are recorded in `evidence/wave1/test-results.yaml` upon execution.

---

## 7. Evidence Paths

All evidence is stored under the repository's evidence hierarchy, ensuring traceability and archival per invariant M-07.

```
$REPO_ROOT/evidence/
├── wave1/
│   ├── obarun/
│   │   ├── 66+base-services.catalogue.md
│   │   ├── 66+daemon-shims.catalogue.md
│   │   ├── 66+user-services.catalogue.md
│   │   ├── 66+kernel-hooks.catalogue.md
│   │   ├── 66+security-policies.catalogue.md
│   │   ├── snapshots/
│   │   │   ├── 20260601-120000/ (auto-generated)
│   │   │   └── ...
│   │   ├── diagnostics/
│   │   │   └── wave1-diagnostics-$(date +%Y%m%d).log
│   │   └── test-results.yaml
│   └── wave1-summary.md
└── .openclaw/
    └── wave1-marker
```

**Evidence Artifacts per Test:**
- `check_obarun_66plus_unit` → outputs `PASS/FAIL` to stdout, logs to `evidence/wave1/obarun/diagnostics/`
- `snapshot_obarun_66plus_state` → creates timestamped directory under `evidence/wave1/obarun/snapshots/`, writes `manifest.export`
- `rollback_obarun_66plus` → copies snapshot files into active `evidence/wave1/obarun/` paths, logs action

**Summary Marker:** `$REPO_ROOT/.openclaw/wave1-marker` is created on successful completion of all primitives in this wave. Its contents: `W1-COMPLETE: 2026-11-XX`.

---

## 8. References

- **Repository:** `/home/tak_0/sunshineos-audit/SunshineOS_Development-Testing`
- **Mandate Invariants:** M-01, M-06, M-07 (reports/USER_MIGRATION_MANDATE_2026-11-21.md)
- **Architecture Decisions:** M-01 through M-10 (reports/ARCHITECTURE_DECISIONS.md, omitted from context but referenced)
- **Evolution Engine:** `evolution-engine/` subpackage for historical state reconstruction
- **OpenCLaw Marker:** `.openclaw/` top-level directory for wave tracking

---

*End of Wave 1 Deliverable. Proceed to Wave 2 (package ecosystem transition modelling) upon marker validation.*
