# SunshineOS source audit

**Scope:** read-only audit of the local clone at `/home/tak_0/sunshineos-audit/SunshineOS` (git HEAD `a144e807f94e2b81d9dc5118c7ac75379a47bce5`, 2026-11-19) and the companion website at `/home/tak_0/sunshineos-audit/sunshineos-site`.

**Method:** manual review of build scripts, Dockerfile, worker, tools, profile, overlays, packages, catalogue, docs, tests and site assets; targeted `grep` for credentials, dangerous primitives (`eval`, `curl|sh`, `rm -rf`, unsafe permissions) and download/verification code; verification of the live-user password hash with `openssl passwd -6`. No repository files were modified and no commits were made.

**Working-tree note:** the repo has 9 pre-existing uncommitted modifications (UI/logo/night messages and `sunshine-update-run` using `sudo` in a terminal instead of only polkit). They were reviewed and do not change any finding below. Line numbers refer to the working tree as audited.

---

## Summary

SunshineOS is a thoughtfully assembled Arch ISO with several genuinely good safety controls: the tool updater verifies a signed manifest, per-file SHA-256 sums, a path allow-list and rollback; the installers strip the live-only SSH/sudo/autologin configuration; no `eval`, `curl | sh`, world-writable source files or hardcoded production tokens were found; ISOs get SHA-256 sums at build and publish time.

The main risks are concentrated in three places:

1. **The live ISO is effectively a public root shell.** It ships a published password for a `wheel` user with passwordless sudo, enables SSH with password auth, permits root login, and autologins both a GUI user and root on tty1. Anyone on the same network can log in as `sunshine` and become root in one command. Installed systems are cleaned up, but the live medium is the thing users boot and often leave running while installing.
2. **The build chain trusts unverified third-party code while running a privileged container.** AUR git clones, `--skippgpcheck`, `sha256sums=('SKIP')`, unpinned repos and a `FROM archlinux:latest` base feed packages into an ISO that is assembled with `docker run --privileged`. A compromised upstream or dependency can become root on the build host and/or code in the shipped image.
3. **Download and auxiliary update paths trust remote metadata without final verification.** The Cloudflare worker joins ISO parts without checking the published SHA-256; the Chaotic keyring is bootstrapped from a CDN without a pinned fingerprint; theme/config "restore" clones an unpinned repo into user config.

Severity distribution: **2 Critical, 4 High, 7 Medium, 6 Low**. Details and exact evidence follow.

---

## Critical findings

### C1 — Live ISO: default known password + passwordless sudo + SSH/root login enabled (Critical)

**Evidence**
- `profile/airootfs/etc/shadow:1-2` — `root::14871::::::` (empty root password) and a `sunshine` hash. `openssl passwd -6 -salt as5wFKHd.5UEe6yM sunshine` reproduces the stored hash exactly: the password is **`sunshine`**.
- `profile/airootfs/etc/motd:4` — the password is printed on the live console: `Live user: sunshine / password: sunshine`.
- `profile/airootfs/etc/group:4` — `wheel:x:10:sunshine`.
- `profile/airootfs/etc/sudoers.d/10-live:1` — `%wheel ALL=(ALL:ALL) NOPASSWD: ALL`.
- `profile/airootfs/etc/ssh/sshd_config.d/10-archiso.conf:1-3` — `PasswordAuthentication yes`, `PermitRootLogin yes`.
- `profile/airootfs/etc/systemd/system/multi-user.target.wants/sshd.service` — a symlink to `/usr/lib/systemd/system/sshd.service`, i.e. sshd starts at boot.
- `profile/airootfs/etc/sddm.conf.d/autologin.conf:1-4` — GUI autologin as `sunshine`; `profile/airootfs/etc/systemd/system/getty@tty1.service.d/autologin.conf:1-3` — tty1 autologin as **root**.
- `test/break-repair.sh:8` and `test/install-test.sh:5` independently confirm the intended test workflow: SSH user `sunshine`, password `sunshine`, "passwordless sudo".

