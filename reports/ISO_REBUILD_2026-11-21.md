# SunshineOS ISO rebuild — work record 2026-11-21

## Result

A real image artifact was produced by CI at commit
`b8488fba4509fef29f459b6805880507c0377189`:
`sunshineos-2026.11.21-x86_64.iso`, 1,191,051,264 bytes, SHA-256
`bf6f16279b8c89022d267f3c9fe1d21775db0d1e13f69a3e14e2450bac3ae035`. It passed
structural verification, artifact-level staged-toolkit checks, and a VirtualBox
GUI/serial boot to an automatic root shell with SunshineOS identity. No
installation test has been performed, so no install claim is made. Details are in
`reports/ISO_ARTIFACT_2026-11-21.md`.

The local host still cannot run `mkarchiso` (missing `mkarchiso`, `pacstrap`,
`mksquashfs`, `unsquashfs`, and no passwordless sudo). The build script reports
that explicitly instead of fabricating an image locally.

## Published code

- `iso/tools/sunshine_live.py` — read-first live toolkit: `health`, `sanity`,
  `update`, `upgrade`, `migrate`, `repair`, `rescue`, `report`. `update` now includes
  automatic Arch-family migration planning; standalone `migrate` is reserved for
  edge cases. Mutating paths require root, `--apply`, sanity gates, a snapshot
  unless explicitly waived, and signed Stage A inputs for engine upgrade/migration.
  All actions are journaled.
- `evolution-engine/src/evolution/updater.py` — deterministic `plan_automatic_migration()`
  records the B-1 Arch 2015 → M → B0 Arch 2026 → target lineage, base/kernel/packages
  scope, and broken-upgrade recovery inputs. It never mutates state or deletes locks.
- `evolution-engine/src/engine.py` — first-class read-only `--rescue` mode using
  captured evidence; missing or invalid evidence fails closed.
- `iso/tools/stage_profile.py` — stages `evolution-engine/` and the toolkit into
  the archiso `airootfs`, generates command wrappers, writes build metadata and
  validates the staged profile.
- `iso/tools/sunshine-live`, `iso/build.sh`, `iso/verify.sh` — dispatcher,
  build entry point and offline ISO verification.
- `iso/profile/sunshine/` — archiso profile: x86_64, BIOS syslinux + UEFI
  systemd-boot, zstd squashfs, `install_dir=sunshine`, 4 GiB CoW, package list,
  mirror/pacman config, mkinitcpio-archiso hooks, SunshineOS identity hook, and
  optional startup assessment service enabled by `sunshine.assess=1`.
- Live console identity: `/etc/hostname=sunshineos`, SunshineOS `/etc/issue`,
  SunshineOS MOTD, and a tty1 root autologin drop-in. No live login credentials
  are required.
- `iso/tests/` — 34 tests covering health/sanity, update previews and gating,
  automatic evolution migration, engine argv binding, assessment-only repair,
  native Arch rescue evidence, captured servicing evidence, staging, profile
  integrity, and live console identity/autologin.
- `iso/README.md` — operator reference and honest build-host limitation.
- `.github/workflows/iso-build.yml` — digest-pinned Arch container build path that
  uploads the ISO plus SHA-256 manifest as a CI artifact.

Two runtime defects found during earlier review were fixed before publication:
`sunshine-report` now reuses the repair assessment without requiring repair-only
arguments, and `migrate --source arch --apply` checks Arch identity instead of
incorrectly demanding SunshineOS identity.

## Verification actually run

- 34 ISO toolkit tests: OK.
- 339 evolution-engine regression tests: OK.
- `shellcheck` on build scripts, dispatcher, profiledef and generated wrappers: clean.
- `./iso/build.sh --check --skip-tests`: staged profile validated; no missing files;
  `profiledef.sh` syntax OK.
- CI trust-policy audit: `NO_DETECTED_POLICY_FINDINGS` across 6 workflows.
- CI run `44937532208`: 34 ISO tests, 339 engine tests, build, verification,
  artifact upload and policy audit all passed.
- Artifact checks: manifest SHA-256, `iso/verify.sh`, squashfs SHA-512, staged
  identity/autologin files, literal boot parameters, and read-only toolkit probes OK.
- Artifact-focused tests: 7 native rescue, 10 first-class rescue CLI, and 4
  automatic-migration tests OK.
- VirtualBox GUI/serial boot: root autologin on tty1 and ttyS0 with
  `hostname=sunshineos`, SunshineOS issue/MOTD, no password prompt.
- Booted commands: `sunshine-update` preview rc 0 (no mutation),
  `sunshine-rescue --reboot-state settled` rc 1 (fail-closed),
  `sunshine-health --deep` rc 0 with expected live-root warnings.

## Remaining validation

- Install the artifact to a scratch VM/disk.
- Run the live toolkit and an end-to-end update/migration check on the installed
  system with configured snapshots, trusted inputs and explicit `--apply`.
- Verify coupled bootable-snapshot restore health, RAUC-style boot-success gates,
  snapper retention/watchdog evidence, and Obarun 66 capability checks on real
  target systems.
- On a local Arch build host with `archiso`, `squashfs-tools`, `mtools` and
  `xorriso`, the same script re-runs tests, stages the profile, calls `mkarchiso`,
  verifies the ISO with `iso/verify.sh`, and writes `iso/out/manifest.sha256`.
