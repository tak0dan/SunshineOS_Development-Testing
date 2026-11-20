# `sunshine-update` repository integration proposal — 2026-11-21

- Source: OpenClaw task `repo-integration`, architect role, 1 attempt.
- Scope: `tak0dan/sunshineos-repo`; all changes proposed for `Development_Anesthesia`, never direct `main`.
- No credential values or private key material in the proposal.

---

# Stage A integration: `sunshine-update 0.9.0-1`

## Branch rule

- Create `Development_Anesthesia` from `main`; do all work there and open a PR to `main`. No direct commits to `main`.
- Expected commit set: `packages/sunshine-update/PKGBUILD`, `package-list/desktop.txt`, `packages/sunshine-base/PKGBUILD`, `scripts/stage-src.sh`, `scripts/build-repo.sh`, `scripts/publish.sh`, and new tests under `test/`.

## 1. Package and repository integration

- Add `packages/sunshine-update/PKGBUILD`:
  - `pkgname=sunshine-update`
  - `pkgver=0.9.0`
  - `pkgrel=1`
  - `arch=('any')` if Stage A is a shell wrapper; otherwise `x86_64`.
  - `depends=('pacman')`
  - `optdepends=('sunshine-base: full doctor/converge checks')`
  - `conflicts=('sunshine-update-git')`
  - `replaces=('sunshine-update-git')` only if needed.
  - Install the wrapper as `/usr/bin/sunshine-update`; package data under `/usr/share/sunshine/`.
- Add `sunshine-update` to `package-list/desktop.txt` — or to whichever list `packages/sunshine-base/PKGBUILD` actually sources. Keep one source of truth; do not duplicate.
- In `packages/sunshine-base/PKGBUILD`:
  - Add `sunshine-update>=0.9.0-1` to `depends`.
  - Do **not** add `sunshine-update` to `conflicts`.
  - Avoid a dependency cycle: `sunshine-update` must not hard-depend on `sunshine-base` or on `sunshine-doctor` if `sunshine-doctor` is shipped by `sunshine-base`. Use `optdepends` or split `sunshine-doctor` into its own package.
- `scripts/build-repo.sh`:
  - Build `packages/sunshine-update` with `makepkg --sign`.
  - Ensure `repo-add -s` produces `sunshine.db.sig` and that `sunshine-update-0.9.0-1-x86_64.pkg.tar.zst.sig` exists.
- `scripts/publish.sh`:
  - Upload package and `.sig` first, then `sunshine.db` and `sunshine.db.sig`, then `sunshine.files`/`.sig` if used.
  - Verify in a clean `archlinux` container before declaring the `repo` release good.
  - Never upload private key material; only public key/fingerprint metadata.
- `bootstrap.sh` needs no change: `pacman -Sy sunshine-base` should pull `sunshine-update` through the new dependency.

## 2. `scripts/stage-src.sh`

Add a `stage_sunshine_update()` path:

- Source: `$SUNSHINE_UPDATE_SRC` or `../SunshineOS/packages/sunshine-update`.
- Destination: `packages/sunshine-update/`.
- Copy only `PKGBUILD`, `sunshine-update`, `sunshine-update.install` if present, and `LICENSE`.
- Never copy `.git`, private keys, `*.pkg.tar.zst`, `*.sig`, or build artifacts.
- Verify `pkgver=0.9.0` and `pkgrel=1`; fail on mismatch.
- Idempotent: skip if `packages/sunshine-update/PKGBUILD` exists unless `--force`.
- Add `--check` mode for CI: verify staged version matches the published `0.9.0-1`.
- If Stage A is a wrapper, stage `packages/sunshine-update/sunshine-update` and install it to `/usr/bin/sunshine-update`; the wrapper must be idempotent and call `sunshine-doctor --fix` only when present.
- `scripts/build-repo.sh` should run `scripts/stage-src.sh --check` before `makepkg`.

## 3. Converge/upgrade flow

- Pass 3 of `sunshine-doctor --fix` installs `sunshine-base`, which now pulls `sunshine-update`.
- Pass 4 verifies `/usr/bin/sunshine-update`, version `0.9.0`, and policy.
- Stage A `sunshine-update` should be a thin, idempotent wrapper:
  1. Run `sunshine-doctor --fix` pass 1: pacman healthy.
  2. Verify the `[sunshine]` signed chain.
  3. Run `pacman -Syu` — never `pacman -Sy <pkg>`.
  4. Run `sunshine-doctor --fix` passes 2–5; loop while exit 1; exit 2 on unfixable.
  5. Post-upgrade hooks: identity restore, initramfs/GRUB rebuild, NixOS entry; snapshot before/after when snapper/btrfs is present.
  6. Defer full UNI/Flatpak/AppImage/Nix and `--rollback` to later stages, but keep hook points.