**Why it matters**
A live session on any shared or untrusted network (cafe, LAN, public WiFi, VM with a bridged adapter) exposes sshd on port 22. Knowing the password from `/etc/motd` (or from the docs/tests) gives a shell as `sunshine`; `sudo -i` then needs no password because of `10-live`. That is full root control of the live environment: the installer, the target disks, and the generated installed system can all be tampered with. Root's empty shadow field does not by itself allow SSH root login because `PermitEmptyPasswords` is not enabled, but `PermitRootLogin yes` plus a password-set root would be even worse, and the `sunshine` path is sufficient. Physical access is also trivial: tty1 is root-autologin.

**Mitigating factors**
`profile/airootfs/usr/local/bin/sunshine-install:242-252` and `sunshine-post-install:4-16` remove `10-live`, `10-archiso.conf`, the sshd wants-symlink, the autologin configs and the live user; the text installer also runs `passwd -l root` and re-enables the normal `wheel` rule (`sunshine-install` chroot script, `passwd -l root` / `sed` lines). Installed systems are therefore much better configured than the live ISO. This does not protect the live session itself.

**Recommendations**
- Do not enable sshd by default in the live image; enable it only by an explicit boot parameter or a user-run helper.
- If remote live repair is required, generate a random per-boot password (or require a key), bind to loopback, and drop `PermitRootLogin yes`.
- Replace the fixed hash/`motd` password with a per-boot generated credential, and remove or randomise the tty1 root autologin.
- Keep the installer/post-install cleanup, and add a smoke check that verifies those files are absent on the installed target.

---

### C2 — Privileged, unpinned build pipeline fed by unverified AUR/Git sources (Critical)

**Evidence**
- `build.sh:17-19` — `docker run --rm --privileged ...` with host directories bind-mounted.
- `Dockerfile:1-3` — `FROM archlinux:latest` and `pacman -Syu --noconfirm` with no pinning or lockfile.
- `build-aur.sh:22` — local build repo is configured with `SigLevel = Optional TrustAll`.
- `build-aur.sh:24-25` — builder user gets `builder ALL=(ALL) NOPASSWD: ALL`.
- `build-aur.sh:31` — AUR sources are cloned from `https://aur.archlinux.org/$p.git` with no commit pin or signature check.
- `build-aur.sh:33` — `makepkg -sCf --noconfirm --needed --skippgpcheck` explicitly disables source PGP verification.
- `pkgs/illogical-impulse-bibata-modern-classic-bin/PKGBUILD:12-13`, `pkgs/sunshine-icon-theme/PKGBUILD:13-14`, `pkgs/uni-pkg-git/PKGBUILD:12-13` — `sha256sums=('SKIP')`; `pkgs/illogical-impulse-microtex-git/PKGBUILD:19-20` — unpinned `-git` source with `SKIP`.
- `tools/import-end4.sh:8,13-21` — one upstream is pinned (`PIN=2f2a...`), but `Sunshine_end4_Dots` is pulled at whatever the current branch head is (`git -C $SU pull -q --ff-only || true`) and its patch plus the local patch are applied with no signature verification.
- `build.sh:41` — `mkarchiso` installs those packages into the image inside the privileged container.

**Why it matters**
`--privileged` gives the container essentially host-root capabilities. The packages installed into the ISO come from AUR PKGBUILDs and git heads that can change at any time, with PGP and checksum checks disabled. A malicious or compromised AUR package can execute code as root inside the build container (its `PKGBUILD`/install scripts, and later package install hooks under `mkarchiso`) and therefore has a direct path to the build host and to whatever ships in the ISO. Even ignoring container escape, this is an unreproducible, attacker-influenceable supply chain for an operating-system image.

