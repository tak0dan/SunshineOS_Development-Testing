# SunshineOS ISO rebuild

This directory builds a SunshineOS live image whose maintenance toolkit is the
same fail-closed engine used by the migration/repair work. The image is a
read-first rescue and migration environment: nothing is changed unless an
operator explicitly passes `--apply`, and signed/rollback prerequisites are
checked before mutation.

## What is in the image

- `sunshine-health` — read-only facts: OS identity, kernel, mounts, disk,
  memory, load, GPU activity, package count, clock, snapshots and package
  integrity (with `--deep`).
- `sunshine-sanity` — preflight gates: writable root, free space, `/boot`,
  pacman availability, package locks, running transactions, clock sync,
  snapshot capability, optional OS identity and Stage A trust files.
- `sunshine-update` — package update. Preview is read-only; `--apply` runs
  sanity, creates a snapshot, journals the transaction, runs `pacman -Syu`,
  and re-checks health.
- `sunshine-upgrade` — target-state convergence through the evolution engine.
  Preview uses `--plan`; `--apply` requires signed Stage A inputs, a rollback
  checkpoint, then engine apply and optional `--verify`.
- `sunshine-migrate` — source qualification (`auto`, `arch`, `sunshine`),
  engine check, plan/apply, and optional verification. It refuses a source
  profile that contradicts observed `os-release`.
- `sunshine-repair` — assessment-only by default: package health, stale locks,
  missing-file packages, SteamOS read-only/developer-mode consistency, captured
  Windows servicing evidence, and A/B slot activation evidence. Explicit
  `--fix-lock` / `--reinstall-missing` repairs require `--apply`.
- `sunshine-report` — combined health, sanity and repair assessment.

Every command accepts `--json`, `--out PATH`, `--root PATH`, and Stage A
options after the subcommand as well as before it. Reports are written under
`/var/log/sunshine/reports`; mutations append to
`/var/log/sunshine/journal.jsonl`.

## Safety model

1. Read-only by default. `--apply` is mandatory for mutation.
2. Root is mandatory for mutation.
3. A rollback snapshot is mandatory unless `--allow-no-snapshot` is explicit.
4. Engine upgrade/migration require signed Stage A index, policy and keyring.
5. Missing, stale or contradictory evidence produces `fail`/`blocked`, never a
   guessed success.
6. The assessment modules from the evolution engine are reused directly; they
   do not remount, rewrite slots or invoke repair operations on their own.

## Build

On an Arch-based build host with `archiso`, `squashfs-tools` and `xorriso`:

```sh
sudo pacman -S archiso squashfs-tools xorriso
./iso/build.sh              # tests, stage, mkarchiso, verify, sha256 manifest
./iso/build.sh --check      # stage and validate without requiring root/deps
./iso/build.sh --skip-tests # not recommended
```

`build.sh` stages `evolution-engine/` and `iso/tools/` into
`iso/.staged-profile/airootfs/`, generates the command wrappers, writes build
metadata, runs mkarchiso, verifies the result with `iso/verify.sh`, and records
`iso/out/manifest.sha256`.

The checked-in profile is at `iso/profile/sunshine/`. It uses
`bios.syslinux` + `uefi.systemd-boot`, `install_dir=sunshine`, zstd squashfs,
and a 4 GiB copy-on-write limit. `sunshine.assess=1` on the kernel command line
enables the optional startup assessment service.

The migration engine and live toolkit are staged directly from this repository
into `airootfs`, so building the image does not depend on a separately published
SunshineOS package repository being available on the build host.

## Continuous integration

`.github/workflows/iso-build.yml` runs the same build in a digest-pinned Arch
Linux container on `workflow_dispatch` and on pushes to `development` that
touch `iso/**`, `evolution-engine/**` or the workflow itself. The resulting ISO
and `manifest.sha256` are uploaded as the `sunshineos-iso` artifact. This is the
path that can produce a real image without local root access.

## Current host limitation

The host used to prepare this rebuild is Garuda Linux with `pacman`, `xorriso`,
`grub-mkimage`, `btrfs`, `snapper` and `shellcheck` available, but without
`mkarchiso`, `pacstrap`, `mksquashfs`, `unsquashfs` or passwordless sudo.
Therefore `./iso/build.sh --check` and all tests can be executed here; the
final `mkarchiso` stage cannot. The build script fails with an explicit tool
list rather than pretending an ISO was produced.

## Verification already run

- `python3 -m unittest discover -s iso/tests -p 'test_*.py' -v` — 18 tests OK.
- `python3 -m unittest discover -s evolution-engine/tests -p 'test_*.py' -v` — 317 tests OK.
- `shellcheck iso/build.sh iso/verify.sh iso/tools/sunshine-live iso/profile/sunshine/profiledef.sh`
- `./iso/build.sh --check` — staged profile validated, no missing files, profiledef syntax OK.
- Engine smoke test: `sunshine-live --fixture clean-arch upgrade` returned a real plan (rc 0).
