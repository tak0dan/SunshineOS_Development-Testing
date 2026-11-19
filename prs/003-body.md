## Problem

`96-sunshine-wallpapers.hook` is packaged in sunshine-base and rewritten to `Exec = /usr/bin/sunshine-theme-wallpapers`, but `theme-wallpapers` is not in the tool list of `stage-src.sh`. So the program is not in the package.

On installed systems the hook fails after every `plasma-workspace` update with `call to execv failed`, and the Sunshine wallpaper disappears from the Breeze themes until toolsync runs again. toolsync writes the same hook file with `/usr/local/bin/...`, so the hook keeps flipping between the two paths.

The ISO 13.4.7.1.5 shipped sunshine-base 0.6, which had the same problem with `migrate` and `state-hook`, already fixed in 2f83545. The `94-sunshine-migrate.hook` and `98-sunshine-state.hook` failures show up in a fresh `sunshine-install` log.

## Fix

- Add `theme-wallpapers` to the tool list.
- Add a check to `stage-src.sh`. After the `/usr/local/bin` → `/usr/bin` rewrite, every `Exec=` / `ExecStart*=` / `ExecStop=` in the packaged hooks, units and `.desktop` files that runs `/usr/bin/sunshine*` or `/usr/lib/sunshine*` must point to something inside the package. If not, the build stops with the list. The next new tool can no longer ship with a broken hook.

## Tested

I ran the check on the hooks of the current SunshineOS `main`, rewritten the same way `stage-src.sh` does it:
- With the upstream list, it reports exactly `/usr/bin/sunshine-theme-wallpapers`.
- With this list, it reports nothing.

`bash -n` passes. I have **not** done a full `stage-src.sh` + `makepkg` run yet.

Design question: sunshine-base and toolsync both write `/usr/share/libalpm/hooks/*-sunshine-*.hook`, with different `Exec` paths. Would it be better if only one of them owned the hooks?

🤖 Generated with [Claude Code](https://claude.com/claude-code)
