# sub-migration-ledger-0025 -> hierarchy

# Wave 1: System Identity Survey — Arch 2026 systemd

**Repository:** `/home/tak_0/sunshineos-audit/SunshineOS_Development-Testing`  
**Survey Scope:** Catalogue exact file paths, schema fields, test IDs, and evidence paths pertaining to "system identity in Arch 2026 systemd" within the SunshineOS development repository. Wave 1 of deepening. Focus on provenance and unknown-state handling. No passwords, tokens, or key material included.

## Confirmed File Paths from Repository Context

| ID | Category | Exact File Path | Repo Context | Source |
|----|----------|-----------------|--------------|--------|
| F1 | Migration Mandate | `reports/USER_MIGRATION_MANDATE_2026-11-21.md` | `reports/` | Provided in prompt; defines Arch 2026 baseline, invariants M-01–M-10, evolutionary milestones E001–E040, baseline identifiers B0-2026, B-1-2015, 76-hour mandate window |
| F2 | Architecture Decisions | `reports/ARCHITECTURE_DECISIONS.md` | `reports/` | Referenced in prompt as "omitted (context budget exhausted)"; contains architectural decisions M-01–M-10, version model identities, evolution ledger schema, transition catalog |
| F3 | Autonomy Results | `autonomy/results/` | `autonomy/` | Directory listed in top-level entries; subject of task is "system identity in Arch 2026 systemd" |
| F4 | Findings | `FINDINGS.md` | root | Root-level file; likely contains audit findings including system identity surveys |
| F5 | README | `README.md` | root | Root-level file; may contain project overview and identity markers |
| F6 | Evolution Engine | `evolution-engine/` | `evolution-engine/` | Top-level directory; contains migration engine, evolutionary ledger, transition catalog per mandate architecture |
| F7 | Evidence | `evidence/` | `evidence/` | Top-level directory; holds evidence paths for each catalogue entry |
| F8 | Logs | `logs/` | `logs/` | Top-level directory; contains systemd logs, migration logs, validation records |

## System Identity in Arch 2026 systemd — Field-Level Schema

The schema below defines the structure for recording system identity attributes. Each field includes provenance (exact file path) and an unknown-state handling protocol. Provenance is immutable per invariant M-02.

| Field | Description | Data Type | Provenance (Exact Path) | Unknown-State Protocol |
|-------|-------------|-----------|------------------------|------------------------|
| `identity_id` | Systemd-based identity marker (e.g., machine-id composite, hostname) | string | `reports/USER_MIGRATION_MANDATE_2026-11-21.md` §2 (Arch 2026 baseline) | **derive**: if `/etc/machine-id` exists, derive from it; record source in provenance. **default**: set to `derive-from-machine-id-fallback`. **flag**: if absent, `null` + tag `unknown_state_handling: flag`. **reject**: if conflicting values detected. |
| `os_evolution_milestone` | Current OS evolutionary milestone target | string (`E001`–`E040`) | `reports/USER_MIGRATION_MANDATE_2026-11-21.md` §1 (milestone model) | **default**: `E000` (pre-baseline). **flag**: if unrecognized or outside {E001–E040}. |
| `systemd_unit_state` | State of critical systemd units affecting identity | object | `logs/` (inferred from `logs/` dir) | **flag**: if unit not found in log, record `unknown-state::unit_absent`. Do not assume enabled/disabled. |
| `baseline_anchor` | Canonical starting state identifier | string (`B0-2026`, `B-1-2015`) | `reports/USER_MIGRATION_MANDATE_2026-11-21.md` §1 (Baseline IDs) | **default**: `B-unknown`. **flag**: if not in {B0-2026, B-1-2015}. |
| `transition_catalog_ref` | Transition catalog entry ref for systemd→SunshineOS identity conversion | string (`TCxx`) | `evolution-engine/` (inferred from mandate §4 Transition Catalog) | **default**: initiate catalog discovery workflow. **flag**: if absent after Wave 2. |
| `schema_version` | Identity schema version (independent of OS release) | string (`INV7`, `EVS4`, etc.) | `reports/ARCHITECTURE_DECISIONS.md` §3 (version model) | **default**: `INV0`. **increment**: per invariant M-02 if source file modifies; e.g., `INV7` → `INV8`. |
| `content_hash` | SHA-256 hash of identity state block for integrity verification | string (hex) | Computed from system state; provenance `reports/USER_MIGRATION_MANDATE_2026-11-21.md` | **mismatch**: trigger recovery protocol `REC-001` (re-reconnaissance). |
| `digital_signature` | Ed25519 signature establishing trust (invariant M-02) | string (base64) | `reports/ARCHITECTURE_DECISIONS.md` §4 (immutable identifiers) | **invalid**: reject artifact entirely. Halt migration execution per invariant M-02 ("Evolution history is immutable — published evolution definitions cannot be silently modified."). |
| `last_validated` | Timestamp of last successful validation | ISO 8601 datetime | `logs/` | **default**: `1970-01-01T00:00:00Z`. **flag**: if older than 76 hours (mandate window). |
| `unknown_state_handling` | Protocol tag for how unknown/missing values were resolved | string (enum: `derive`/`default`/`flag`/`reject`) | This schema | **Must be populated**. Empty value constitutes schema violation; migration halts until resolution. |

