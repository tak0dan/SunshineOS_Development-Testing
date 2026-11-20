# Stage A adversarial review and hardening — 2026-11-21

## Source

OpenClaw reviewer task `stage-a-review` (free model role `reviewer`) audited the
Stage A verification chain using
`evolution-engine/bootstrap-rust/src/gpg.rs`, `src/trust/model.py`,
`bootstrap-rust/test-stage-a.sh`, `bootstrap-rust/test-rotation.sh`,
`bootstrap-rust/ROTATION.md`, and `reports/STAGE-A-DEPLOYMENT-2026-11-20.md`.
The full result is retained in the OpenClaw task store; no credential values
appeared in the task, result, or this report.

## Accepted findings

### P1 — keyring permissions were not enforced during verification

`verify_detached()` checked only that the keyring was a file. A
group/world-writable keyring could be modified by another local user before
GPG ran, even though `ensure_keyring_permissions()` existed for the deployment
path.

**Fix:** `verify_detached()` now calls `ensure_keyring_permissions()` before any
GPG invocation. The Python reference verifier applies the same `0o022` check
when `gpg_verifier()` is created and raises `PermissionError` otherwise.

### P2 — VALIDSIG matching scanned all status fields

Both implementations accepted a `[GNUPG:] VALIDSIG` line if *any* token after
the marker equalled the expected fingerprint. A timestamp or metadata field
could therefore satisfy the check even when the signer was a different key.

**Fix:** both implementations now expose `validsig_matches()` and compare only
field 2, the signer fingerprint. New unit tests prove that a matching
fingerprint in a later field is rejected, and that `GOODSIG` alone is
insufficient.

### P5 — temporary-directory cleanup was silent or incomplete

Cleanup failures were ignored, and several early error paths left
`sunshine-bootstrap-*` directories behind.

**Fix:** added `cleanup_temp()` in Rust and propagated cleanup failures on all
paths after directory creation. Python already used `TemporaryDirectory`, so
it needed no cleanup change.

## Findings not adopted as-is

- **P3 (signature freshness/expiry window):** GPG validity already rejects
  expired keys, and adding an arbitrary age window would change the trust
  policy without a rotation/custody decision. Recorded for the 20-year
  architecture track instead.
- **P4 (Rust-side receipt-key allowlist):** the privileged wrapper
  `sunshine-evolution` already refuses to start unless the policy fingerprint
  is installed in the root-only receipt home. Adding a second allowlist inside
  `sign_detached()` would need an API change; deferred to the package-audit
  task where wrapper and Rust can be assessed together.

## Regression evidence

| Check | Result |
|---|---|
| Python engine suite | 163 tests, OK (was 161; +2 VALIDSIG/keyring tests) |
| Rust unit tests | 7 tests, OK (was 5; +2 VALIDSIG/keyring tests) |
| `test-stage-a.sh` | verify, handoff, receipt, tamper rejection OK |
| `test-rotation.sh` | chained rotation and all rejection cases OK |
| Canonical and vendored engines | both updated and green |

These fixes preserve the OLD→NEW rotation blocker: no production rotation
material was generated, and no private key material was handled or written.