**Recommendations**
- Remove `--privileged`; use the minimum Linux capabilities/namespaces needed by `mkarchiso`, or build in an isolated VM.
- Pin the base image by digest, pin Arch package sets (or record exact versions), and pin every git source to a commit; verify signed tags where available.
- Stop using `--skippgpcheck` and `SKIP` checksums; fail closed when a source cannot be verified.
- Do not give the AUR builder blanket `NOPASSWD: ALL`; use a constrained `sudoers` rule or run the whole build in a disposable, network-restricted VM.
- Produce and publish a build attestation/SBOM so users can tell what actually went into an ISO.

---

## High findings

### H1 — Chaotic-AUR key and packages bootstrapped without a pinned fingerprint (High)

**Evidence**
- `overlay/system/etc/sunshine/repos.conf:1-3` — `chaotic=on` by default.
- `sunshine-repo` (`profile/airootfs/usr/local/bin/sunshine-repo:32-47`) — `ensure_chaotic()` adds `[chaotic-aur]`; its fallback at line 39 runs `pacman-key --recv-key 3056513887B78AEB --keyserver keyserver.ubuntu.com`, `pacman-key --lsign-key ...`, then `pacman -U https://cdn-mirror.chaotic.cx/chaotic-aur/chaotic-keyring.pkg.tar.zst ...` with no detached signature or pinned fingerprint check.
- `tools/fetch-chaotic.sh:6-12` — the same keyring/mirrorlist packages are downloaded from the Chaotic CDN with `curl` and added to the local repo, which `build-aur.sh:22` treats as `TrustAll`.

**Why it matters**
This is trust-on-first-use for a third-party signing key that is then used to authenticate every Chaotic-AUR package installed on the machine. A compromised CDN, keyserver response or DNS path can substitute a keyring, and from there substitute arbitrary "signed" packages — shipped into the ISO at build time or installed later on users' systems. The website advertises Chaotic kernels and packages as a feature, so this affects a large part of the package surface.

**Recommendations**
- Ship the Chaotic keyring/mirrorlist in the repo with a pinned fingerprint and a checked SHA-256; verify the exact fingerprint (`3056513887B78AEB` and its full fingerprint) before locally signing it.
- Never fall back to `--recv-key` from a keyserver without an out-of-band fingerprint comparison.
- Verify detached signatures on the two bootstrap packages instead of `pacman -U <bare URL>`.

---

### H2 — ISO download worker does not verify the published SHA-256 (High)

**Evidence**
- `worker/iso-download.js:8,12-19` — the worker trusts `https://tak0dan.github.io/sunshineos-site/release.json` to choose the newest release and its part URLs.
- `worker/iso-download.js:24-43` — `openSlice()` checks only HTTP status, declared Content-Length and a non-empty first chunk.
- `worker/iso-download.js:56-63,78-96` — parts are concatenated and streamed; no digest is computed.
- `sunshineos-site/release.json:4-12` — entries contain a `sha256` for the assembled ISO; the worker ignores it.
- `worker/iso-download.js:62` — `Access-Control-Allow-Origin: *`.
- Manual verification is possible (`tools/release-github.sh:48,51` publishes `.sha256` and explains `sha256sum -c`; `index.html:896` displays a truncated digest), but nothing in the download path enforces it.

**Why it matters**
An attacker who can alter `release.json` (site repo/Pages compromise) or the release assets/URLs can serve a modified ISO that is joined and delivered as if it were the official image. The site even shows the correct checksum while the button delivers unverified bytes, which encourages users to assume verification happened. For an OS image, silent corruption or malicious substitution is a full-device compromise at install time.

**Recommendations**
- Have the worker verify each part (or the final assembled stream) against digests obtained from an authenticated source, and abort before delivering bytes on mismatch.
- Publish per-part hashes in `release.json` and check them in `openSlice()`; at minimum, expose the full expected SHA-256 in the download response header and document mandatory local verification.
- Consider signing `release.json` and having the worker verify the signature with a key compiled into the worker.

---

### H3 — Environment-overridable URL and key in the signed tool updater (High)

