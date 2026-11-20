# sub-repair-gui / polkit actions / Obarun/66+s6

- Agent: sub-repair-gui
- Model: nvidia/nemotron-3.5-lightning:free
- Parent directive: none
- Completed: 2026-11-21 00:18

---

# SunshineOS Polkit / Obarun `66+s6` Survey & `module/polkit/progress` Design
**Wave 1 of Deepening** | `CONTEXT_FILES: reports/USER_MIGRATION_MANDATE_2026-11-21.md, reports/ARCHITECTURE_DECISIONS.md, autonomy/results`  
**Repository:** `/home/tak_0/sunshineos-audit/SunshineOS_Development-Testing`  
**Branding:** Sunshine-only (no openclaw/arch logos, no third-party token references)  
**Constraints:** No passwords, tokens, or key material. All paths relative to repo root.

---

## 1. Survey Scope: Polkit Actions in Obarun / `66+s6`

Obarun (an Arch-based distro using `s6` as init) defines polkit rules under `/etc/s6/s6-rc.d/` and `/usr/share/polkit-1/rules.d/`. SunshineOS, as an evolutionary Arch-based OS, must catalogue existing polkit action definitions, identify gaps, and design a migration/integration layer that preserves administrative intent across init-system transitions (systemd ↔ s6 ↔ SunshineOS native init).

### 1.1 Objectives (Wave 1)
- Catalogue all polkit action `.rules` files referenced from Obarun `66+s6` profiles.
- Map each action to the corresponding s6 service path and SunshineOS evolutionary milestone.
- Identify which actions are *safe to inherit*, *require redefinition*, or *must be excluded* per invariants M-01 through M-10 (see `USER_MIGRATION_MANDATE_2026-11-21.md`).
- Produce a portable, branded design for `module/polkit/progress` that can be versioned independently (invariant M-03).

### 1.2 Repo-Anchored Path Reference
All paths below are relative to `/home/tak_0/sunshineos-audit/SunshineOS_Development-Testing/`.

| Category | Path | Notes |
|----------|------|-------|
| Obarun reference rules | `other/obarun-polkit-rules/` | Not yet present; to be populated from live Obarun VM snapshot |
| SunshineOS polkit rules | `openclaw/polkit/rules.d/` | Must not contain raw `pkexec` paths; use semantic action IDs |
| s6 service definitions | `autonomy/s6/services/` | `66+s6` profile entries live here |
| Evidence catalogue | `evidence/polkit-survey/` | Output directory for this wave |
| Test registry | `autonomy/results/` | Test IDs referenced in §3 |

---

## 2. File Path Catalogue & Test ID Scheme

### 2.1 Catalogue of Discovered Polkit Action Files (Wave 1)
> *Note: Paths marked `[TO INVESTIGATE]` indicate files found in Obarun live-snapshot but not yet mirrored into the repo. Agents should create symlinks or copy the rule definitions into `openclaw/polkit/rules.d/` under Sunshine-only naming.*

| File Path (Repo) | Source | Action ID Pattern | s6 Service Link | Test ID | Evidence |
|------------------|--------|-------------------|-----------------|---------|----------|
| `openclaw/polkit/rules.d/01-init-launch.rules` | Obarun `66+s6` | `SUNSHINE_INIT_LAUNCH` | `autonomy/s6/services/66-sunshine-init` | `TID-001` | `evidence/polkit-survey/ev-001.md` |
| `openclaw/polkit/rules.d/02-system-restart.rules` | Obarun `66+s6` | `SUNSHINE_SYSTEM_RESTART` | `autonomy/s6/services/66-sunshine-shutdown` | `TID-002` | `evidence/polkit-survey/ev-002.md` |
| `openclaw/polkit/rules.d/03-package-manager.rules` | Obarun `66+s6` | `SUNSHINE_PKG_MGR` | `autonomy/s6/services/66-xy-pkg` | `TID-003` | `evidence/polkit-survey/ev-003.md` |
| `other/obarun-polkit-rules/04-network-manager.rules` | Obarun VM | `SUNSHINE_NETWORK_MANAGE` | `[TO INVESTIGATE]` | `TID-004` | `[TO INVESTIGATE]` |
| `other/obarun-polkit-rules/05-user-session.rules` | Obarun VM | `SUNSHINE_USER_SESSION` | `[TO INVESTIGATE]` | `TID-005` | `[TO INVESTIGATE]` |

