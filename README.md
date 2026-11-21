# Sunshine OS — Development, Testing & Audit

This repository holds development testing artifacts for Sunshine OS: audit reports,
live VM test results, logs, screenshots, test ideas, and the **Sunshine Evolution
Engine** prototype.

Code changes are published to their own repositories:
- `tak0dan/SunshineOS` — OS build, tools and configuration source
- `tak0dan/sunshineos-site` — website (including the Releases gallery)

## Contents

- `reports/source-audit.md` — read-only source audit of the OS repo and site (findings with file:line evidence).
- `reports/live-test-plan.md` — step-by-step live VM verification plan and results.
- `reports/update-hang-investigation.md` — why `sunshine-update` appears to hang on "Apps you chose", and why the new animation was not delivered.
- `reports/evolution-engine-breakfix-cycle.md` — 11 real break/fix cycles found by tests and the live VM, each with a regression test.
- `evolution-engine/` — desired-state migration engine that converges both old Sunshine OS and pure Arch to the current Sunshine OS with one implementation.
- `logs/download/` — ISO download logs (curl + aria2).
- `evidence/screenshots/` — GRUB, boot, SDDM, Welcome app and terminal captures from the audit VM.

## Sunshine Evolution Engine

Run from `evolution-engine/`:

```
python3 -m unittest discover -s tests -v   # 317 tests
python3 src/engine.py --root fixtures/clean-arch --plan
python3 src/engine.py --root / --check
python3 src/engine.py --root / --apply --dry-run \
  --state-root /tmp/eve-state --decide desktop-profile=hyprland
```

Five principles, documented in `evolution-engine/docs/ARCHITECTURE.md`:

1. **Desired-state convergence** — the machine is compared to a declarative target; only the delta is applied.
2. **Capability discovery** — facts are observed with explicit confidence, and low confidence never authorises destructive work.
3. **Evolutionary components** — each component declares schema, lifecycle and dependencies and is planned independently.
4. **Declarative transformation plans** — typed operations form a dependency DAG with checkpoints and idempotency markers.
5. **Upstream Arch preservation** — foreign packages and user configuration are never silently replaced.

Additional docs: `docs/SECURITY.md` (trust/privilege/threat model) and
`docs/TESTING.md` (fixtures and test strategy).

Current result: all three fixtures and the live VM complete a full dry-run
with zero failed operations. See `reports/evolution-engine-breakfix-cycle.md`.

## Audit VM

- Name: `SunshineOS-Audit`, GUI visible in VirtualBox.
- ISO: `SunshineOS_13.4.7.1.6_Release_2026-11-19.iso`, SHA-256 `fca813a623eada74a2f15ff5295082c87eae37fd014016c1c6f90bd01d453a97`.
- Control: NAT SSH `127.0.0.1:2222`, VNC `127.0.0.1:5901` (password `AuditVNC2026`), serial TCP `55123`, VirtualBox guest control.
- Credentials: user `sunshine`, password `111` (also used for sudo). Guest control must run as `sunshine`; `root` guest-control logon is not available.
- Guest control example:

```
VBoxManage guestcontrol SunshineOS-Audit run --username sunshine --password 111 \
  --exe /bin/bash -- -c 'echo 111 | sudo -S -p "" pacman -Q | wc -l'
```

- Tools are delivered by signed release through `sunshine-toolsync`; pushing source alone does not update installed tools. Installed tools version at the end of this cycle: `2026.11.20.4`.