**Evidence**
- `profile/airootfs/usr/local/bin/sunshine-toolsync:10` — the script runs as root (`exec sudo "$0" "$@"`).
- `sunshine-toolsync:13-14` — `BASE=${SUNSHINE_TOOLS_URL:-https://github.com/...}` and `KEY=${SUNSHINE_TOOLS_KEY:-/usr/share/pacman/keyrings/sunshine.gpg}`.
- `sunshine-toolsync:38-49,52-63` — the whole trust decision (manifest signature, tarball checksums, install) derives from those two variables.

**Why it matters**
The code does implement strong verification (GPG signature, per-file SHA-256, allow-list, rollback), so this is not a direct user-to-root bug. But the trust anchor and download endpoint are runtime-environment inputs rather than compile-time constants. Any context that can set root's environment (a service unit, a wrapper script, a compromised admin workflow, or `sudo -E` with a permissive sudoers policy) can redirect "signed" tool updates to an attacker URL and key, then overwrite root-owned scripts in `/usr/local/bin`. In the live ISO, the `sunshine` account already has passwordless sudo (C1), which makes this realistic there.

**Recommendations**
- Remove the env overrides from the installed/root path, or gate them behind a build-time flag that is off in shipped images.
- Resolve `BASE` and `KEY` to constants (or to values read from a root-owned config file with a pinned path) and log every update's source URL and key fingerprint.
- Add a regression test that refuses `SUNSHINE_TOOLS_URL`/`SUNSHINE_TOOLS_KEY` overrides in the shipped image.

---

### H4 — AUR package sources are unpinned with disabled checksum verification (High)

**Evidence**
- `build-aur.sh:31,33` (see C2) clones AUR git repos at branch head and builds with `--skippgpcheck`.
- `pkgs/illogical-impulse-bibata-modern-classic-bin/PKGBUILD:12-13`, `pkgs/sunshine-icon-theme/PKGBUILD:13-14`, `pkgs/uni-pkg-git/PKGBUILD:12-13`, `pkgs/illogical-impulse-microtex-git/PKGBUILD:19-20` — `SKIP` checksums / moving `-git` sources.
- `tools/import-end4.sh:13` — the vendor dots repo is updated to latest with `|| true` rather than pinned to a reviewed commit.

**Why it matters**
Separate from the privileged-container issue, this means the exact contents of the ISO are not reproducible or auditable after the fact. A source tarball or git head can change without any repository commit in SunshineOS changing, yet the resulting binaries are installed into a released OS image. This also undermines the site's "every change was run in a VM before it was kept" claim (`index.html:532`), because upstream changes arrive silently.

**Recommendations**
- Record every external source as `name@commit` plus sha256; update those pins deliberately in a reviewed commit.
- Generate PKGBUILDs with real checksums; fail builds on `SKIP` unless a reviewed exception is documented.
- Mirror critical upstream sources internally so the build does not depend on mutable third-party branches.

---

## Medium findings

### M1 — Unpinned external config repository is copied into user config (Medium)

**Evidence**
- `profile/airootfs/usr/local/bin/sunshine-restore-visuals:5,7-19` — `git clone -q --depth 1 "$REPO" "$NEW/src"` (default `https://github.com/tak0dan/sunshineos-assets.git`), then `cp -a "$NEW/src/config/"* "$HOME/.config/"` and `cp -a "$NEW/src/share/." "$HOME/.local/share/"`. `SUNSHINE_ASSETS_REPO` can override the URL.

**Why it matters**
This copies arbitrary files into the user's config directory, including autostart-capable locations, from a mutable branch with no commit pin, signature or checksum. If the assets repository is compromised, the next "restore visuals" (or an update with `visuals_on_update=on`, `tools.conf:13`) can place executable desktop entries or shell config in the user's session. Default `visuals_on_update=off` limits exposure, but the tool is advertised and user-invokable.

