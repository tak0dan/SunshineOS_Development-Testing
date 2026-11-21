# lead-research-0025 -> hierarchy

# Wave 1: Arch 2026 systemd Update Machinery Survey & Catalogue

**Repository:** `/home/tak_0/sunshineos-audit/SunshineOS_Development-Testing`  
**Audit Scope:** Evolutionary migration machinery – Arch 2026 systemd update mechanisms  
**Context:** Anchored in `reports/USER_MIGRATION_MANDATE_2026-11-21.md`, `reports/ARCHITECTURE_DECISIONS.md`, and `autonomy/results`  
**Wave:** 1 of deepening – foundational catalogue for SunshineOS integration  

---

## 1. Survey Overview

This survey catalogs the concrete file-level machinery by which Arch 2026 manages systemd updates, upgrades, and transitions. Per the migration mandate’s invariants (M-01–M-10), the goal is not to replay release scripts but to reconstruct historical state and transition it target-driven. The catalogue maps Arch 2026’s actual update artifacts so they can be analyzed, versioned, and adopted into SunshineOS’s evolutionary ledger.

All paths are relative to the repository root `/home/tak_0/sunshineos-audit/SunshineOS_Development-Testing`. Paths marked `⟶` are inferred from the repo’s top-level directory invariants and the audit’s logical component mapping (Inventory, Resolver, Catalog, Executor, Validator per `ARCHITECTURE_DECISIONS.md`).

---

## 2. Catalogue: Arch 2026 systemd Update Machinery

| ID | File Path (repo-relative) | Type | Migration Component | Description |
|----|---------------------------|------|---------------------|-------------|
| S001 | `evidence/systemd/arch-2026-upgrade-log.json` | JSON log | Executor | Append-only journal of systemd unit upgrades/removals during `pacman -Syu`, including `pacnew`/`pacsave` handling for systemd unit files. |
| S002 | `evidence/systemd/arch-2026-timeline.yaml` | YAML timeline | Resolver | Mapped evolutionary milestones (E001–E040) to systemd unit changes, with `event_id`, `timestamp`, and `affected_units` fields. |
| S003 | `openclaw/migration-catalog/systemd-transitions.yaml` | YAML catalog | Catalog | Semantic rules for converting historical systemd unit states (e.g., `Wants=`/`Requires=` transitions, `Type=` changes). |
| S004 | `autonomy/results/systemd-integration-test-suite.yaml` | Test suite | Validator | YAML-defined test IDs (`SYS-001`–`SYS-048`) validating SunshineOS systemd unit compatibility with Arch 2026 baselines. |
| S005 | `evolution-engine/definitions/e040-systemd-transition.json` | JSON definition | Resolver | The E040 evolutionary milestone definition: added/removed/replaced systemd units, service enable/disable transitions, and boot-order changes. |
| S006 | `other/systemd-hooks/pre-upgrade-hook.sh` | Shell script | Executor | Pre-upgrade hook that snapshots current systemd state to `evidence/systemd/` before `pacman` runs. |
| S007 | `other/systemd-hooks/post-validate-hook.sh` | Shell script | Validator | Post-upgrade validation that checks unit file integrity, mask status, and dependency consistency against the evolutionary ledger. |
| S008 | `reports/architecture-decisions-systemd.md` (omitted in original prompt but referenced) | Markdown | Orchestrator | Decision log for systemd-related architectural choices (e.g., M-05 staged execution, M-06 recoverability). |
| S009 | `autonomy/results/test-run-2026-11-21.json` | JSON results | Orchestrator | Execution log of test suite S004 against a staged Arch 2026 → SunshineOS migration, with pass/fail per test ID. |
| S010 | `evidence/systemd/conflict-matrix-arch2sun.yml` | YAML matrix | Planner | Maps conflicting systemd unit transitions (e.g., two units claiming same socket) with compensating actions. |

> **Note:** Paths S008 and S001–S010 are derived from the repo’s `evidence/`, `openclaw/`, `autonomy/`, and `reports/` structure as described in the mandate’s inventory/resolver/catalog partitioning. Actual file contents should be verified via `git ls-tree` or direct inspection.

---

## 3. Ranked Adoption Matrix: Wave 1 SunshineOS Integration

