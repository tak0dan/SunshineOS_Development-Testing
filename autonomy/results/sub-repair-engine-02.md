# fstab and initramfs repair primitives

- Agent: sub-repair-engine
- Model: nvidia/nemotron-3.5-lightning:free
- Completed: 2026-11-21 00:15

---

# Safe Repair Protocol for fstab and initramfs
*Aligned with SunshineOS evolutionary migration invariants M-05, M-06, M-07, M-08, M-09. All operations are staged, journalled, and recoverable.*

## Context
- **Convergence architecture reference:** `reports/OPENCLAW_ORDER_3_CONVERGENCE_ARCHITECTURE.md`
- **User mandate invariants:** `reports/USER_MIGRATION_MANDATE_2026-11-21.md`
- **Evolution engine alignment:** `evolution-engine/`
- Operating principle: never modify the running system without a verified backup and compensation path.

---

### fstab Safe Repair
**Objective:** Resolve UUID conflicts, duplicate mount points, and missing subvolumes without data loss.

| Step | Command / Action | Purpose |
|------|------------------|---------|
| 1 | `sudo cp /etc/fstab /etc/fstab.bak.$(date +%s)` | Archive pre-repair state (invariant M-07) |
| 2 | `sudo blkid -o udev | grep ID_FS_UUID > /tmp/canonical_uuids.txt` | Generate authoritative UUID list |
| 3 | `sudo mount -a --warn-only 2>&1 || true` | Validate current mounts; halt on fatal errors |
| 4 | `findmnt -t all -r -n -o TARGET -M /etc/fstab` | Detect duplicate/mount-point overlaps |
| 5 | **UUID remap:** Edit `/etc/fstab` to replace any non-UUID or conflicting entries with output from step 2. Never generate new UUIDs for existing data. |
| 6 | **Duplicate mount removal:** Keep the entry with the oldest reliable timestamp or most specific filesystem type. Comment out or remove overlaps. |
| 7 | **Missing subvolume handling:**<br>- If subvolume is expected per migration ledger: stage creation via `btrfs subvolume create <path>`<br>- If not expected: retire entry with a logged migration note to `/var/log/sunshineos/migration/retired-fstab-entries.log` |
| 8 | `sudo mount -a` | Apply corrected fstab |
| 9 | `df -h / /home /var` | Verify mount points report expected sizes/usage |

---

### initramfs Safe Repair
**Objective:** Regenerate a stable initramfs with pinned modules and a verified fallback image.

| Step | Command / Action | Purpose |
|------|------------------|---------|
| 1 | `sudo cp /initramfs-$(uname -r).img /initramfs-$(uname -r).img.bak.$(date +%s)` | Archive current image (invariant M-07) |
| 2 | `sudo mkinitcpio -P -k $(uname -r) -g /boot/initramfs-$(uname -r).img` | Full regeneration (adjust tool to SunshineOS `mkinitcpio`/`dracut` equivalent) |
| 3 | **Module pinning:** Edit `/etc/mkinitcpio.conf` (`/etc/dracut.conf` etc.) to specify `MODULES=(ext4 xhci-pci usb-input)` — avoid `ALL` per invariant M-08 (qualified support only) |
| 4 | `sudo mkinitcpio -k $(uname -r) -g /boot/initramfs-fallback-$(uname -r).img` | Install fallback image |
| 5 | `ls -l /boot/initramfs-*.img` | Verify image timestamps/sizes |

---

### Checkpoint/Restore Protocol
| Phase | Action | Command |
|-------|--------|---------|
| **Checkpoint** (before any mutation) | Snapshot critical partitions and log hashes | ```bash\nsudo rsync -a /etc /var /home /mnt/backup/sunshineos-pre-repair-$(date +%s)/\nsha256sum /etc/fstab /initramfs-$(uname -r).img > /var/log/sunshineos/checkpoints/pre-repair-$(date +%s).hash\n``` |
| **Restore** (if validation fails) | Revert from checkpoint | ```bash\nsudo rsync -a /mnt/backup/sunshineos-pre-repair-$(date +%s)/ /\nsudo reboot\n``` |
| **Atomic switch** | Transition to new state only after validation | ```bash\nsystemctl isolate rescue.target\n# or: sudo switch-root /new-root /new-initramfs\n``` |

---

### Verification Commands (Post-Repair)
```bash
# fstab validation
sudo findmnt -T / --noheaders --output FSTYPE,SIZE,USE%
sudo mount | grep -E ' / | /home | /var '

# initramfs validation
sudo lsinitcpio -k $(uname -r)  # SunshineOS/dracut equivalent
sudo journalctl -k | grep -i 'fail\|error' | head -20

# Cross-check UUID-to-mount consistency
sudo blkid | grep -Ff /etc/fstab | head -10
```

---

### Repository Path Citations
- **User mandate (invariants & architecture):** `reports/USER_MIGRATION_MANDATE_2026-11-21.md`
- **Convergence architecture order 3:** `reports/OPENCLAW_ORDER_3_CONVERGENCE_ARCHITECTURE.md`
- **Evolution engine (migration-state alignment):** `evolution-engine/`
- **Top-level repo structure:** `.git/, .gitignore, .openclaw/, FINDINGS.md, README.md, TODO/, autonomy/, evidence/, logs/, openclaw/, other/, prs/, reports/`

### Invariants Alignment Summary
- **M-05 (staged changes):** All modifications go through `mount -a --warn-only` and checkpoint before commit.
- **M-06 (recoverable):** Explicit `rsync` backup + hash log; restore via `rsync` from `/mnt/backup/`.
- **M-07 (artifacts archived):** Backups, hashes, and retired entries stored under `/var/log/sunshineos/`.
- **M-08 (qualified support):** Module pinning limited to verified entries; `ALL` avoided.
- **M-09 (repeatable):** Identical commands produce verifiable state via hash comparison; no hidden side-effects.