**Recommendations**
- Pin a commit/tag and verify a signed manifest or at least pinned SHA-256 values for each copied file.
- Restrict which subpaths may be copied (deny `autostart/`, shell rc files, etc.) and keep the existing per-file backups.

### M2 — Broad `--overwrite '*'` when registering `sunshine-base` (Medium)

**Evidence**
- `profile/airootfs/usr/local/bin/sunshine-apps:48-51` — `pacman -S --noconfirm --needed --overwrite '*' sunshine-base`.

**Why it matters**
`--overwrite '*'` tells pacman to replace *any* conflicting file, not just the known tool paths. If another package owns a file with the same name, it will be silently overwritten and the database will claim ownership for `sunshine-base`, potentially breaking that other package. This runs automatically during catalogue app installs.

**Recommendations**
- Enumerate the exact `sunshine-base` file globs that legitimately exist in the image and pass only those to `--overwrite`, or use `pacman -Qo` checks and fail with a clear error on unexpected conflicts.

### M3 — Build orchestrator mutates tracked files and tolerates failures (Medium)

**Evidence**
- `make-iso.sh:10` — `set -uo pipefail` (no `-e`).
- `make-iso.sh:31-44` — `resolve_dead_deps()` runs `sed -i` directly on `pkgs/*/PKGBUILD` in the checkout when a dependency is missing.
- `make-iso.sh:81-84` — `cp -a overlay/system/. profile/airootfs/` and `rm -rf profile/airootfs/etc/skel` are not error-checked, while later steps depend on them.

**Why it matters**
A build can silently modify the source tree, so the ISO contents no longer match the committed state; a failed copy can still produce an ISO that is missing fixes. This conflicts with the reproducible-build intent and with the site's claim that building "never modifies your own system" (`index.html:424`) if read as including the checkout.

**Recommendations**
- Work on a temporary copy of the profile/pkgs trees inside the container; leave the checkout read-only.
- Use `set -euo pipefail` and check or `die` on each critical copy/generation step.
- Record PKGBUILD modifications as patches with explicit review rather than `sed -i` during builds.

### M4 — Weak installer password policy and environment/plaintext password handling (Medium)

**Evidence**
- `profile/airootfs/etc/calamares/modules/users.conf:10-14` — `minLength: 1`, `allowWeakPasswords: true`, `allowWeakPasswordsDefault: true`, `setRootPassword: false`.
- `profile/airootfs/usr/local/bin/sunshine-install:4-5` — auto mode takes `SUNSHINE_PASS=secret` from the environment; `:91` reads it; `:324,326-327` writes `USERNAME:PASS` to `/root/.sunshine-cred`, feeds it to `chpasswd`, then `shred -u`.

**Why it matters**
Users can create accounts with a one-character password through the graphical installer. In automated installs the password is exposed in the environment (visible to root/`/proc` inspection) and briefly on disk; shredding on a CoW/SSD filesystem is not a guaranteed erasure. Root stays locked, which limits the impact, but the account is in `wheel`, so its password is effectively the admin password.

**Recommendations**
- Set a sane minimum length (e.g. 8-12) and disable `allowWeakPasswords` or require an explicit "I know this is weak" override.
- Pass passwords over a pipe/FD or temporary file in a tmpfs with strict permissions rather than the environment; avoid relying on `shred` for CoW filesystems.

### M5 — "Firewall is on by default" is only true after a later migration (Medium)

**Evidence**
- Site claim: `sunshineos-site/index.html:537` — "The firewall is on by default."
- `overlay/system/usr/share/sunshine/migrations/0004-firewall-on.sh:5` — exits immediately when `[ -d /run/archiso ]` (live session); `:10-14` enables ufw and `ufw.service`.
- The migration is invoked from `sunshine-toolsync:75`, `sunshine-apps:62` and `sunshine-doctor --fix`, not from the installers (`sunshine-install`, `sunshine-post-install` contain no `sunshine-migrate` call).

