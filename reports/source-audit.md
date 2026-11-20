# SunshineOS source audit

**Scope:** read-only audit of the local clone at `/home/tak_0/sunshineos-audit/SunshineOS`, git HEAD `85506eae4d766faceb22e6b07886c3b983f96662` (2026-11-20). The companion website/download worker is out of scope for this pass.

**Method:** manual reading of the build scripts, `profile/airootfs`, `overlay/system`, `overlay/sirius`, packages, catalogue, Calamares configs, tests and tools; targeted greps for credentials, dangerous primitives, dangling references and privilege transitions; `bash -n` on all shipped shell scripts and `python3 -m compileall` for Python scripts; verification of the live-user password hash with `openssl passwd -6`; inspection of the shipped `sunshine-base` package contents. Line numbers refer to this HEAD and the working tree was clean at audit time. No repository files were changed and no commit or push was made.

---

## Executive summary

SunshineOS has a lot of thoughtful safety engineering: the installer/post-install path strips the live-only SSH/sudo/autologin configuration, the tool updater verifies a signed manifest plus per-file hashes with an allow-list and rollback, the update tool holds the running live kernel, and the support collector redacts personal data. The code is also syntactically clean: no genuine Bash syntax errors were found and Python bytecode compilation succeeds.

The main risks are concentrated in four areas:

1. **The live ISO is effectively a public root shell.** A published password, passwordless `wheel` sudo, SSH password/root login, GUI and tty1 autologin, and the `script=` cmdline hook all combine into a very large live-session attack surface.
2. **The build chain is privileged and not reproducible.** A `--privileged` Docker build consumes AUR git heads, `--skippgpcheck`, `SKIP` checksums and mutable vendor dots. An upstream compromise becomes a build-host and shipped-image compromise.
3. **Cryptographic trust anchors are inconsistent or overridable.** The 2026-11-20 tools-key rotation updated `sunshine.gpg` but left `sunshine-trusted` on the old fingerprint; Chaotic-AUR keys are bootstrapped from a CDN/keyserver with no pinned fingerprint; both the tools updater and repo helper accept URL/key overrides from the environment of a root process.
4. **Several repair/install paths can make things worse.** Broad `--overwrite '*'`, copying a `.pacnew` sudoers file over a working one, a keyfile baked into the initramfs, and a few architecture/config mismatches can break a system or weaken encryption.

**Severity distribution: 2 Critical, 4 High, 7 Medium, 6 Low (19 findings total).**

### Top 5

1. **[CRITICAL] Live ISO ships a known root-equivalent login** — `shadow:1-2`, `motd:4`, `sudoers.d/10-live:1`, `sshd_config.d/10-archiso.conf:1-3`.
2. **[CRITICAL] Privileged, unpinned build pipeline** — `build.sh:17-19`, `build-aur.sh:31,33`, `Dockerfile:1-3`.
3. **[HIGH] Rotated tools signing key but stale `sunshine-trusted`** — `sunshine-trusted:1`, `sunshine.gpg`, `pacman.conf:85-87`.
4. **[HIGH] Chaotic-AUR key bootstrapped without a pinned fingerprint** — `sunshine-repo:32-47`, `repos.conf:3`, `tools/fetch-chaotic.sh:6-12`.
5. **[HIGH] LUKS keyfile embedded in initramfs and GRUB cmdline** — `sunshine-crypt-setup:5-11`, `sunshine-install:234-235,289,331-332`.

---

## Findings

### [CRITICAL] Live ISO ships a known root-equivalent login

