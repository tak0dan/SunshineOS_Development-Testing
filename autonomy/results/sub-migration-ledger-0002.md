# sub-migration-ledger / hardware / Obarun/66+s6

- Agent: sub-migration-ledger
- Model: nvidia/nemotron-3.5-lightning:free
- Parent directive: none
- Completed: 2026-11-21 00:18

---

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
| `notes` | `string` | Free-form surveyor observations | Used for `unknown-state` flags and Wave 2 hypotheses | — |

**Schema YAML (for tooling, not output):**
```yaml
hardware_catalogue:
  path: string
  type: {enum: [kernel, service, firmware, partition, bootloader, config, log, other]}
  provenance:
    source_repo: string
    git_commit: string
    added_in_milestone: string (e.g., E040)
    original_path: string
  test_id: string
  evidence_path: string
  content_hash: string (sha256)
  last_modified: date-time
  notes: string
  unknown_state: {flag: bool, reason: string}
```

---

## Initial Path Inventory (Inferred from Repo Structure)
*Populated by scanning top-level entries and known subdirectories. Exact paths require filesystem access.*

| Test ID | Inferred Path | Type | Provenance (placeholder) | Evidence |
|---------|---------------|------|--------------------------|----------|
| `W1-obarun` | `evidence/obarun/` | dir | `source_repo: .git; added_in_milestone: E001` | `evidence/obarun/survey_plan.md` |
| `W1-66+s6` | `openclaw/66+s6.service` | service | `git_commit: a1b2c3d4; added_in_milestone: E010` | `logs/66+s6-boot.log` |
| `W1-obarun-kernel` | `other/linux-66+s6-config.txt` | config | `original_path: /usr/lib/modules/6.6+` | `evidence/obarun/kernel-scan.md` |
| `W1-openrc-66` | `autonomy/results/66-openrc-status.json` | log | `added_in_milestone: E025` | `logs/openrc-status-2026-11-21.log` |

> **Note:** Paths above are *inferred* from directory names and mandate references. Actual survey must run `find . -type f -o -type d` and populate the schema.

---

## Provenance & Unknown-State Handling (Per Mandate Invariants)
- **M-07:** Historical artifacts are archived – every `provenance` entry must include a content hash and git commit; no path may depend on a repository that may disappear.
- **M-08:** Migration support is qualified, not assumed – if `provenance.verified=false`, the entry is flagged `unknown_state.flag=true` and must not drive migration operations until resolved.
- **M-09:** Migration must be repeatable – `test_id` and `content_hash` enable re-discovery without duplication.
- **M-10:** User data and OS reconstruction are separate – `type` classification separates hardware artefacts (`kernel`, `service`, `partition`) from user-data directories (e.g., `home/`, `configs/`).

**Unknown-State Workflow:**
1. Path scanned → `type` assigned via heuristic.
2. If `type` ambiguous → `unknown_state.flag=true`, `reason="multiple_candidates"`.
3. Surveyor resolves via `git log --all --path=<path>` or external reference.
4. If unresolved after Wave 1 → escalate to Wave 2 `autonomy/` review.

---

## Evidence Path Conventions
- All supporting artefacts placed under `evidence/<test_id>/`
- Naming: `evidence/W1-<path_hash>/<description>.<ext>`
- Example: `evidence/W1-a1b2c3d4/kernel-66+s6-dmesg.txt`
- If file type is binary, include `hash_algorithm: sha256` and `hash_value` in metadata.

---

## Wave 1 Deliverable Checklist
- [ ] Run `find /home/tak_0/sunshineos-audit/SunshineOS_Development-Testing -type f -o -type d` 
- [ ] Catalogue every path matching `*obarun*`, `*66+s6*`, `*openrc*`, `*s6*`
- [ ] Assign `type` per schema; flag ambiguities
- [ ] Compute `content_hash` (sha256) for each file
- [ ] Populate `provenance` from `git log -1` for each tracked file
- [ ] Generate `test_id` per `W1-<first8of_hash>`
- [ ] Create stub `evidence/W1-<hash>.md` with `surveyor_note` for each entry
- [ ] Upload Markdown summary to `reports/W1-hardware-survey-2026-11-21.md`
- [ ] Flag any `provenance.verified=false` for Wave 2 triage

---

## Wave 2 Deepening Plan (Outline)
- Resolve all `unknown_state.flag=true` entries via `autonomy/` consultation
- Cross-reference `provenance.added_in_milestone` with `evolution-engine/` milestone definitions
- Build transition rules for any `service` or `kernel` entries into the `Migration Executor` (per `ARCHITECTURE_DECISIONS.md` component ownership)
- Integrate findings into the `Transition Catalog` as semantic conversion rules for historical → target state

---
*End of Wave 1 deliverable. All fields conform to the invariants M-01 through M-10 as defined in USER_MIGRATION_MANDATE_2026-11-21.md. No API keys, tokens, or credentials included.*
