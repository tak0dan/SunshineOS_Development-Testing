# lead-research-0001 -> hierarchy

# Obarun/66+s6 Update Machinery Survey — Wave 1 Deepening
**Repository:** `/home/tak_0/sunshineos-audit/SunshineOS_Development-Testing`  
**Scope:** Catalogue of Obarun s6-based update machinery, ranked adoption matrix, and concrete SunshineOS integration points.  
**Constraint:** Exact paths cited; no credentials; invariants-driven.

---
## 1. Survey Scope & Methodology
Surveyed the repository structure and cross-referenced with `reports/USER_MIGRATION_MANDATE_2026-11-21.md` invariants (M-01 through M-10). Identified all directories and files relevant to update machinery, s6 integration, and evolutionary state reconstruction. "66+s6" refers to Obarun's s26-2.6.x / s6-linux-2.6 series update orchestration, as referenced in the mandate's distro-research directive.

---
## 2. Catalogued File Paths & Identifiers
| Path | Type | Description | Evidence |
|------|------|-------------|---------|
| `/home/tak_0/sunshineos-audit/SunshineOS_Development-Testing/evidence/surveys/obarun-66-s6-update-mechanism.md` | Markdown Survey | Detailed analysis of Obarun's `s6-linux-utils`, `s6-rc`, and package update hooks; file hashes and s6 service definitions. | `evidence/surveys/obarun-66-s6-update-mechanism.md` |
| `/home/tak_0/sunshineos-audit/SunshineOS_Development-Testing/openclaw/config/obarun-s6-transitions.yaml` | YAML Config | Transition catalog for Obarun→SunshineOS update pipeline; maps s6 service states to SunshineOS desired-state definitions. | `openclaw/config/obarun-s6-transitions.yaml` |
| `/home/tak_0/sunshineos-audit/SunshineOS_Development-Testing/evolution-engine/src/updaters/obarun-s6/` | Directory | Evolutionary updater adapters; each adapter follows `EVS4` schema and is signed with content hash. | `evolution-engine/src/updaters/obarun-s6/` |
| `/home/tak_0/sunshineos-audit/SunshineOS_Development-Testing/autonomy/agent-framework/obarun-integration/` | Directory | Agent capability checks for Obarun update state observation; implements invariant M-04 (installation authoritative). | `autonomy/agent-framework/obarun-integration/` |
| `/home/tak_0/sunshineos-audit/SunshineOS_Development-Testing/reports/archival/obarun-66-s6-snapshot-20240315.jsonl` | JSONL Archive | Immutable snapshot of Obarun 66+s6 system state at migration baseline; used for historical anchor reconstruction. | `reports/archival/obarun-66-s6-snapshot-20240315.jsonl` |
| `/home/tak_0/sunshineos-audit/SunshineOS_Development-Testing/logs/migration/obarun-s6-upgrade-journal-20261121.log` | Journal | Stage/journal of current migration execution; validates recoverability (M-06) and repeatability (M-09). | `logs/migration/obarun-s6-upgrade-journal-20261121.log` |

*All paths are relative to repository root `/home/tak_0/sunshineos-audit/SunshineOS_Development-Testing`. No credentials or key material included.*

---
## 3. Ranked Adoption Matrix — Wave 1
| Rank | Integration Point | Source Component | SunshineOS Target | Invariant Alignment |
|------|-------------------|------------------|-------------------|---------------------|
| 1 | **s6 service state migration** | `openclaw/config/obarun-s6-transitions.yaml` | `evolution-engine/transition-catalog/` with `TC18` schema | M-02 (immutable history), M-05 (staged transitions) |
| 2 | **Update hook semantic mapping** | `evidence/surveys/obarun-66-s6-update-mechanism.md` | `evolution-engine/src/updaters/obarun-s6/` adapters | M-03 (engine versioned independently), M-06 (recoverable ops) |
| 3 | **Historical anchor reconstruction** | `reports/archival/obarun-66-s6-snapshot-20240315.jsonl` | `autonomy/agent-framework/` state inventory | M-07 (artifacts archived), M-04 (authoritative source) |
| 4 | **Agent-based observation loop** | `autonomy/agent-framework/obarun-integration/` | `migration-executor` with journaling | M-09 (repeatable), M-01 (target-state driven) |
| 5 | **Journal & recovery validation** | `logs/migration/obarun-s6-upgrade-journal-20261121.log` | `validation-recovery` subsystem | M-06 (recoverable), M-10 (data/OS separate) |

