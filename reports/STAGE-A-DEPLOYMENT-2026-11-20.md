# Stage A deployment and installer hardening — 2026-11-20

## Scope

This cycle continued the `implement → test → break → fix → break again` loop after the live VM
validation in `VM_EVOLUTION_VALIDATION.md`. It covers the dedicated `sunshine-update` package,
production trust material, two newly found verifier bugs, and the terminal-tools deployment gaps
listed in the audit notes.

## What broke

### 1. Host GPG configuration bypassed a dedicated keyring

The Rust Stage A verifier and the Python reference verifier both invoked:

    gpg --no-default-keyring --keyring <dedicated-keyring> --verify ...

On a host with GnuPG keyboxd enabled, gpg reported:

    Note: Specified keyrings are ignored due to option "use-keyboxd"
    Can't check signature: No public key

The ephemeral-key regression tests passed because they create a fresh `GNUPGHOME` without that
configuration. A production install using the shipped `repository-root.gpg` failed closed.

**Fix (in both implementations):** run detached verification with `GNUPGHOME` pointing at the
per-invocation temporary directory. The dedicated keyring is then the only trust source. The Python
verifier also now requires a `[GNUPG:] VALIDSIG` line naming the declared fingerprint instead of
ignoring the fingerprint argument; the Rust verifier already did this.

**Proof:** `test-stage-a.sh`, `test-rotation.sh`, 161 Python engine tests and 5 Rust tests pass;
the production NEW-signed index verifies with the shipped keyring on the same host that previously
failed. A full Rust `handoff` produced a signed receipt and Core accepted it.

### 2. Production OLD→NEW rotation cannot be signed in this workspace

`ROTATION.md` requires a rotation record signed by OLD
`8253720323C575207CC781B5DB345EF676CCD13D` before any NEW-signed artifact is published. Only the
NEW private key (`2FEC611A7F97ED9A37294C90D16F3BE763A4B6BE`) is available locally. Self-signing the
rotation or re-pinning NEW in a new policy would break already-installed OLD-root systems.

**Decision:** do not fabricate the chain. The generated production material pins NEW for fresh
installs (`key_rotations: []`, `allow_key_rotation: false`) and documents the blocker. Existing
installs stay on their OLD root until the OLD private key signs the chained record. The regression
proof with ephemeral OLD/NEW keys remains `test-rotation.sh`. Receipt private key custody is also
out of band: `sunshine-update` ships only public material and fails closed if
`/etc/sunshine/trust/receipt-home` does not contain the policy fingerprint.

### 3. Installer used plaintext secret environment values and hid long operations

`sunshine-install` documented `SUNSHINE_PASS` and `SUNSHINE_LUKS_PASS` and piped secrets into
`cryptsetup`/`chpasswd`; it also performed several minute-long steps with no Sunshine UI feedback.
`sunshine-profiles.service` is not involved; the real post-install target is the
`sunshine-post-install` script inside the installed system.

**Fix:** auto-mode secrets now come from `SUNSHINE_PASS_FILE` and `SUNSHINE_LUKS_PASS_FILE`.
The LUKS passphrase is written once to a root-only temporary file used by `cryptsetup` and shredded
by `cleanup`. The user credential file is created mode 0600 and shredded inside the chroot. Long
steps (`copy_system`, Hyprland install, restore points, chroot configuration, kernel densification,
identity apply) now use `sun_run`, so they show the shared animated graph and success logo, and
failures print captured output plus a fix hint. The live-only no-password sudo file is explicitly
documented and remains removed by post-install before first boot.

`bash -n` passes for both installer scripts.

## Published artifacts

- `tak0dan/SunshineOS` branch `Development_Anesthesia`, commit `f0b544d`:
  - `packages/sunshine-update/` — PKGBUILD, vendored canonical engine, Rust bootstrap, signed
    NEW-pinned trust material, polkit action, tmpfiles, wrapper, provisioning script and docs.
  - Installer/post-install hardening described above.
- Built package (release asset candidate, not committed):
  `packages/sunshine-update/sunshine-update-0.9.0-1-x86_64.pkg.tar.zst`.
- This report and the two verifier fixes are published in `SunshineOS_Development-Testing/main`.

## Results

| Check | Result |
|---|---|
| Python engine suite (canonical and vendored) | 161 tests, OK |
| Rust unit tests (canonical and vendored) | 5 tests, OK |
| `test-stage-a.sh` | verify, handoff, Core receipt and tamper rejection OK |
| `test-rotation.sh` | chained rotation, self-signed/untrusted/disabled/unapproved rejection OK |
| Production index verify with shipped keyring | `passed: true`, artifact `core`, generation 1 |
| Production handoff with receipt key | Core accepted receipt; `--check` completed |
| Package build | `sunshine-update 0.9.0-1` built successfully |
| Private key leak scan of package source | no private key material found |
| Installer syntax | `bash -n` OK |

## Next break attempts

1. Repeat Stage A verification on a host whose global GPG config enables keyboxd and confirm the
   empty-`GNUPGHOME` fix still fails closed for a wrong fingerprint.
2. Run the built package in a VM with no receipt key and confirm the wrapper refuses to start.
3. Publish a signed `tak0dan/sunshine-tools` release after the UI commits and verify toolsync in
   the GUI VM; the currently installed signed release predates those commits.
4. Obtain or safely provision the OLD private key to publish the real OLD→NEW rotation, then repeat
   the chain test with the production fingerprints.
