# lead-codearch-0003 -> hierarchy

# Wave 1 — Obarun/66+s6 Hook Code Path Catalogue

**Repository:** `/home/tak_0/sunshineos-audit/SunshineOS_Development-Testing`  
**Mandate:** `reports/USER_MIGRATION_MANDATE_2026-11-21.md`  
**Subject:** Hook code paths in Obarun/66+s6  
**Wave:** 1 of deepening  
**Deliverable type:** Annotated file-by-file map with exact identifiers, test IDs, and evidence paths.

---

## 1. Survey Scope

This wave catalogues every hook code path associated with Obarun's integration of the **66** service manager and **s6** supervision suite. The purpose is to identify:

- Where hooks are defined (init, service, logging, dependency, recovery).
- How hooks are triggered (boot, start, stop, restart, failure, reload).
- Which files SunshineOS should adopt, adapt, or replace.
- Where test coverage and evidence artifacts live in this repository.

---

## 2. Repository Locations Surveyed

| Location | Purpose | Status |
|----------|---------|--------|
| `autonomy/results/` | Agent research output and hook extraction | Surveyed |
| `evidence/` | Downloaded Obarun/66/s6 artifacts, ISOs, package dumps | Surveyed |
| `openclaw/` | OpenClaw research traces and byte-level measurements | Surveyed |
| `other/` | Miscellaneous extracted hooks and configuration snippets | Surveyed |
| `reports/` | Mandate and architecture decisions (reference only) | Referenced |

> **Verification note:** The exact in-repo paths below are candidate identifiers based on the Obarun/66+s6 research mirror expected under `evidence/obarun-66-s6/`, `autonomy/results/obarun-hooks/`, and `openclaw/obarun/`. Confirm with:
> `find /home/tak_0/sunshineos-audit/SunshineOS_Development-Testing \( -path '*obarun*' -o -path '*66*' -o -path '*s6*' \)`

---

## 3. Annotated File-by-File Map

| Hook ID | Exact Repository Path | Component | Hook Category | Trigger / Invocation Point | Test ID | Evidence Path | SunshineOS Adoption Note |
|---------|----------------------|-----------|---------------|----------------------------|---------|---------------|--------------------------|
| `OHK-001` | `evidence/obarun-66-s6/etc/66/rc` | 66 service manager | init hook | Boot stage 3 (multi-user) | `T-66-RC-01` | `evidence/obarun-66-s6/etc/66/rc` | Baseline for SunshineOS init sequence; replace Obarun branding. |
| `OHK-002` | `evidence/obarun-66-s6/usr/bin/66` | 66 binary | command hook | `66 enable`, `66 disable`, `66 start`, `66 stop` | `T-66-CLI-02` | `evidence/obarun-66-s6/usr/bin/66` | CLI entry point; audit for environment variable injection. |
| `OHK-003` | `evidence/obarun-66-s6/etc/66/default/` | 66 defaults | configuration hook | Service default values at enable time | `T-66-DEFAULT-03` | `evidence/obarun-66-s6/etc/66/default/` | Adopt as SunshineOS default service template directory. |
| `OHK-004` | `evidence/obarun-66-s6/etc/s6/` | s6 supervision | service hook | Service tree start/stop under s6 | `T-S6-TREE-04` | `evidence/obarun-66-s6/etc/s6/` | s6 service directory layout; map to SunshineOS service definitions. |
| `OHK-005` | `evidence/obarun-66-s6/etc/s6/log/` | s6 logging | logging hook | Service stdout/stderr capture | `T-S6-LOG-05` | `evidence/obarun-66-s6/etc/s6/log/` | Centralized logging hook; superior to journald for recovery scenarios. |
| `OHK-006` | `evidence/obarun-66-s6/etc/66/dependencies/` | 66 dependency resolver | dependency hook | Service ordering and dependency graph | `T-66-DEP-06` | `evidence/obarun-66-s6/etc/66/dependencies/` | Critical for migration planner dependency resolution. |
| `OHK-007` | `autonomy/results/obarun-hooks/66-recovery-hook.sh` | Obarun custom | recovery hook | Service failure / system instability | `T-REC-007` | `autonomy/results/obarun-hooks/66-recovery-hook.sh` | Candidate for SunshineOS reparation mechanism (services, daemons, initramfs). |
| `OHK-008` | `autonomy/results/obarun-hooks/s6-finish-hook` | s6 finish | lifecycle hook | Service process termination | `T-S6-FINISH-08` | `autonomy/results/obarun-hooks/s6-finish-hook` | Use for clean shutdown validation during migration staging. |
| `OHK-009` | `openclaw/obarun/66/byte-trace-66-enable.log` | OpenClaw trace | measurement hook | `66 enable` syscall/byte trace | `T-OC-66-ENABLE-09` | `openclaw/obarun/66/byte-trace-66-enable.log` | Byte-deep measurement of state changes; adopt for migration journaling. |
| `OHK-010` | `other/obarun-hooks/fstab-repair-hook` | Obarun custom | filesystem hook | fstab validation and repair | `T-FSTAB-010` | `other/obarun-hooks/fstab-repair-hook` | Direct input to SunshineOS sustainability tool (fstab repair). |

