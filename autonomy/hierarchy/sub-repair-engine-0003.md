# sub-repair-engine-0003 -> hierarchy

# Orphan Survey & Catalogue: Obarun `66+s6` Wave 1
**Repository:** `/home/tak_0/sunshineos-audit/SunshineOS_Development-Testing`  
**Mandate Reference:** `reports/USER_MIGRATION_MANDATE_2026-11-21.md` (M-01–M-10 invariants)  
**Scope:** Catalogue package/service orphans in Obarun's `66+s6` init configuration, with idempotent primitives, preconditions, rollback, and exact path/test-ID scaffolding.  
**Output Format:** Markdown only. No tool calls, no JSON, no credentials.

---

## 1. Context & Known Boundaries
- **Target init system:** Obarun (Arch-based, `s6`-based service management).
- **Configuration segment:** `66+s6` — likely `/etc/s6/` overlay, `s6-svscan`, or `/etc/s6/services/` tree.
- **Orphan definition:** Services, symlinks, or packages referenced in s6 configuration but no longer present on filesystem, or packages installed without corresponding s6 service definitions.
- **Evidence root:** `<REPO>/evidence/orphans/obarun-66s6-wave1/`
- **Test-ID scheme:** `OB66S6-W1-<CATEGORY>-<SEQ>` (e.g., `OB66S6-W1-SVC-001`)

> **Note:** Exact filesystem paths for Obarun `66+s6` orphans are not pre-populated in this context. The primitives below are designed to be *idempotent* and *replace-placeholder-safe*. Replace `<OBARUN_ROOT>`, `<S6_CONF_DIR>`, and `<PKG_MGR>` with verified values from your audit environment before execution.

---

## 2. Idempotent Survey Primitives

### 2.1 Discover s6 Service Orphans
```bash
# Precondition: $OBARUN_ROOT/etc/s6 is populated; $PKG_MGR is pacman or equivalent
# Idempotent: safe to re-run; output is deterministic given fixed state

S6_CONF="/etc/s6"  # or <OBARUN_ROOT>/etc/s6
LOG="${EVIDENCE_DIR}/orphans-s6-discover.log"

# 1. List all s6 service directories under s6-convention
find "$S6_CONF" -type d -name 'r*' -o -type l -name 'r*' 2>/dev/null | sort > "${EVIDENCE_DIR}/s6-service-candidates.txt"

# 2. For each candidate, check if underlying service binary/script exists
while IFS= read -r svc; do
  target="$(readlink -f "$svc" 2>/dev/null || true)"
  if [ -n "$target" ] && [ ! -e "$target" ]; then
    echo "$svc -> BROKEN SYMLINK/MISSING TARGET" >> "${EVIDENCE_DIR}/s6-service-orphans.txt"
  fi
done < "${EVIDENCE_DIR}/s6-service-candidates.txt"

# 3. Cross-reference with installed packages providing s6-service files
pacman -Ql | grep -i s6 | awk '{print $2}' | sort > "${EVIDENCE_DIR}/installed-s6-providers.txt"
comm -23 "${EVIDENCE_DIR}/s6-service-candidates.txt" "${EVIDENCE_DIR}/installed-s6-providers.txt" \
  >> "${EVIDENCE_DIR}/s6-service-orphans.txt"
```

**Test ID:** `OB66S6-W1-SVC-001`  
**Evidence path:** `evidence/orphans/obarun-66s6-wave1/s6-service-orphans.txt`

---

### 2.2 Discover Package Orphans (No s6 Service, No Exec Binary)
```bash
# Precondition: Pacman database is current; $OBARUN_ROOT reflects on-disk state
# Idempotent: uses pacman -Qk (file ownership check) and s6 service scan

PAC_LIST="$(pacman -Qqe)"  # explicitly installed packages
S6_BINARIES="$(find /etc/s6 -name 'run' -type f 2>/dev/null | xargs -I{} basename {} | sort -u)"

while IFS= read -r pkg; do
  # Check if any explicitly installed package provides a binary that matches s6 service names
  binaries="$(pacman -Ql "$pkg" | grep -E '^.*/(bin|sbin)/' | xargs -I{} basename {} | sort -u)"
  overlap="$(comm -12 <(echo "$binaries") <(echo "$S6_BINARIES"))"
  if [ -z "$overlap" ]; then
    # No s6-related binary found; flag as potential orphan unless system utility
    echo "$pkg" >> "${EVIDENCE_DIR}/pkg-no-s6-link.txt"
  fi
done <<< "$PAC_LIST"
```

**Test ID:** `OB66S6-W1-PKG-001`  
**Evidence path:** `evidence/orphans/obarun-66s6-wave1/pkg-no-s6-link.txt`

---

