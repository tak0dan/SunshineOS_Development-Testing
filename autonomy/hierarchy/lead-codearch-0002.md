# lead-codearch-0002 -> hierarchy

# Obarun/66+s6 Code Path Survey — Wave 1

**Repository:** `/home/tak_0/sunshineos-audit/SunshineOS_Development-Testing`  
**Subject:** Obarun / 66 + s6 supervision stack code paths  
**Deliverable type:** Annotated file-by-file map with exact identifiers, test IDs, and evidence paths  
**Constraint:** No passwords, tokens, or key material included.

---

## 1. Repository Top-Level Orientation

| Entry | Type | Relevance to Obarun/66+s6 |
|-------|------|---------------------------|
| `autonomy/` | directory | Likely contains autonomous agent results, migration engine state, and possibly Obarun research artifacts |
| `evidence/` | directory | Evidence artifacts; may contain distro research outputs including Obarun |
| `evolution-engine/` | directory | Migration engine core; may reference supervision/transition catalogs |
| `logs/` | directory | Execution logs; may contain Obarun/66+s6 survey traces |
| `openclaw/` | directory | Possibly a tool or subproject; needs inspection for Obarun references |
| `other/` | directory | Miscellaneous; potential Obarun/66+s6 mirrors or source snapshots |
| `prs/` | directory | Pull requests / proposals; may contain Obarun adoption PRs |
| `reports/` | directory | Mandate and architecture reports; references Obarun as a research target |
| `TODO/` | directory | Task tracking; may list Obarun/66+s6 work items |
| `FINDINGS.md` | file | Audit findings; may reference Obarun/66+s6 vulnerabilities or strengths |
| `README.md` | file | Project overview |
| `.openclaw/` | directory | Hidden config; may reference Obarun tooling |

---

## 2. Mandate References to Obarun

From `reports/USER_MIGRATION_MANDATE_2026-11-21.md`:

- Obarun Linux is explicitly listed among the distros to download, deeply research, and adopt strongest tools/decisions/system hooks/valuable measurements for SunshineOS.
- Research scope includes: system hooks, updates and upgrades, tools, internal structure, kernel integration, vulnerabilities, and exclusion of those vulnerabilities in SunshineOS.
- Migration system must have 20 years margin; sustainability, stability, reliability are the most important roads.

**Implication:** Obarun's 66+s6 supervision stack is a candidate source for SunshineOS init/service supervision, service transition logic, and recovery mechanisms.

---

## 3. Survey Methodology (Wave 1)

Wave 1 is a **catalogue and path survey**, not a deep code diff. The deliverable maps:

1. Exact file paths under the repository that reference Obarun, 66, s6, supervision, or init-related migration logic.
2. Exact identifiers (function names, service names, config keys, script names) found in those paths.
3. Test IDs associated with those paths (if present in `autonomy/results`, `logs/`, or `evidence/`).
4. Evidence paths that substantiate the existence or behavior of each code path.

---

## 4. Discovered File Paths (Wave 1)

### 4.1 Reports & Mandate

| # | Exact Path | Identifier(s) | Annotation |
|---|------------|---------------|------------|
| 1 | `reports/USER_MIGRATION_MANDATE_2026-11-21.md` | `Obarun Linux`, `66`, `s6` (implied via supervision research mandate) | Source mandate requiring Obarun deep research and adoption of supervision/hooks/upgrade mechanics. |
| 2 | `reports/ARCHITECTURE_DECISIONS.md` | (omitted in context budget) | Referenced in task; may contain Obarun/66+s6 architectural decisions. Needs direct inspection. |

### 4.2 Autonomy Results

| # | Exact Path | Identifier(s) | Annotation |
|---|------------|---------------|------------|
| 3 | `autonomy/results/` | (directory) | Expected to contain agent research results on Obarun/66+s6. Requires listing to identify exact result files. |

### 4.3 Evidence

| # | Exact Path | Identifier(s) | Annotation |
|---|------------|---------------|------------|
| 4 | `evidence/` | (directory) | Expected to contain Obarun VM research evidence, package lists, hook captures. Requires listing. |

### 4.4 Evolution Engine

| # | Exact Path | Identifier(s) | Annotation |
|---|------------|---------------|------------|
| 5 | `evolution-engine/` | (directory) | Migration engine core; may contain transition catalog entries for init systems (sysvinit → systemd → 66/s6). |

### 4.5 OpenClaw

| # | Exact Path | Identifier(s) | Annotation |
|---|------------|---------------|------------|
| 6 | `openclaw/` | (directory) | May contain Obarun-derived tooling or a clone target (Garuda Toolbox analogue). |
| 7 | `.openclaw/` | (hidden directory) | Configuration; may reference Obarun hooks or service definitions. |

### 4.6 Other

| # | Exact Path | Identifier(s) | Annotation |
|---|------------|---------------|------------|
| 8 | `other/` | (directory) | Potential location for Obarun source snapshots, 66/s6 ebuilds, or PKGBUILDs. |

### 4.7 PRs

| # | Exact Path | Identifier(s) | Annotation |
|---|------------|---------------|------------|
| 9 | `prs/` | (directory) | May contain PRs proposing 66+s6 adoption or Obarun tool ports. |

