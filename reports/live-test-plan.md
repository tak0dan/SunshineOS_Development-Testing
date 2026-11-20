# SunshineOS live VM test plan

**Purpose:** exercise the exact behaviours reviewed in `source-audit.md` on a throwaway VM: live-session security posture, GRUB/splash, Calamares, Welcome, terminal tools, Hyprland, clipboard, network detection and privilege prompts. The goal is to confirm expected behaviour, reproduce suspected bugs and capture evidence — not to "fix" anything during the run.

**ISO under test:** record the full path and SHA-256 in the run header before starting:

```text
run-id:          2026-11-20-audit-01
iso:             <path/to/SunshineOS.iso>
sha256:          <sha256sum output>
git HEAD:        85506eae4d766faceb22e6b07886c3b983f96662
VM:              QEMU 7.0 / VirtualBox 7.x
firmware:        UEFI (repeat key boot checks in BIOS/legacy mode)
resources:       4 vCPU, 6 GB RAM, 64 MB video RAM, 3D acceleration enabled
network modes:   isolated (no NIC), NAT, NAT with broken DNS, host-only for SSH checks
```

## Evidence conventions

For every run, create `evidence/<run-id>/` with:

- `00-run-header.txt` — the block above, host OS, hypervisor version, kernel cmdline from `/proc/cmdline`.
- `screenshots/NN-topic.png` — numbered screenshots; use the full VM window, not a crop.
- `terminal/<tool>.txt` — terminal captures made with `script -q -c '<command>' terminal/<tool>.txt` or by piping through `tee`.
- `logs/journal-before.txt`, `logs/journal-after.txt`, `logs/systemd-failed.txt`, `logs/calamares.log`, `logs/sunshine-*.log`.
- `results.md` — a PASS / FAIL / OBSERVED table using the same section numbers as below.

Useful bootstrap commands once the live desktop is up (copy into a terminal and save the output):

```bash
mkdir -p ~/audit-evidence/{terminal,logs,screenshots}
{
  echo "=== cmdline ==="; cat /proc/cmdline
  echo "=== id ==="; id
  echo "=== os-release ==="; cat /etc/os-release
  echo "=== systemd failed ==="; systemctl --failed --no-legend
  echo "=== relevant units ==="; systemctl is-active sshd sddm NetworkManager dbus-broker
  echo "=== sunshine version/state ==="; sunshine-info 2>/dev/null || true
  echo "=== repo check ==="; sunshine-repo check || true
  echo "=== toolsync status ==="; sunshine-toolsync status || true
} | tee ~/audit-evidence/terminal/00-bootstrap.txt
journalctl -b > ~/audit-evidence/logs/journal-before.txt
```

> Use snapshots. Tests that break sudoers, pacman, LUKS or partitions must be done on a snapshot that can be rolled back. Do not run them on the VM that holds any real data.

---

## 1. GRUB menu and boot entries

| Step | Action | Expectation | Log / screenshot |
|---|---|---|---|
| 1.1 | Boot the ISO in UEFI mode without pressing anything. | Firmware hands off to GRUB; no "no bootable device" or silent black screen. | Screenshot the first GRUB frame. |
| 1.2 | At the menu, press `e` on the default entry. | Menu uses the Sunshine theme, readable text, entries for boot / copy-to-RAM / driver modes as provided by archiso. No stray `grub.d` output or duplicate text. | Screenshot menu and edited entry. Save `cat /proc/cmdline` after boot. |
| 1.3 | Boot normally to the live desktop. | Boots to SDDM autologin as `sunshine`; no password prompt. | Screenshot desktop, save `systemctl is-active sddm`. |
| 1.4 | Reboot into firmware setup / one more boot in BIOS mode if the ISO supports both. | Legacy BIOS entry boots to the same live session; no `x86_64-efi` assumption at this stage. | Screenshot BIOS GRUB menu. |
| 1.5 | On a separate snapshot, append `script=/tmp/audit-script.sh` to the kernel cmdline after placing a harmless script in the initramfs-accessible path. | Document that the root tty1 hook executes it as root (source-audit C1). Do not use a destructive payload. | Save script contents and `journalctl -b | grep -i automated_script`. |

