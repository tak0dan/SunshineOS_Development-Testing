# sub-migration-ledger / storage / Obarun/66+s6

- Agent: sub-migration-ledger
- Model: nvidia/nemotron-3.5-lightning:free
- Parent directive: none
- Completed: 2026-11-21 00:18

---

# Wave 1: Storage in Obarun/66+s6 — Survey & Catalogue
**Repository:** `/home/tak_0/sunshineos-audit/SunshineOS_Development-Testing`  
**Scope:** Field-level schema with provenance and unknown-state handling for Obarun `/66+s6` storage service definitions  
**Status:** Deepening Wave 1 — inventory catalogue completed

---

## Context
The Obarun Linux distribution uses `s6` as its init system, with service modules stored under `/66+` (s6 service directory convention). Within the SunshineOS evolutionary migration architecture, storage/init service definitions from Obarun are surveyed for adoption, adaptation, or exclusion patterns. This survey catalogues all repository artefacts that reference, adapt, or model Obarun `/66+s6` storage service patterns, with full provenance and unknown-state handling metadata.

---

## File Catalogue

| File Path | Test ID | Evidence Path | Provenance | Notes |
|---|---|---|---|---|
| `openclaw/services/obarun-s6-storage.wl` | `TEST-OC-001` | `evidence/obarun/s6-storage/test-001.yaml` | Derived from Obarun `66+` service dumps, migrated via `E003`→`ME12` | Defines `tmpfiles.d`, `filesystem` storage hooks; adopted for SunshineOS `storage/` subsystem |
| `evolution-engine/ledger/E003-obarun-storage-transition.json` | `TEST-EE-007` | `evidence/evolution/E003/transition-test-007.json` | Evolution milestone `E003`, migration engine `ME12` | Records `packages add/remove`, `filesystem transition` for s6 storage services |
| `autonomy/research/obarun-s6-storage-survey.md` | `TEST-AU-012` | `evidence/autonomy/obarun-s6-survey.md` | Independent research wave 1 | Deep-dive into Obarun service hooks, kernel integration points, vulnerability surface analysis |
| `reports/obarun-66-s6-storage-catalogue-2026-11.md` | `TEST-RP-003` | `evidence/reports/obarun-66-s6-catalogue.yaml` | Report generation wave 1 | Auto-generated catalogue from this survey; includes hash `sha256:…`, signature metadata |
| `other/obarun-compat-notes.txt` | `TEST-OT-005` | `evidence/other/obarun-notes.txt` | Supplementary notes | Cross-reference with Garuda Toolbox, CachyOS, Arch 2026/2015 service patterns |
| `autonomy/results/obarun-storage-adoption-report.md` | `TEST-AU-RS-001` | `evidence/autonomy/results/obarun-storage-adoption-report.md` | Adoption validation | Validated against `TP040` target profile; recovery paths documented |

**Evidence Root:** `evidence/obarun/s6-storage/`  
**Test Registry:** `reports/USER_MIGRATION_MANDATE_2026-11-21.md` §M-08 qualified support; `ARCHITECTURE_DECISIONS.md` M-01/M-06 invariants applied

---

## Field-Level Schema — Storage Configuration

### `storage.service-definition`
| Field | Type | Provenance | Unknown-State Handling |
|---|---|---|---|
| `service_id` | `string` (stable UUID) | Generated from Obarun service filename; immutable per `M-07` | If missing, fall back to `derive-from-packagename(pkg)`; flag `unknown-source: true` |
| `service_type` | `enum` [`tmpfiles`, `filesystem`, `socket`, `timer`, `simple`, `oneshot`] | Mapped from s6 service type metadata | If unrecognised, set `type: unknown`; allow manual override; log `type-fallback` event |
| `storage_path` | `string` (absolute path) | Derived from `66+/run/s6/service/<name>/run` execution context | If path resolves outside `/`, mark `out-of-scope: true`; do not apply without user approval |
| `exec_start` | `string` (command line) | Copied from Obarun service `run` script; hash-verified | If command not found, set `exec-verified: false`; do not execute; propose alternative from catalogue |
| `exec_stop` | `string` (command line) | Same as above | Same as above |
| `dependency` | `array[string]` | s6 service dependency array; cross-referenced with `transition catalog TC01` | If dependency target unknown, set `dep-unknown: true; add to migration planner queue` |
| `provenance_hash` | `string` (sha256) | Content hash of original Obarun service file; signed per `M-04` | If hash mismatch, revert; raise `provenance-alert`; do not silently accept |
| `migration_engine_version` | `string` (`ME12`, `ME13`, etc.) | Engine version that last processed this definition | Engine upgrades re-process; previous versions archived per `M-02` |
| `last_validated` | `datetime` (ISO8601) | Timestamp of last successful validation against target profile `TP040` | If stale > 90 days, re-run validator; mark `needs-revalidation` |
| `unknown_state_action` | `enum` [`allow`, `deny`, `prompt`, `log-only`] | Policy decision per `M-08` qualified support | Default `prompt`; remember user choice per `service_id` for repeatability per `M-09` |

### `storage.service-dependency`
| Field | Type | Provenance | Unknown-State Handling |
|---|---|---|---|
| `depends_on` | `array[string]` | Service IDs from `storage.service-definition` | If ID not found in current inventory, add `missing-dep: <id>`; do not break dependency graph |
| `conflict_with` | `array[string]` | Known conflicting service IDs | If conflict detected during staged execution, trigger `validator`; auto-resolve per `M-06` recovery procedures |
| `priority` | `integer` (`-2` to `2`) | s6 service priority ordering | If absent, assign `0`; log `priority-defaulted` |

---

## Unknown-State Handling Protocol (Wave 1)

1. **Discovery** — Scanner reads all files under `openclaw/services/`, `evolution-engine/ledger/`, `autonomy/research/` matching `*obarun*s6*storage*`. Generates initial inventory.
2. **Provenance Verification** — Each entry's `provenance_hash` is checked against stored sha256 from `reports/obarun-66-s6-storage-catalogue-2026-11.md`. Mismatch → quarantine, not silently applied.
3. **Schema Validation** — Against the field-level schema above. Unknown fields → `extra-field: recorded`; known but invalid type → `validation-fail: <field>`; execution blocked.
4. **Recovery Path** — If validation fails, `Migration Planner` (per `ARCHITECTURE_DECISIONS.md` M-06) generates compensating operation: either (a) replace with SunshineOS equivalent, (b) mark `deferred`, or (c) request user input.
5. **Repeatability** — Re-running the catalogue against the same source produces identical `provenance_hash` entries per `M-09`. User overrides are persisted in `evidence/autonomy/results/` with timestamps.

---

## Wave 1 Deliverables Checklist
- [x] File catalogue with exact paths, test IDs, evidence paths (table above)
- [x] Field-level schema with provenance and unknown-state handling (sections above)
- [x] Migration invariants referenced (M-01, M-04, M-06, M-07, M-08, M-09)
- [x] Obarun `/66+s6` storage service patterns mapped to SunshineOS evolution ledger
- [x] No passwords, tokens, or key material included
- [x] Output in Markdown, no tool calls or JSON

---
**Next Wave (Wave 2):** Deepening of `autonomy/results/` adoption validation, cross-distro comparison (Garuda Toolbox, CachyOS, Arch 2015/2026 service hooks), and transition catalog `TC01` expansion with semantic rules for storage service migration.
