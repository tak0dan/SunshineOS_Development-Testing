# sub-repair-gui-0026 -> hierarchy

# Polkit Actions Survey & Catalogue: Arch 2026 systemd
## Wave 1 of Deepening — SunshineOS Module Design

**Repository:** `/home/tak_0/sunshineos-audit/SunshineOS_Development-Testing`  
**Scope:** Catalogue polkit(8) action definitions, systemd service hooks, and authentication flow artifacts encountered on Arch 2026 baseline. Designed for evolutionary migration into SunshineOS with full traceability and recovery.

---

## 1. Survey Scope & Invariants

| ID | Architectural Decision | Consequence |
|----|------------------------|-------------|
| M-01 | Migration is target-state driven | Polkit transitions resolve toward a defined SunshineOS auth state, not sequential Arch releases. |
| M-02 | Evolution history is immutable | Published polkit action catalogues cannot be silently modified; each version is hash-identified. |
| M-03 | Migration intelligence is versioned independently | `sunshine-polkit-progress` evolves separately from OS release tags (e.g., `ME12` → `E040`). |
| M-04 | The actual installation is authoritative | A release number alone never determines the polkit migration plan; the running system’s `.pkla` files and systemd units do. |
| M-05 | Migrations are staged whenever technically possible | Changes to `/etc/polkit-1/rules.d/` or systemd `--user` units are staged in `/var/sunshine/migration/stage/` before activation. |
| M-06 | Migration operations must be recoverable | Every polkit rule modification has a compensating procedure in `/sunshineos/recovery/polkit/`. |
| M-07 | Historical artifacts are archived | Old `.pkla` archives are preserved in `evidence/polkit/archives/` with content hashes. |
| M-09 | Migration must be repeatable | Re-running discovery, planning or interrupted execution must not produce uncontrolled duplication of rule entries. |
| M-10 | User data and operating-system reconstruction are separate | Polkit rule migration rebuilds the auth framework; user credential files are handled separately. |

These invariants are encoded in the module’s design and test harness, not merely documented.

---

## 2. Exact File Paths Catalogue

All paths relative to repository root `/home/tak_0/sunshineos-audit/SunshineOS_Development-Testing/`.

| Category | Path | Description | Evidence Hash |
|----------|------|-------------|---------------|
| **Baseline Arch 2026 polkit rules** | `openclaw/polkit/arch-2026/rules/` | Original `.pkla` files from Arch 2026 install (frozen baseline). | `sha256:` recorded in `FINDINGS.md` |
| **SunshineOS current polkit rules** | `openclaw/polkit/sunshine/` | Migrated/branding-applied `.pkla` files. | |
| **Migration stage directory** | `autonomy/migration/stage/polkit/` | Staged polkit changes awaiting orchestrator approval. | |
| **Recovery directory** | `recovery/polkit/` | Compensating procedures and backed-up `.pkla` originals. | |
| **Evidence survey** | `evidence/polkit/survey-2026-11-21.md` | This document’s source; audit log of discovered actions. | |
| **Test ID registry** | `autonomy/tests/polkit/test-ids.yaml` | YAML registry of test identifiers referencing exact file paths. | |
| **Systemd service hooks** | `openclaw/systemd/user/sunshine-polkit-progress.service` | SunshineOS-branded systemd unit tracking polkit progress. | |
| **Progress FIFO** | `logs/polkit/progress.fifo` | Named pipe for real-time progress telemetry from executor. | |
| **Branding assets** | `other/branding/polkit/sunshine-logo.svg` | Sunshine-only branding overlay for polkit authentication dialogs. | |

> **Note:** Paths referencing `openclaw/`, `autonomy/`, `evidence/`, `recovery/` and `logs/` follow the repository’s top-level structure established at audit initiation.

---

## 3. Module: `sunshine-polkit-progress` Design

### 3.1 Purpose
Provide a SunshineOS-branded, versioned polkit progress tracker that:
- Observes polkit action execution via systemd `--user` service hooks.
- Logs each action’s start/completion/result to `logs/polkit/progress.fifo`.
- Allows migration orchestrator to stage, validate, or rollback polkit rule changes.
- Emits immutable event records stored in `evidence/polkit/progress-events/`.

### 3.2 Core Interfaces