- **File:** `profile/airootfs/etc/shadow:1-2`; `profile/airootfs/etc/motd:4`; `profile/airootfs/etc/group:4`; `profile/airootfs/etc/sudoers.d/10-live:1`; `profile/airootfs/etc/ssh/sshd_config.d/10-archiso.conf:1-3`; `profile/airootfs/etc/systemd/system/multi-user.target.wants/sshd.service`; `profile/airootfs/etc/sddm.conf.d/autologin.conf:2-3`; `profile/airootfs/etc/systemd/system/getty@tty1.service.d/autologin.conf:3`; `profile/airootfs/root/.automated_script.sh:5-37`.
- **What:** `root` has an empty shadow field; the `sunshine` hash was verified to be the literal password `sunshine` and is printed in `/etc/motd`. That account is in `wheel`, and `10-live` grants `wheel` passwordless sudo. sshd is enabled and configured with `PasswordAuthentication yes` and `PermitRootLogin yes`. SDDM autologins `sunshine`, tty1 autologins `root`, and the root login runs `/root/.automated_script.sh`, which fetches and executes a `script=` kernel-cmdline URL/path as root.
- **Why it matters:** Anyone on the same network as a live session can SSH in as `sunshine`, become root with `sudo -i`, and tamper with the installer, target disks or generated installed system. Physical access is equally trivial via the root autologin console. The `script=` hook additionally turns a boot parameter into arbitrary root code execution. Installed systems are cleaned up, but the live medium is what users actually boot while installing.
- **Suggestion:** Do not enable sshd in the live image by default; enable it only through an explicit boot parameter or user-run helper. If remote live repair is needed, generate a random per-boot password or require an SSH key, bind to loopback if possible, and drop `PermitRootLogin yes`. Replace the fixed hash with per-boot credentials, remove the tty1 root autologin, and gate `script=` behind an explicit opt-in Boot Parameter.

### [CRITICAL] Privileged, unpinned build pipeline consumes unverified third-party code

- **File:** `build.sh:17-19`; `Dockerfile:1-3`; `build-aur.sh:22,24-25,31,33`; `pkgs/illogical-impulse-bibata-modern-classic-bin/PKGBUILD:13`; `pkgs/sunshine-icon-theme/PKGBUILD:14`; `pkgs/uni-pkg-git/PKGBUILD:13`; `tools/import-end4.sh:8,13-21`; `make-iso.sh:81-84`.
- **What:** `build.sh` runs `docker run --privileged` with host directories bind-mounted. The builder is `FROM archlinux:latest` with no digest or package lock. AUR packages are cloned from mutable git heads and built with `makepkg --skippgpcheck`; several local PKGBUILDs use `sha256sums=('SKIP')`. The Sunshine dots repo is pulled at its current branch head (`git pull ... || true`) and its patch is applied without signature verification. `build-aur.sh` also creates a builder user with `NOPASSWD: ALL` and a local repo with `Optional TrustAll`.
- **Why it matters:** `--privileged` gives the container near-host-root capabilities. A compromised AUR source, git branch or patch can execute code as root inside the build container and therefore reach the build host or the shipped ISO. Even without a container escape, released images are not reproducible: upstream bytes can change without any SunshineOS commit changing.
- **Suggestion:** Remove `--privileged` or build in a disposable VM with minimal capabilities. Pin the base image by digest, pin every git source to a reviewed commit, record checksums instead of `SKIP`, and stop using `--skippgpcheck`. Replace blanket builder `NOPASSWD: ALL` with constrained rules, mirror critical upstream sources, and publish an SBOM/attestation.

### [HIGH] Rotated tools signing key but stale `sunshine-trusted`

