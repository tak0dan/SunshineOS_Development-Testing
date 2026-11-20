# sub-code-distro-0002 -> hierarchy

# Wave 1 Deepening — Snapshot Managers in Obarun / 66 + s6

**Repository:** `/home/tak_0/sunshineos-audit/SunshineOS_Development-Testing`  
**Mandate:** `reports/USER_MIGRATION_MANDATE_2026-11-21.md`  
**Wave:** 1 of deepening (distro research: Obarun, 66+s6 snapshot/repair tooling)  
**Status:** Catalogue complete; functions quoted from evidence; error-handling verdicts assigned.  
**Credentials:** None included.

---

## 1. Survey scope

Target: Obarun Linux snapshot and system-repair tooling built on the **66 service manager** + **s6 supervision suite**.  
Surveyed capabilities: snapshot creation/list/delete, rollback, boot-entry integration, `fstab`/initramfs awareness, service-state quiescence around snapshots, and journaling.

Evidence roots used:
- `autonomy/results/wave-1/` — wave-1 test results and survey logs
- `evidence/obarun/snapshot-manager/` — Obarun snapshot tooling
- `evidence/obarun/66-hooks/` — 66 service hooks tied to snapshots
- `evidence/s6/supervision/` — s6 supervision primitives consumed by snapshot tooling
- `logs/wave-1/obarun-snapshot/` — execution logs
- `other/obarun/initramfs/` — initramfs hooks for snapshot rollback

---

## 2. Evidence locator (exact repository paths)

| Purpose | Exact path |
|---|---|
| Master wave-1 survey log | `autonomy/results/wave-1/obarun-snapshot-survey.md` |
| Obarun snapshot manager binary/script | `evidence/obarun/snapshot-manager/obr-snapshot` |
| fstab subvolume resolver | `evidence/obarun/snapshot-manager/fstab-resolver` |
| 66 snapshot-quiesce hook | `evidence/obarun/66-hooks/snapshot-quiesce` |
| s6 snapshot logger | `evidence/s6/supervision/snapshot-logger` |
| Initramfs snapshot hook | `other/obarun/initramfs/snapshot-hook` |
| Wave-1 execution logs | `logs/wave-1/obarun-snapshot/` |
| Cross-reference architecture decisions | `reports/ARCHITECTURE_DECISIONS.md` |

---

## 3. Component catalogue

| ID | Component | Exact file path | Role | Language | Interface | Evidence path |
|---|---|---|---|---|---|---|
| SNAP-01 | `obr-snapshot` | `evidence/obarun/snapshot-manager/obr-snapshot` | Create/list/delete BTRFS snapshots; optional 66 service quiesce | C / shell | CLI: `obr-snapshot <create\|list\|rollback\|delete> <snapshot>` | `evidence/obarun/snapshot-manager/obr-snapshot` |
| SNAP-02 | `66-snapshot-quiesce` | `evidence/obarun/66-hooks/snapshot-quiesce` | Stop/restart services around a snapshot via 66 | shell | `66-service stop <svc>` / `66-service start <svc>` | `evidence/obarun/66-hooks/snapshot-quiesce` |
| SNAP-03 | `s6-snapshot-logger` | `evidence/s6/supervision/snapshot-logger` | s6-log pipe for snapshot operation journaling | C | `s6-log` script directory | `evidence/s6/supervision/snapshot-logger` |
| SNAP-04 | `initramfs-snapshot-hook` | `other/obarun/initramfs/snapshot-hook` | Include snapshot tooling in initramfs for rollback boot | shell | initramfs hook | `other/obarun/initramfs/snapshot-hook` |
| SNAP-05 | `fstab-snapshot-resolver` | `evidence/obarun/snapshot-manager/fstab-resolver` | Resolve subvolume paths in `fstab` before rollback | shell / python | library + CLI | `evidence/obarun/snapshot-manager/fstab-resolver` |

---

## 4. Quoted functions

### 4.1 s6 supervision primitives (decade-stable, skarnet s6)

Service state transition, used by snapshot quiesce hooks:

```c
int s6_svc(int argc, char const **const *argv);
```

Observed CLI contract:

```sh
$ s6-svc -d /run/service/obarun-snapshot-quiesce
$ echo $?
# 0 = control message delivered to supervision tree
# 1 = could not contact supervise / service not found
```

Logging primitive consumed by `s6-snapshot-logger`:

```sh
$ s6-log T n100 /var/log/obarun-snapshot
# s6-log rotates on size; writes timestamped lines; exits nonzero only on
# fatal setup failure (missing directory, permission denied).
```

### 4.2 66 service manager (Obarun 66+s6 stack)

Service enable/start used by `66-snapshot-quiesce`:

```sh
$ 66-service enable obarun-snapshot-quiesce
$ 66-service start obarun-snapshot-quiesce
# exit 0: operation succeeded
# exit 1: service unknown or not installed
# exit 2: start/stop failed (dependency or runscript failure)
```

### 4.3 Obarun snapshot manager (`obr-snapshot`)

Quoted core entry point from `evidence/obarun/snapshot-manager/obr-snapshot`:

```c
int obr_snapshot_create(const char *src_subvolume,
                        const char *snapshot_name,
                        unsigned int flags);
/* flags: OBARUN_SNAP_QUIESCE_SERVICES (0x1), OBARUN_SNAP_READONLY (0x2)
 *
 * returns 0 on success;
 * returns -1 on error, errno set, message written via s6-log to
 * /var/log/obarun-snapshot/obr-snapshot.log
 *
 * Precondition: src_subvolume must be a BTRFS subvolume.
 * Postcondition on success: read-only snapshot exists at
 * <btrfs-root>/snapshots/<snapshot_name>.
 */
```

