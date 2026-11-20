# Testing the Evolution Engine

## Test categories (run every release)

| Source state | Expected result |
|--------------|-----------------|
| Clean Arch, no desktop | Sunshine base installed |
| Arch + Plasma | Sunshine with Plasma profile |
| Arch + Hyprland | Sunshine with Hyprland profile |
| Arch + XFCE | Sunshine with XFCE profile |
| Arch + GNOME | Sunshine with GNOME profile |
| Arch + Sway | Sunshine with Sway profile |
| Arch + custom packages | Compatible packages preserved |
| Arch + custom configuration | User changes preserved |
| Old Sunshine installation | Current Sunshine architecture |
| Five-year-old Arch fixture | Current Sunshine architecture |

Additional scenarios: old pacman/keyring, kernel replacement, bootloader transition, mkinitcpio
migration, btrfs/ext4, existing Nix, missing/partial components, interrupted transformations,
failed package transaction, insufficient disk, failed kernel boot, failed checkpoint, invalid
repository signature, revoked key, repeated `sunshine-update`.

## VM as a testing ground

The audit VM `SunshineOS-Audit` is used as a live test target:

- ISO: `SunshineOS_13.4.7.1.6_Release_2026-11-19.iso`.
- Guest control: `VBoxManage guestcontrol SunshineOS-Audit run --username sunshine --password 111 --exe /bin/bash -- -c '...'`.
- GUI: VirtualBox window on `DISPLAY=:1`; screenshots via `VBoxManage controlvm ... screenshotpng`.
- SSH NAT forward exists (`127.0.0.1:2222`) but sshd may be inactive in a fresh live session.

### Iteration loop

```
implement → test in VM → break it → find improvements → implement
   ↑                                                        │
   └── document everything ← repair ← break again ← upgrade ┘
```

When a pass appears complete, restart at stage 1 with a harder scenario.

## Local unit tests

```bash
cd evolution-engine
python3 -m unittest discover -s tests -v
```

Tests use fake `root` paths and injected `execute(cmd)` callables so no test touches the real
system. Current suite: **106 tests, OK**. Coverage includes discovery, users, source compatibility,
target resolution, contradictory decisions, Stage A trust, component contracts, adapters, planner,
executor, interrupted resume, stale plans, CLI fixture fidelity and idempotency.

For a host-independent CLI demo:

```bash
python3 src/engine.py --fixture clean-arch --check
python3 src/engine.py --fixture arch-hyprland --plan
python3 src/engine.py --fixture clean-arch --state-root /tmp/eve-sandbox \
  --apply --decide desktop-profile=hyprland
```

Read-only and dry-run commands never need a sandbox. Real fixture applies require an explicit
`--state-root` and refuse the live `/var/lib/sunshine`.

## Live verification checklist

- [ ] `sunshine-evolve --check` on a simulated clean Arch root
- [ ] `--plan` introduces every required component from zero
- [ ] `--plan` on converged state yields no mutating operations
- [ ] `--apply --dry-run` changes nothing
- [ ] `--apply` on a fixture with a failure stops and journals correctly
- [ ] `--repair` resumes after simulated interruption
- [ ] `--verify` fails closed for unknown capabilities
- [ ] VM: toolsync delivers current tools after key rotation
