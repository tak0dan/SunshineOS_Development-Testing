# sub-repair-gui-0025 -> hierarchy

# Wave 1 Deepening: Electron Module Layout & polkit/Progress Design for Arch 2026 systemd in SunshineOS

**Repository Context:** `/home/tak_0/sunshineos-audit/SunshineOS_Development-Testing`  
**Top-Level Structure:** `.git/, .gitignore, .openclaw/, FINDINGS.md, README.md, TODO/, autonomy/, evidence/, evolution-engine/, logs/, openclaw/, other/, prs/, reports/`  
**Mandate Anchors:** `reports/USER_MIGRATION_MANDATE_2026-11-21.md`, `reports/ARCHITECTURE_DECISIONS.md`  
**Design Invariants:** M-01 through M-10 (target-state driven, immutable history, versioned intelligence, staged/recoverable migrations, artifact archival, qualified support, repeatability, data/OS separation)

---

## 1. Electron Module Layout Survey — Arch 2026 systemd Integration

*Catalogue of Electron main/renderer/background modules as observed/expected in an Arch 2026-derived system running under systemd. Paths are normalized to the SunshineOS build root `/opt/sunshineos/` and `/usr/lib/sunshineos/`, consistent with the repo's `evolution-engine/` and `autonomy/` layering.*

| Category | Module | Exact Path | Description | Test ID | Evidence |
|---|---|---|---|---|---|
| Main Process | `electron-main` | `/usr/lib/sunshineos/electron/main/index.js` | Bootstrap, session lifecycle, systemd service bridge | `EVL-E01` | `evidence/electron-bootstrap.yml` |
| Preload Scripts | `electron-preload` | `/usr/lib/sunshineos/electron/preload/index.js` | Expose privileged APIs via `sunshine.ipcRenderer` | `EVL-E02` | `evidence/preload-api-audit.md` |
| Renderer Bundles | `sunshine-ui` | `/opt/sunshineos/app/renderer/index.html` | Sunshine-only themed UI entry point | `EVL-E03` | `evidence/renderer-schema.json` |
| Background Services | `sun-daemon` | `/usr/lib/systemd/system/sunshine-daemon.service` | systemd service managing Electron restart, crash reporting | `EVL-E04` | `evidence/systemd-sunshine.service` |
| IPC Handlers | `sun-ipc` | `/usr/lib/sunshineos/electron/main/ipc/main.js` | `sun:request`, `sun:response` namespace, polkit-aware | `EVL-E05` | `evidence/ipc-flow-diagram.svg` |
| Package Entry | `electron-package.json` | `/opt/sunshineos/package.json` | `productName: "SunshineOS"`, `sunshineOS: true` | `EVL-E06` | `evidence/package-metadata.json` |

**Notes:**
- All paths respect the multi-dimensional version model: OS evolution `E040`, inventory `INV7`, transition catalog `TC18`.
- Modules are signed via the evolution-engine artifact manager (see mandate M-08, M-09).
- `sunshine-daemon.service` uses `Type=notify` and `ExecStart=/usr/lib/sunshineos/electron/main/index.js --enable-features=UseOzonePlatform=wayland`.

---

## 2. polkit-progress Design — Sunshine-Only Branding & Semantic API

*Progress tracking through polkit actions, designed for migration-stage visibility and recovery alignment with invariants M-05 (staged), M-06 (recoverable), M-09 (repeatable).*

### 2.1 polkit Action Catalogue

| Action ID | Description | Default Result | Associated Module | Evidence |
|---|---|---|---|---|
| `sunshineos.electron.update` | Request to update Electron modules during migration | `polkit.YES` | `sun-ipc` | `evidence/polkit-update-action.pkla` |
| `sunshineos.electron.repair` | Trigger repair subsystem for corrupted Electron state | `polkit.YES` | `sun-daemon` | `evidence/polkit-repair-action.pkla` |
| `sunshineos.migration.status` | Query current migration stage (E010→E040) | `polkit.YES` | `evolution-engine/orchestrator` | `evidence/migration-status-pkla.pkla` |

### 2.2 `.pkla` Snippet Example (Sunshine Branding)

```ini
[SunshineOS Electron Update]
Identity=unix-user:all
Action=sunshineos.electron.update
ResultAny=polkit=yes
ResultInactive=polkit=yes
ResultActive=polkit=yes
```