- **File:** `profile/airootfs/usr/share/pacman/keyrings/sunshine.gpg` (binary; current fingerprint `2FEC611A7F97ED9A37294C90D16F3BE763A4B6BE`); `profile/airootfs/usr/share/pacman/keyrings/sunshine-trusted:1`; `overlay/system/usr/share/pacman/keyrings/sunshine-trusted:1`; `profile/airootfs/etc/pacman.conf:85-87`; `profile/airootfs/usr/local/bin/sunshine-toolsync:14,21-25`.
- **What:** HEAD `85506ea` rotates `sunshine.gpg` to a new RSA-4096 key created 2026-11-20, but both `sunshine-trusted` files still contain only the old fingerprint `8253720323C575207CC781B5DB345EF676CCD13D:4`. `sunshine-toolsync` imports `sunshine.gpg` directly for tool manifests, while pacman uses the keyring/trust files for the `[sunshine]` repository with `PackageRequired`.
- **Why it matters:** The repository can reject packages signed by the new key as "unknown trust" or "required key not available", and tools/repo signatures no longer share a single trust anchor. A key rotation that updates only half of the keyring is likely to break updates or encourage someone to weaken `SigLevel` as a workaround.
- **Suggestion:** Update both `sunshine-trusted` files to the new fingerprint in the same commit as the keyring, remove or explicitly retire the old key, and add a build-time check that every fingerprint in `sunshine.gpg` has the intended trust entry. Add a VM smoke test that runs `pacman -Sy` and `sunshine-toolsync verify` against a newly signed release.

### [HIGH] Chaotic-AUR key bootstrapped from CDN/keyserver with no pinned fingerprint

- **File:** `overlay/system/etc/sunshine/repos.conf:3`; `profile/airootfs/usr/local/bin/sunshine-repo:32-47`; `tools/fetch-chaotic.sh:6-12`; `profile/airootfs/usr/local/bin/sunshine-fix-pacman:38-40`.
- **What:** `chaotic=on` by default. When the Chaotic keyring/mirrorlist is missing, `sunshine-repo` falls back to `pacman-key --recv-key 3056513887B78AEB --keyserver keyserver.ubuntu.com`, locally signs it, and installs keyring/mirror packages from a bare CDN URL. `fetch-chaotic.sh` downloads the same bootstrap packages from the CDN into the build repo with no detached signature check. There is no out-of-band full-fingerprint comparison before trusting the key.
- **Why it matters:** This is trust-on-first-use for a key that then authenticates a large third-party package repository. A compromised keyserver response, CDN or DNS path can substitute a keyring and then substitute arbitrary "signed" packages at build time or on a user's first update.
- **Suggestion:** Ship the Chaotic keyring and mirrorlist with pinned full fingerprints and checked SHA-256 values; verify detached signatures on the bootstrap packages; never blindly `lsign-key` a short key ID fetched at runtime. Offer a documented `chaotic=off` path and make the fingerprint check fail closed.

### [HIGH] Root scripts accept URL/key overrides from the environment

- **File:** `profile/airootfs/usr/local/bin/sunshine-toolsync:10,13-14,38-45,52-63`; `profile/airootfs/usr/local/bin/sunshine-repo:8-9`.
- **What:** Both root-running helpers take their trust anchors from environment variables: `SUNSHINE_TOOLS_URL`, `SUNSHINE_TOOLS_KEY`, `SUNSHINE_REPO_URL`, `SUNSHINE_PACMAN_CONF`. All manifest verification, checksum enforcement and file installation in `sunshine-toolsync` derive from those two variables. The signature verification itself is well implemented, but it verifies against whatever key and URL the caller supplied.
- **Why it matters:** Any context that can set a root process environment — a service unit, a wrapper, a compromised admin workflow or `sudo -E` with a permissive policy — can redirect "signed" tool updates to an attacker URL and key, then overwrite root-owned scripts under `/usr/local/bin`. In the live ISO the barrier is especially low because `wheel` has passwordless sudo.
- **Suggestion:** Use compile-time constants or a root-owned config file at a fixed path for these values in shipped images. Reject the override variables unless an explicit development flag is set, log the source URL and key fingerprint on every update, and add a regression test that refuses overrides in release builds.

### [HIGH] LUKS keyfile is baked into the initramfs and exposed via GRUB

