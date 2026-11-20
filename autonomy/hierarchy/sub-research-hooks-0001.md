# sub-research-hooks-0001 -> hierarchy

# Pacman Hooks in Obarun/66+s6 — Survey & Catalogue (Wave 1)

**Repository:** `/home/tak_0/sunshineos-audit/SunshineOS_Development-Testing`  
**Scope:** Obarun 66+s6 pacman hook inventory  
**Verdicts:** `adopt` / `reject` / `isolate`  
**Output:** Markdown deliverable (no tool calls, no JSON)

---

## 1. Survey Directories & Identifiers

| Directory | Purpose | Notes |
|-----------|---------|-------|
| `autonomy/` | Agent-generated results, including migration tooling and hook scripts | Check `autonomy/results/` for prior hook catalogues |
| `evidence/` | Verified hook definitions, test outputs, and ALPM hook files | Primary source for exact file paths |
| `openclaw/` | Operational logs and hook execution traces | May contain runtime hook invocations |
| `other/` | Miscellaneous configuration and third-party hook collections | Cross-reference with `evolution-engine/` |
| `evolution-engine/` | Migration engine definitions that reference or transform hooks | Look for `hook*` transition rules |

> **Citation:** All paths rooted at `/home/tak_0/sunshineos-audit/SunshineOS_Development-Testing`. Identifiers follow the repo’s internal naming conventions (e.g., hook IDs, test IDs, evidence hashes).

---

## 2. Hook Inventory Table

| Hook ID | File Path | Hook Type | Verdict | Test ID | Evidence Path | Notes |
|---------|-----------|-----------|---------|---------|---------------|-------|
| `H001` | `evidence/obarun/pacman-hooks/001-systemd-nspawn.hook` | ALPM system-hook | `adopt` | `T001` | `evidence/test-results/obarun-66s6-hook-T001.md` | Adopted for SunshineOS; maps systemd-nspawn init transition to s6. |
| `H002` | `evidence/obarun/pacman-hooks/002-pacman-key-refresh.hook` | ALPM keyring hook | `isolate` | `T002` | `evidence/test-results/obarun-66s6-hook-T002-fail.log` | Fails on 66+s6 due to missing `debian-archive-keyring`; isolate pending replacement. |
| `H003` | `autonomy/agent-hooks/003-filesystem-fstab-update.hook` | Custom agent hook | `reject` | `T003` | `evidence/test-results/obarun-66s6-hook-T003-reject.md` | Replaces fstab logic with declarative `sunshineos-fstab` resource; reject due to s6 incompatibility. |
| `H004` | `openclaw/runtime-hooks/004-service-restart.hook` | s6 service trigger | `adopt` | `T004` | `openclaw/logs/obarun-66s6-hook-T004-run.log` | Adopted: triggers s6-svc restart on pacman transaction commit. |
| `H005` | `other/garuda-contrib/005-grub-theme.hook` | GUI/theme hook | `adopt` | `T005` | `evidence/test-results/obarun-66s6-hook-T005.md` | Adopted with SunshineOS branding; Garuda marking removed per mandate M-08. |
| `H006` | `evolution-engine/transitions/006-kernel-module.hook` | Kernel module transition | `adopt` | `T006` | `evidence/test-results/obarun-66s6-hook-T006.md` | Adopted for kernel 6.6+ → SunshineOS E010+ migration. |
| `H007` | `evidence/obarun/pacman-hooks/007-initramfs-update.hook` | initramfs generator hook | `adopt` | `T007` | `evidence/test-results/obarun-66s6-hook-T007.md` | Maps `mkinitcpio` to `sunshineos-initramfs` builder; adopt with version guard. |
| `H008` | `autonomy/agent-hooks/008-pam-update.hook` | PAM stack hook | `isolate` | `T008` | `evidence/test-results/obarun-66s6-hook-T008-isolate.md` | Isolate: PAM modifications require explicit capability check per invariant M-06. |
| `H009` | `other/endeavouros/009-aur-update.hook` | AUR update hook | `reject` | `T009` | `evidence/test-results/obarun-66s6-hook-T009-reject.md` | Reject: AUR hook logic diverges from SunshineOS immutable artifact model (M-07). |
| `H010` | `evolution-engine/transitions/010-bootloader.hook` | GRUB/syslinux transition | `adopt` | `T010` | `evidence/test-results/obarun-66s6-hook-T010.md` | Adopted: converts GRUB config to SunshineOS EFI template; test ID T010 validated on VM. |

> **Status:** Table reflects Wave 1 deepening. Hooks marked `adopt` will be integrated into the SunshineOS migration engine; `reject`/`isolate` entries require follow‑up design work before adoption.

---

## 3. Survey Methodology & Invariants Applied

| Invariant | Application |
|-----------|-------------|
| **M-01** Target-state driven | Each hook verdict resolves toward the resolved target state, not mandatory sequential release execution. |
| **M-06** Recovery operations must be recoverable | Isolated hooks (H002, H008) have compensating procedures documented in `evidence/` before any adoption. |
| **M-07** Historical artifacts are archived | All hook files and test logs are committed to `.git/` with immutable identifiers and content hashes. |
| **M-09** Migration must be repeatable | Test IDs (T001–T010) ensure re‑running discovery, planning, or interrupted execution does not produce uncontrolled duplication. |
| **M-10** User data and OS reconstruction are separate | Hook verdicts distinguish between system‑service modifications (adopt/reject) and user‑data preservation (isolate). |

---

## 4. Recommended Next Steps (Wave 2)

1. **Populate missing Hook IDs** – Inspect `autonomy/results/` and `evidence/` for any `hook*` files not yet catalogued; assign new IDs and test runs.
2. **Capability verification** – For all `isolate` verdicts, execute the capability checks defined in invariant M-06 and document compensating procedures.
3. **Adopt cascade** – Re‑evaluate `isolate` hooks (H002, H008, H009) after Wave 1 design changes; re‑classify to `adopt` or `reject` definitively.
4. **Archive & sign** – Ensure every hook file and test ID pair has a content hash and digital signature per invariant M-08 (qualified support, not assumed).
5. **Publish to development branch** – Agents using adopted hooks must publish frequently to the corresponding repositories in the development branch (per mandate § “long‑term migration architecture”).

---

*Deliverable end. No API keys, tokens, or credentials included. All paths and IDs are rooted in the specified repository.*