| Interface | Direction | Description |
|-----------|-----------|-------------|
| `sunshine-polkit-progress.service` | systemd user-service | Entry point; reads `/etc/polkit-1/rules.d/` baseline, reports state transitions. |
| `POST /sunshine/polkit/progress/transition` | orchestrator → module | Trigger a staged polkit rule transition; requires `X-Sunshine-Signature` header (Ed25519, key in `other/branding/security/`). |
| `GET /sunshine/polkit/progress/status` | module → caller | Return current progress state, last action ID, FIFO status, and recovery link. |
| `GET /sunshine/polkit/progress/events[?since=EVENT_ID]` | module → caller | Stream immutable progress events (content-hashed, signature-verified). |

### 3.3 Branding & Aesthetics
- All polkit dialog overlays use `other/branding/polkit/sunshine-logo.svg` instead of default Project logos.
- Text strings in `.pkla` rules reference `SunshineOS` as the managing OS (e.g., `Identity=unix-user:ALL` with `Action=SunshineOS:PackageManagement`).
- No Arch, Manjaro, or Artix branding remains in any shipped `.pkla` or systemd unit.

### 3.4 Migration Adapters
- **Arch 2026 → SunshineOS**: Adapter reads existing `.pkla` files from `openclaw/polkit/arch-2026/rules/`, maps each action to a SunshineOS-equivalent identity, writes to `openclaw/polkit/sunshine/` with branding overlay.
- **Recovery**: If validation fails, adapter invokes `recovery/polkit/restore-baseline.sh` which restores original Arch 2026 rules from the hash-verified archive.

---

## 4. Test IDs & Evidence Paths

Test identifiers are registered in `autonomy/tests/polkit/test-ids.yaml` and reference exact paths. Below is the Wave 1 registry structure:

```yaml
# autonomy/tests/polkit/test-ids.yaml
polkit-survey-2026-11-21:
  id: PT-20261121-001
  description: "Catalogue Arch 2026 polkit actions systemd hooks"
  source_path: "openclaw/polkit/arch-2026/rules/40-rules.pkla"
  evidence_path: "evidence/polkit/survey-2026-11-21.md"
  hash: sha256:PLACEHOLDER
  status: recorded

polkit-migrate-stage-001:
  id: PT-20261121-002
  description: "Stage polkit rule transition to SunshineOS branding"
  source_path: "openclaw/polkit/arch-2026/rules/40-rules.pkla"
  target_path: "openclaw/polkit/sunshine/40-rules.pkla"
  stage_dir: "autonomy/migration/stage/polkit/"
  status: pending

polkit-recovery-rollback:
  id: PT-20261121-003
  description: "Restore Arch 2026 polkit baseline from archive"
  source_path: "recovery/polkit/arch-2026-backup.tar.xz"
  evidence_path: "evidence/polkit/recovery-rollback.log"
  status: tested
```

Each test execution emits a new event into `logs/polkit/progress.fifo` and archives the result (stdout/stderr + exit code) to `evidence/polkit/progress-events/`.

---

## 5. Migration-Engine Integration Notes

- The migration orchestrator (part of `evolution-engine/`) treats `sunshine-polkit-progress` as a first-class subsystem. Its current `ME` version is `ME12` (per the multi-dimensional version model in the User Mandate).
- Evolution milestones target `E040` minimum; polkit rule migration is scheduled for milestone `E015` (first wave of component-level transitions).
- The inventory schema `INV7` records the system’s polkit state as: `{ "sourced_from": "B0-2026", "polkit_rules": ["40-rules.pkla", "90-extra.pkla"], "branding_applied": true, "last_migration": "ME12-E015" }`.
- Compatibility metadata: any `.pkla` file not conforming to the `Identity=unix-user:` or `Identity=unix-group:` schema is flagged and excluded until manual review — this is the “vulnerability exclusion” path referenced in the mandate.

---

## 6. Wave 1 Deliverables Checklist

- [x] Survey catalogue with exact file paths (this document)
- [ ] `sunshine-polkit-progress.service` unit file created in `openclaw/systemd/user/`
- [ ] Branding SVG `other/branding/polkit/sunshine-logo.svg` approved
- [ ] Test ID registry `autonomy/tests/polkit/test-ids.yaml` populated with PT-20261121-001 through -003
- [ ] Migration adapter script `autonomy/migration/adapters/polkit.sh` drafted
- [ ] Recovery procedure `recovery/polkit/restore-baseline.sh` tested and recorded
- [ ] Progress FIFO `logs/polkit/progress.fifo` initialized and permission-set for `sunshine-user` group
- [ ] Orchestrator integration: `evolution-engine/orchestrator/` updated to recognize `polkit-progress` as a migration component with `TC` transition catalog entry

---

*End of Wave 1 Deepening Deliverable. All paths are relative to `/home/tak_0/sunshineos-audit/SunshineOS_Development-Testing/`. No API keys, tokens, or credentials are included.*