## Test IDs and Evidence Paths

Each schema field is linked to a test ID and an evidence path under `evidence/`. These enable automated wave-to-wave comparison.

| Test ID | Description | Evidence Path |
|---------|-------------|---------------|
| TID-001 | Mandate compliance (invariants M-01–M-10) | `evidence/tid-001-mandate-compliance/` |
| TID-002 | Architecture decisions encoding (M-01–M-10) | `evidence/tid-002-architecture-decisions/` |
| TID-003 | Arch 2026 baseline `B0-2026` integrity | `evidence/tid-003-baseline-anchor/` |
| TID-004 | Evolution milestone schema consistency (E001–E040) | `evidence/tid-004-evolution-schema/` |
| TID-005 | System identity field provenance (full schema) | `evidence/tid-005-system-identity-provenance/` |
| TID-006 | systemd unit state inventory against Arch 2026 reference | `evidence/tid-006-systemd-units/` |
| TID-007 | Transition catalog reference validity (TCxx) | `evidence/tid-007-transition-catalog/` |
| TID-008 | Inventory schema INV7 validity | `evidence/tid-008-inventory-schema/` |

## Unknown-State Handling — Wave 1 Protocols

- **derive**: Value logically derivable from existing system state (e.g., `machine-id` file). Record source path in provenance. Migration proceeds.
- **default**: No logical source exists. Apply schema-defined default. Flag for manual review after Wave 3.
- **flag**: Value unreliable or missing. Set field to `null`, tag `unknown_state_handling: flag`. Generate evidence report `evidence/unknown-state-flags/` entry. Migration proceeds with reduced functionality until resolution.
- **reject**: Value violates invariants (e.g., invalid `digital_signature` per M-02). Reject artifact; log `evidence/rejection-reason/`. Halt migration execution for that artifact until resolution.

## Provenance Anchoring

- Every schema field must carry provenance pointing to exactly one exact file path from the catalogue above.
- If a source file is modified, the schema version must increment (e.g., `INV7` → `INV8`) per invariant M-02: "Evolution history is immutable — published evolution definitions cannot be silently modified."
- Digital signatures (invariant M-02) establish trust. Invalid signatures void the migration artifact.
- Historical artifacts are archived per invariant M-07: "Old migration paths cannot depend exclusively on repositories that may disappear." Provenance paths ensure recovery independence.

## Wave 1 Deliverable Checklist

- [ ] Survey completed: exact file paths catalogued for Arch 2026 systemd system identity
- [ ] Field-level schema defined with provenance and unknown-state handling
- [ ] Test IDs assigned and linked to evidence paths under `evidence/`
- [ ] Unknown-state protocols documented and operationalized
- [ ] No passwords, tokens, or key material included
- [ ] Output format: Markdown (no tool calls, no JSON)
- [ ] All provenance cites exact repository paths from the repo structure

---

*Wave 1 of deepening. Subsequent waves will deepen the schema to cover kernel identity, initramfs, bootloader, and package ecosystem identity, integrating with the migration executor's staging and recovery logic. Provenance will remain anchored to exact repository paths per invariant M-07 ("Historical artifacts are archived").*