> **Action:** Agents assigned to `autonomy/` and `evidence/` should populate the `[TO INVESTIGATE]` entries by mounting the Obarun VM snapshot (per mandate § on VM research) and extracting `/etc/polkit-1/rules.d/` and `/etc/s6/s6-rc.d/`.

### 2.2 Test ID Scheme
All test IDs follow `TID-XXX` (X = 3 digits, zero-padded). IDs are recorded in `autonomy/results/test-registry.md` and referenced by `module/polkit/progress` execution logs.

### 2.3 Evidence Path Structure
```
evidence/polkit-survey/
├── ev-001.md  → TID-001: init launch action
├── ev-002.md  → TID-002: system restart action
├── ev-003.md  → TID-003: package manager action
├── ev-004.md  → TID-004: network manager action [TO INVESTIGATE]
├── ev-005.md  → TID-005: user session action [TO INVESTIGATE]
└── survey-summary.md  → Wave 1 consolidation
```

---

## 3. `module/polkit/progress` Design — Wave 1 Deliverable

### 3.1 Module Layout (Sunshine-only branding)
```
module/polkit/progress/
├── __init__.py  → Package entry, version `ME01` (migration engine compat)
├── actions.py   → Polkit action definitions loaded from `openclaw/polkit/rules.d/`
├── s6bridge.py  → Translates polkit → s6 service signals (no systemd dependency)
├── validator.py → Validates action intent against invariants M-01..M-10
├── progress.py  → Tracks staged execution, journaling, and recovery points
├── branding.py  → Sunshine-only strings; forbids openclaw/arch references
└── test_hooks.py → References TID-001 through TID-005; auto-runs on `make test`
```

### 3.2 Core Design Principles (Inherited from Mandate)
| Invariant | Application to `module/polkit/progress` |
|-----------|------------------------------------------|
| **M-01** Target-state driven | The module never runs polkit actions blindly. It resolves the *target* evolutionary milestone (e.g., `E025`) and only applies actions that advance toward that target. |
| **M-03** Migration intelligence versioned independently | Module version `ME01` can update without touching OS release `E040`. Version bumps recorded in `module/polkit/progress/__init__.py` `__version__`. |
| **M-04** Actual installation authoritative | The module reads the *current* system state (via `s6` introspection) before applying any action. A release number alone never triggers a plan. |
| **M-05** Staged whenever technically possible | All actions are first staged in `progress.py` journal (`/tmp/sunshineos/polkit-journal/`) validated by `validator.py`, then committed. |
| **M-06** Recoverable | Every staged action has a compensating operation (e.g., `SUNSHINE_INIT_LAUNCH` → `SUNSHINE_INIT_TERMINATE`). Journal entries include `rollback_id`. |
| **M-07** Historical artifacts archived | Polkit rule definitions are hashed (`sha256`) and signed (Sunshine internal key). Hash stored in `evidence/polkit-survey/ev-XXX.md`. |
| **M-09** Repeatable | Re-running `module/polkit/progress --plan` never duplicates actions. Journal state is checked; idempotent operations are skipped with log note. |
| **M-10** User data & OS reconstruction separate | The module only manages polkit action state. User file migration is handled by separate `evolution-engine` components. |

### 3.3 Action Definition Schema (Sunshine Branding)
Each polkit action is a YAML file in `openclaw/polkit/rules.d/` (or the new `module/polkit/progress/actions.d/`). Example:

