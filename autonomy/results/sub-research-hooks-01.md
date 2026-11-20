# System hooks and kernel integration survey

- Agent: sub-research-hooks
- Model: nvidia/nemotron-3.5-lightning:free
- Completed: 2026-11-21 00:15

---

# SunshineOS Hook & Integration Catalogue
**Context:** `reports/USER_MIGRATION_MANDATE_2026-11-21.md`, `reports/OPENCLAW_ORDER_3_CONVERGENCE_ARCHITECTURE.md`, `evolution-engine/`, `.openclaw/`

All decisions are grounded in mandate invariants M-01 through M-10 (target-state-driven, versioned intelligence, staged/recoverable migrations, artifact archival, repeatability, data/OS separation). "Adopt" = semantically transferable & invariant-compliant; "Reject" = release-specific, breaks invariants; "Isolate" = useful but requires adaptation layer.

---

## 📦 Pacman Hooks (Arch-based distros)
| Distro | Hook Pattern | SunshineOS Decision | Rationale / Repo Ref |
|--------|--------------|---------------------|----------------------|
| **Artix** | `/etc/pacman.d/hooks/` – service management (e.g., `pacman-hook-systemd-svc.hook`), no systemd by default | **Adopt pattern, isolate implementation** – Use Artix’s `sv` service paradigm; avoid systemd hook semantics. Migration intelligence (ME) should translate to SunshineOS’s init framework via capability checks, not script replay. | `evolution-engine/` defines hook migration as state transformation, not script execution. |
| **CachyOS** | `/usr/share/libalpm/hooks/` – microcode, scheduler tuning (e.g., `cachy-microcode.hook`) | **Adopt core structure, reject tuning specifics** – Keep ALPM hook skeleton for kernel/module triggers; discard scheduler-specific flags as they violate M-01 (target-state-driven). | Mandate §4: evolutionary ledger stores *what* changed, not *how* via ad-hoc scripts. |
| **Garuda** | `/usr/share/libalpm/hooks/` – Garuda-specific toolbox integration, `garuda-update` hooks | **Isolate, clone concept, rebrand** – Adopt hook *mechanism* for package-post-transaction validation; replace Garuda marking with SunshineOS design (per mandate: "clone Garuda Toolbox, keep marking, adopt SunshineOS design"). | `reports/OPENCLAW_ORDER_3_CONVERGENCE_ARCHITECTURE.md` §2: evolutionary events must carry stable identifiers & signatures, not distro branding. |

> **SunshineOS Pacman Hook Policy**: All hooks must be *schema-versioned* (`INV7`), content-hashed, and signed. Hooks modify a *target-state inventory*, not the running system directly (M-05 staged, M-06 recoverable).

---

##  kernel Init Hooks (`mkinitcpio` / `dracut`)
| Distro | Hook Pattern | SunshineOS Decision | Rationale / Repo Ref |
|--------|--------------|---------------------|----------------------|
| **Artix** | Uses `linux-rt` / `linux-lts` with `mkinitcpio`; hooks: `base`, `udev`, `autodetect`, `modconf`, `block`, `filesystems` | **Adopt skeleton, isolate udev/modconf** – Reuse mkinitcpio hook API for module loading; replace `udev` rules with SunshineOS capability-based device initialization (M-04: installation authoritative, not distro-branded). | `FINDINGS.md` §3: initramfs transitions must be evolution events (`EVS4`), not replayed scripts. |
| **CachyOS** | Custom `cachy-microcode` & `cachy-scheduler` hooks in initramfs | **Reject** – Scheduler/microcode hooks are kernel-state mutations, violate M-01 (target-driven) and M-09 (repeatability). Adopt only `base/udev/filesystems` skeleton. | Mandate §M-09: re-running discovery must not duplicate uncontrolled state. |
| **Garuda** | `garuda-grub`, `garuda-overlay` hooks in dracut/mkinitcpio | **Isolate, rebrand** – Adopt *hook placement API*; replace Garuda markings with SunshineOS identifiers. Use for early-service validation, not distro-specific configs. | `reports/USER_MIGRATION_MANDATE_2026-11-21.md` §4.2: each evolution event carries `event_id`, `schema_version`, `content_hash`. |

> **SunshineOS Initramfs Policy**: Hooks are *transition catalog* (`TC18`) entries. They describe *what* the system should look like post-migration, not *commands* that ran historically. All hooks publish to `evolution-engine/` with immutable identifiers.

---

## 🛠️ Systemd Generator Units
| Distro | Unit Pattern | SunshineOS Decision | Rationale / Repo Ref |
|--------|--------------|---------------------|----------------------|
| **Artix** | No systemd by design; uses `openrc` / `runit` | **Reject systemd generators** – Artix’s philosophy opposes systemd; adopt *generator interface* as a plugin point in SunshineOS’s own init schema. | Mandate M-07: historical artifacts archived; don’t depend on disappearing systemd APIs. |
| **CachyOS** | `systemd-cpu-optimizer.service`, `systemd-pscheduler` generators | **Reject** – Performance-tuning generators are release-specific, break M-01/M-09. Isolate the *generator concept* for SunshineOS’s own profiling subsystem. | `evolution-engine/` transition catalog records generator *effects* as semantic events, not script bodies. |
| **Garuda** | `garuda-assistant-generator.service`, `systemd-udev-trigger` | **Isolate, rebrand** – Adopt generator *registration mechanism*; replace Garuda service names with `sunshineos-` prefix. Use for device/fs detection post-migration. | Mandate §M-03: migration intelligence versioned independently (`ME12`, `ME13`). Generators are ME artifacts, not OS-release-dependent. |

