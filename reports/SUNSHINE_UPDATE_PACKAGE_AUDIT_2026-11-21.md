# `sunshine-update` package consistency audit — 2026-11-21

## Source

OpenClaw task `package-audit` was delegated with the reviewer role, but every supplied credential
returned `HTTP 429` during completion calls. This report is the manual backstop. It audits the
package source in `tak0dan/SunshineOS` on `Development_Anesthesia` under
`packages/sunshine-update/`. No private key material or credential values appear below.

## Findings and applied fixes

### A1 — privileged entry could fall back to `sudo`

`sunshine-evolution` accepted an interactive TTY path that re-executed itself via `sudo`. The
signed policy declares `required_privileged_channel: polkit`, so a broad sudoers grant could be used
to reach Core without the intended polkit authorization.

**Fix:** unprivileged callers now use `pkexec` only; root may invoke the binary directly. No sudo
fallback remains. `sh -n` passes.

### A2 — trust provisioning could import into the wrong keyring

`tools/provision-stage-a.sh` imported the public key with `--no-default-keyring --keyring ...` while
inheriting the operator's `GNUPGHOME`. Host keyboxd configuration can make `--keyring` be ignored,
the same failure mode already fixed in the Python and Rust verifiers. The script also accepted an
arbitrary `SUNSHINE_SIGNING_FP` string and contained an unused `sign_hex` helper.

**Fix:** the import and post-import key listing now run with a pristine temporary `GNUPGHOME`; the
fingerprint is validated as 40 hexadecimal characters; the dead helper was removed. `bash -n`
passes.

### A3 — vendored engine could drift silently

`PKGBUILD` built from `engine/` with `source=()` and no manifest. A local edit to the vendored
engine would be compiled and shipped without detection, even though `ENGINE-NOTES.md` says the
tree must be copied verbatim from `SunshineOS_Development-Testing`.

**Fix:** generated `engine.sha256` (154 files, excluding `target/`, `pkg/`, and `__pycache__/`) and
added a `prepare()` step in `PKGBUILD` that runs `sha256sum -c` before compilation. The vendored
engine now has zero source-file differences from the canonical engine at DevTesting `9999a0f`.

### A4 — package release metadata lagged source changes

The published asset was `sunshine-update-0.9.0-1`. After the fixes above, `pkgrel` was bumped to 2
and a new release asset was published.

## Regression evidence

| Check | Result |
|---|---|
| Vendored Python engine suite | 163 tests, OK |
| Rust unit tests | 7 tests, OK |
| `test-stage-a.sh` | verify, handoff, receipt, tamper rejection OK |
| `test-rotation.sh` | chained rotation and all rejection cases OK |
| `sha256sum -c engine.sha256` | 154 files OK |
| `sh -n sunshine-evolution`, `bash -n tools/provision-stage-a.sh` | OK |
| `makepkg -f` | `sunshine-update 0.9.0-2` built successfully |
| Package contents scan | no private keys or secret files; only empty `etc/sunshine/trust/receipt-home/` |

Published asset: `sunshine-update-0.9.0-2-x86_64.pkg.tar.zst`
SHA-256: `f11ab1a9a9465c5310acdb155aa08d9c121235b79e2378bd80d7fbfec7ea6152`
Release: `https://github.com/tak0dan/SunshineOS_Development-Testing/releases/tag/sunshine-update-0.9.0-2`

The production OLD→NEW rotation blocker is unchanged: no OLD-signed rotation record was fabricated,
and no private key was written to the package tree.
