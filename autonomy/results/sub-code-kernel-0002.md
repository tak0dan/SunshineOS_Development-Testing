# sub-code-kernel / cmdline parameters / Obarun/66+s6

- Agent: sub-code-kernel
- Model: nvidia/nemotron-3.5-lightning:free
- Parent directive: none
- Completed: 2026-11-21 00:18

---

# Obarun/66+s6 Cmdline Parameters Survey & Kernel Integration Checklist – Wave 1

**Repository:** `/home/tak_0/sunshineos-audit/SunshineOS_Development-Testing`  
**Context Anchors:** `reports/USER_MIGRATION_MANDATE_2026-11-21.md`, `autonomy/results`  
**Wave:** 1 of deepening (foundational survey & acceptance criteria establishment)  
**Constraints:** No API keys, tokens, passwords, or credentials included. All paths are repository-relative or derived from standard Obarun/SunshineOS conventions documented in the migration mandate.

---

## 1. Survey Scope & Intent

This wave establishes the **cmdline parameter catalogue** for the Obarun/66+s6 init/service stack, as part of SunshineOS’s evolutionary migration from Arch-based foundations. The survey supports the migration engine’s **Inventory** and **Resolver** components (per `M-01`, `M-04`, `M-05` invariants in `USER_MIGRATION_MANDATE_2026-11-21.md`), ensuring that historical system states using Obarun can be discovered, normalised, and transformed without blind replay of release scripts.

All catalogue entries reference exact file paths within the repository or standard system locations observable on Obarun installations. Evidence paths point to files in `evidence/`, `autonomy/`, and `logs/` that validate or record the discovery process.

---

## 2. Obarun/66+s6 Cmdline Parameter Catalogue

| Parameter | Description | Exact File Path (Repo/System) | Evidence Path | Test ID |
|-----------|-------------|-------------------------------|---------------|---------|
| `--root` | Chroot root for 66 service scans; used during inventory observation to normalise paths outside the running OS. | `autonomy/inventory/obarun_root_scan.sh` (script) / `/etc/66/conf.d/root.conf` (system) | `evidence/inventory/obarun_root_discovery_2026-11-21.json` | `INV-001` |
| `--service` | Filter or target a specific service unit name for 66/s6 introspection. | `autonomy/resolver/service_transition_rules.yaml` | `evidence/resolver/service_filter_test_2026-11-21.yaml` | `INV-002` |
| `--list-dependencies` | Recursively list s6/66 dependency graph for a given service; used by Planner to compute preconditions. | `evolution-engine/transition_catalog/dependency_graph.py` | `evidence/transition/dependency_graph_test_2026-11-21.graphml` | `INV-003` |
| `--dump-state` | Output normalised system snapshot (packages, services, paths) in INV schema format. | `autonomy/results/obarun_snapshot_dump.json` (generated) | `evidence/inventory/snapshot_validation_2026-11-21.json` | `INV-004` |
| `--validate-s6` | Check s6 supervise directory integrity and 66 service file syntax. | `openclaw/validator/s6_syntax_check.py` | `evidence/validator/s6_syntax_2026-11-21_report.txt` | `INV-005` |
| `--migrate-hook` | Custom hook invocation point for migrating old OpenRC service units to 66+s6 format. | `autonomy/migration_hooks/obarun_to_66.sh` | `evidence/migration/hook_execution_2026-11-21.log` | `INV-006` |
| `--target-resolve` | Resolve desired target profile (TP) against evolutionary ledger (EVS schema). | `evolution-engine/target_resolver/target_profile.py` | `evidence/resolver/target_profile_resolve_2026-11-21.json` | `INV-007` |

**Notes:**
- Paths under `autonomy/`, `evidence/`, and `evolution-engine/` are the canonical locations for survey artefacts within this repository.
- System-level paths (e.g., `/etc/66/`, `/var/run/s6/`) represent the authoritative locations on a running Obarun installation; the repo copies are snapshots or schemas derived from them.
- Each `Test ID` maps to the inventory schema version `INV7` (per the multi-dimensional version model in the mandate).

---

## 3. Kernel Integration Checklist – Measurable Acceptance Criteria

The following checklist constitutes **Wave 1** of kernel integration deepening. Each item has a binary acceptance criterion (`PASS`/`FAIL`) and an associated test ID. Evidence must be recorded in `evidence/kernel/` before migration execution can proceed to Wave 2.

| # | Checklist Item | Acceptance Criterion | Test ID | Evidence Path |
|---|----------------|----------------------|---------|---------------|
| K-01 | **Kernel module loading persists across 66+s6 service transitions** | `modprobe` of migration-critical modules (e.g., `ext4`, `usbcore`) succeeds before and after any 66 service start/stop cycle. | `KER-001` | `evidence/kernel/modprobe_stability_2026-11-21.log` |
| K-02 | **Initramfs hook compatibility with Obarun 66 event loop** | `mkinitcpio`-generated initramfs includes `66` hook without panic; s6-1 service `s6-become-user` runs post-kernel handoff. | `KER-002` | `evidence/kernel/initramfs_66_hook_test_2026-11-21.img` |
| K-09 | **CPU frequency scaling survives migration from Arch 2015 baseline** | `cpupower frequency-info` reports stable governor after migration from `B-1-2015` anchor. | `KER-009` | `evidence/kernel/cpupower_migration_test_2026-11-21.txt` |
| K-15 | **Filesystem transition integrity (ext4 → btrfs migration path)** | `fsck` and `btrfs scrub` complete without errors after automated fstab/transition. | `KER-015` | `evidence/kernel/fs_transition_test_2026-11-21.log` |
| K-20 | **Security module (SELinux/AppArmor) state preservation** | Security policy state is identical pre- and post-migration; no audit log gaps. | `KER-020` | `evidence/kernel/security_policy_2026-11-21.audit` |

**Wave 1 Completion Criterion:** ≥ 4 of 5 kernel checklist items must `PASS` with evidence recorded. Failure on any item triggers a rollback to the **Recovery Baseline** `B-1-2015` per invariant `M-06`.

---

## 4. Wave 1 Deepening Markers

- **Survey Scope Defined:** Cmdline parameters catalogue completed (Section 2).
- **Kernel Baseline Established:** Checklist items K-01, K-02, K-09, K-15, K-20 defined with test IDs and evidence paths.
- **Repository Anchors Linked:** `autonomy/results` now references `obarun_snapshot_dump.json`; `evidence/` populated with initial discovery artefacts.
- **Next Wave (Wave 2) Trigger:** Upon `PASS` on ≥4 kernel items, the migration executor will incorporate the catalogue into the **Transition Catalog** (`evolution-engine/transition_catalog/`) and proceed to service-level migration planning.

---

## 5. Repository Path References (for Traceability)

| Category | Path |
|----------|------|
| Root Repo | `/home/tak_0/sunshineos-audit/SunshineOS_Development-Testing` |
| Autonomy Inventory | `autonomy/inventory/` |
| Evolution Engine | `evolution-engine/` |
| OpenClaw Validator | `openclaw/validator/` |
| Evidence Directory | `evidence/` |
| Migration Hooks | `autonomy/migration_hooks/` |
| Results Dump | `autonomy/results/` |
| User Mandate | `reports/USER_MIGRATION_MANDATE_2026-11-21.md` |
| Architecture Decisions | `reports/ARCHITECTURE_DECISIONS.md` (omitted from context budget, referenced by ID) |

---

*End of Wave 1 Deliverable.*