## 2. Splash / start-up animation

| Step | Action | Expectation | Log / screenshot |
|---|---|---|---|
| 2.1 | Reboot and capture the Plasma splash at ~1 s, ~5 s and ~8 s. | Pixel logo builds up, strip opens through the middle, "SUNSHINE OS" is written, rays appear, then the ~10 s loop repeats until the session is ready. | Three screenshots: `02-splash-01s.png`, `02-splash-05s.png`, `02-splash-08s.png`. |
| 2.2 | Confirm the splash theme actually selected. | `ksplashrc` selects `com.sunshineos.sunshine` and `Splash.qml` plus `intro-sheet.png` / `loop-sheet.png` exist. | Save `grep -R KSplash ~/.config /usr/share/plasma/look-and-feel/com.sunshineos.sunshine/contents/defaults`. |
| 2.3 | Watch for a black or frozen splash. | No black screen; no QML errors in the journal. | `journalctl -b | grep -Ei 'ksplash|qml|splash'`. |

## 3. Welcome window

| Step | Action | Expectation | Log / screenshot |
|---|---|---|---|
| 3.1 | After autologin, wait for `sunshine-welcome --autostart`. | Welcome window appears with install, update, restore points, Flathub, tips and "don't show again" controls. | Screenshot full window. |
| 3.2 | Check the "don't show again" marker. | Toggling it creates/removes `~/.config/sunshine/welcome-disabled`; a relogin honours it. | Save `ls -l ~/.config/sunshine/welcome-disabled` before/after. |
| 3.3 | Click **Restore points**. | On live btrfs RAM root it should explain restore points are unavailable or open `sunshine-snapshot status`; no crash. | Screenshot result and save terminal output if opened. |
| 3.4 | Click **Flathub** with no network. | `pkexec flatpak remote-add ...` produces a clear failure, not a hung window. | Screenshot prompt and terminal output. |
| 3.5 | Click **Install** but close Calamares at the first page. | Starts `sudo -E /usr/bin/calamares` (or the text installer fallback) without a password prompt in the live session. | Screenshot launched installer; log process with `pgrep -a calamares`. |

## 4. Terminal tools

Run each tool from Konsole with output captured. Use `sunshine-toolbox` once to confirm the GUI entry points also start.

| Command | Expectation | Log / screenshot |
|---|---|---|
| `sunshine-doctor` | Check-only. Reports live session as live, skips installed-system boot/snapshot checks, exits without repairs. | `terminal/sunshine-doctor.txt` |
| `sunshine-doctor --fix` | Repairs only safe live-session issues; no destructive cache/package removal expected. Note any "fixed" lines. | `terminal/sunshine-doctor-fix.txt` |
| `sunshine-fix` (no destructive subcommand) | Prints help / available categories. Do not run `all` on the live session. | `terminal/sunshine-fix-help.txt` |
| `sunshine-fix-pacman` | Checks keyring/mirrors; does not reset keys unless broken. | `terminal/sunshine-fix-pacman.txt` |
| `sunshine-info`, `sunshine-secureboot status`, `sunshine-snapshot status` | Report identity, Secure Boot state (BIOS vs UEFI) and snapshot backend. | `terminal/sunshine-info.txt` etc. |
| `sunshine-toolsync status`, then `sunshine-toolsync verify` | Status shows installed version; verify either says no manifest (expected in the image) or every tool matches. Log any signature/key errors. | `terminal/sunshine-toolsync.txt` |
| `sunshine-repo check` | Reports `[sunshine]` first, signed, correct URL. | `terminal/sunshine-repo.txt` |
| `sunshine-pacnew list` | Lists pending `.pacnew` files or none. | `terminal/sunshine-pacnew.txt` |
| `sunshine-support --print` | Redacts username, hostname, IP/MAC, email, SSID and serial-like strings. Inspect output manually before sharing. | `terminal/sunshine-support.txt` |
| `sunshine-update` | Live warning appears; running kernel package is held; Arch news gate appears if applicable; "Final health check" and later "Health check" both run (source-audit L1). Capture full output — it can take several minutes. | `terminal/sunshine-update.txt`, `logs/sunshine-update.log` |
| `sunshine-toolbox` | GUI opens; buttons for update, fixes, snapshots, Flathub, KDE Connect are present; each launches the expected command. | Screenshot toolbox. |

