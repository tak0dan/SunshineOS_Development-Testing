# Investigation: `sunshine-update` appears to hang on "Apps you chose"

**Date:** 2026-11-20
**Environment:** VM `SunshineOS-Audit`, live ISO `SunshineOS_13.4.7.1.6_Release_2026-11-19.iso`,
SHA-256 `fca813a623eada74a2f15ff5295082c87eae37fd014016c1c6f90bd01d453a97`.

## Symptom

Running `sunshine-update` in the live session prints the section `** Apps you chose` and then
appears to stop producing output for several minutes. The user perceives this as a hang on
"the packages you chose".

Observed terminal output (from `evidence/screenshots/05-welcome-app.png` and the later terminal
capture) included:

```
+ Checking for updates
No system package updates right now.
...
+ Updating Flatpak apps
Nothing to update.
+ Final health check
! failed services: sunshine-apps.service
+ Tidying up
+ Apps you chose
[sudo] password for sunshine:
zen: installing from the AUR: zen-browser-bin
zen: done
warning: sunshine-app-zen-322-1 is up to date - skipping
warning: sunshine-app-libreoffice-322-1 is up to date - skipping
+ Health check
ALL good (2 note(s))
+ ALL done
All done. Have a warm cup of tea and enjoy the sunshine ☀️🍵
```

The command eventually completed after roughly **3m57s**. It was not deadlocked.

## Root cause

Two things combine to make a slow step look like a hang:

1. **Output is buffered until the sub-command finishes.** In
   `profile/airootfs/usr/local/bin/sunshine-update-run:156-158`:

   ```bash
   say "Apps you chose"
   /usr/local/bin/sunshine-apps apply 2>&1 | tail -5
   /usr/local/bin/sunshine-apps first-update 2>&1 | tail -5
   ```

   Piping through `tail -5` means nothing is printed until `sunshine-apps` exits. The AUR helper's
   own progress (downloading a large binary, resolving dependencies, building) is redirected to
   `/var/log/sunshine/apps.log` in `profile/airootfs/usr/local/bin/sunshine-apps:35`:

   ```bash
   sudo -u "$u" $h -S --needed --noconfirm $aur >> "$LOG" 2>&1
   ```

   So for the entire install the user sees only the section title.

2. **The queued AUR package is large and has no timeout.** `zen-browser-bin` is fetched from the
   AUR by `paru`/`yay` with `--noconfirm`. On this VM it took several minutes. If the download
   stalls, there is no `timeout` around the helper, so the tool can wait indefinitely.

A related warning in the same run, `failed services: sunshine-apps.service`, comes from the
final health check; the queued app work was later completed successfully by the update run.

## Why the new animation did not appear

`sunshine-update` starts with (`:28`):

```bash
/usr/local/bin/sunshine-toolsync update || true
```

`sunshine-toolsync` does **not** pull tools from the `SunshineOS` git repository. It pulls a
signed release from the separate repository `tak0dan/sunshine-tools`
(`profile/airootfs/usr/local/bin/sunshine-toolsync:12`):

```
BASE=https://github.com/tak0dan/sunshine-tools/releases/download/tools
```

The published manifest at the time of testing was version `2026.11.19.221`, which contains the
pre-change `ui.sh` (sha256 `8456de9d54cccd9ae27e745eb3fbae0c1bac2027bc2489f7fbc8587c21fd76cc`).
The animation/graph/night-mode changes were committed to `tak0dan/SunshineOS` only
(`1b2a487`, `3bfbf61`). Since no new signed tools release was published, toolsync reported the
installed tools as up to date and left the old scripts in place. Upgrading system/AUR packages
does not upgrade the Sunshine tools.

## Fixes applied in source

- `tools/publish-tools.sh` now includes `usr/share/sunshine/logo-anim/*` in the published files
  (previously omitted, so the new sprite player would never reach systems).
- `ui.sh` `sun_success_anim()` now only invokes the sprite player when it supports `--tool`, and
  wraps it in `timeout 15`. Without this, a new `ui.sh` paired with an old `play.py` would run the
  endless site animation and hang the tool.

Publishing these to the VM still requires a new signed `sunshine-tools` release; the signing key
(`~/sunshineos-build/signing/key-fingerprint` + GPG home) is not present on this machine.

## Suggested product fixes (not yet applied)

- Stream `sunshine-apps apply` output instead of `| tail -5`, or print a live spinner/progress
  line and keep only the last lines for the summary.
- Put a `timeout` (e.g. `timeout 900`) around the AUR helper call and report a clear failure.
- Show the queued app ids before starting so the user knows what is being installed.
- Make `sunshine-update` print the toolsync version before and after so it is visible when tools
  are (or are not) updated.
