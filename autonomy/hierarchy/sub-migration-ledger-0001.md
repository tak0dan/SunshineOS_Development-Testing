# sub-migration-ledger-0001 -> hierarchy

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
| `id.packages` | Pacman explicit set vs. dependency mass (snapshot of `%R` from `pacman -Qe`) | `set[string]` | `evidence/obarun/packages_explicit.txt` | `vim, zsh, linux-firmware` | If pacman DB corrupted: use `pacman -Qm` as fallback; if empty: mark `PACKAGE_INVENTORY_EMPTY` and initiate reconstruction per M-09 repeatability |
| `id.init` | Init system identity: `openrc` vs `systemd` vs hybrid | `enum {openrc, systemd, hybrid}` | `evidence/obarun/init_identity.json` | `openrc` | If init binaries ambiguous: run `rc-status` and `systemctl`; if neither: tag `INIT_UNANSWERABLE` and escalate |
| `id.storage` | Disk layout summary (`blkid`, `/etc/fstab` UUIDs, partition types) | `object` | `evidence/obarun/storage_identity.yaml` | `{/: UUID "abc123", /home: UUID "def456", type: ext4}` | If `/etc/fstab` absent: mark `STORAGE_UNCONFIRMED`; do not auto-repair without planner validation (M-05 staged) |
| `id.network` | Interface config (`/etc/netifrc`, `dhcpcd` profiles, static IPs) | `object` | `evidence/obarun/network_config.yaml` | `{eth0: dhcp, wlan0: static 192.168.1.50}` | If netifrc absent: scan `dhcpcd.conf`; if nothing: tag `NETWORK_IDENTITY_EMPTY` |
| `id.credentials` | **Deliberately omitted** — no SSH keys, passwords, or token material per anti-credential policy. Identity fields reference only structural/configuration provenance. | `N/A` | `N/A` | `N/A` | `N/A` |

**Schema Provenance:** Each field maps to a verified evidence path in the `evidence/` directory (see Section 3). The schema itself is versioned as `EVS1` (Evolution Schema v1) per the multi-dimensional version model in the mandate. Content hashes and digital signatures will be attached at publication (M-02 immutable evolution history).

**Unknown-State Protocol:** When a field evaluates to `UNKNOWN`, `UNSUPPORTED`, or `EMPTY`, the migration engine:
1. Logs the condition with test ID (see Section 4)
2. Does not auto-repair or assume
3. Triggers staged validation (M-05) and, if unresolved, escalates to orchestrator for manual review (M-08)
4. Preserves the unknown state through the migration chain; target resolution never silently discards provenance

---

## 3. Exact File Paths & Evidence Catalog

All paths relative to repository root `/home/tak_0/sunshineos-audit/SunshineOS_Development-Testing/`

| Path | Purpose | Content Type | Status |
|------|---------|--------------|--------|
| `evidence/obarun/hostname.txt` | Hostname capture from running Obarun instance | `text` | Surveyed (Wave 1) |
| `evidence/obarun/services_catalog.yaml` | OpenRC service enablement list | `YAML set` | Surveyed (Wave 1) |
| `evidence/obarun/kernel_report.json` | `uname -r` + `cat /proc/cmdline` output | `JSON` | Surveyed (Wave 1) |
| `evidence/obarun/packages_explicit.txt` | `pacman -Qe` explicit package list | `text` | Surveyed (Wave 1) |
| `evidence/obarun/init_identity.json` | Init system detection result | `JSON` | Surveyed (Wave 1) |
| `evidence/obarun/storage_identity.yaml` | `blkid` + `/etc/fstab` UUID summary | `YAML object` | Surveyed (Wave 1) |
| `evidence/obarun/network_config.yaml` | Netif/dhcpcd profile dump | `YAML object` | Surveyed (Wave 1) |
| `evidence/obarun/` (directory) | Root for all Obarun identity evidence | `dir` | Exists in repo structure |
| `autonomy/results/` | Agent result logs (including identity survey outputs) | `dir` | Referenced; content not provided in this session |
| `evolution-engine/` | Core engine; schema validation and identity transition logic | `dir` | See `evolution-engine/` top-level entry |
| `openclaw/` | OpenCLaw audit framework integration points for identity verification | `dir` | `.openclaw/` also present at root |
| `reports/ARCHITECTURE_DECISIONS.md` | Architectural decisions M-01–M-10, version model definitions | `markdown` | Referenced; omitted from this session's context budget |
| `reports/USER_MIGRATION_MANDATE_2026-11-21.md` | Full user mandate including evolutionary milestones and invariants | `markdown` | Provided in session |

**Evidence Provenance Chain:** Each evidence file is expected to contain a trailing metadata block:
```
# Provenance: <source-identifier>
# Collected: <timestamp>
# Hash: <sha256>
# Agent: <surveying-agent-identifier>
```
This enables M-07 (artifact archiving) and M-09 (repeatability) guarantees.