## 5. Calamares install

Run on a disposable VM with a 40 GB+ virtual disk. Snapshot before starting.

| Step | Action | Expectation | Log / screenshot |
|---|---|---|---|
| 5.1 | Launch from the desktop "Install Sunshine OS" icon and separately from Welcome. | Both start `sudo -E /usr/bin/calamares` without a password prompt in the live session. | Screenshot each launch. |
| 5.2 | Walk through welcome, locale, keyboard. | Normal Calamares pages, Sunshine branding, no missing-module errors. | Screenshot each page. |
| 5.3 | On the partition page, select erase + btrfs + automated LUKS. | `partition.conf` offers btrfs, LUKS1 automation, ESP size 2G; no ZFS encryption. | Screenshot partition summary and chosen options. |
| 5.4 | On the users page, try a one-character password. | Calamares accepts it (`minLength: 1`, `allowWeakPasswords: true`); root password is disabled. Record this as expected-but-poor policy. | Screenshot the accepted state; do not reuse the password outside the lab. |
| 5.5 | Inspect the summary page. | Shows target disk, bootloader, users, locale, filesystem and netinstall choices. | Screenshot summary. |
| 5.6 | Apply and wait for exec steps. | Exec order follows `settings.conf`: partition → mount → unpackfs → machineid → fstab → luksbootkeyfile → locale/keyboard → location → cleanup → hyprland → netup → packages → netdown → ownbase → users → usershell → crypt → snapshots → networkcfg → hwclock → services → initcpio → grubcfg → bootloader → umount. | `cp /var/log/calamares.log ~/audit-evidence/logs/`; screenshot finished page. |
| 5.7 | Reboot into the installed system. | Boots to SDDM, no live autologin, normal sudo requires the chosen password. | Screenshot login and first desktop. |
| 5.8 | Verify live cleanup. | `test ! -e /etc/sudoers.d/10-live`, `test ! -e /etc/ssh/sshd_config.d/10-archiso.conf`, `systemctl is-enabled sshd` not enabled, `getent passwd sunshine` absent, root locked. | Save a command transcript. |
| 5.9 | Verify first-boot state. | `sunshine-identity check --quiet` passes; `sunshine-repo check` passes; btrfs subvolumes `@`, `@home`, `@log`, `@cache`, `@tmp` exist; first Snapper restore point is created if enabled. | Save `btrfs subvolume list /`, `snapper -c root list`. |

## 6. Encrypted install specifics

| Step | Action | Expectation | Log / screenshot |
|---|---|---|---|
| 6.1 | Install with LUKS enabled. | GRUB asks for the passphrase once; the initramfs does not ask again. | Screenshot GRUB unlock prompt and successful boot. |
| 6.2 | Inspect the boot image. | `lsinitcpio /boot/initramfs-linux.img | grep crypto_keyfile` finds the keyfile (source-audit H4). | Save full `lsinitcpio` output and `grep -R cryptkey /boot/grub/grub.cfg`. |
| 6.3 | Check encryption config. | LUKS1 used, `GRUB_ENABLE_CRYPTODISK=y`, `FILES=(/crypto_keyfile.bin)`. | Save `grep` output from `/etc/default/grub` and `/etc/mkinitcpio.conf.d/`. |

## 7. Hyprland session

