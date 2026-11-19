## Problem

The live session's welcome window offers **Update everything**. A full update there upgrades `linux`, and that deletes `/usr/lib/modules/<running kernel>`. From then on the running ISO kernel cannot load any module it has not loaded yet.

Seen on 13.4.7.1.5 in VirtualBox:
- `modprobe: FATAL: Module nf_tables not found in directory /lib/modules/7.3.4-arch1-2`, and `nft` fails.
- `98-sunshine-state.hook` reports "the boot files are incomplete".
- `pacman.log` shows the second pass did it: `pacman -Syu --noconfirm`, which runs after Chaotic-AUR is added.

## Fix

In `sunshine-update-run`, only in the live session (`/run/archiso`, and not inside sunshine-rescue's chroot):
- It says that the update only lives in memory, and asks `[y/N]` before going on.
- It holds back the package that owns `/usr/lib/modules/$(uname -r)` (and its `-headers`) in all three upgrade calls: both `pacman -Su` passes in `run_update`, and the `pacman -Syu --noconfirm` that runs after a new repository is added.

Updating the live session is still possible for testing, as in `logs/VM_Test_Report_2026-11-19/live-session.md`. Nothing changes on an installed system.

## Tested

On an installed 13.4.7.1.5, with `/run/archiso` created by hand:
- Answering `n` prints the notice and exits 0 without changing anything.
- The `bash -x` trace shows `kpkg=linux` and `HOLD='--ignore linux,linux-headers'`.
- `pacman -Qu` has `linux` pending, but `pacman -Sup --ignore linux,linux-headers` lists no kernel package.
- Without `/run/archiso`, `HOLD` is empty and there is no prompt.

`overlay/system` and `profile/airootfs` carry the same change, as in the rest of the repo.

🤖 Generated with [Claude Code](https://claude.com/claude-code)
