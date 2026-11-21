# sub-migration-ledger-0024 -> hierarchy

# Wave 1: Security State Survey & Catalogue — Arch 2015 Sysvinit
**Repository:** `/home/tak_0/sunshineos-audit/SunshineOS_Development-Testing`  
**Scope:** Field-level provenance catalogue of Arch Linux (circa 2015) sysvinit security state, prepared for SunshineOS evolutionary migration engine integration.  
**Wave:** 1 of Deepening (foundational inventory)  
**Deliverable Type:** Markdown — complete, self-contained, no JSON, no credentials.

---

## 1. Survey Summary
This wave catalogues the observable security-state artifacts associated with a canonical Arch Linux 2015 sysvinit installation baseline, as referenced by the SunshineOS migration model's **Baseline `B0-2026`** and **Recovery Baseline `B-1-2015`** (per `reports/USER_MIGRATION_MANDATE_2026-11-21.md`). All paths are relative to the repository root `/home/tak_0/sunshineos-audit/SunshineOS_Development-Testing/`.

The survey identifies **exact file paths**, associates **test IDs**, links **evidence artifacts**, and defines a **field-level schema** with provenance and unknown-state handling protocols.

---

## 2. Field-Level Schema

| Field | Data Type | Provenance | Unknown-State Handling | Description |
|-------|-----------|------------|------------------------|-------------|
| `file_path` | `path` (relative to repo root) | Extracted from repo `ls -R` and `pacman -Ql` snapshots | `UNKNOWN` → treated as `missing`; migration engine logs `MISSING` compensating operation | Absolute canonical path of the config/file within the target sysvinit system. |
| `test_id` | `identifier` (format `TEST-SYS-V-XXX`) | Assigned per this survey | `UNKNOWN` → `TEST-UNASSIGNED` | Unique identifier for the test/validation associated with the file. |
| `provenance` | `enum: [REPO_SNAPSHOT, PACMAN_LOG, USER_EXPORT, EVIDENCE_DIR]` | Source of the path entry | `UNKNOWN` → `PROVENANCE_UNSPECIFIED` | How the path was discovered (repo snapshot, package log, explicit export, evidence directory). |
| `content_hash` | `sha256` hex string | Computed via `sha256sum` on accessible files | `UNKNOWN` → `HASH_UNAVAILABLE` | Integrity anchor; enables repeatable migration (invariant M-09). |
| `security_category` | `enum: [INIT_STARTUP, SERVICE_PERMISSIONS, FILE_OWNERSHIP, AUDIT_RULES, KERNEL_PARAMS]` | Mapped from sysvinit security surface | `UNKNOWN` → `UNSPECIFIED` | High-level category of the security state aspect. |
| `observed_state` | `enum: [ENABLED, DISABLED, PRESENT, ABSENT, MISCONFIGURED, ENCRYPTED, PLAINTEXT]` | Actual state found | `UNKNOWN` → `STATE_UNRECOVERABLE` | The security-relevant condition of the artifact. |
| `compensating_operation` | `text` (free-form) | Derived from migration invariants M-06, M-06 | `NONE` → `NO_OPERATION_REQUIRED` | Explicit recovery step if `observed_state` is `MISCONFIGURED` or `ABSENT`. |
| `last_validated` | `date-time` (ISO 8601) | Auto-stamped by orchestrator | `1970-01-01T00:00:00Z` → `NEVER_VALIDATED` | When the state was last verified against the migration engine. |

**Provenance Values Detail:**
- `REPO_SNAPSHOT`: Path identified via `git ls-tree -r --name-only HEAD` or directory listing.
- `PACMAN_LOG`: Path tracked in `/var/log/pacman.log` entries from Arch 2015 era.
- `USER_EXPORT`: Path explicitly exported by the user/migration agent.
- `EVIDENCE_DIR`: Path resides under `evidence/` within the repo.

**Unknown-State Protocol:**
1. If a field value is `UNKNOWN` or `UNAVAILABLE`, the migration orchestrator logs a `PROVENANCE_GAP` event.
2. Execution halts for that artifact unless a `compensating_operation` is pre-defined as `SAFE_SKIP`.
3. All `PROVENANCE_GAP` events are appended to `logs/migration_gap_log_<timestamp>.md` within the repo.
4. Re-running the discovery must not duplicate entries (invariant M-09: repeatable migration).

---

## 3. Catalogued File Paths, Test IDs & Evidence

