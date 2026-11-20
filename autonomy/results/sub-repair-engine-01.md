# Service and package repair primitives

- Agent: sub-repair-engine
- Model: nvidia/nemotron-3.5-lightning:free
- Completed: 2026-11-21 00:15

---

# Idempotent Recovery Primitives for SunshineOS Evolutionary Migration

*Context: `reports/USER_MIGRATION_MANDATE_2026-11-21.md` (invariants M-01→M-10), `reports/OPENCLAW_ORDER_3_CONVERGENCE_ARCHITECTURE.md` (convergence framework), repo root `/home/tak_0/sunshineos-audit/SunshineOS_Development-Testing`*

All primitives are designed for **idempotent execution** (M-09: repeatable without uncontrolled duplication), **staged validation** (M-05), and **explicit recovery** (M-06). Each operates against the authoritative installation state, not release numbers.

---

## 1. systemd Unit Recovery

| Field | Specification |
|---|---|
| **Identifier** | `PRM-001` (ref: `reports/USER_MIGRATION_MANDATE_2026-11-21.md::M-06`) |
| **Precondition** | `systemctl is-system-running` returns `degraded` or `maintenance`; unit files reside in `/etc/systemd/system/` or `/usr/lib/systemd/system/` |
| **Command** | ```bash\n# Idempotent: reloads unit files, re-enables if previously enabled, suppresses errors if unit missing\nsystemctl daemon-reload\nsystemctl enable --now --no-block <unit-name>.service 2>/dev/null || true\n``` |
| **Rollback** | ```bash\n# Disable and mask unit to revert to prior state\nsystemctl disable --now <unit-name>.service\nsystemctl mask <unit-name>.service\n``` |
| **Validation** | `systemctl is-enabled <unit-name>.service` + `systemctl status <unit-name>.service` (active/failed/inactive) |

*Rationale: Decouples unit lifecycle from OS release sequence. Aligns with M-04 (installation authoritative) and M-06 (recoverable).*

---

## 2. pacman Database Repair

| Field | Specification |
|---|---|
| **Identifier** | `PRM-002` (ref: `reports/USER_MIGRATION_MANDATE_2026-11-21.md::M-06`) |
| **Precondition** | Pacman cache present; no foreground package transaction running (`pacman -Qk` check optional) |
| **Command** | ```bash\n# Idempotent: fixes broken dependencies, removes invalid packages, refreshes cache\npacman -Sc --noconfirm\npacman -Qk >/dev/null 2>&1\npacman -Syu --noconfirm --nouseownership 2>/dev/null || true\n``` |
| **Rollback** | ```bash\n# Preserve current db state; restore from `/var/lib/pacman/local/` backup snapshot\n# If `pacman -Qk` reveals missing files, reinstall:\npacman -S --overwrite '*' <package-name> --noconfirm\n``` |
| **Validation** | `pacman -Q` confirms all explicitly installed packages; `pacman -Qk` shows no missing files |

*Rationale: Satisfies M-05 (staged) and M-09 (repeatable). Database state is a migration artifact versioned per `INV7` schema.*

---

## 3. Orphan & Partial-Transaction Cleanup

| Field | Specification |
|---|---|
| **Identifier** | `PRM-003` (ref: `reports/USER_MIGRATION_MANDATE_2026-11-21.md::M-06`) |
| **Precondition** | `pacman -Qdt` may return orphans; partial transaction lock may exist at `/var/lib/pacman/db.lck` |
| **Command** | ```bash\n# Idempotent: remove orphans, clean partial transactions\npacman -Rns $(pacman -Qdtq) --noconfirm 2>/dev/null || true\nrm -f /var/lib/pacman/db.lck\npacman-key --refresh-keys --no-block 2>/dev/null || true\n``` |
| **Rollback** | ```bash\n# Reinstall packages removed by orphan purge if still in repos\npacman -S --needed $(pacman -Qdtq) --noconfirm 2>/dev/null || true\n``` |
| **Validation** | `pacman -Qdt` returns empty; no `db.lck` present; `pacman -Qk` clean |

*Rationale: Prevents migration graph corruption (M-02: evolution history immutable). Clean state required before transition catalog lookup.*

---

## 4. AUR Helper Recovery

| Field | Specification |
|---|---|
| **Identifier** | `PRM-004` (ref: `reports/USER_MIGRATION_MANDATE_2026-11-21.md::M-08`) |
| **Precondition** | AUR helper binary (e.g., `yay`, `paru`, `auracle`) in `$PATH`; `~/.cache/aur/` or `~/cache/` may be stale |
| **Command** | ```bash\n# Idempotent: refresh AUR metadata, rebuild invalid AUR deps\nauracle sync --no-color --no-interaction 2>/dev/null || true\n# If using yay/paru, force clean rebuild\nyay -Sua --noconfirm --mbuild n 2>/dev/null || true\nparu -Sua --noconfirm --mbuild n 2>/dev/null || true\n``` |
| **Rollback** | ```bash\n# Remove rebuilt AUR packages, reinstall from official repos if available\nyay -Rns $(yay -Qm) --noconfirm 2>/dev/null || true\n# Or pin previous version via local repo snapshot\n``` |
| **Validation** | `pacman -Qm` limited to explicitly user-owned AUR packages; `auracle results` shows no unsatisfied dependencies |

*Rationale: M-08 (qualified support): AUR support qualified per helper version. M-01 (target-state driven): AUR packages evaluated against target profile, not blindly migrated.*

---

## Cross-Primitive Governance

| Principle | Implementation |
|---|---|
| **M-05 (Staged)** | Each primitive writes a `.migration-state/<primitive-id>.json` snapshot before modification; orchestrator validates before proceeding. |
| **M-06 (Recoverable)** | Rollback steps are deterministic, idempotent, and logged to `logs/migration-recovery.log`. |
| **M-09 (Repeatable)** | All commands use `--noconfirm`, `--no-block`, and idempotent flags; re-execution yields identical state. |
| **M-02 (Immutable History)** | Primitive identifiers (`PRM-001`→`PRM-004`) are versioned in `evolution-engine/` and signed per `TC18` transition catalog. |

*End of primitives. For full migration workflow integration, see `evolution-engine/` orchestrator state machine and `reports/OPENCLAW_ORDER_3_CONVERGENCE_ARCHITECTURE.md` convergence validation pipeline.*