- **File:** `profile/airootfs/usr/local/bin/sunshine-crypt-setup:5-11`; `profile/airootfs/usr/local/bin/sunshine-install:234-235,289,331-332`; `profile/airootfs/etc/calamares/modules/partition.conf:11,15`.
- **What:** Encrypted installs create `/crypto_keyfile.bin`, set mode `000`, add it to `FILES=(...)` in the mkinitcpio config, and append `GRUB_ENABLE_CRYPTODISK=y` plus `cryptkey=rootfs:/crypto_keyfile.bin` to GRUB. Calamares is configured for LUKS1 ("GRUB can only unlock LUKS1").
- **Why it matters:** Putting the keyslot key inside the initramfs means anyone who can read `/boot` can unpack the initramfs, extract the key and decrypt the root filesystem offline. Mode `000` and a root-only initramfs do not protect against someone who boots another OS or mounts the EFI/boot partition. The design avoids a second passphrase prompt but largely defeats the benefit of encryption against physical disk/boot-partition access.
- **Suggestion:** Prefer GRUB-only unlocking without placing the key in the initramfs, or use TPM2/systemd-cryptenroll with a recovery key. If a keyfile in initramfs is retained for usability, document the threat-model trade-off explicitly and keep the initramfs on an encrypted or otherwise protected boot path.

### [MEDIUM] Broad `--overwrite '*'` when registering or repairing `sunshine-base`

- **File:** `profile/airootfs/usr/local/bin/sunshine-apps:48-50`; `profile/airootfs/usr/local/bin/sunshine-doctor:62-63`; `profile/airootfs/usr/share/sunshine/pkgs/sunshine-base-0.8-1-any.pkg.tar.zst`.
- **What:** If `sunshine-base` is not registered with pacman, `sunshine-apps install` runs `pacman -S --noconfirm --needed --overwrite '*' sunshine-base`. `sunshine-doctor --fix` does the same when `sunshine-base` is among the missing core packages. The shipped package contains `/etc/sunshine/repos.conf`, `snapshots.conf`, `tools.conf` and many root-owned tools.
- **Why it matters:** `--overwrite '*'` tells pacman to replace any conflicting file, not just the known Sunshine paths. Local edits to `/etc/sunshine/*.conf` can be silently replaced, and an unrelated package owning a colliding filename could have its file stolen by `sunshine-base`. This runs automatically during catalogue app installs and during the repair path.
- **Suggestion:** Enumerate the exact shipped file globs and pass only those to `--overwrite`; otherwise check conflicts with `pacman -Qo` and fail with a clear error. Preserve user-edited configs by comparing checksums or moving them to `.sunshine-old` before reinstalling.

### [MEDIUM] Installer allows one-character passwords and handles secrets via environment/plaintext file

- **File:** `profile/airootfs/etc/calamares/modules/users.conf:6,10-14`; `profile/airootfs/usr/local/bin/sunshine-install:4-5,91,324-327`.
- **What:** Calamares sets `setRootPassword: false`, `minLength: 1`, `allowWeakPasswords: true`, `allowWeakPasswordsDefault: true`. The text installer accepts `SUNSHINE_PASS` from the environment, writes `USERNAME:PASS` to `/root/.sunshine-cred`, feeds it to `chpasswd`, then uses `shred -u`.
- **Why it matters:** Users can create the administrator account with a one-character password through the GUI. In automated installs the password is exposed in the environment and briefly on disk; `shred` is not reliable on CoW/SSD filesystems. Root stays locked, which is good, but the created user is in `wheel`, so the weak password is effectively the admin password.
- **Suggestion:** Require a reasonable minimum length and disable weak-password defaults, or require an explicit "I understand" override. Pass secrets over a pipe/FD or a tmpfs file with strict permissions instead of the environment, and avoid relying on `shred` for erasure.

### [MEDIUM] `profiledef.sh` contains a dangling tool entry and over-broad permission normalization