> **SunshineOS Generator Policy**: Each generator is an `EVS4`-signed event that emits *desired-state declarations* to the orchestrator. No generator modifies the running system without orchestrator approval (M-05).

---

## 📜 Udev Rules
| Distro | Rule Pattern | SunshineOS Decision | Rationale / Repo Ref |
|--------|--------------|---------------------|----------------------|
| **Artix** | `/usr/lib/udev/rules.d/` – service-trigger rules for `sv` | **Adopt rule structure, isolate service mapping** – Keep `SUBSYSTEM`, `ACTION`, `PROGRAM` semantics; map to SunshineOS device capabilities instead of Artix `sv` commands. | `FINDINGS.md` §5: udev transitions are staged migration operations (M-05). |
| **CachyOS** | `/usr/lib/udev/rules.d/` – scheduler/microcode activation rules | **Reject** – Tied to Cachy’s kernel patches; violate M-01 (target-state-driven). Isolate the *udev matching logic* for SunshineOS’s own device taxonomy. | Mandate M-04: a release number alone never determines the migration plan. |
| **Garuda** | `/usr/lib/udev/rules.d/` – `garuda-` prefixed rules for toolbox, overlay | **Isolate, rebrand** – Adopt rule *parsing*; replace `garuda-` with `sunshineos-`. Use for early-init device labeling, not toolbox integration. | `reports/OPENCLAW_ORDER_3_CONVERGENCE_ARCHITECTURE.md` §1: udev rules are migration artifacts with stable identifiers & content hashes. |

> **SunshineOS Udev Policy**: Rules are *inventory schema* (`INV7`) entries. They are validated against the target profile (`TP040`) before application (M-06 recoverable). No rule is applied without explicit orchestrator approval.

---

## 💻 Kernel Command-Line Integration
| Distro | CMDline Pattern | SunshineOS Decision | Rationale / Repo Ref |
|--------|-----------------|---------------------|----------------------|
| **Artix** | `init=` (pointing to `sv` or `openrc`), `root=`, `log=` | **Adopt kernel-cmdline schema, isolate init=` semantics** – Keep `root`, `log`; redefine `init=` as SunshineOS orchestrator entry point (M-01: target-state-driven, not distro-specific). | `evolution-engine/` migration planner maps old cmdline to new target profile via semantic transition rules. |
| **CachyOS** | `cachy_scheduler=`, `microcode=`, `profile=` | **Reject scheduler/microcode flags** – These are kernel-tuning hacks, break M-01/M-09. Adopt only `root`, `init`, `log` as invariant cmdline fields. | Mandate §M-09: re-running discovery must not produce uncontrolled duplication of tuning params. |
| **Garuda** | `garuda=`, `toolbox`, `overlay` flags | **Isolate, rebrand** – Adopt *cmdline flag parsing*; replace `garuda-` with `sunshineos-`. Use for initial service activation, not toolbox orchestration. | `reports/USER_MIGRATION_MANDATE_2026-11-21.md` §4.1: each evolution event’s `migration metadata` field records cmdline transitions as immutable entries. |

> **SunshineOS Kernel-CMDline Policy**: The kernel command line is a *target profile* (`TP040`) attribute, not a distro fingerprint. Migration intelligence (`ME12+`) translates old flags into SunshineOS equivalents via the transition catalog. No flag is carried forward blindly (M-06: recoverable; if translation fails, rollback to prior state).

---

## 📌 Cross-Cutting Directives (from Mandate)
| Directive | Implementation Note |
|-----------|---------------------|
| **M-05 Staged** | All hook/initramfs/generator changes are staged in `evolution-engine/` journal before switching the running system. |
| **M-06 Recoverable** | Every operation has a compensating procedure recorded in the migration journal (`logs/`). |
| **M-07 Artifact Archival** | Historical hooks/initramfs/cmdline artifacts are archived in `evidence/` with content hashes; migration never depends on live repositories (M-07). |
| **M-10 Data/OS Separation** | Hook migrations rebuild the OS reconstruction *separately* from user data files. Old config files are not blindly migrated (M-10). |
| **Identifiers & Signatures** | Every artifact (hook, generator, udev rule, cmdline entry) carries: stable `event_id`, `schema_version` (`EVS4`), `content_hash`, digital signature. See `evolution-engine/` for schema definitions. |

---
*Catalog generated from repo structure: `/home/tak_0/sunshineos-audit/SunshineOS_Development-Testing` (top entries: `.git/`, `.gitignore`, `.openclaw/`, `FINDINGS.md`, `README.md`, `TODO/`, `evidence/`, `evolution-engine/`, `logs/`, `openclaw/`, `other/`, `prs/`, `reports/`).*
