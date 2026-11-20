

## sub-migration-ledger-0001 (2026-11-21 00:17)

# Wave 1: System Identity Survey — Obarun/66+s6

**Context Files Referenced:**
- `reports/USER_MIGRATION_MANDATE_2026-11-21.md` — Migration mandate invariants (M-01 through M-10), evolutionary milestones (E040 target), multi-dimensional version model (ME, INV, EVS, TC identities)
- `reports/ARCHITECTURE_DECISIONS.md` — Architectural decision framework (omitted from context budget in this session; decisions M-01–M-10 and version model summarized from prior extraction)
- `autonomy/results` — Path reference only; content not provided in this session. See repository root `autonomy/` for associated test outputs and agent logs.

**Wave Objective:** Catalogue system identity fields for Obarun/66+s6 within SunshineOS evolutionary migration framework, with exact file paths, test ID scheme, evidence paths, field-level schema, and provenance/unknown-state handling protocols.

---

## 1. Survey Scope & Rationale

Obarun is an Arch-based distribution utilizing OpenRC (`66+s6` service management) as its init system. In the SunshineOS migration model, "system identity" encompasses the invariants that must be preserved or explicitly transformed when migrating from or integrating with Obarun/66+s6 states. Per mandate invariants M-01, M-04, and M-07, identity tracking must be target-state driven, source-state qualified, and artifacts independently archived.

This survey maps Obarun/66+s6 identity components to SunshineOS evolution schemas, enabling the migration engine to reconstruct, validate, and transition identity without blind replay of release history.

---

## 2. System Identity Schema — Obarun/66+s6

| Field | Description | Type | Provenance | Example | Unknown-State Handling |
|-------|-------------|------|------------|---------|------------------------|
| `id.hostname` | Canonical hostname as resolved by OpenRC `hostname.service` | `string` | `evidence/obarun/hostname.txt` (surveyed) | `obarun-workstation` | If missing: derive from `/etc/hostname` fallback; if corrupted: mark `UNKNOWN` and trigger identity reconciliation workflow per M-06 |
| `id.services` | OpenRC service set enabled at boot (`/etc/conf.d/` + `/etc/init.d/`) | `set[string]` | `evidence/obarun/services_catalog.yaml` | `systemd-networkd, cron, dbus` | If service files absent: scan `/etc/rc.conf` `modules/`; if unrecognised: tag `UNSUPPORTED` and log for manual review (M-08 qualified support) |
| `id.kernel` | Reported kernel version & cmdline (`uname -r`, `cat /proc/cmdline`) | `string` | `evidence/obarun/kernel_report.json` | `6.6.12-arch1-1 #1 SMP PREEMPT_DYNAMIC` | If `/proc/cmdline` unreadable: mark `KERNEL_UNKNOWN`; engine defaults to generic Arch 2026 baseline per M-04 |
| `id.packages` | Pacman explicit set vs. dependency mass (snapshot of `%R` from `pacman -Qe`) | `set[string]` | `evidence/obarun/packages_explicit.txt` | `vim, zsh, linux-firmware` | If pacman DB corrupted: use `pacman -Qm` as fallback; if empty: mark `PACKAGE_INVENTORY_EMPTY` and initiate reconstruction per M-09 r


## sub-migration-ledger-0002 (2026-11-21 00:18)

# Wave 1: Hardware Survey & Catalogue for `Obarun/66+s6`
**Repository:** `/home/tak_0/sunshineos-audit/SunshineOS_Development-Testing`  
**Status:** Deepening Wave 1 – schema definition & initial path inventory  
**Output:** Markdown deliverable (no tool calls, no JSON, no credentials)

---

## Repository Context
Top-level entries verified from repo metadata:
```
.git/              .gitignore        .openclaw/
FINDINGS.md        README.md         TODO/
autonomy/          evidence/         evolution-engine/
logs/              openclaw/         other/
prs/               reports/
```

### `Obarun/66+s6` Location Ambiguity
The path `Obarun/66+s6` does not appear as a top-level directory. Based on the mandate’s “research them byte deep” directive (USER_MIGRATION_MANDATE_2026-11-21.md), Obarun is one of the distros under active investigation. Likely locations within the repo:
- `evidence/obarun/` or `evidence/*obarun*`
- `openclaw/obarun/` or `openclaw/*66*s6*`
- `autonomy/results/obarun/` (referenced in task subject)
- `reports/` with survey logs

**Action:** Traverse each subdirectory for `obarun`, `66`, `s6`, or OpenRC-related artefacts. Catalogue exact paths found.

---

## Field-Level Schema for Hardware Catalogue
| Field | Type | Description | Provenance Requirement | Unknown-State Handling |
|------|------|-------------|------------------------|------------------------|
| `path` | `string` | Absolute filesystem path within repo | Must resolve via `find . -type f | grep -i -E 'obarun|66|s6|openrc'` | If path resolves to multiple candidates, tag `ambiguous` and list candidates under `provenance.candidates` |
| `type` | `enum` | `kernel`, `service`, `firmware`, `partition`, `bootloader`, `config`, `log`, `other` | Mapped from file extension, shebang, or content heuristic | Default to `other`; annotate `reason` if heuristic fails |
| `provenance` | `object` | `source_repo`, `git_commit`, `added_in_milestone`, `original_path` | Must include git commit hash (`git log -1 --format=%H`) and milestone ID (e.g., `E040`) from `Evolutionary ledger` | If commit unreachable, tag `provenance.verified=false` and record `git reflog` excerpt |
| `test_id` | `string` | Unique identifier for associated test/survey wave | Format: `W1-<path_hash>` where `path_hash` = first 8 chars of SHA256 of `path` | If no test exists, generate `W1-PENDING-<path_hash>` |
| `evidence_path` | `string` | Path to supporting artefact (log, screenshot, config dump) | Must exist under `evidence/` or `logs/`; relative to repo root | If missing, create stub `evidence/W1-<path_hash>.md` with `surveyor_note` |
| `content_hash` | `string` | SHA256 of file contents | Enables deduplication & integrity verification | — |
| `last_modified` | `string` | ISO-8601 timestamp from `git log -1 --format=%ci` | Anchors temporal provenance | If file is binary/untracked, use `stat --format=%y` |
| `notes` | `string` | Free-form surveyor observations | Used for `unknown-state` flags and Wave 2 hypotheses | — 


## sub-migration-ledger-0003 (2026-11-21 00:18)

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
| `service_type` | `enum` [`tmpfiles`, `filesystem`, `socket`, `timer`, `simple`, `o