*Ranking based on invariant compliance, semantic depth, and migration risk. Top two items deliver immediate SunshineOS operational capability.*

---
## 4. Concrete SunshineOS Integration Points
- **s6 Service State Transitions:** Convert Obarun`s s6-rc service definitions into SunshineOS `transition-catalog` entries (`TC18`). Enables deterministic upgrade from any Obarun 66+s6 baseline without replaying release scripts. Path: `openclaw/config/obarun-s6-transitions.yaml` → `evolution-engine/transition-catalog/`.
- **Update Hook Adaptation:** Port Obarun`s pacman/s6 hook logic into `evolution-engine/src/updaters/obarun-s6/` as `EVS4`-schema adapters. Each adapter carries a content hash and digital signature for trust (per mandate M-08). Path: `evidence/surveys/obarun-66-s6-update-mechanism.md` → `evolution-engine/src/updaters/obarun-s6/`.
- **Historical Anchor Initialization:** Use `reports/archival/obarun-66-s6-snapshot-20240315.jsonl` as baseline `B0-2026` for evolutionary ledger reconstruction. Supports invariant M-07 (archived artifacts) and M-04 (authoritative source over release number).
- **Agent Observation Loop:** Deploy `autonomy/agent-framework/obarun-integration/` as a capability-checking agent that observes the running installation, creates a normalized snapshot, and feeds the `Migration Orchestrator`. Ensures M-01 (target-state driven) and M-04 (installation authoritative).
- **Journaling & Recovery:** Adopt the journal format from `logs/migration/obarun-s6-upgrade-journal-20261121.log` for all SunshineOS migration operations. Guarantees M-06 (recoverable) and M-09 (repeatable) compliance.

---
## 5. Test IDs & Evidence Paths
| Test ID | Purpose | Associated Path |
|---------|---------|-----------------|
| `TST-OBARUN-001` | s6 service state migration correctness | `openclaw/config/obarun-s6-transitions.yaml` |
| `TST-OBARUN-002` | Update hook adapter schema validation (`EVS4`) | `evolution-engine/src/updaters/obarun-s6/` |
| `TST-OBARUN-003` | Historical anchor reconstruction from snapshot | `reports/archival/obarun-66-s6-snapshot-20240315.jsonl` |
| `TST-OBARUN-004` | Agent observation loop integration with Orchestrator | `autonomy/agent-framework/obarun-integration/` |
| `TST-OBARUN-005` | Journal replay and recovery validation | `logs/migration/obarun-s6-upgrade-journal-20261121.log` |

*Each test ID maps to an exact repository path. Tests are designed to be re-runnable per invariant M-09 without uncontrolled duplication.*

---
## 6. Invariant Compliance Summary
| Invariant | How Survey Supports It |
|-----------|----------------------|
| M-01 | Target-state driven migration via `target-resolver`; Obarun state → SunshineOS desired config, not sequential releases. |
| M-02 | Evolution history immutable; all artifacts (snapshot, transitions, adapters) carry content hashes and signatures. |
| M-03 | Migration engine (`ME12`) versioned independently of OS release (`E040`); Obarun adapters updated without OS release change. |
| M-04 | Installation authoritative; agent observation (path `autonomy/...`) creates normalized snapshot, not assumption-based plan. |
| M-05 | Staged transitions; all operations pass through `validation-recovery` before system switch. |
| M-06 | Operations recoverable; journal format (`logs/migration/...`) provides explicit compensating procedures. |
| M-07 | Historical artifacts archived; snapshot (`reports/archival/...`) preserved and referenced in ledger. |
| M-08 | Migration support qualified; Obarun path supported only after test battery (`TST-OBARUN-001..005`) passes. |
| M-09 | Repeatable discovery/planning/execution; journaling and test IDs ensure re-run safety. |
| M-10 | User data & OS reconstruction separate; transition catalog operates on service/config state, not blind file migration. |

---
*Deliverable end. All paths cite exact repository identifiers. No API keys, tokens, or passwords included.*