- **File:** `profile/profiledef.sh:40,45-51`; `profile/airootfs/usr/share/plasma/look-and-feel/com.sunshineos.sunshine/contents/splash/images/background.jpg`.
- **What:** `file_permissions` includes `/usr/local/bin/sunshine-firstlogin`, but no such file exists in `profile/airootfs`, `overlay/system`, the Sirius overlay or the shipped `sunshine-base` package. A later loop sets every executable airootfs file to `0:0:755`; the shipped splash `background.jpg` itself has mode 755 and is therefore made executable in the image.
- **Why it matters:** The dangling entry is either ignored or fatal depending on the `mkarchiso` version, so builds are version-sensitive and the stale intent is misleading. Marking an image file executable is harmless functionally but shows that the normalization trusts source modes instead of file type; a stray executable bit on shipped content is easy to miss.
- **Suggestion:** Remove the `sunshine-firstlogin` entry or add the missing tool if it is still intended. Fix the source mode of `background.jpg` to 644 and keep the permission loop, but log or fail on stale `file_permissions` paths during build.

### [MEDIUM] Calamares installer is hardcoded to x86_64 despite aarch64 profile support

- **File:** `profile/airootfs/etc/calamares/modules/unpackfs.conf:3`; `profile/profiledef.sh:16`; `profile/packages.aarch64:1-118`; `profile/airootfs/usr/local/bin/sunshine-doctor:57,125`.
- **What:** `unpackfs.conf` hardcodes `/run/archiso/bootmnt/arch/x86_64/airootfs.sfs`. The repository also ships `packages.aarch64`, an aarch64 kernel parameter line and aarch64 image compression, but that package list has no `plasma-desktop`, `sddm`, `calamares`, `python-pillow` or `python-numpy`. `sunshine-doctor` separately hardcodes `grub-install --target=x86_64-efi` for the EFI fallback repair.
- **Why it matters:** A Calamares install from an aarch64 ISO would look for the wrong squashfs path and fail before unpacking. The doctor would also report the desktop packages as missing and attempt an x86_64 EFI install on an ARM system. Either aarch64 is unsupported and should be removed from the build/profile, or these paths and package expectations need to be architecture-aware.
- **Suggestion:** Derive the unpackfs source from the running archiso architecture instead of hardcoding `x86_64`; select `grub-install --target=$(...)` based on `uname -m`; and either complete the aarch64 desktop package set or document that aarch64 images are rescue-only and skip Calamares/desktop checks there.

### [MEDIUM] `sunshine-doctor --fix` can replace a working sudoers file from `.pacnew`

- **File:** `profile/airootfs/usr/local/bin/sunshine-doctor:214-220`.
- **What:** When `visudo -c` fails, the repair loop renames invalid files under `/etc/sudoers.d` to `.broken`. If validation still fails and `/etc/sudoers.pacnew` exists, it copies the current sudoers to `sudoers.broken` and copies the `.pacnew` over `/etc/sudoers`.
- **Why it matters:** A `.pacnew` can be an upstream default that removes local rules or contains configuration the administrator has not reviewed. Automatically promoting it during a repair can lock the administrator out of sudo or silently change privilege policy, with only a `.broken` backup.
- **Suggestion:** Never install a `.pacnew` sudoers file unattended. Leave it for `sunshine-pacnew review` or `visudo -c -f /etc/sudoers.pacnew`, print the diff, and require an explicit confirmation. Keep the rename of syntactically invalid drop-ins as a separate, clearly logged step.

### [MEDIUM] Build orchestrator mutates tracked PKGBUILDs and tolerates critical copy failures

- **File:** `make-iso.sh:10,31-44,81-84`.
- **What:** The top-level build script uses `set -uo pipefail` without `-e`. `resolve_dead_deps()` runs `sed -i` directly on `pkgs/*/PKGBUILD` when a dependency disappears. The overlay sync into `profile/airootfs` uses `cp -a` and `rm -rf` without checking failure, yet later steps depend on the result.
- **Why it matters:** A build can silently modify the source checkout, so the ISO contents no longer match the committed state; a failed copy can still produce an image missing fixes. This undermines reproducibility and makes bug reports hard to trust.
- **Suggestion:** Work on a temporary copy of `profile/`, `pkgs/` and `overlay/` inside the container, leave the checkout read-only, use `set -euo pipefail` with explicit `die` checks, and record dependency substitutions as reviewed patches rather than build-time `sed`.