**Why it matters**
Neither the live session nor a freshly installed system (before the first update/toolsync/app apply) has the firewall enabled by the shipped configuration, even though the release notes present it as a default. Users who install offline and stay offline keep incoming services exposed. `ufw` is only listed as a package (`profile/packages.x86_64:179`), not enabled via a systemd preset/symlink in the profile.

**Recommendations**
- Enable ufw with the intended defaults during installation (or ship an enabled `ufw.service` preset), while preserving the "don't overwrite user rules" checks.
- Either change the website wording to "first update enables the firewall" or make the claim true in the image.

### M6 — Version claims are inconsistent across site, repo and branding (Medium)

**Evidence**
- `sunshineos-site/index.html:532` — "What is new in Sol 1.5 and Sirius 0.3".
- `SunshineOS/VERSION:1` — `1.6`; `sunshineos-site/release.json:4,10` — newest release version `13.4.7.1.6` (anchor-encoded scheme from `tools/release-github.sh:32-39`).
- `profile/airootfs/etc/calamares/branding/sunshine/branding.desc:13-16` — installer still says `1.5`.
- `profile/airootfs/etc/os-release:1-11` — no version field at all.

**Why it matters**
Users cannot reliably tell which version they downloaded or installed. The installer branding, the website release notes and the published file names disagree, which also complicates support and bug reports.

**Recommendations**
- Generate branding/`os-release` version strings from `VERSION` at build time (the `build.sh:31` Sirius path already does a manual `sed` for 0.3 — generalise it).
- Update the site's "what is new" section to the currently published release or link it to `release.json`.

### M7 — Sunshine Store installs unverified AppImages and fetches arbitrary icon URLs (Medium)

**Evidence**
- `profile/airootfs/usr/lib/sunshine-store/appimage.py:66-78` — resolves a GitHub release via API, downloads the `.AppImage` asset, writes it under `~/Applications` and sets execute bits; no signature or checksum verification.
- `appimage.py:73,90-93` — the asset name is used verbatim as a filename and embedded in a generated `.desktop` entry; `--no-sandbox` is always added.
- `appimage.py:80-86` — `icon_url` is fetched with `urllib.request.urlopen` (which supports more than HTTP(S)) and written without scheme restriction.

**Why it matters**
A compromised third-party release (or a crafted catalogue/store input) yields an executable running in the user's session. AppImages are commonly unsigned, so this is an accepted trade-off in many stores, but it should be explicit. The unrestricted URL fetch can also be abused to read local `file://` content into a user-visible icon file, and unsanitised names in a `.desktop` `Exec=` line are fragile.

**Recommendations**
- Require an explicit user confirmation that the AppImage is unsigned/unverified; record and display the asset digest.
- Restrict `icon_url` to `https://` and validate/sanitise asset names and desktop-entry fields.

---

## Low findings

### L1 — Test-only hardcoded credentials and disabled SSH host-key checks (Low)
`test/tssh.sh:2-4` embeds `testpass123` and uses `sshpass -p` with `StrictHostKeyChecking=no` / `UserKnownHostsFile=/dev/null`; `test/vbox.sh:5-6`, `test/break-repair.sh:8`, `test/install-test.sh:5` document the `sunshine`/`sunshine` and empty-root-password test workflow; `test/vbox.sh:14` passes `--password "${GP:-}"`. These are lab scripts, not shipped ISO code, but the defaults are easy to reuse accidentally. **Recommend:** require credentials via environment with no insecure defaults and keep test VMs on loopback-only NAT.

### L2 — Stale comment about the live user having no password (Low)
`profile/airootfs/usr/local/bin/sunshine-live-setup:8` says "the live user has no password", contradicting `shadow:2` and `motd:4`. **Recommend:** correct the comment so future maintainers do not remove the (currently known) password and break SSH tests unintentionally — or, better, implement C1's random-password fix and update this logic.