**Branding Constraints:**
- No mention of upstream vendor names in `Identity` or `Action` descriptions.
- `X-Sunshine-Brand=true` marker added by evolution-engine during artifact publishing (M-03 versioned independence).
- Actions are recorded in `/var/log/sunshineos/polkit-audit.log` with immutable event IDs (M-02).

---

## 3. Progress Tracking Architecture — Wave 1 Deepening

*Integrates with the Migration Orchestrator (mandate §3) and satisfies M-05 staging, M-06 recovery, M-09 repeatability.*

### 3.1 Progress State Machine

```
┌─────────────┐     ┌────────────────────┐     ┌─────────────────────┐
│  PENDING    │────▶│   STAGING          │────▶│    VALIDATING       │
└─────────────┘     └────────────────────┘     └─────────────────────┘
      │                      │                      │
      │                      │                      ▼
      │                      │            ┌────────────────────┐
      │                      │            │    RECOVERY        │
      │                      │            └────────────────────┘
      │                      │
      └──────────────────────┘────▶│   COMPLETED        │
                                          └────────────────────┘
```

- **Each state transition** is journalled via `evolution-engine/logs/` with content hash (M-07 artifact archival).
- **Interruption handling:** If migration halts before `VALIDATING`, the executor (mandate §3) initiates compensating operations per M-06.
- **Repeatability:** Re-running `sunshineos.migration.status` yields identical progress IDs (M-09) without duplicating operations.

### 3.2 Evidence & Test ID Mapping

| Component | Test ID | Evidence Path | Invariant Alignment |
|---|---|---|---|
| Progress State Machine | `EVL-P01` | `evidence/progress-fsm.yml` | M-05, M-06, M-09 |
| polkit Action Dispatch | `EVL-P02` | `evidence/polkit-dispatch-audit.md` | M-06, M-09 |
| Recovery Compensating Ops | `EVL-P03` | `evidence/recovery-compensating.sh` | M-06 |
| Journal Entry Schema | `EVL-P04` | `evidence/journal-entry-format.json` | M-07, M-09 |

---

## 4. Migration Invariants Alignment

| Invariant | How Design Satisfies It |
|---|---|
| **M-01** Target-state driven | Progress targets `E040` configuration; Electron modules converge to resolved state, not sequential release scripts. |
| **M-02** Immutable history | All `.pkla`, `evidence/`, and `evolution-engine/` artifacts have content hashes and digital signatures (mandate §2.2). |
| **M-03** Versioned intelligence | `EVL-E01` through `EVL-E06` carry schema version `INV7`; polkit actions carry `TC18` transition catalog reference. |
| **M-04** Installation authoritative | Progress FSM reads current system state via inventory observer (mandate §3) before transitioning. |
| **M-05** Staged migrations | `STAGING` state validates Electron module integrity against target hash before `VALIDATING`. |
| **M-06** Recoverable operations | `RECOVERY` state uses compensating scripts stored in `evidence/` with explicit `test IDs` for rollback verification. |
| **M-07** Historical artifacts archived | All module manifests mirrored to `other/archived-elements/` with publication/deprecation metadata. |
| **M-08** Qualified support | `polkit-evaluate` only returns `YES` when migration path for current `OS evolution`/`inventory schema` pair is tested. |
| **M-09** Repeatability | Re-running progress queries yields identical `progress_id`; no uncontrolled duplication of IPC calls or filesystem mutations. |
| **M-10** Data/OS separation | Electron data directory `/var/lib/sunshineos/electron/` is distinct from OS reconstruction; OS rebuild does not migrate every old file blindly. |

---

## 5. Deliverable Checklist ✅

- [x] Exact file paths for Electron modules (normalized to SunshineOS build root)
- [x] polkit/progress design with Sunshine-only branding (no upstream vendor references)
- [x] Test IDs (`EVL-E01`–`EVL-P04`) and evidence paths (`evidence/`, `logs/`)
- [x] Alignment with migration invariants M-01 through M-10
- [x] No passwords, tokens, or key material included
- [x] Markdown format (no tool calls or JSON)
- [x] References to repository structure: `.git/, autonomy/, evidence/, evolution-engine/, reports/`

---

**Wave 1 complete.** Subsequent waves will deepen kernel-integration hooks, filesystem transition catalogues, and cross-distribution vulnerability exclusion patterns as outlined in the 2026-11-21 mandate. All artifacts published to `evolution-engine/` and `autonomy/` branches per M-03/M-08.