### [MEDIUM] `sunshine-restore-visuals` clones an unpinned repo into user config

- **File:** `overlay/system/usr/local/bin/sunshine-restore-visuals:5,7-19`; `overlay/system/etc/sunshine/tools.conf:12-13`; `profile/airootfs/usr/local/bin/sunshine-update-run:164`.
- **What:** The tool clones `SUNSHINE_ASSETS_REPO` (default GitHub URL) with `--depth 1` and copies everything under `config/` and `share/` into `$HOME/.config` and `$HOME/.local/share`. There is no commit pin, signature or checksum. `visuals_on_update` can enable this automatically during updates.
- **Why it matters:** The assets repository can contain desktop entries, shell fragments or autostart files. A compromised branch could place executable configuration in the user's session the next time the tool runs. Backups are kept, but the copied paths are not restricted.
- **Suggestion:** Pin a reviewed commit or signed manifest, restrict the copy to known-safe subpaths, and explicitly deny `autostart/`, shell rc files and `*.desktop` with `Exec=` unless reviewed. Keep `visuals_on_update=off` as the default.

### [LOW] `sunshine-update-run` runs the full doctor repair twice

- **File:** `profile/airootfs/usr/local/bin/sunshine-update-run:145,160`.
- **What:** The update calls `/usr/local/bin/sunshine-doctor --quiet --fix` before "Tidying up" and again after the app steps as "Health check".
- **Why it matters:** Each invocation can perform repairs, take a Snapper restore point, clean caches and regenerate boot files. Running twice wastes time and makes the update log harder to interpret; the second run can report or undo state changed by the apps step without a clear boundary.
- **Suggestion:** Keep one full `--fix` pass at the end, or make the first call check-only and the final call the single repair pass. Log which phase produced each repair.

### [LOW] Network diagnosis labels TCP success as `dns-or-http` but never explains it

- **File:** `overlay/system/usr/local/lib/sunshine/ui.sh:135-137,146-153`.
- **What:** When raw TCP to `1.1.1.1:443` etc. succeeds, `sun_online()` returns success and sets `SUN_NET_WHY=dns-or-http`. `sun_net_explain()` has cases for `route`, `dns`, `portal` and `blocked`, then a generic fallback.
- **Why it matters:** The code correctly treats TCP reachability as online, but if a caller uses `SUN_NET_WHY` for the message, the user gets the generic "No internet connection" even though a route exists and only DNS/HTTP is broken. This makes diagnosis less precise than the comment promises.
- **Suggestion:** Either do not set `SUN_NET_WHY` on success, or add a `dns-or-http` case that reports "Route works but DNS/web requests are failing" and points to `sunshine-fix network`.

### [LOW] `ui.sh` uses unsanitized keys in `sed` and unquoted translation paths

- **File:** `overlay/system/usr/local/lib/sunshine/ui.sh:8,24-25`.
- **What:** `sun_conf()` interpolates its first argument directly into `sed -n "s/^$1=//p"`. The i18n directory expansion `${SUNSHINE_I18N:-/usr/share/sunshine/i18n}/uk.tsv` is unquoted in both the `-r` test and the input redirection.
- **Why it matters:** Callers currently pass fixed key names, so this is not a live exploit, but a key containing regex metacharacters would behave unexpectedly or match the wrong setting. An i18n path with spaces or glob characters could break the redirection or expand to multiple files when the variable is set by a launcher.
- **Suggestion:** Validate keys against `^[A-Za-z0-9_]+$` before using them in `sed`, escape regex metacharacters, and always quote the expanded i18n path.

### [LOW] Logo animation dependencies are missing from the aarch64 package set