### L3 — Minor publish-script issues (Low)
`tools/release-github.sh:15` computes `ver` but never uses it; `:29` requires a git-ignored `ANCHOR` file (documented in `docs/RELEASING.md:16`) so a fresh checkout cannot publish a Sol Release without extra setup. **Recommend:** remove dead code and provide an `ANCHOR.example` plus a clear preflight error.

### L4 — Unsigned package-repository database metadata (Low)
`profile/airootfs/etc/pacman.conf:50-51` sets global `SigLevel = Required DatabaseOptional` and `[sunshine]` at `:85-87` uses `PackageRequired DatabaseOptional`; `profile/pacman.conf:103-105` uses `Optional TrustAll` for the build-time local repo (acceptable for a local `file://` repo). `DatabaseOptional` permits an unsigned repo database; package signatures still protect package contents, but an attacker able to replace the database can roll back version information or hide updates. **Recommend:** use `DatabaseRequired` for `[sunshine]` if the signing key pipeline can sign the database.

### L5 — Wildcard CORS on the ISO download endpoint (Low)
`worker/iso-download.js:62` sends `Access-Control-Allow-Origin: *`. The ISO is public, so this is not a confidentiality issue, but it lets any page script fetch the download and measure sizes/timing. **Recommend:** drop the header unless a documented cross-origin consumer needs it.

### L6 — Secrets-handling documentation is good but test/draft examples are risky (Low)
`docs/team/drafts/TOOLS-opencode-draft.md:177-181` documents `SUNSHINE_NEW_PASS` while noting it appears in process lists and shell history; `sunshine-rescue:18,39` accepts `SUNSHINE_LUKS_PASS` similarly. No plaintext secret is committed, but these patterns encourage unsafe automation. **Recommend:** support reading secrets from a file descriptor or tmpfs file and document that as the preferred non-interactive path.

---

## Claims vs reality

| Website / documentation claim | Evidence in repo | Assessment |
|---|---|---|
| "The firewall is on by default" (`sunshineos-site/index.html:537`; Ukrainian page mirrors it) | ufw is only a package (`profile/packages.x86_64:179`); `0004-firewall-on.sh:5` skips live, `:14` enables it; invoked only by later migrations (`sunshine-toolsync:75`, `sunshine-apps:62`) | **Partly false.** Not on in live or on a fresh install until an update/toolsync/app step runs. |
| "What is new in Sol 1.5 and Sirius 0.3" (`index.html:532`) | `VERSION:1` = 1.6; `release.json:4` = 13.4.7.1.6; `branding.desc:13-16` = 1.5 | **Outdated/inconsistent.** See M6. |
| "Every change was run in a virtual machine before it was kept" (`index.html:532`) | A good VM test suite exists (`test/smoke.sh:1-137`, `test/break-repair.sh`, headless installers), but AUR/vendor sources are pulled at mutable heads with verification disabled (`build-aur.sh:31,33`, `import-end4.sh:13`) | **Overstated.** Tested snapshots are not the same as the bytes that get built later. |
| "building it never modifies your own system" (`index.html:424`) | `build.sh:17` is a container; but `make-iso.sh:81-84` and `:31-44` rewrite files in the checkout | **True for the host OS, misleading for the source checkout.** |
| "sunshine-update asks for your password in the terminal when started there (polkit only from a launcher)" (`index.html:447,473`) | Working-tree `sunshine-update-run` now uses `sun_exec_priv` (sudo on a TTY, pkexec otherwise); committed HEAD version only used `pkexec` | **True in the audited working tree, false at HEAD.** The uncommitted change must be committed/released for the claim to hold. |
| "signed manifest, checksums, rollback" for `sunshine-toolsync` (`index.html:535`; docs) | `sunshine-toolsync:38-49` GPG-verifies the manifest, `:52-63` checks path allow-list and SHA-256, `:68,77-81` supports rollback | **Accurate**, with the caveat in H3 about env-overridable trust anchors. |
| "SHA-256 of the image" shown on the site (`sunshineos-site/README.md:32`, `index.html:896`) | Digest is present in `release.json:11` and displayed truncated with full value in a `title`; worker never verifies it (`worker/iso-download.js:24-43`) | **Accurate as display, not as enforcement.** See H2. |
| "Boot GRUB on UEFI and legacy BIOS", "btrfs snapshots", "Calamares + text installer", "Hyprland added by installer", "signed [sunshine] repo" | `build.sh:28-31`, `profile/airootfs/etc/pacman.conf:85-87`, `sunshine-install` and `sunshine-hyprland-install`, `sunshine-snapshots-setup`, `test/smoke.sh:94-110` | **Substantiated.** |

