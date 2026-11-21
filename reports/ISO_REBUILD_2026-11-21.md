# SunshineOS ISO rebuild — work record 2026-11-21

## Result

A real image artifact was produced by CI at commit `82082b1`:
`sunshineos-2026.11.21-x86_64.iso`, 1,191,051,264 bytes, SHA-256
`0bd1bd6c8bb692a7b34b8688545fcda7aff7841723e603a38b65dab572ff5e3c`. It passed
structural verification (boot catalog, kernel, identity, checksum manifest). A
BIOS/UEFI boot test and installation test have not been performed, so no boot
claim is made.

The local host still cannot run `mkarchiso` (missing `mkarchiso`, `pacstrap`,
`mksquashfs`, `unsquashfs`, and no passwordless sudo). The build script reports
that explicitly instead of fabricating an image locally.

## Published code

- `iso/tools/sunshine_live.py` — read-first live toolkit: `health`, `sanity`,
  `update`, `upgrade`, `migrate`, `repair`, `rescue`, `report`. Mutating paths require
  root, `--apply`, sanity gates, a snapshot unless explicitly waived, and
  signed Stage A inputs for engine upgrade/migration. All actions are journaled.
- `iso/tools/stage_profile.py` — stages `evolution-engine/` and the toolkit into
  the archiso `airootfs`, generates command wrappers, writes build metadata and
  validates the staged profile.
- `iso/tools/sunshine-live`, `iso/build.sh`, `iso/verify.sh` — dispatcher,
  build entry point and offline ISO verification.
- `iso/profile/sunshine/` — archiso profile: x86_64, BIOS syslinux + UEFI
  systemd-boot, zstd squashfs, `install_dir=sunshine`, 4 GiB CoW, package list,
  mirror/pacman config, mkinitcpio-archiso hooks, SunshineOS identity hook, and
  optional startup assessment service enabled by `sunshine.assess=1`.
- `iso/tests/` — 28 tests covering health/sanity, update previews and gating,
  engine argv binding, assessment-only repair, native Arch rescue evidence,
  captured servicing evidence, staging and profile integrity.
- `iso/README.md` — operator reference and honest build-host limitation.
- `.github/workflows/iso-build.yml` — digest-pinned Arch container build path that
  uploads the ISO plus SHA-256 manifest as a CI artifact.

Two runtime defects found during review were fixed before publication:
`sunshine-report` now reuses the repair assessment without requiring repair-only
arguments, and `migrate --source arch --apply` checks Arch identity instead of
incorrectly demanding SunshineOS identity.

## Verification actually run

- 28 ISO toolkit tests: OK.
- 325 evolution-engine regression tests: OK.
- `shellcheck` on build scripts, dispatcher, profiledef and generated wrappers: clean.
- `./iso/build.sh --check`: staged profile validated; no missing files; profiledef syntax OK.
- CI trust-policy audit: `NO_DETECTED_POLICY_FINDINGS` across 6 workflows.
- Real engine smoke test: `sunshine-live --fixture clean-arch upgrade` returned an
  actual plan with engine rc 0.
- CI run `44900167130`: build, verification, artifact upload and policy audit all
  passed; artifact details are in `reports/ISO_ARTIFACT_2026-11-21.md`.

## Next required action

Boot the CI artifact in BIOS and UEFI, install it to a scratch VM/disk, and run
the live toolkit plus an end-to-end update/migration check there. On a local Arch
build host with `archiso`, `squashfs-tools`, `mtools` and `xorriso`, the same
script re-runs tests, stages the profile, calls `mkarchiso`, verifies the ISO with
`iso/verify.sh`, and writes `iso/out/manifest.sha256`.