- Partial-upgrade protection: refuse `-Sy <pkg>` style installs from store/UNI; always `-Syu`.
- Derivative handling: detect Garuda/EndeavourOS/Manjaro via `/etc/os-release`; exit 2 and do not remove packages.

## 4. Signed-chain checks

Add doctor/update checks with these identifiers:

- `check_sunshine_repo_siglevel`: `[sunshine]` in `/etc/pacman.conf` must not contain `TrustAll`; when policy is `required`, use `Required`.
- `check_sunshine_repo_key`: pinned fingerprint in `/usr/share/sunshine/sunshine-repo-key.conf` or `/etc/sunshine/repo-key.conf`; `pacman-key --list-keys` matches; key not expired.
- `check_sunshine_db_sig`: `sunshine.db.sig` exists and `pacman-key --verify` succeeds; same for `sunshine.files.sig` if published.
- `check_sunshine_pkg_sigs`: `sunshine-update` and `sunshine-base` package `.sig` files verify; `pacman -Si` emits no signature warnings.
- `check_sunshine_update_self`: `sunshine-update --version` reports `0.9.0`; before network operations it verifies `sunshine.db.sig` and aborts with exit 2 if invalid under `required`.
- `check_sunshine_update_policy`: `/etc/sunshine/system.toml` `[repo] signing = "required" | "warn"`; default `warn` until the repo key is published, then `required`.
- `check_repo_behind_arch`: if `pacman -Syu` fails because `[sunshine]` is behind Arch/soname, report “repo behind Arch” and exit 2; do not force a broken upgrade.

No private key material belongs in the repository. Only the public fingerprint/key file and verification logic are committed.

## 5. Regression tests to add

Add `test/sunshine-update-stage-a.sh`, `test/signed-chain.sh`, `test/upgrade-stage-a.sh`, and `test/stage-src.sh`; wire them into `test/smoke.sh` or CI.

| ID | Setup | Command | Expected |
|---|---|---|---|
| `repo-add` | Built repo | `pacman -Sy` in clean `archlinux` container; `pacman -Si sunshine-update` | Version `0.9.0-1`; `sunshine.db.sig` verifies |
| `base-dep` | Built repo | `pacman -Si sunshine-base` | `Depends On` includes `sunshine-update`; `Conflicts With` does not |
| `bootstrap` | Stock Arch container | `bootstrap.sh --loop` | Exit 0; `pacman -Q sunshine-update` = `0.9.0-1`; second run changes nothing |
| `doctor-idempotence` | Converged container | `sunshine-doctor --fix` twice | Second run exits 0 and changes nothing |
| `upgrade` | Old image with `sunshine-update 0.8.0` | `sunshine-update` | Upgrades to `0.9.0-1`; `pacman -Dk` clean; no partial upgrade |
| `signed-chain` | `SigLevel = Required` | `pacman -Sy`; tamper `sunshine.db` | Valid succeeds; tampered fails; doctor exits 2 |
| `unsigned-policy` | `SigLevel = Optional TrustAll` | `sunshine-doctor --fix`; `sunshine-update` | Warn under `warn`; abort under `required` |
| `stage-src` | Source tree | `scripts/stage-src.sh --check`; rerun | Stages `0.9.0-1`; idempotent; wrong version fails |
| `derivative` | `/etc/os-release` ID=garuda | `sunshine-doctor --fix` | Exit 2; no packages removed |
| `partial-upgrade` | Store/UNI install path | `sunshine-update` | Refuses `pacman -Sy <pkg>`; uses `-Syu` |
| `rollback` | VM with snapper/btrfs | `sunshine-update --rollback` | Restores pre-upgrade snapshot |
| `smoke` | VM after upgrade | `test/smoke.sh` | Plasma/Hyprland session starts |

Definition of done: `Development_Anesthesia` builds the repo, publishes `sunshine-update 0.9.0-1` with signatures, `sunshine-base` pulls it, doctor converges idempotently, and the signed-chain and upgrade tests pass in a clean Arch container and a VM.