---

## Controls that were verified as working

- `sunshine-toolsync:21-26,38-49,52-63,68-81`: detached GPG signature on the manifest, per-file SHA-256, strict `ALLOW` path regex, symlink/mode checks, atomic install and rollback; signing key in `profile/airootfs/usr/share/pacman/keyrings/sunshine.gpg` matches `sunshine-trusted` fingerprint `8253720323C575207CC781B5DB345EF676CCD13D`.
- `sunshine-install:242-252`, `sunshine-post-install:4-16`: live-only sudo/SSH/autologin artifacts and live user are removed on installed systems; root is locked and the normal wheel rule enabled.
- `sunshine-rescue:26,85-109,248-265`: current working-tree version has idempotent cleanup, INT/TERM/HUP traps and a non-`die` password path (the older criticism in `docs/team/reports/rescue-review.md` no longer applies to this code).
- No `eval`, `curl | sh`, world-writable files, setuid/setgid files in the tree, or hardcoded production tokens were found by targeted greps.
- `make-iso.sh:124` and `tools/release-github.sh:48,51` generate and publish whole-ISO SHA-256 sums; the site renders them.
- `profile/airootfs/etc/sudoers.d/20-sunshine` only adds `pwfeedback`; it does not add passwordless sudo.

---

## Top 10 findings (priority order)

1. **Critical — Live ISO ships known password `sunshine` + passwordless wheel sudo + SSH password auth and root-login enabled** (`shadow:2`, `motd:4`, `10-live:1`, `10-archiso.conf:1-3`, sshd wants-symlink).
2. **Critical — Privileged Docker build (`build.sh:17`) fed by unpinned AUR/git sources with `--skippgpcheck`, `SKIP` checksums and `TrustAll`** (`build-aur.sh:22-34`, `Dockerfile:1-3`, `import-end4.sh:13`).
3. **High — Chaotic-AUR keyring bootstrapped from a CDN/keyserver without pinned fingerprint verification** (`sunshine-repo:38-40`, `fetch-chaotic.sh:6-12`, `repos.conf:3`).
4. **High — ISO download worker ignores the published SHA-256; no verification of joined parts** (`worker/iso-download.js:24-43,78-96`, `release.json:11`).
5. **High — `sunshine-toolsync` trust URL/key are environment-overridable in a root script** (`sunshine-toolsync:10,13-14`).
6. **High — Moving git heads and `SKIP` checksums make released ISO contents unreproducible and upstream-changeable** (`build-aur.sh:31,33`, `pkgs/*/PKGBUILD`, `import-end4.sh:13`).
7. **Medium — Unpinned assets repo copied into user config by `sunshine-restore-visuals`** (`:5,10-19`).
8. **Medium — `sunshine-apps` registers `sunshine-base` with `pacman --overwrite '*'`** (`:50`).
9. **Medium — Build script mutates tracked PKGBUILDs and lacks `set -e`** (`make-iso.sh:10,31-44,81-84`).
10. **Medium — Installer allows 1-character passwords and handles secrets via env/plaintext file** (`users.conf:10-14`, `sunshine-install:4-5,91,324-327`).

*(Immediately following: firewall claim mismatch (M5), version mismatch (M6), unverified AppImages (M7), then the Low items.)*