- **File:** `profile/airootfs/usr/share/sunshine/logo-anim/play.py:14-15`; `profile/packages.x86_64:164-165`; `profile/packages.aarch64` (no Python packages); `overlay/system/usr/local/lib/sunshine/ui.sh:79-92`.
- **What:** `play.py` imports `numpy` and `PIL`. x86_64 lists `python-pillow` and `python-numpy`; aarch64 lists no Python interpreter or modules. `sun_success_anim()` falls back to a plain coloured logo line if the player fails, and the current `ui.sh` also checks for `--tool` support and applies `timeout 15`.
- **Why it matters:** Tool-success animation and terminal splash will silently degrade on aarch64. The fallback prevents a hard failure, but the behaviour is inconsistent between architectures and the timeout guard hides the real cause unless stderr is inspected manually.
- **Suggestion:** Add the Python dependencies to the aarch64 package set if the full tool UI is expected there, or make the logo assets self-contained (pre-rendered frames) and drop hard dependencies for the terminal player.

### [LOW] Toulouse-to-Ukrainian locale quirk depends on an external geolocation call

- **File:** `overlay/system/etc/sunshine/tools.conf:6`; `overlay/system/usr/local/bin/sunshine-detect-location:3-10`; `overlay/system/usr/local/lib/sunshine/i18n.py:28-30`; `overlay/system/usr/local/lib/sunshine/ui.sh:19-22`.
- **What:** When language is `auto`, a Europe/Paris install calls `https://ipapi.co/city/` once and stores the city in `/etc/sunshine/install-location`. If the city matches "toulouse", both the Python i18n helper and the shell UI force Ukrainian.
- **Why it matters:** This is surprising, undocumented behaviour for end users and maintainers: a French city determines a Ukrainian UI language. It also introduces a third-party network dependency into installer language selection and stores a geolocation-derived value on disk.
- **Suggestion:** Make the rule explicit in the installer UI and docs, or replace it with a normal user-selected locale. If retained, avoid the external service by deriving the preference from a reviewed local mapping and document why the exception exists.

### [LOW] Root repair scripts write logs to predictable `/tmp` paths

- **File:** `profile/airootfs/usr/local/bin/sunshine-doctor:63,106`.
- **What:** The root-running doctor redirects pacman and mkinitcpio output to fixed paths `/tmp/sunshine-core.log` and `/tmp/sunshine-mkinitcpio.log`, then tails them on failure.
- **Why it matters:** A local user can pre-create a symlink at one of those paths; root's `>` redirection follows symlinks and can truncate or overwrite the target. The attacker does not control the written text, but predictable root-writable `/tmp` paths are a classic local-denial-of-service primitive.
- **Suggestion:** Use `mktemp` files in a root-owned directory (for example `/var/log/sunshine/`) or `mktemp` in `/tmp` with 0600 permissions, and print the generated path in the error message.

---

## Verified good decisions

