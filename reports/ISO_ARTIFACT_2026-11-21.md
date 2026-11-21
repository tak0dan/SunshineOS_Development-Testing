# SunshineOS image artifact — 2026-11-21

## CI result

The final image build workflow completed successfully on commit
`3e4257bae9c018e960a843cfb1109402a3b7640b`.

- Workflow: `SunshineOS image build` (`iso-build.yml`)
- Run: `44925165261`
- Artifact: `sunshineos-iso`
- Image: `sunshineos-2026.11.21-x86_64.iso`
- Size: `1,191,051,264` bytes
- SHA-256: `d1a8e54dc7b00db2295a985a24275e2077386c5ea96488277448fbb936e8d79c`

Earlier runs in this work record (`44900167130`, `44904585231`,
`44919024957`, `44919344366`, `44921770515`) are superseded. The hash above is
the only one that corresponds to the published source tree.

## Build-time verification

The workflow ran:

- 30 ISO toolkit tests: OK
- 325 evolution-engine regression tests: OK
- `shellcheck` on build scripts, dispatcher, profiledef and generated wrappers: clean
- `python3 autonomy/codex/ci_policy_audit.py .`: `NO_DETECTED_POLICY_FINDINGS` across 6 workflows
- `iso/verify.sh` on the produced image: boot catalog, kernel, publisher/application identity: OK

## Artifact-level verification

The downloaded artifact was verified independently of CI:

- `manifest.sha256`: `sha256sum -c` OK
- `iso/verify.sh` on the downloaded image: all checks OK
- `airootfs.sha512` after extracting `airootfs.sfs` from the image: OK
- `BUILD_INFO.json`: `source_commit` is the published commit; commands include all
  eight wrappers, including `sunshine-rescue`
- staged files present: `sunshine_live.py`, `engine.py`, `src/target/__init__.py`,
  `arch_rescue.py`, `native-arch-rescue-wave1.json`, startup assessment service,
  and `usr/local/bin/sunshine-*`
- generated BIOS and UEFI boot entries contain `systemd.firstboot=no` and
  `console=tty0 console=ttyS0,115200n8`
- staged `sunshine_live.py` uses snapper's supported `-t single` type for listing
  and creating snapshots

The staged toolkit was exercised directly from the extracted image with captured
read-only probes:

- `health`, `sanity`, `update` preview, `repair` assessment and `report`: OK, no mutation
- `rescue`: healthy classification with exact Arch-native argv; no `rm`, `systemctl`
  or package-install command was issued
- `repair --apply --fix-lock`: blocked with no `db.lck` deletion
- `report`: embeds the Arch-native rescue assessment
- `upgrade`, `migrate --source arch`, `migrate --source sunshine`: engine plan rc 0
- staged `test_arch_rescue.py`: 7 tests OK

## Booted-toolkit verification

The ISO was booted through its own bootloader in QEMU with KVM.

- BIOS: reached an automatic root shell on `ttyS0`; all eight `sunshine-*`
  commands were executed.
- UEFI: reached an automatic root shell on `ttyS0` using OVMF firmware.
- Exit codes in the booted BIOS run:

| Command | Result |
|---|---|
| `sunshine-health --deep` | 0 (`WARN`, expected live-root package/snapper observations) |
| `sunshine-sanity --require-snapshot` | 1 (fail: snapper `root` config is not configured in the live image) |
| `sunshine-update` | 0 (`PREVIEW`, no mutation) |
| `sunshine-upgrade --fixture clean-arch` | 0 (`PASS`, engine rc 0) |
| `sunshine-migrate --fixture old-sunshine --source sunshine` | 0 (`PASS`, engine rc 0) |
| `sunshine-repair` | 0 (`ASSESSMENT`, no mutation) |
| `sunshine-rescue --reboot-state settled` | 1 (`BLOCKED`, fail-closed on live-root evidence) |
| `sunshine-report` | 0 (`WARN`) |

This is boot and booted-toolkit verification, not an installation test. No scratch
disk install or installed-system end-to-end update/migration was performed, so no
install claim is made.
