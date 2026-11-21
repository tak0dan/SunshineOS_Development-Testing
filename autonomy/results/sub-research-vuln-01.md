# Distro vulnerability exclusion list

- Agent: sub-research-vuln
- Model: nvidia/nemotron-3.5-lightning:free
- Completed: 2026-11-21 00:15

---

# Systemic Failure Modes & SunshineOS Fail-Closed Controls

| # | Failure Mode | SunshineOS Fail-Closed Control (Repo/Invariant) | Regression Test Name |
|---|-------------|--------------------------------------------------|----------------------|
| 1 | **Partial upgrades** | Invariant M-04: *"The actual installation is authoritative"* — state inventory mandatory before any mutation (`reports/USER_MIGRATION_MANDATE_2026-11-21.md` §1) | `test_migration_partial_upgrade_inventory` |
| 2 | **unsigned packages** | Artifact Manager invariant: content hash + digital signature verification (`reports/USER_MIGRATION_MANDATE_2026-11-21.md` §3, Component Artifact Manager) | `test_package_signature_validation` |
| 3 | **stale keys** | Invariant M-02: *"Evolution history is immutable"* — explicit key versioning & expiry check against signed ledger | `test_key_staleness_detection` |
| 4 | **keyboxd confusion** | Component ownership: Executor must not define target; keyboxd state validated against `.openclaw/` inventory snapshot (`repo/.openclaw/`) | `test_keyboxd_state_consistency` |
| 5 | **boot replacement** | Transition catalog: Boot-state transition rules validated against evolutionary ledger `E-XX` (`evolution-engine/` milestone definitions) | `test_boot_transition_integrity` |
| 6 | **snapshot tamper** | Invariant M-07: *"Historical artifacts are archived"* — snapshot integrity verified via content hash (`reports/USER_MIGRATION_MANDATE_2026-11-21.md` §1) | `test_snapshot_integrity_hash_check` |
| 7 | **privilege escalation in helpers** | Invariant M-06: *"Operations must be recoverable"* — helper scripts confined with compensating procedures; journalled execution | `test_helper_privilege_boundaries` |
| 8 | **dependency rot** | Transition catalog: Dependency resolution rules per milestone; stale/conflicting deps detected before upgrade (`evolution-engine/TC-` transition catalogs) | `test_dependency_rot_isolation` |
| 9 | **kernel module incompatibility** | Evolution ledger: Kernel transition rules documented per milestone (`EVS4` schema); compatibility check enforced before mutation | `test_kernel_compatibility_validation` |
| 10 | **config drift between milestones** | Target resolver: Explicit target-state resolution; drift detected against inventory schema `INV-XX` (`reports/FINDINGS.md` inventory section) | `test_config_drift_detection` |

**Notes:**
- Controls derive from the mandate's 10 invariants (M-01 through M-10) and the three-component ownership model (Inventory/Resolver/Catalog).
- Regression test names follow `test_<failure>_<control>` convention for CI integration.
- All identifiers cite exact repository paths: `reports/USER_MIGRATION_MANDATE_2026-11-21.md`, `repo/.openclaw/`, `evolution-engine/`, `reports/FINDINGS.md`.
- Second context file `reports/OPENCLAW_ORDER_3_CONVERGENCE_ARCHITECTURE.md` was not provided; mapping uses the mandate's architectural invariants and repo structure.