- **Live-only artifacts are removed on installed systems.** `profile/airootfs/usr/local/bin/sunshine-install:242-252,297-300` and `profile/airootfs/usr/local/bin/sunshine-post-install:4-16` remove `10-live`, the sshd drop-in and wants-symlink, SDDM/getty autologin, the root automated-script hook and the live user; the text installer also locks root. This does not fix the live-session exposure, but installed systems are much safer.
- **Tool updates verify before installing.** `profile/airootfs/usr/local/bin/sunshine-toolsync:21-26,38-45,51-81` checks a detached GPG signature on the manifest, per-file SHA-256 sums, a strict path allow-list, symlink/mode checks, atomic replacement, backups and downgrade protection. The env-override and key-rotation findings above are trust-anchor issues, not failures of the verification loop itself.
- **The updater protects the running live kernel and asks about Arch news.** `profile/airootfs/usr/local/bin/sunshine-update-run:13-23` holds the package that owns the running kernel modules in the live session; `:43-55` stops for recent "manual intervention" news items.
- **Privilege prompts are context-aware.** `overlay/system/usr/local/lib/sunshine/ui.sh:48-53` and `profile/airootfs/usr/local/bin/sunshine-update:8-14` use sudo in a terminal and pkexec from a launcher instead of always forcing one mechanism. No custom polkit rules were found, so the stock polkit defaults apply.
- **Initramfs repair is atomic.** `profile/airootfs/usr/local/bin/sunshine-doctor:103-107` builds into a `mktemp` file under `/boot`, checks size, then moves it into place; failure removes the temporary file.
- **Support output is privacy-aware.** `overlay/system/usr/local/bin/sunshine-support:10-16` redacts username, hostname, MAC/IP, email, serial-like strings and Wi-Fi SSIDs, and explicitly says nothing is uploaded.
- **Btrfs layout separates user data from system snapshots.** `profile/airootfs/etc/calamares/modules/mount.conf:50-74` places `@home`, `@root`, `@log`, `@cache` and `@tmp` in separate subvolumes so Snapper rollbacks do not touch user data or logs.
- **Package identity and repo hooks are present.** `profile/airootfs/usr/share/libalpm/hooks/90-sunshine-identity.hook:9-12` and `91-sunshine-repo.hook:9-11` restore Sunshine branding and the signed repo configuration after relevant pacman transactions.
- **Sirius-only declarative tooling is isolated.** `overlay/sirius/usr/local/bin/sunshine-declare` is shipped only through `overlay/sirius`, which `build.sh:31` copies solely for the Sirius edition; no dangling `sunshine-declare` reference was found in the base profile.
- **Scripts are syntactically clean.** All shipped Bash/sh scripts passed `bash -n` when filtered by shebang, and Python scripts passed `python3 -m compileall`. Earlier false positives came from Python-shebang files and one executable JPEG.

---

## Test ideas

These are condensed manual checks; the full step-by-step matrix is in `live-test-plan.md`.

1. **Live exposure:** boot the ISO on a NAT network, run `nmap -p22 <vm-ip>` from the host, SSH in as `sunshine`/`sunshine`, and confirm `sudo -i` needs no password. Log the result; this is expected from C1, not a regression.
2. **Key rotation:** in a throwaway VM, run `pacman -Sy` and `sunshine-toolsync verify`; log any "required key not available"/"unknown trust" errors and compare `pacman-key --list-keys sunshine` with the new fingerprint `2FEC...`.
3. **GRUB and splash:** screenshot the GRUB menu, then capture the Plasma splash at roughly 1 s, 5 s and 8 s; expect logo build-up, the strip with "SUNSHINE OS", rays and the idle loop.
4. **Installer cleanup:** perform a Calamares install, reboot into the installed system, and verify `10-live`, the sshd drop-in, autologin configs and the `sunshine` user are gone; log `visudo -c` and `systemctl is-enabled sshd`.
5. **Repair safety:** on a snapshot, create `/etc/sudoers.pacnew` plus a deliberate sudoers syntax error and run `sunshine-doctor --fix`; confirm whether it replaces sudoers and whether `visudo -c` still succeeds.
6. **LUKS install:** install with encryption in a VM, reboot, then inspect `/boot/initramfs-linux.img` with `lsinitcpio` and confirm `/crypto_keyfile.bin` is present; log the `cryptkey=` GRUB argument and screenshot the unlock prompt.
7. **Logo fallback in a terminal:** run a successful tool such as `sunshine-toolsync verify` in Konsole and `sunshine-update` from a launcher; compare the terminal versus GUI privilege prompt and whether the animation ends within 15 seconds.
8. **Offline network messages:** boot with `-nic none`, source `/usr/local/lib/sunshine/ui.sh`, run `sun_online; echo "$SUN_NET_METHOD $SUN_NET_WHY"; sun_net_explain`, and screenshot the result; repeat with broken DNS to check whether the `dns-or-http` gap appears.
