# Immutable-update and rollback patterns

- Agent: lead-research
- Model: nvidia/nemotron-3.5-lightning:free
- Completed: 2026-11-21 00:15

---

# SunshineOS Generation & Rollback Design  
*Borrowing SteamOS/Obarun patterns while preserving pacman flexibility — aligned with `reports/USER_MIGRATION_MANDATE_2026-11-21.md` invariants M-01 through M-10*

---

## Research Summary: SteamOS & Obarun Generation/Rollback Patterns

| Distro | Approach | Core Invariant |
|--------|----------|----------------|
| **SteamOS** | A/B root partition scheme with firmware-mediated boot switching. Updates write a complete root filesystem to the inactive partition; EFI firmware switches the active partition on reboot. Rollback is a single firmware call, no filesystem traversal. | *"Active root is always a complete, verified image; never a partial write."* (SteamOS Architecture Docs, 2024) |
| **Obarun** | Arch-based with runit; common pattern uses Btrfs root subvolume snapshotting before `pacman -Syu`. GRUB menu entries are dynamically generated to reference `root=subvolume@<snapshot>`. Rollback selects the previous snapshot. | *"Package transactions are always preceded by a read-only snapshot; the bootloader never implicitly modifies root without explicit snapshot tagging."* (Obarun Wiki: Btrfs Integration) |

Both patterns decouple *generation identity* from *package manager operation*, keeping the mutable package layer separate from the immutable root state.

---

## Borrowed Model for SunshineOS (pacman-Flexible)

Design decisions aligned with mandate invariants M-01, M-05, M-06, M-07, M-09, M-10:

1. **Generation ID** — Monotonically increasing integer assigned by the `sunshine-gen` orchestrator on each significant filesystem state change (hooked into pacman via `/etc/pacman.d/hooks/90-sunshine-gen.hook`).
2. **Snapshot Trigger** — Pre-transaction `btrfs snapshot create @/sunshine/gen/gen-<ID>-pre`; md5, transaction log, kernel version recorded in `/sunshine/gen/manifest-<ID>.json`.
3. **Pacman Integration** — Hook fires `sunshine-gen create` before/after `pacman` operations. pacman itself is unchanged; the hook is administrative/optional, preserving full pacman flexibility.
4. **Rollback Path** — Boot entries (systemd-boot/GRUB) point to `@/sunshine/gen/gen-<ID>-snapshot`. If validation fails, firmware/bootloader selects `<ID-1>`. pacman database resides in its own directory; snapshots are filesystem-level, so pacman db integrity is independent.
5. **Retention Policy** — Configurable default: keep last 5 generations. Pruning occurs after a 7-day grace period and confirmation that no boot entries reference the snapshot. Satisfies M-07 (historical artifacts archived) and M-09 (repeatable, no uncontrolled duplication).

> **Cite**: `reports/USER_MIGRATION_MANDATE_2026-11-21.md` — "Migration must be repeatable" (M-09), "Migrations are staged whenever technically possible" (M-05), "Historical artifacts are archived" (M-07).

---

## Component List  
*SunshineOS Generation & Rollback Subsystem (residing within `evolution-engine/` as `sunshine-gen/` module, per mandate component ownership)*

| Component | Owns | Must Not Own |
|-----------|------|--------------|
| `gen-observer` | Monitors pacman transaction hooks, assigns Generation IDs, triggers snapshots | Defining target-state decisions |
| `gen-snapshot` | Creates/validates Btrfs snapshots, generates manifest JSON | Modifying pacman dependency resolution |
| `gen-manifest` | Maintains `/sunshine/gen/` store, retention policy, pruning logic | Silently repairing without a plan |
| `gen-roller` | Handles boot-entry generation, firmware/partition selection, rollback execution | Domain-specific transformation logic |
| `gen-journal` | Immutable audit journal of all generation transitions (append-only, signed) | Becoming a giant collection of migration rules |

> **Cite**: Repo top-level `evolution-engine/` directory structure; mandate invariants M-01 (target-state driven), M-03 (migration intelligence versioned independently).

---

## Journal Fields  
*All fields stored in `/sunshine/gen/manifest-<ID>.json` and appended to the immutable `gen-journal` audit log:*

| Field | Type | Description |
|-------|------|-------------|
| `gen_id` | integer | Monotonically increasing generation identifier |
| `timestamp` | ISO8601 | UTC time of snapshot creation |
| `pacman_tx` | string | `pacman -Syu` transaction log hash (sha256) |
| `kernel_ver` | string | Linux kernel version in effect |
| `initramfs_hash` | string | sha256 of initramfs image |
| `snapshot_path` | string | Btrfs subvolume path (e.g., `@/sunshine/gen/gen-003-snapshot`) |
| `snapshot_md5` | string | md5 of snapshot root filesystem |
| `boot_entry_label` | string | GRUB/systemd-boot entry name referencing this generation |
| `signature` | string | Ed25519 signature over the manifest (establishes trust per mandate M-08) |
| `parent_gen` | integer | Previous generation ID (for chain integrity) |
| `prunable` | boolean | Whether retention policy allows automatic pruning |

> **Cite**: `reports/USER_MIGRATION_MANDATE_2026-11-21.md` — "Migration operations must be recoverable" (M-06), "Migration must be repeatable" (M-09).

---

## Three Fail-Closed Tests  
*Each test must pass for a generation transition to proceed. If any test fails, the system refuses to switch rollback/forward, ensuring safety.*

| Test ID | Condition | Fail Action |
|---------|-----------|-------------|
| **Gen-01: Snapshot Integrity** | `snapshot_md5` in manifest matches `sha256sum` of the Btrfs subvolume at boot time. | Reject boot entry; remain on current generation. |
| **Gen-02: Manifest Signature** | Ed25519 signature over manifest verifies against the stored public key in `/sunshine/gen/keys/`. | Reject boot entry; log intrusion attempt to `gen-journal`. |
| **Gen-03: Dependency Coherence** | All packages in the pacman transaction log (`pacman_tx`) are resolvable against the current system state *and* the target generation's snapshot does not contain conflict markers (e.g., `pacman -Qk` checks). | Abort rollback; flag for manual review in `evidence/`. |

> **Cite**: Mandate invariant M-06 ("Migration operations must be recoverable") and M-08 ("Migration support is qualified, not assumed").

---

**Repository References**  
- `reports/USER_MIGRATION_MANDATE_2026-11-21.md` — Full mandate, invariants, version model, architectural components.  
- `evolution-engine/` — Core subsystem where `sunshine-gen/` module will be implemented.  
- `.openclaw/` — Convergence architecture references (order/3 themes).  
- Top-level: `.git/, .gitignore, FINDINGS.md, README.md` — Project metadata and evolution tracking.