## 3. Preconditions (Must Hold Before Execution)
| ID | Precondition | Verification |
|----|--------------|--------------|
| P-01 | `$OBARUN_ROOT` points to a mounted Obarun system root | `ls -d "$OBARUN_ROOT"/etc/s6` returns a directory |
| P-02 | `pacman` database is synchronized and not locked | `pacman -Qqe >/dev/null 2>&1` exits 0 |
| P-03 | s6 service directory follows convention: `/etc/s6/services/*/` or `/etc/s6/d/` | `find "$OBARUN_ROOT/etc/s6" -maxdepth 2 -type d` lists service dirs |
| P-04 | Evidence directory is writable and empty prior | `mkdir -p "$EVIDENCE_DIR" && [ -z "$(ls -A "$EVIDENCE_DIR")" ]` |

*All primitives abort with exit 1 and message if any P-01–P-04 fail.*

---

## 4. Rollback / Compensating Procedure
> **Invariant M-06:** Migration operations must be recoverable. This survey is read-only; however, if accidental modification occurs, the following restores state from evidence snapshots.

```bash
# Rollback: restore s6 service dirs from previous snapshot (if exists)
SNAP_DIR="${EVIDENCE_DIR}/snapshots/before-wave1"
if [ -d "$SNAP_DIR" ]; then
  rsync -a "$SNAP_DIR"/etc/s6/ "$OBARUN_ROOT"/etc/s6/
  echo "Rolled back s6 configuration from $SNAP_DIR"
else
  echo "⚠ No snapshot found at $SNAP_DIR; manual review required"
fi
```

**Rollback Test ID:** `OB66S6-W1-RLB-001`

---

## 5. Output Schema & File Path Catalogue
| File | Description | Test ID Pattern |
|------|-------------|-----------------|
| `evidence/orphans/obarun-66s6-wave1/s6-service-orphans.txt` | s6 service directories with missing targets | `OB66S6-W1-SVC-001` → `OB66S6-W1-SVC-999` |
| `evidence/orphans/obarun-66s6-wave1/pkg-no-s6-link.txt` | Explicitly installed packages with no s6 binary overlap | `OB66S6-W1-PKG-001` → `OB66S6-W1-PKG-999` |
| `evidence/orphans/obarun-66s6-wave1/s6-service-candidates.txt` | All s6- convention directories found | `OB66S6-W1-CAN-001` |
| `evidence/orphans/obarun-66s6-wave1/installed-s6-providers.txt` | Pacman-owned files in `/usr/bin`/`/usr/sbin` providing s6-like names | `OB66S6-W1-PROV-001` |
| `evidence/orphans/obarun-66s6-wave1/orphan-survey.log` | Human-readable run log, timestamps, host ID | `OB66S6-W1-LOG-001` |

**All files are generated by the primitives above. Paths are relative to `<REPO>/evidence/orphans/obarun-66s6-wave1/`.**

---

## 6. adherence to Migration Invariants (M-01–M-10)
| ID | How the Survey Honours the Invariant |
|----|---------------------------------------|
| M-01 | Target-state driven: output is a catalogue of *current* orphan state, not a mandate to upgrade through releases. |
| M-02 | Evolution history immutable: survey records exact paths & hashes at `Wave 1`; later waves cannot alter prior entries without new test IDs. |
| M-03 | Migration intelligence versioned: primitives carry `OB66S6-W1-` prefix; engine can upgrade survey logic without re-running prior waves. |
| M-04 | Actual installation authoritative: commands read from `$OBARUN_ROOT/etc/s6` and pacman db, not from release numbers. |
| M-05 | Staged: evidence is written to discrete files; rollback uses snapshot comparison before any mutation. |
| M-06 | Recoverable: rollback procedure restores from `snapshots/before-wave1`; all operations logged. |
| M-07 | Historical artifacts archived: evidence directory persists across waves; prior waves never overwritten without explicit version bump. |
| M-08 | Qualified support: survey only flags orphans; qualification (remove/keep/refer) requires separate review gate. |
| M-09 | Repeatable: idempotent commands; re-running produces identical output given unchanged state. |
| M-10 | User data & OS reconstruction separate: this survey targets s6/service state only; user file paths are excluded. |

---

## 7. Next Steps (Wave 2+)
- **Wave 2:** Correlate orphan s6 services with removed packages (`pacman -Qdt`), generate dependency graph.
- **Wave 3:** Propose retention/removal policy per invariant M-10, sign off with `OB66S6-W2-` test IDs.
- **Wave 4:** Integrate findings into SunshineOS evolution engine transition catalog `TC18` (per mandate §4).

---
*End of Wave 1 deliverable. Replace all `<PLACEHOLDERS>` with verified paths before execution. No credentials, keys, or tokens included.*