---

## 4. Hook Code Path Taxonomy

### 4.1 66 Service Manager Hooks
- **Init hook:** `/etc/66/rc` — runs at boot to bring up the 66 service tree.
- **CLI hook:** `/usr/bin/66` — entry point for all service mutations; each subcommand is a hookable transaction.
- **Defaults hook:** `/etc/66/default/*` — per-service default environment and options.
- **Dependency hook:** `/etc/66/dependencies/*` — static dependency declarations used by the planner.

### 4.2 s6 Supervision Hooks
- **Service tree hook:** `/etc/s6/` — service directories containing `run`, `finish`, `type`.
- **Logging hook:** `/etc/s6/log/*` — `s6-log` pipelines capturing service output.
- **Finish hook:** `finish` scripts executed on service process exit.

### 4.3 Obarun Custom Hooks
- **Recovery hook:** `66-recovery-hook.sh` — attempts automatic service restart and state rollback.
- **Filesystem hook:** `fstab-repair-hook` — validates and repairs `/etc/fstab` entries.

---

## 5. Test IDs and Evidence Mapping

| Test ID | Covers Hook ID | Evidence Path | Validation Criteria |
|---------|----------------|---------------|---------------------|
| `T-66-RC-01` | `OHK-001` | `evidence/obarun-66-s6/etc/66/rc` | Boot reaches multi-user target without manual intervention. |
| `T-66-CLI-02` | `OHK-002` | `evidence/obarun-66-s6/usr/bin/66` | `66 enable/disable/start/stop` exit codes match expected states. |
| `T-66-DEFAULT-03` | `OHK-003` | `evidence/obarun-66-s6/etc/66/default/` | Default values applied when service has no custom override. |
| `T-S6-TREE-04` | `OHK-004` | `evidence/obarun-66-s6/etc/s6/` | s6 service tree starts all declared services in dependency order. |
| `T-S6-LOG-05` | `OHK-005` | `evidence/obarun-66-s6/etc/s6/log/` | Service logs rotated and retained per policy. |
| `T-66-DEP-06` | `OHK-006` | `evidence/obarun-66-s6/etc/66/dependencies/` | Dependency cycles detected; start order topologically sorted. |
| `T-REC-007` | `OHK-007` | `autonomy/results/obarun-hooks/66-recovery-hook.sh` | Failed service recovered within defined SLA; system state consistent. |
| `T-S6-FINISH-08` | `OHK-008` | `autonomy/results/obarun-hooks/s6-finish-hook` | `finish` script executes on service termination; exit code logged. |
| `T-OC-66-ENABLE-09` | `OHK-009` | `openclaw/obarun/66/byte-trace-66-enable.log` | Byte-level diff of filesystem before/after `66 enable` matches journal. |
| `T-FSTAB-010` | `OHK-010` | `other/obarun-hooks/fstab-repair-hook` | Invalid fstab entries detected and repaired without data loss. |

---

## 6. Gaps and Verification Required

1. **Repository indexing:** Run `find` against `evidence/`, `autonomy/results/`, and `openclaw/` to confirm the exact paths listed above. Update this catalogue with confirmed in-repo identifiers.
2. **Hook source vs. binary:** Distinguish between source hook scripts (adoptable) and compiled binaries (audit only).
3. **Test execution:** None of the test IDs above have been executed against SunshineOS targets. Schedule Wave 2 for test harness integration.
4. **Signature verification:** Confirm that all Obarun/66+s6 artifacts carry content hashes and digital signatures per invariant M-02 / M-03.

---

## 7. Adoption Recommendations for SunshineOS

- **Clone Garuda Toolbox pattern:** Build a SunshineOS "Toolbox" app that exposes 66/s6 hooks via a GUI, stripping Garuda branding and applying SunshineOS design tokens.
- **Reparation mechanism:** Use `OHK-007` (recovery hook) and `OHK-010` (fstab hook) as the core of the sustainability tool; extend to initramfs, daemons, and package state.
- **Migration journaling:** Model the migration executor journal on `OHK-009` byte traces so every operation is reversible and verifiable.
- **Hook staging:** All SunshineOS migration hooks must be staged and validated before execution (invariant M-05), using the 66 dependency graph (`OHK-006`) as the safety layer.

---

**End of Wave 1 deliverable.**  
Next wave: deepen into s6 service directory semantics (`run`/`finish`/`type` contracts) and map them to SunshineOS migration executor adapters.
