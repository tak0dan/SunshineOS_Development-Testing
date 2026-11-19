## Problem

Every live boot is a systemd "first boot" because the machine-id is empty, and so is the first boot of an installed system. On a first boot systemd runs `preset-all` in enable-only mode. `/usr/lib/systemd/system-preset/90-systemd.preset` then enables `systemd-networkd`, its sockets and `systemd-networkd-wait-online`, next to NetworkManager.

**Live (13.4.7.1.5, VirtualBox):**
- `networkctl` shows `enp0s3 … routable configured`, so networkd is managing the interface that NetworkManager also manages.
- The DHCP routes show up twice.
- NetworkManager logs `dns-sd-resolved … SetLinkDomains@2 failed: org.freedesktop.resolve1.LinkBusy: Link enp0s3 is managed`.
- `systemd-networkd-wait-online` slows the boot down.

**Installed system (`sunshine-install`, btrfs):**
- `systemd-networkd` and its socket come up `enabled active`. They sit idle, because the installer removes the `20-*.network` files.
- The journal logs `Failed to preset all unit: Unit /etc/systemd/system/systemd-networkd-wait-online.service is masked`: the installer masks the unit and `90-systemd.preset` still tries to enable it.
- Migration `0005-faster-boot` is meant to clean this up afterwards, but it never runs on a 13.4.7.1.5 install: the ISO ships sunshine-base 0.6, whose `94-sunshine-migrate.hook` points to a `/usr/bin/sunshine-migrate` that is not in that package.

## Fix

This adds `overlay/system/etc/systemd/system-preset/10-sunshine.preset`, which disables `systemd-networkd` (service, socket and varlink/resolve-hook sockets) and `systemd-networkd-wait-online`. It sorts before `90-systemd.preset`, and the first matching line wins. `make-iso.sh` copies it into the profile, so both the live image and the installed system get it.

## Tested

I ran `systemctl preset-all --preset-mode=enable-only`, which is the first-boot mode, on both systems.

| | networkd.service / .socket / wait-online | NetworkManager, resolved, sshd |
|---|---|---|
| live, without the preset | enabled / enabled / enabled | enabled |
| live, with the preset | disabled / disabled / disabled | enabled |
| installed, without the preset | enabled / enabled / masked (+ "is masked" warning) | enabled |
| installed, with the preset | disabled / disabled / masked (no warning) | enabled |

With the preset in place, the network still works: DHCP comes up, the per-link DNS is set in resolved, and HTTPS returns 200.

Note: plain `systemctl preset <unit>` (full mode) disables NetworkManager too, because of Arch's `99-default.preset` (`disable *`). That is not what a first boot does, so it is no problem here, but don't use full mode to test this.

I have not built a new ISO with this yet (`./make-iso.sh`).

🤖 Generated with [Claude Code](https://claude.com/claude-code)