| Step | Action | Expectation | Log / screenshot |
|---|---|---|---|
| 7.1 | Log out of Plasma and choose a Hyprland session at SDDM. | Sunshine-patched session appears; login succeeds with 3D acceleration enabled. | Screenshot SDDM session list and desktop. |
| 7.2 | Check bar, wallpaper and first-run scripts. | `sunshine-windfall-default`, bar, wallpaper and `/etc/skel` dotfiles apply; no "permission denied" from stripped exec bits. | Screenshot desktop; save `~/.cache/hyprland/hyprlandCrashReport*.txt` if present. |
| 7.3 | If the screen is black or Hyprland exits, disable/enable 3D acceleration and retry. | With software rendering it may fail with `eglInitialize` / `EGL_NOT_INITIALIZED`; this is the case the doctor expects to warn about. | Screenshot crash/fallback and log the exact error. |
| 7.4 | Switch back to Plasma. | Session change works without losing the user account or dotfiles. | Screenshot Plasma desktop. |

## 8. Clipboard

| Step | Action | Expectation | Log / screenshot |
|---|---|---|---|
| 8.1 | In Konsole, select text and copy with the mouse/Ctrl+Shift+C, then paste into a text editor or the Welcome URL field. | Text pastes correctly in Plasma/Wayland. | Screenshot before/after. |
| 8.2 | Copy a URL from Firefox and paste into Konsole. | Works in both directions; no X11-only dependency on Wayland. | Screenshot. |
| 8.3 | In a terminal, run `command -v wl-copy wl-paste xclip xsel` and try `wl-copy` / `wl-paste` if available. | At least one clipboard path works; report which. | Save command output. |
| 8.4 | With Hyprland active, repeat 8.1. | Clipboard still works; KDE Connect pairing text in Toolbox mentions clipboard but is not required locally. | Screenshot Hyprland paste. |

## 9. Network checks and diagnostics

Use three network states: isolated (`-nic none`), NAT with working DNS, and NAT with `/etc/resolv.conf` pointed at an unreachable resolver.

| Step | Action | Expectation | Log / screenshot |
|---|---|---|---|
| 9.1 | Isolated VM: `source /usr/local/lib/sunshine/ui.sh; sun_online; echo "$SUN_NET_METHOD / $SUN_NET_WHY"; sun_net_explain`. | Returns non-zero; reason should be `route` or generic. No hang longer than the combined timeouts (~40 s). | Save output and timing. |
| 9.2 | NAT, working DNS: repeat. | Success with a method such as `HTTPS archlinux.org`. | Save output. |
| 9.3 | NAT, broken DNS: repeat. | Expected `dns` reason and "names do not resolve" message. | Save output. |
| 9.4 | TCP-only case: allow raw TCP but block HTTP/DNS, repeat. | Success is reported, but `SUN_NET_WHY=dns-or-http` has no specific explanation (source-audit L2); record the generic message. | Save output. |
| 9.5 | Captive-portal simulation: point DNS at a local server returning 30x for connectivity checks. | `SUN_NET_WHY=portal` and the portal message appears. If hard to simulate, document as not tested. | Save output or note. |
| 9.6 | Run `sunshine-update` in each network state. | Offline fails cleanly at the connectivity gate with a specific message; online proceeds. | `terminal/net-update-*.txt` |

## 10. Privilege prompts

| Step | Action | Expectation | Log / screenshot |
|---|---|---|---|
| 10.1 | In Konsole, run `sudo sunshine-doctor`. | In the live session no password is asked (C1); in the installed system the user's password is asked in the same terminal. | Screenshot terminal prompt. |
| 10.2 | From Welcome / application menu, click **Update**. | `sunshine-update` opens a Konsole window running `pkexec sunshine-update-run`; polkit GUI prompt appears, not a terminal `sudo` prompt. | Screenshot the polkit prompt and the following update window. |
| 10.3 | Run `sunshine-update` directly in Konsole on the installed system. | Uses `sudo SUNSHINE_UPDATE_HERE=1` in the same terminal; no separate window. | Screenshot. |
| 10.4 | Run `sunshine-toolbox` → Flathub / restore points. | GUI actions use `pkexec`; terminal actions use `sudo`. No custom polkit rules are shipped, so stock prompts are expected. | Screenshot prompts. |
| 10.5 | Run `visudo -c` on the installed system. | Valid; no `NOPASSWD: ALL` for `wheel` remains. | Save output. |