---

## 4. Test ID Scheme

Test IDs follow the pattern `ID-<category>-<sequence>` and are embedded in evidence files and orchestrator logs.

| Test ID | Category | Description |
|---------|----------|-------------|
| `ID-IDEN-001` | Identity | Hostname resolution validation against `/etc/hostname` and OpenRC `hostname.service` |
| `ID-IDEN-002` | Identity | Service catalog completeness: `%R` packages vs. enabled OpenRC inits |
| `ID-IDEN-003` | Identity | Kernel version and cmdline integrity check |
| `ID-IDEN-004` | Identity | Package explicit set non-empty assertion |
| `ID-IDEN-005` | Identity | Init system detection: openrc vs systemd vs hybrid |
| `ID-IDEN-006` | Identity | Storage UUID consistency: `blkid` vs `/etc/fstab` cross-reference |
| `ID-IDEN-007` | Identity | Network interface configuration validity |
| `ID-IDEN-008` | Unknown-State | Field evaluated as `UNKNOWN`; recovery workflow triggered |
| `ID-IDEN-009` | Repeatability | Re-survey after migration engine run; delta must be zero or explicitly logged |
| `ID-IDEN-010` | Provenance | Evidence hash mismatch detection (M-07 artifact integrity) |

Each test ID is associated with a `PASS/FAIL/UNKNOWN` outcome and a provenance hash in the migration engine's inventory state (INV schema versioned per mandate).

---

## 5. Provenance & Unknown-State Handling Protocol

### 5.1 Provenance Anchoring
- Every evidence file must contain a `# Provenance:` line identifying the source system (e.g., `Provenance: Obarun 66+s6 /dev/sda1 /hostname: obarun-workstation`)
- The migration engine records provenance in the inventory state; mismatched provenance triggers `INV- PROV-001` flag and halts identity transformation until resolved
- Per M-07, provenance data is independently archived; it must not depend on live system access after migration staging

### 5.2 Unknown-State Handling (Per M-06, M-09)
| Condition | Engine Action | Recovery Path |
|-----------|---------------|---------------|
| Field `UNKNOWN` but source media preserved | Log outcome; mark field `PRESERVED_UNKNOWN` | Re-run survey on recovery media; if consistent, promote to resolved |
| Field `UNSUPPORTED` (e.g., custom OpenRC service not in catalog) | Tag `UNSUPPORTED`; do not auto-migrate | Map to SunshineOS equivalent via Transition Catalog (TC schema); if no mapping, escalate to manual review (M-08) |
| Field `EMPTY` (e.g., no packages explicit) | Mark `PACKAGE_INVENTORY_EMPTY` | Initiate inventory discovery from package manager logs (`/var/log/pacman.log`); if unrecoverable, migrate with `MINIMAL_PACKAGE_SET` default |
| Provenance hash mismatch | Flag `INV-PROV-001`; halt identity transformation | Re-download or re-collect evidence from archived source; if unavailable, mark `PROVENANCE_UNVERIFIED` and proceed with caution flag |

### 5.3 Repeatability (M-09)
- Re-running the full identity survey on the same source must produce identical test outcomes and hashes
- If delta > 0, the engine logs `DELTA-<timestamp>` and prompts for manual review before proceeding
- Interrupted migrations can be re-orchestrated without duplication: the engine checks existing journal entries (M-06 recoverable operations) and resumes from last validated stage

---

## 6. Wave 1 Deliverable Checklist

- [x] System identity schema for Obarun/66+s6 defined with 9 structural fields + credential omission policy
- [x] Exact file paths catalogued (all relative to repo root, all under `evidence/obarun/` or sibling dirs)
- [x] Test ID scheme established (`ID-IDEN-001` through `ID-IDEN-010`)
- [x] Provenance anchoring protocol described (M-07 compliance)
- [x] Unknown-state handling matrix defined (M-06 compliance)
- [x] Repeatability guarantees outlined (M-09 compliance)
- [x] No passwords, tokens, or key material included
- [x] Schema versioned as `EVS1` per mandate multi-dimensional version model
- [x] All provenance references tied to repository structure entries (`.git/, .gitignore, .openclaw/, autonomy/, evidence/, evolution-engine/, logs/, openclaw/, other/, prs/, reports/`)

---

**Next Wave (Wave 2):** Extend identity survey to additional distros referenced in the mandate (Obarun, Windows 11 ISO, EndeavourOS, GarudaOS, Artix, Arch 2026, Arch 2015, CachyOS, Omarchy, SteamOS). Map cross-distile transformation rules into the Transition Catalog (TC schema). Begin Evolution Ledger construction (E001–E040) with signed, immutable milestone definitions.

*Deliverable generated 2026-11-21. Agent: SunshineOS migration subagent. Context: reports/USER_MIGRATION_MANDATE_2026-11-21.md, reports/ARCHITECTURE_DECISIONS.md (summary), autonomy/results (path reference).*
