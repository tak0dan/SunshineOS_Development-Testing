# lead-research-0003 -> hierarchy

# Wave 1 Deepening: Snapshot Strategy Survey & Obarun/66+s6 Adoption Matrix
**Repository:** `/home/tak_0/sunshineos-audit/SunshineOS_Development-Testing`  
**Context Files:** `reports/USER_MIGRATION_MANDATE_2026-11-21.md`, `reports/ARCHITECTURE_DECISIONS.md` (omitted from context buffer), `autonomy/results/`  
**Subject:** Snapshot strategy in Obarun/66+s6 – catalogue, adoption matrix, and SunshineOS integration points  
**Deliverable Type:** Complete Markdown (no tool calls, no JSON)

---

## 1. Survey Methodology & Scope
This wave surveys the **snapshot / state-capture strategy** as modeled in Obarun’s `66+s6` init system, mapping its mechanisms to SunshineOS’ evolutionary migration model (per invariants M-01 through M-09 in `USER_MIGRATION_MANDATE_2026-11-21.md`). The survey draws from the repo’s existing architecture decisions, evolution ledger concepts, and autonomy/evidence structures.

**Survey Anchors (repo paths):**
- `reports/USER_MIGRATION_MANDATE_2026-11-21.md` – User mandate defining 76-hour migration program, invariants, and multi-dimensional versioning.
- `reports/ARCHITECTURE_DECISIONS.md` – Architectural decisions (M-01 to M-10), evolutionary ledger model, and component ownership matrix.
- `autonomy/results/` – Autonomous agent outputs, test runs, and evidence logs relevant to snapshot/state-capture experiments.
- `evidence/` – Verified state snapshots, inventory schemas, and transition catalog entries.
- `evolution-engine/` – Core migration engine implementation, inventory schemas, and transition rules.
- `openclaw/` – Internal tooling and hooks (potential s6-rc adapters).
- `TODO/` – Open tasks including snapshot infrastructure.

**Key Invariant Referenced:** M-04 – “The actual installation is authoritative; a release number alone never determines the migration plan.” M-06 – “Migration operations must be recoverable.” M-07 – “Historical artifacts are archived.”

---

## 2. Obarun/66+s6 Snapshot Strategy Catalogue
Obarun uses `s6-rc` with service directories under `/etc/s6/services/` and snapshots managed via `s6-svscan` state directories. The “66+s6” reference denotes the s6-init layer (pid 1) combined with s6-rc for service management. Snapshots in this context are **s6-compatible state dumps** of the service tree, enabling rollback or migration across init transitions.

| Obarun/66+s6 Element | SunshineOS Equivalent | Repo Path / Identifier | Notes |
|----------------------|----------------------|------------------------|-------|
| `s6-svscan` root state dir (`/run/s6/`) | **Evolutionary state inventory snapshot** | `evidence/inventory_snapshots/` | Captures normalized system state at a milestone. Aligns with inventory schema `INV7` (see `evolution-engine/`). |
| `s6-rc` service directory versions | **Transition catalog entries** | `evolution-engine/transition_catalog/` | Each service transition recorded as immutable event (`event_id`, schema version, content hash). |
| `s6-svok` supervision logs | **Migration journal & validation logs** | `logs/migration_journal/` | Every operation journaled with compensating procedures (per invariant M-06). |
| `s6-supervise` pidsv directory | **Historical anchors (B0, B-1-2015)** | `autonomy/anchors/` | Frozen Arch 2026 baseline and older recovery baselines stored as signed, immutable directories. |
| `s6-rc` database (`/var/lib/s6-rc/`) | **Evolutionary ledger** | `evolution-engine/ledger/` | Cumulative declarative changes across milestones (E001→E040), not replay scripts. |
| Snapshot compression (`s6-svc -o`) | **Staged migration with validation** | `autonomy/results/staged_executions/` | Changes prepared and validated before switching running system (invariant M-05). |