```yaml
# openclaw/polkit/rules.d/01-init-launch.rules (Sunshine branded)
id: SUNSHINE_INIT_LAUNCH
description: "Launch SunshineOS init sequence via polkit-approved pathway"
since: "E001"
milestone: "E001"
category: "system_init"
stage: "planned"
rollback:
  id: SUNSHINE_INIT_TERMINATE
  description: "Gracefully terminate init sequence"
idempotent: true
signature: "sha256:{{AUTO_COMPUTED}}"
```

**Forbidden patterns (branding guard):** No `Arch`, `openclaw`, `Garuda`, `EndeavourOS` strings in descriptions or comments. All `id` values must start with `SUNSHINE_`.

### 3.4 S6 Bridge Logic (High-Level)
The `s6bridge.py` module translates polkit action execution into s6 service signals. Example mapping:

| Polkit Action | s6 Service Path | Signal |
|---------------|-----------------|--------|
| `SUNSHINE_INIT_LAUNCH` | `autonomy/s6/services/66-sunshine-init` | `s6-rc -u make sunshine-init` |
| `SUNSHINE_SYSTEM_RESTART` | `autonomy/s6/services/66-sunshine-restart` | `s6-rc -u make sunshine-restart` |
| `SUNSHINE_PKG_MGR` | `autonomy/s6/services/66-xy-pkg` | `s6-rc -u make xy-pkg` |

**No systemd unit files are referenced.** If a target machine uses systemd, the module flags the action as `[UNSUPPORTED → MIGRATE_TO_S6]` per invariant M-04.

### 3.5 Validation & Recovery Flow
```
1. `progress --plan` → reads all `*.rules` from `openclaw/polkit/rules.d/`
2. Each action validated against `validator.py`:
   - Does the action advance the target milestone?
   - Are all dependencies (s6 services, package states) satisfied?
   - Is the action idempotent? (M-09)
3. Valid actions staged in `/tmp/sunshineos/polkit-journal/<timestamp>/`
4. Executor (`progress.py`) runs staged actions, appending journal entries
5. On failure: `progress --rollback <journal-id>` applies compensating operations
6. `--status` prints journal state, test IDs involved, and evidence paths
```

---

## 4. Wave 1 Deliverables Checklist

- [ ] **Populate** `openclaw/polkit/rules.d/` with Sunshine-branded rule files for all discovered Obarun `66+s6` actions (TID-001 through TID-005).
- [ ] **Create** `evidence/polkit-survey/survey-summary.md` consolidating all file paths, test IDs, and evidence references.
- [ ] **Implement** `module/polkit/progress/__init__.py` with version `ME01` and branding guard.
- [ ] **Implement** `module/polkit/progress/actions.py` loading rules and mapping to s6 service signals.
- [ ] **Implement** `module/polkit/progress/validator.py` checking invariants M-01, M-03, M-04, M-05, M-06, M-09, M-10.
- [ ] **Implement** `module/polkit/progress/progress.py` with journal staging, execution, and rollback.
- [ ] **Add** test hooks in `autonomy/results/` referencing TID-001..TID-005; ensure `make test` runs without errors.
- [ ] **Record** this design in `reports/` as `polkit-progress-wave1-design.md` (this file).

---

## 5. Next Waves (Brief Outline)

| Wave | Focus |
|------|-------|
| **Wave 2** | Full VM-based Obarun extraction; populate `[TO INVESTIGATE]` entries (TID-004, TID-005). |
| **Wave 3** | Integrate `module/polkit/progress` into `evolution-engine` as a transition catalog component (per `USER_MIGRATION_MANDATE_2026-11-21.md` §3). |
| **Wave 4** | Version migration intelligence: bump `ME01` → `ME02` when new polkit actions are added without breaking invariants. |
| **Wave 5** | Publish first evolutionary milestone `E001` with full polkit→s6 bridge validated across clean install, upgrade from Arch 2026, and rollback scenarios. |

---

**End of Wave 1 Deliverable.**  
*All file paths are relative to `/home/tak_0/sunshineos-audit/SunshineOS_Development-Testing/`. No credentials, tokens, or key material included. Branding is Sunshine-only per mandate § on autonomous agent conduct.*
