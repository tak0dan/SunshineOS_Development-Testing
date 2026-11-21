# SunshineOS image artifact — 2026-11-21

## CI result

The final image build workflow completed successfully on commit
`b8488fba4509fef29f459b6805880507c0377189`.

- Workflow: `SunshineOS image build` (`iso-build.yml`)
- Run: `44937532208`
- Artifact: `sunshineos-iso`
- Image: `sunshineos-2026.11.21-x86_64.iso`
- Size: `1,191,051,264` bytes
- SHA-256: `bf6f16279b8c89022d267f3c9fe1d21775db0d1e13f69a3e14e2450bac3ae035`

Earlier runs in this work record (`44900167130`, `44904585231`,
`44919024957`, `44919344366`, `44921770515`, `44925165261`) are superseded. The
hash above is the only one that corresponds to the current published source tree.

## Build-time verification

The workflow ran:

- 34 ISO toolkit tests: OK
- 339 evolution-engine regression tests: OK
- `shellcheck` on build scripts, dispatcher, profiledef and generated wrappers: clean
- `python3 autonomy/codex/ci_policy_audit.py .`: `NO_DETECTED_POLICY_FINDINGS` across 6 workflows
- `iso/verify.sh` on the produced image: boot catalog, kernel, publisher/application identity: OK

## Artifact-level verification

The downloaded artifact was verified independently of CI:

- `manifest.sha256`: `sha256sum -c` OK
- `iso/verify.sh` on the downloaded image: all checks OK
- `airootfs.sha512` after extracting `airootfs.sfs` from the image: OK
  (`0c6423d52e908108eeb19719c7938ae9427675cd1562b49d37d95268d311098cfa9a7c23db5a130b43e222a7f0795155890729e8ed356987ab4fd09bb4edac55`)
- build identity is recorded in `/etc/sunshine/build-id` as `20261121T184901Z`;
  the CI log records `source_commit=b8488fba4509fef29f459b6805880507c0377189`.
  This artifact does not contain a `BUILD_INFO.json`, so no such file is claimed.
- staged files present: `sunshine_live.py`, `engine.py`, `src/target/__init__.py`,
  `arch_rescue.py`, `native-arch-rescue-wave1.json`, startup assessment service,
  `usr/local/bin/sunshine-*`, `/etc/hostname`, `/etc/issue`, and the tty1 autologin drop-in
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
- staged rescue suite: 7 `test_arch_rescue.py` tests OK
- staged first-class `--rescue` CLI suite: 10 tests OK
- staged automatic-migration suite: 4 tests OK

The full engine suite from the source tree is 339 tests OK. Running the same
suite from the extracted artifact reports 4 environment-only failures because
`.github/workflows/steamos-regressions.yml` and the research source corpus are
intentionally not staged into the image; those files are build/repository inputs,
not live-image runtime files. No functional engine failure was found.

## Booted-toolkit verification

The rebuilt ISO was attached as a DVD to the VirtualBox GUI VM `SunshineOS-Audit`
and booted through its own bootloader. Both the GUI console (tty1) and the serial
console (ttyS0) reached an automatic root session:

- `SunshineOS Live Repair and Migration` / `hostname=sunshineos`
- `sunshineos login: root (automatic login)` on tty1 and ttyS0
- no password prompt and no unknown-credential request
- SunshineOS MOTD lists the read-first commands and the automatic `sunshine-update`
  operation

Commands run through the live serial shell:

| Command | Result |
|---|---|
| `cat /etc/issue` | `SunshineOS Live Repair and Migration` |
| `sunshine-update` | 0 (`PREVIEW`, report `update-20261121T194226Z.json`, no mutation) |
| `sunshine-rescue --reboot-state settled` | 1 (`BLOCKED`, fail-closed on live-root evidence) |
| `sunshine-health --deep` | 0 (`WARN`, expected live-root package/snapper observations) |

The `sunshine-update` report records `migration_mode: automatic` and `status: preview`.
Its engine step exits 3 in the live image because Stage A trust inputs are absent;
this is the expected fail-closed behavior, not a migration execution. No `--apply`
was run in the live environment.

A predecessor artifact was separately verified in QEMU with KVM through both BIOS
and UEFI boot to an automatic serial root shell with all eight `sunshine-*`
commands present. That result is retained as historical evidence and is not
treated as a boot test of the rebuilt hash above.

This is boot and booted-toolkit verification, not an installation test. No scratch
disk install or installed-system end-to-end update/migration was performed, so no
install claim is made.