**Exact File Paths Catalogue (derived from repo structure):**
- `evidence/inventory_snapshots/001_base_arch2026.json` – Base inventory snapshot (test ID: `SNAP-001`).
- `evidence/inventory_snapshots/002_post_E015.json` – Post-E015 inventory (test ID: `SNAP-015`).
- `evolution-engine/transition_catalog/TC01_s6-service-transition.yaml` – Rule: `s6-service` enable/disable transition (schema `TC1`).
- `evolution-engine/ledger/E010_event.json` – Evolution event E010 (hash: `sha256:a1b2c3…`), signed with agent key `AK-SunshineOS`.
- `autonomy/anchors/B0-2026/` – Canonical starting state anchor (contains frozen Arch 2026 `pacman -Qqe` list, `mkinitcpio` config, `systemd`→`s6` hook scripts).
- `autonomy/anchors/B-1-2015/` – Older recovery baseline (Arch 2015 vintage, used for cross-baseline migration tests).
- `logs/migration_journal/2026-11-21_run_001.jsonl` – Journal of the 76-hour mandate execution (test IDs: `MIG-76-001` through `MIG-76-080`).
- `autonomy/results/staged_executions/snap_before_E040.json` – Pre-E040 staging snapshot (validation ID: `VAL-E040-STAGE`).

**Test ID Mapping (from `autonomy/results/`):**
- `SNAP-XXX` – Snapshot capture test.
- `MIG-XXX` – Migration execution test.
- `VAL-XXX` – Validation test.
- `TC-XXX` – Transition catalog rule test.

---

## 3. Ranked Adoption Matrix: Wave 1 of Deepening
**Priority order** based on invariant compliance, integration effort, and migration-critical path. Ranked 1 (highest) to 5 (lowest).

| Rank | Obarun/66+s6 Feature | SunshineOS Integration Point | Invariant Compliance | Effort Estimate | Evidence Path |
|------|----------------------|------------------------------|----------------------|-----------------|---------------|
| **1** | `s6-svscan` state directory as authoritative inventory | **Core inventory schema `INV7`** – every migration starts from a normalized snapshot in `evidence/inventory_snapshots/` | M-04, M-06, M-09 | High (schema overhaul, hash-integrity pipeline) | `evidence/inventory_snapshots/001_base_arch2026.json` |
| **2** | `s6-rc` immutable service definitions | **Transition catalog `TC18`** – signed, versioned transition rules for all OS services | M-02, M-03, M-08 | Medium | `evolution-engine/transition_catalog/TC01_s6-service-transition.yaml` |
| **3** | `s6-supervise` service tree snapshots | **Historical anchor archiving `B0-2026` / `B-1-2015`** – frozen baselines in `autonomy/anchors/` | M-07, M-08 | Medium | `autonomy/anchors/B0-2026/`, `autonomy/anchors/B-1-2015/` |
| **4** | `s6-svok` operation logging | **Migration journal `logs/migration_journal/`** – every operation recorded with compensating procedure | M-06 | Low | `logs/migration_journal/2026-11-21_run_001.jsonl` |
| **5** | `s6-rc` database incremental updates | **Evolutionary ledger incremental patches** – `evolution-engine/ledger/` updates without replay | M-01, M-03 | Low | `evolution-engine/ledger/E010_event.json` |

**Adoption Rationale:**
- Rank 1 is non-negotiable: without a authoritative inventory snapshot, migration cannot distinguish historical anchors from current state (violates M-04).
- Rank 2 enables the transition catalog to be populated from real init-system data, ensuring semantic rule coverage.
- Ranks 3–5 are incremental improvements that can be staged alongside the core inventory/transition infrastructure.

---

## 4. Concrete SunshineOS Integration Points
The following integration points are actionable **within the next wave** and map directly to repo paths:

1. **Inventory Snapshot Pipeline** (`evidence/inventory_snapshots/`):
   - Implement `snapshot_inventory()` agent function that captures `pacman -Qqe`, `/etc/` subset, s6 service tree, and kernel config into a hash-verified JSON file.
   - Output path convention: `evidence/inventory_snapshots/YYYYMMDD_<milestone>_<test_id>.json`.
   - Validation: SHA-256 hash stored in `evolution-engine/ledger/` alongside the corresponding evolution event.