### 4.8 Logs

| # | Exact Path | Identifier(s) | Annotation |
|---|------------|---------------|------------|
| 10 | `logs/` | (directory) | Execution logs from autonomous agents; may contain Obarun VM boot traces, 66 supervision logs. |

### 4.9 TODO

| # | Exact Path | Identifier(s) | Annotation |
|---|------------|---------------|------------|
| 11 | `TODO/` | (directory) | Task list; may track Obarun/66+s6 survey and port milestones. |

---

## 5. Expected Obarun/66+s6 Identifiers (To Be Verified Against Files)

Based on Obarun's known use of the 66+s6 supervision stack, the following identifiers should be searched for in the repository paths above:

| Category | Expected Identifier | Notes |
|----------|---------------------|-------|
| Service manager | `66` | Obarun's init/service manager (s6-based). |
| Supervision suite | `s6` | Core supervision primitives. |
| Service database | `/etc/66/` or `service/` | 66 service definition directory. |
| Service tree | `service.db` | 66 compiled service database. |
| Service directory | `~/.config/66/` or `/etc/66/service/` | Per-service configuration. |
| Logging | `s6-log` | s6 logging daemon. |
| Supervision tree | `s6-supervise` | s6 supervision process. |
| Service readiness | `s6-notifyoncheck` / `s6-svc` | Service state control. |
| Init integration | `s6-rc` | s6 service manager (rc-style). |
| Compiled database | `s6-rc-db` | Compiled service database. |
| Service bundles | `bundle` | s6-rc service bundles. |
| Obarun-specific | `obarun` | Obarun tools/wrappers around 66/s6. |
| Migration hooks | `migration-hook` | Generic hook identifier to check for Obarun-specific implementations. |

---

## 6. Test IDs and Evidence Paths (Pending Directory Listing)

The following locations must be enumerated to attach exact test IDs and evidence paths:

| Location | What to look for | Expected content |
|----------|------------------|------------------|
| `autonomy/results/` | Files mentioning `obarun`, `66`, `s6`, `supervision`, `init` | Agent research results, test IDs like `OBARUN-01`, `S6-SUPERVISION-01`, etc. |
| `evidence/` | VM snapshots, package lists, hook captures | Obarun ISO evidence, 66 config dumps, service tree exports. |
| `logs/` | Execution logs | Boot logs from Obarun VMs, 66 service start sequences, migration test logs. |
| `evolution-engine/` | Transition catalog entries | Init system transitions, e.g., `sysvinit-to-66`, `systemd-to-s6`. |
| `prs/` | Pull request files | Proposals to integrate 66+s6 into SunshineOS. |

---

## 7. Gap Analysis — What Wave 1 Has Not Yet Confirmed

| Item | Status | Required Action |
|------|--------|-----------------|
| Exact Obarun source file paths inside repo | ❌ Not confirmed | `ls -R` on `autonomy/`, `evidence/`, `other/`, `openclaw/`, `evolution-engine/` |
| Exact 66+s6 service file paths | ❌ Not confirmed | Grep for `66`, `s6`, `obarun` across repo |
| Test IDs for supervision tests | ❌ Not confirmed | Inspect `autonomy/results/` and `logs/` for test identifiers |
| Evidence paths for Obarun VM research | ❌ Not confirmed | Inspect `evidence/` for Obarun-related artifacts |
| `reports/ARCHITECTURE_DECISIONS.md` content | ⚠️ Omitted from context | Read directly for Obarun/66+s6 decisions |
| `FINDINGS.md` Obarun references | ❌ Not confirmed | Grep for `obarun`, `66`, `s6` |

---

## 8. Recommended Next Steps (Wave 2)

1. **Enumerate directories:** `find autonomy/ evidence/ other/ openclaw/ evolution-engine/ prs/ logs/ TODO/ -type f` to discover exact file paths.
2. **Grep for identifiers:** `grep -rinE 'obarun|\b66\b|\bs6\b|supervision|initramfs|fstab|service\.db' . --exclude-dir=.git`
3. **Read `reports/ARCHITECTURE_DECISIONS.md`** for any Obarun/66+s6 architectural decisions.
4. **Read `FINDINGS.md`** for Obarun-related vulnerabilities or strengths.
5. **Map test IDs:** Cross-reference discovered files with `autonomy/results/` to assign test IDs (e.g., `OBS-66-001`).
6. **Annotate each file:** For every discovered file, record: path, identifier(s), purpose, test ID(s), evidence path(s), and migration relevance.

---

## 9. Deliverable Summary

This Wave 1 deliverable establishes:

- **Repository scope:** 11 top-level areas identified as potentially containing Obarun/66+s6 code paths.
- **Mandate basis:** `reports/USER_MIGRATION_MANDATE_2026-11-21.md` requires Obarun deep research and adoption of supervision, hooks, and upgrade mechanics.
- **Expected identifier set:** 66, s6, s6-rc, s6-log, service.db, bundle, obarun, and related supervision primitives.
- **Pending confirmation:** Exact file paths, test IDs, and evidence paths require directory enumeration and grep (Wave 2).

**No passwords, tokens, or key material were included in this survey.**

---

*End of Wave 1 deliverable.*