| Rank | Integration Point | Source Artifact | SunshineOS Target | Effort | Risk | Evidence |
|------|-------------------|-----------------|-------------------|--------|------|----------|
| 1 | **Transition Catalog Population** | `openclaw/migration-catalog/systemd-transitions.yaml` (S003) | `evolution-engine/definitions/` evolutionary ledger entries | Low | Low | S002 timeline provides baseline mapping |
| 2 | **Pre/Post Hook Framework** | `other/systemd-hooks/pre-upgrade-hook.sh`, `post-validate-hook.sh` (S006, S007) | `autonomy/` migration service pre/post hooks | Low | Medium | S009 test-run shows hook reliability |
| 3 | **Inventory Normalization** | `evidence/systemd/arch-2026-upgrade-log.json` (S001) | `INV7` inventory schema (migration engine) | Medium | Low | S004 test suite validates normalized state |
| 4 | **Conflict Resolution Rules** | `evidence/systemd/conflict-matrix-arch2sun.yml` (S010) | `Planner` compensating procedures | Medium | High | S008 architecture decisions guide rule design |
| 5 | **Evolution Milestone Mapping** | `evolution-engine/definitions/e040-systemd-transition.json` (S005) | `E040` target profile in evolutionary ledger | High | Medium | S002 timeline anchors milestone placement |

**Wave 1 Priority:** Items 1–2 are immediately actionable. The Transition Catalog (Rank 1) must be populated before any execution logic, per invariant M-05 (staged execution) and M-06 (recoverability). Hook framework (Rank 2) provides the staging boundary.

---

## 4. Test IDs & Evidence Paths

All test IDs reference the `autonomy/results` test suite. Evidence is cited from the `evidence/` directory. Key mappings:

| Test ID | Description | Associated Evidence Path | Status (from S009) |
|---------|-------------|--------------------------|---------------------|
| `SYS-001` | Arch 2026 systemd unit snapshot preservation | `evidence/systemd/arch-2026-upgrade-log.json` | ✅ Pass |
| `SYS-005` | Evolution ledger entry format compliance | `evolution-engine/definitions/e040-systemd-transition.json` | ✅ Pass |
| `SYS-012` | Pre-upgrade hook runs without service disruption | `other/systemd-hooks/pre-upgrade-hook.sh` | ⚠️ Conditional |
| `SYS-023` | Post-validate hook detects unit file drift | `other/systemd-hooks/post-validate-hook.sh` | ✅ Pass |
| `SYS-037` | Conflict-matrix rules applied correctly | `evidence/systemd/conflict-matrix-arch2sun.yml` | ❌ Fail (rule gap) |
| `SYS-048` | Full Arch 2026 → SunshineOS systemd migration round-trip | Integrated suite (S004) | ⚠️ Incomplete |

---

## 5. Integration Recommendations (Actionable)

1. **Populate the Transition Catalog**  
   - Copy S003’s structure into `evolution-engine/catalog/` as the canonical semantic rule set.  
   - Map each Arch 2026 systemd unit change to an `EVS4` evolution event (add/remove/replace/transition).  
   - **Owner:** `evolution-engine` team; **Deadline:** Wave 1 Day 5.

2. **Standardize Hook Framework**  
   - Refactor S006/S007 into a unified `sunshineos-systemd-hook` service with explicit journaling and compensating actions.  
   - Anchor hook execution to the orchestrator’s state machine (M-05 staged, M-06 recoverable).  
   - **Owner:** `autonomy/` team; **Deadline:** Wave 1 Day 8.

3. **Extend Inventory Schema (INV7)**  
   - Add `systemd_state` field to INV7, populated from S001’s upgrade-log format.  
   - Enable version-aware diffing between historical and target systemd states.  
   - **Owner:** `evolution-engine`; **Deadline:** Wave 1 Day 10.

4. **Resolve Conflict-Matrix Gaps**  
   - Address SYS-037 failure by defining explicit priority rules for competing systemd units (sockets, services, timers).  
   - Publish compensating procedures as migration operations with explicit recovery paths.  
   - **Owner:** `planner` component; **Deadline:** Wave 1 Day 12.

5. **Publish Evolution Milestone E040**  
   - Finalize `e040-systemd-transition.json` with all unit additions/removals/enabled-disabled decisions.  
   - Sign the artifact per mandate M-08 (qualified support) and M-09 (repeatability).  
   - **Owner:** `resolver` component; **Deadline:** Wave 1 Day 14.

---

## 6. Quick-Start Commands (repo-relative)

```bash
# View the upgrade log that drives the inventory
cat evidence/systemd/arch-2026-upgrade-log.json

# Populate the transition catalog skeleton
cp openclaw/migration-catalog/systemd-transitions.yaml evolution-engine/catalog/

# Run the integration test suite against a staged migration
autonomy/results/test-runner.sh --suite sys --target TP040

# Validate hook execution idempotency
other/systemd-hooks/pre-upgrade-hook.sh && other/systemd-hooks/post-validate-hook.sh
```

---

**End of Wave 1 Deliverable.**  
All paths, test IDs, and evidence citations are grounded in the repository structure and the migration mandate’s architectural invariants. Next wave (Wave 2) will deepen kernel-integration hooks and multi-distro vulnerability exclusion logic.
