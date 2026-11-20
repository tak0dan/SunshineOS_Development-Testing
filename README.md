# Sunshine OS — Development, Testing & Audit

This repository holds development testing artifacts for Sunshine OS: audit reports,
live VM test results, logs, screenshots, and test ideas.

Code changes are published to their own repositories:
- `tak0dan/SunshineOS` — OS build, tools and configuration source
- `tak0dan/sunshineos-site` — website (including the Releases gallery)

## Contents

- `reports/source-audit.md` — read-only source audit of the OS repo and site (findings with file:line evidence).
- `reports/update-hang-investigation.md` — why `sunshine-update` appears to hang on "Apps you chose", and why the new animation was not delivered.
- `logs/download/` — ISO download logs (curl + aria2).
- `evidence/screenshots/` — GRUB, boot, SDDM, Welcome app and terminal captures from the audit VM.

## Audit VM

- Name: `SunshineOS-Audit`, GUI visible in VirtualBox.
- ISO: `SunshineOS_13.4.7.1.6_Release_2026-11-19.iso`, SHA-256 `fca813a623eada74a2f15ff5295082c87eae37fd014016c1c6f90bd01d453a97`.
- Control: NAT SSH `127.0.0.1:2222` (sunshine/sunshine), VNC `127.0.0.1:5901` (password `AuditVNC2026`), serial TCP `55123`, VirtualBox guest control.