## 11. Repair and update stress checks (snapshot required)

| Step | Action | Expectation | Log / screenshot |
|---|---|---|---|
| 11.1 | Create a condition the doctor detects, e.g. a stale `/var/lib/pacman/db.lck` with no running pacman. | `sunshine-doctor` reports it; `--fix` removes it and logs "fixed". | Before/after terminal captures. |
| 11.2 | Put a deliberate syntax error in a drop-in under `/etc/sudoers.d/` and run `sunshine-doctor --fix`. | The bad file is renamed to `.broken`; `visudo -c` still succeeds. Do not leave the VM in a state where sudo is unusable without a snapshot. | Save `visudo -c` output and file list. |
| 11.3 | Add a harmless `/etc/sudoers.pacnew` and repeat the broken-sudoers scenario. | Record whether the repair copies `.pacnew` over `/etc/sudoers` (source-audit M5) and whether the result is valid. | Save diff and `visudo -c`. |
| 11.4 | Run `sunshine-update` through to completion on the installed system. | One full doctor pass is enough; note the duplicated health check before and after apps. Toolsync runs first. | `terminal/installed-update.txt`, `logs/sunshine-update.log`. |
| 11.5 | Run `sunshine-toolsync verify` after the update. | Every tool matches the installed manifest, or log the exact mismatch/fingerprint error. This is the best check for the rotated-key finding. | Save output and `pacman-key --list-keys sunshine`. |

## 12. Optional aarch64 checks

Only if an aarch64 image and VM are available:

| Step | Action | Expectation | Log / screenshot |
|---|---|---|---|
| 12.1 | Boot the aarch64 ISO and run `sunshine-doctor`. | Log missing desktop packages / wrong EFI target if present. | Terminal capture. |
| 12.2 | Run a successful terminal tool with animation enabled. | Logo animation falls back to the plain coloured line because `numpy`/`PIL` are absent from the aarch64 package set (source-audit L4). | Screenshot terminal and save `python3 -c 'import numpy, PIL'`. |
| 12.3 | Attempt Calamares with an aarch64 image. | Expect failure at `unpackfs.conf:3` looking for `arch/x86_64/airootfs.sfs` unless the path is fixed. | Save Calamares log and screenshot. |

---

## Results template

Copy into `evidence/<run-id>/results.md`:

```markdown
| # | Check | Result (PASS/FAIL/OBSERVED) | Evidence | Notes |
|---|---|---|---|---|
| 1.1 | GRUB menu renders |  | screenshots/01-grub.png |  |
| 2.1 | Splash animation phases |  | screenshots/02-splash-*.png |  |
| 3.1 | Welcome autostart |  | screenshots/03-welcome.png |  |
| 4.x | Terminal tools |  | terminal/*.txt |  |
| 5.7 | Installed-system cleanup |  | terminal/05-cleanup.txt |  |
| 6.2 | LUKS keyfile in initramfs |  | logs/06-lsinitcpio.txt | Expected from source audit |
| 7.x | Hyprland |  | screenshots/07-hyprland.png |  |
| 8.x | Clipboard |  | screenshots/08-*.png |  |
| 9.x | Network diagnosis |  | terminal/net-*.txt |  |
| 10.x | Privilege prompts |  | screenshots/10-*.png |  |
| 11.x | Repair stress |  | terminal/11-*.txt |  |
```

At the end, attach the VM serial log if available, the final `journalctl -b`, `systemctl --failed`, and the SHA-256 of the ISO. Do not commit or push the evidence or reports as part of the audit.