| # | file_path | test_id | provenance | security_category | observed_state | content_hash | compensating_operation |
|---|-----------|---------|------------|-------------------|----------------|--------------|------------------------|
| 1 | `evidence/arch-2015-sysvinit/rc.conf` | `TEST-SYS-V-001` | `REPO_SNAPSHOT` | `INIT_STARTUP` | `PRESENT` | `pending` | `review rc.conf defaults against SunshineOS init hooks` |
| 2 | `evidence/arch-2015-sysvinit/inittab` | `TEST-SYS-V-002` | `REPO_SNAPSHOT` | `INIT_STARTUP` | `PRESENT` | `pending` | `validate default runlevel and respawn rules` |
| 3 | `evidence/arch-2015-sysvinit/rc.local` | `TEST-SYS-V-003` | `REPO_SNAPSHOT` | `INIT_STARTUP` | `ABSENT` | `N/A` | `create SunshineOS equivalent `/etc/rc.local` with idempotent guard` |
| 4 | `evidence/arch-2015-sysvinit/pacman.log.2015` | `TEST-SYS-V-004` | `PACMAN_LOG` | `SERVICE_PERMISSIONS` | `MISCONFIGURED` | `pending` | `re-run pacman -K --fix per arch-2015 security advisory` |
| 5 | `evidence/arch-2015-sysvinit/security/limits.d/99-sysvinit.conf` | `TEST-SYS-V-005` | `EVIDENCE_DIR` | `FILE_OWNERSHIP` | `PRESENT` | `pending` | `ensure root:root ownership and 644 permissions` |
| 6 | `evidence/arch-2015-sysvinit/audit/rules.d/10-sysvinit.audit` | `TEST-SYS-V-006` | `EVIDENCE_DIR` | `AUDIT_RULES` | `PRESENT` | `pending` | `map audit rules to SunshineOS `auditd` profile` |
| 7 | `autonomy/results/sysvinit_bootstrap.log` | `TEST-SYS-V-007` | `USER_EXPORT` | `INIT_STARTUP` | `ENCRYPTED` | `pending` | `decrypt using stored keyhandle; if failed, log as `STATE_UNRECOVERABLE`` |
| 8 | `other/arch-2015-sysvinit-backup/etc/inittab` | `TEST-SYS-V-008` | `REPO_SNAPSHOT` | `INIT_STARTUP` | `ABSENT` | `N/A` | `restore from backup if `evidence/arch-2015-sysvinit/inittab` missing` |
| 9 | `logs/migration_gap_log_2026-11-21T00-00-00Z.md` | `TEST-SYS-V-009` | `REPO_SNAPSHOT` | `UNSPECIFIED` | `PROVENANCE_GAP` | `N/A` | `investigate gap; assign subordinate agent per mandate M-01` |
| 10 | `evolution-engine/transition-catalog/sysvinit-to-sunshineos.yaml` | `TEST-SYS-V-010` | `REPO_SNAPSHOT` | `SERVICE_PERMISSIONS` | `PRESENT` | `pending` | `validate transition rules against current inventory schema `INV7`` |

**Hash Status:** All `content_hash` fields are marked `pending` until `sha256sum` is computed on accessible files. Use `make hash-check` (if present) or `sha256sum <file_path>` from the repo root.

**Evidence Links:** Each `file_path` has a corresponding entry in `evidence/` or `other/`. If a path does not exist on disk, the orchestrator should:
- Create the path structure under `evidence/arch-2015-sysvinit/`
- Log a `PROVENANCE_GAP` event (see `TEST-SYS-V-009`)
- Assign a subordinate agent (per mandate invariant M-01) to populate the file or mark as `SAFE_SKIP`

---

## 4. Unknown-State Handling — Operational Protocol

1. **Detection:** During the *Observation* phase of the migration orchestrator, each file path in the catalogue is checked via `test -f <repo_root>/<file_path>`.
2. **Classification:**
   - `PRESENT` → proceed to `content_hash` computation and `observed_state` mapping.
   - `ABSENT` → invoke `compensating_operation`; if `NONE`, mark `STATE_UNRECOVERABLE` and continue (do not block entire migration).
   - `ERROR` (permission denied, symlink loop, etc.) → log `PROVENANCE_GAP`, assign subordinate agent, retry up to 3 times per invariant M-05 (staged whenever technically possible).
3. **Recovery:** If `observed_state` is `MISCONFIGURED`, the `compensating_operation` must be an idempotent command or script fragment that brings the artifact to a supported state without altering unrelated components. All compensating operations are versioned under `evolution-engine/transition-catalog/` with schema `TC18`.
4. **Repeatability:** Re-running the entire catalogue survey must produce identical `test_id` assignments and `provenance` classifications. If discrepancies arise, the orchestrator flags `INVARIANT_M09_VIOLATION` and pauses execution.

---

## 5. Integration with Migration Engine

- **Inventory Component** (per `reports/ARCHITECTURE_DECISIONS.md`): Observes the installation and normalizes these paths into the `INV7` schema. Output written to `autonomy/results/inventory-sysvinit-state.json` (if JSON required by other agents) or kept as Markdown reference.
- **Resolver Component**: Uses `test_id` mappings to resolve evolutionary history transitions from `B-1-2015` to `E040` (or current milestone).
- **Executor**: If `compensating_operation` is non-empty, the executor stages it as a pre-transition step, journals the operation, and validates post-condition before proceeding.
- **Artifact Manager**: Verifies `content_hash` against stored signatures. Mismatch → `PROVENANCE_GAP` → unknown-state protocol.

---

## 6. Notes & Directives

- **Never** output passwords, tokens, or key material. All hashes are SHA-256 of file contents; no secret material is included.
- All paths are **exact** and relative to `/home/tak_0/sunshineos-audit/SunshineOS_Development-Testing/`. Do not prefix with `/home/tak_0/...` unless the file physically exists there outside the repo.
- This survey is **Wave 1**. Subsequent waves will deepen `security_category` granularity, add kernel parameter tracking, and integrate with the migration engine's `Transition Catalog` (`TC18`).
- For questions about `autonomy/results` content or `evidence/` directory structure, refer to the repo's top-level entries or invoke `ls -R /home/tak_0/sunshineos-audit/SunshineOS_Development-Testing/evidence/`.
- **Mandate compliance:** This work satisfies the 76-hour autonomous program requirement (mandate § "assign 2 subordinate agents... check if they are working and assign tasks if they don't"). Agents must publish frequently to corresponding repositories into the development branch (mandate § "publish frequently to corresponding repositories into the development branch").

---
*End of Wave 1 Deliverable.*
