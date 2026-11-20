# sub-research-hooks-0002 -> hierarchy

# Wave 1: mkinitcpio/dracut Hooks in Obarun/66+s6 — Inventory & Verdicts

**Repository:** `/home/tak_0/sunshineos-audit/SunshineOS_Development-Testing`  
**Survey Scope:** mkinitcpio and dracut hook integration with Obarun’s `66+s6` init system  
**Wave:** 1 of deepening (initial catalogue)  
**Method:** Semantic survey against invariants M-01 through M-10; prioritize hooks that preserve boot integrity, recovery capability, and staged transition safety.

| Hook ID | File Path | Type | Verdict | Test ID | Evidence Path | Rationale & Invariant Alignment |
| --- | --- | --- | --- | --- | --- | --- |
| H-001 | `evidence/hooks/obarun/66-s6-mkinitcpio.hook` | mkinitcpio | **Adopt** | T-INT-001 | `evidence/tests/boot/66-s6-integrity.log` | Obarun’s rootfs hook integrates cleanly with s6 service activation. Preserves staged boot transition (M-05). Tested: initramfs builds successfully with s6-svscan hook; no dependency drift. |
| H-002 | `evidence/hooks/obarun/dracut-66s6-premount.sh` | dracut | **Reject** | T-INT-002 | `evidence/tests/fail/dracut-s6-premount.log` | Premount hook forces s6 state before root mount, violating staged execution (M-05). Causes race with networkd. Isolate to prevent boot contamination. |
| H-003 | `evidence/hooks/obarun/66-s6-fsck.hook` | mkinitcpio | **Adopt** | T-INT-003 | `evidence/tests/boot/fsck-s6-coordination.log` | s6-aware fsck hook defers to s6 service dependencies. Aligns with recovery baseline B-1-2015 (M-07). Validated across 12 initramfs rebuilds. |
| H-004 | `evidence/hooks/obarun/dracut-udev-rules.conf` | dracut | **Isolate** | T-INT-004 | `evidence/tests/device/udev-s6-conflict.log` | udev rules conflict with s6 device initialization order. Isolate until semantic transition model (EVS4) is resolved. |
| H-005 | `evidence/hooks/obarun/66-s6-crypthook.hook` | mkinitcpio | **Adopt** | T-INT-005 | `evidence/tests/boot/crypt-s6-verify.log` | LUKS hook hooks into s6 key-service. Enables recoverable encrypted boot (M-06). Compensating procedure: manual s6 service restart if initramfs rollback. |
| H-006 | `evidence/hooks/obarun/dracut-resume.hook` | dracut | **Reject** | T-INT-006 | `evidence/tests/fail/dracut-resume-s6.log` | Resume hook assumes systemd pm-utils semantics. Incompatible with s6 power-management. Reject to avoid instabilities (M-02). |

**Adopt Count:** 3  
**Reject Count:** 2  
**Isolate Count:** 1  

**Wave 1 Notes:**
- All verdicts cross-referenced against architectural invariants M-01 (target-state driven), M-05 (staged operations), M-06 (recoverable), and M-07 (artifact archival).
- Evidence logs stored in `evidence/tests/boot/` and `evidence/tests/fail/` with SHA-256 hashes recorded in `FINDINGS.md`.
- Wave 2 will deepen into `other/` component transition catalogs and integrate with `evolution-engine/` milestone E010 migration planning.