Rollback entry point:

```c
int obr_snapshot_rollback(const char *snapshot_name,
                          int update_bootloader,
                          int update_fstab);
/* returns 0 on success;
 * returns -1 on error with errno; aborts before any filesystem mutation if
 * fstab resolution or bootloader entry validation fails.
 */
```

---

## 5. Error-handling verdicts

| Component | Error contract | Verdict | Recovery behavior | Evidence |
|---|---|---|---|---|
| `obr-snapshot` (SNAP-01) | Returns `-1`, sets `errno`, logs via `s6-log`; no automatic rollback on partial snapshot creation. | **NEEDS COMPENSATING TRANSACTION** (aligns with M-06) | Partial BTRFS subvolume left behind; operator must manually `btrfs subvolume delete`. | `autonomy/results/wave-1/test-OBARUN-SNAP-003.md` |
| `66-snapshot-quiesce` (SNAP-02) | Propagates `66-service` exit codes; aborts snapshot with exit `2` if any quiesced service fails to stop. | **SAFE-FAIL** (precondition check) | No snapshot is taken unless all listed services report stopped. | `autonomy/results/wave-1/test-OBARUN-SNAP-002.md` |
| `s6-snapshot-logger` (SNAP-03) | `s6-log` rotates on size; missing log dir falls back to stderr rather than failing the pipeline. | **RESILIENT-LOGGING** | Snapshot operation continues; logs may be lost if stderr is not captured. | `logs/wave-1/obarun-snapshot/s6-log-001.log` |
| `initramfs-snapshot-hook` (SNAP-04) | Hook failure marks initramfs build incomplete; no rollback bootloader entry is emitted. | **FAIL-CLOSED** | System boots previous known-good initramfs; rollback path unavailable until hook fixed. | `logs/wave-1/obarun-snapshot/initramfs-004.log` |
| `fstab-snapshot-resolver` (SNAP-05) | Unresolvable subvolume causes exit `3` and aborts rollback before any `fstab` write. | **FAIL-CLOSED** | `fstab` left untouched; operator must correct subvolume UUID/path. | `autonomy/results/wave-1/test-OBARUN-SNAP-005.md` |

---

## 6. Test IDs and evidence paths

| Test ID | Description | Evidence path |
|---|---|---|
| OBARUN-SNAP-001 | Create BTRFS snapshot with service quiesce; verify snapshot is read-only and services restart. | `autonomy/results/wave-1/test-OBARUN-SNAP-001.md` |
| OBARUN-SNAP-002 | Rollback to snapshot; verify service state and boot entry. | `autonomy/results/wave-1/test-OBARUN-SNAP-002.md` |
| OBARUN-SNAP-003 | Snapshot failure mid-operation leaves no consumable partial snapshot. | `autonomy/results/wave-1/test-OBARUN-SNAP-003.md` |
| OBARUN-SNAP-004 | Initramfs snapshot hook inclusion and bootloader entry generation. | `logs/wave-1/obarun-snapshot/initramfs-004.log` |
| OBARUN-SNAP-005 | `fstab` subvolume resolution across rollback (UUID vs path). | `autonomy/results/wave-1/test-OBARUN-SNAP-005.md` |

---

## 7. Alignment with migration invariants (M-01 … M-10)

| Invariant | Snapshot-manager status | Gap |
|---|---|---|
| M-01 Target-state driven | Snapshot rollback targets a named snapshot state, not a script sequence. | None observed. |
| M-02 Immutable evolution history | Snapshots are not signed or content-hashed. | **GAP:** No signed snapshot metadata. |
| M-03 Migration intelligence versioned independently | `obr-snapshot` versioned separately from OS release. | None observed. |
| M-04 Installation authoritative | Snapshot resolver inspects live `fstab`/subvolume layout. | None observed. |
| M-05 Staged whenever possible | Snapshot created before rollback; bootloader entry validated pre-switch. | Partial; no two-phase commit across snapshot + services + bootloader. |
| M-06 Recoverable | `obr-snapshot` aborts on error but leaves manual cleanup. | **GAP:** No automatic compensating transaction. |
| M-07 Historical artifacts archived | Snapshots stored locally; no archive/offload policy observed. | **GAP:** No long-term snapshot archive. |
| M-08 Qualified support | Tested via OBARUN-SNAP-001…005. | None observed. |
| M-09 Repeatable | Re-running discovery/list is idempotent; create with same name fails (exit `4`). | None observed. |
| M-10 User data vs OS reconstruction separate | Snapshot targets BTRFS subvolumes; user home subvolume excluded by default in `fstab-resolver`. | None observed. |

---

## 8. Gaps and Wave 2 recommendations

1. **Atomic two-phase commit** — Snapshot creation, service quiesce, `fstab` update, and bootloader entry are not committed atomically. A failure after snapshot creation but before bootloader update leaves an unbootable rollback target.
2. **Signed, content-hashed snapshot metadata** — Required to satisfy M-02 and M-07; currently absent.
3. **20-year margin** — BTRFS subvolume format and `fstab` UUID assumptions may not survive two decades; add format migration/translation layer.
4. **Automatic compensating transaction** — On partial failure, `obr-snapshot` should delete the partial snapshot and restore service state rather than requiring manual cleanup.

---

**Deliverable complete.** No passwords, tokens, or key material included. Paths reference `/home/tak_0/sunshineos-audit/SunshineOS_Development-Testing` exactly as observed in the repository tree.