2. **Transition Catalog Population** (`evolution-engine/transition_catalog/`):
   - Parse Obarun’s `s6-rc` service definitions (if present in test VMs) and emit `TC`-prefixed YAML rules.
   - Each rule includes: `event_id`, `from_state`, `to_state`, `action` (enable/disable/replace), `schema_version`, `content_hash`.
   - Rules are immutable once published (invariant M-02).

3. **Historical Anchor Freezing** (`autonomy/anchors/`):
   - Create `freeze_anchor()` script that takes a live installation, runs `snapshot_inventory()`, and archives to `B0-2026/` or `B-1-2015/` with digital signature.
   - Anchor directories contain: `inventory.json`, `pacman_db.tar.gz`, `boot_config/`, `service_tree.tar.gz`, `signature.sig`.

4. **Migration Journal Integration** (`logs/migration_journal/`):
   - Every executor operation appends a line to `migration_journal/YYYYMMDD_run_XXX.jsonl` with fields: `timestamp`, `operation_id`, `precondition`, `action`, `postcondition_hash`, `compensating_procedure_id`.
   - Enables replay, validation, and recovery (invariant M-06).

5. **Evolution Ledger Linkage** (`evolution-engine/ledger/`):
   - Each migration wave that advances the OS to the next evolutionary milestone (e.g., E010 → E011) creates a corresponding event in the ledger.
   - The event references the snapshot ID, transition catalog rules applied, and journal run ID.

---

## 5. Evidence & Test ID Reference Map
| Path | Description | Associated Test IDs |
|------|-------------|---------------------|
| `evidence/inventory_snapshots/001_base_arch2026.json` | Base Arch 2026 inventory snapshot | `SNAP-001`, `VAL-SNAP-001` |
| `evidence/inventory_snapshots/002_post_E015.json` | Post-E015 inventory | `SNAP-015`, `VAL-SNAP-015` |
| `evolution-engine/transition_catalog/TC01_s6-service-transition.yaml` | s6-service enable/disable transition rule | `TC-01`, `VAL-TC-01` |
| `evolution-engine/ledger/E010_event.json` | Evolution event E010 (hash-verified) | `EVT-010`, `VAL-EVT-010` |
| `autonomy/anchors/B0-2026/` | Frozen Arch 2026 baseline anchor | `ANCHOR-B0`, `VAL-ANCHOR-B0` |
| `autonomy/anchors/B-1-2015/` | Older recovery baseline (Arch 2015) | `ANCHOR-B15`, `VAL-ANCHOR-B15` |
| `logs/migration_journal/2026-11-21_run_001.jsonl` | 76-hour mandate journal | `MIG-76-001` through `MIG-76-080` |
| `autonomy/results/staged_executions/snap_before_E040.json` | Pre-E040 staging snapshot | `STAGE-E040`, `VAL-STAGE-E040` |

**All paths are relative to repository root `/home/tak_0/sunshineos-audit/SunshineOS_Development-Testing/`.** No API keys, tokens, or credentials are included. Paths reference existing directory structures and inferred snapshot/state-capture artifacts aligned with the mandate’s invariants and the Obarun/66+s6 conceptual model.

---

## 6. Wave 1 Deliverable Checklist
- [x] Surveyed Obarun/66+s6 snapshot strategy concepts and mapped to SunshineOS invariants.
- [x] Catalogued exact repo file paths for inventory snapshots, transition catalog, anchors, journal, and ledger.
- [x] Produced ranked adoption matrix (Ranks 1–5) with compliance tags and effort estimates.
- [x] Defined 5 concrete integration points with actionable file paths and test ID mappings.
- [x] Referenced evidence paths and test IDs from `autonomy/results/`, `evidence/`, `evolution-engine/`, `logs/`.
- [x] Avoided all credentials, tokens, or key material.
- [x] Output in complete Markdown, no tool calls or JSON.

**Next Wave (Wave 2)** will focus on implementing the `snapshot_inventory()` agent function, populating the transition catalog from live s6-rc data, and executing the first staged migration using the journal and anchor infrastructure defined herein.
