# Order 2 — Stage A verifier adversarial hardening review

- Status: done (attempts: 1)
- Agent role: reviewer (nvidia/nemotron-3.5-super-vl:free)
- Source: OpenClaw / OpenRouter delegation from sibling session orders, 2026-11-20

---

## Adversarial review — Stage A verification

Reviewed: `evolution-engine/bootstrap-rust/src/gpg.rs` (full).  
Omitted from context: `evolution-engine/src/trust/model.py`, `evolution-engine/bootstrap-rust/test-stage-a.sh`, `evolution-engine/bootstrap-rust/test-rotation.sh`, `evolution-engine/bootstrap-rust/ROTATION.md`. Locations below for omitted files are inferred from the task and must be confirmed against those files; no rotation material or private keys are invented.

---

### Finding 1 — Caller-controlled keyring, no anchor binding
**Location:** `evolution-engine/bootstrap-rust/src/gpg.rs`, `verify_detached` (signature verification entry).  
**Defect:** `verify_detached` accepts any `keyring: &Path`, checks only `is_file()` and (via `ensure_keyring_permissions`) group/world bits. It never confirms the keyring is the designated Stage A trust anchor, nor that `expected_fingerprint` is actually present in that keyring.  
**Exploit:** A caller (or compromised config) supplies an attacker-controlled keyring containing the attacker’s key and passes the attacker’s fingerprint as `expected_fingerprint`; `--no-default-keyring --keyring <attacker keyring>` then validates a signature the attacker made.  
**Patch:** In `verify_detached`, before `--verify`, canonicalize `keyring` and require it to equal the Stage A keyring constant/path, **or** run `gpg --homedir <temp> --no-default-keyring --keyring <keyring> --list-keys --with-colons` and assert a `pub` record whose fingerprint equals `expected`. Reject otherwise.

### Finding 2 — Stale bootstrap / replay accepted
**Location:** `evolution-engine/bootstrap-rust/src/gpg.rs`, `verify_detached`, VALIDSIG parse loop.  
**Defect:** The code matches only the fingerprint field (`fields[2]` after `[GNUPG:]` `VALIDSIG`) and ignores the signature creation time (`fields[3]`) and expiration (`fields[4]`). A cryptographically valid but old Stage A signature can be replayed.  
**Exploit:** Replay a previously captured valid bootstrap signature after its approval window has closed.  
**Patch:** Add a freshness parameter (e.g. `not_before: u64` / bootstrap mint epoch) to `verify_detached`. Parse `fields[3]` as epoch seconds from the `VALIDSIG` line and reject if `created < not_before` or `created > now + tolerance`. Do not accept signatures without a parseable creation time.

### Finding 3 — VALIDSIG matched but signer never approved
**Location:** `evolution-engine/bootstrap-rust/src/gpg.rs`, `verify_detached`, `fields.iter().skip(2).any(...)`.  
**Defect:** `expected_fingerprint` is caller-supplied and is never checked against an approved-signer allowlist. VALIDSIG only proves *some* key matching `expected` signed; it does not prove `expected` is an authorized Stage A signer.  
**Exploit:** Accept a signature from an unapproved key if the caller passes its fingerprint.  
**Patch:** Add `approved_signers: &[&str]` (or read from the Stage A manifest) and require `expected` to be in that list **in addition** to the VALIDSIG fingerprint match.

### Finding 4 — Receipt-key precondition skipped in `sign_detached`
**Location:** `evolution-engine/bootstrap-rust/src/gpg.rs`, `sign_detached`.  
**Defect:** Only `gpg_home.is_dir()` is checked. The function never confirms `fingerprint` exists in `gpg_home`, is a secret/signing-capable key, or equals the designated receipt key.  
**Exploit:** Signing with a wrong or absent key fails only at gpg invocation time; there is no explicit precondition and no binding of the receipt to an approved receipt key.  
**Patch:** Before `--detach-sign`, run `gpg --homedir <gpg_home> --list-secret-keys --with-colons` and assert a `sec`/`ssb` record for `fingerprint` with signing capability (`S`), or require `fingerprint` to equal a configured `RECEIPT_FINGERPRINT`. Reject if missing.

### Finding 5 — Keyring permissions incomplete
**Location:** `evolution-engine/bootstrap-rust/src/gpg.rs`, `ensure_keyring_permissions`.  
**Defect:** Checks group/world writable bits but not ownership (uid) and not that the path is a regular file vs symlink (though `is_file()` is checked earlier in callers, not here).  
**Patch:** Add ownership check (`metadata.uid() == current uid`) and confirm `metadata.is_file()` and mode `0o600` or stricter.

### Finding 6 — Non-UTF8 path truncation (minor)
**Location:** `evolution-engine/bootstrap-rust/src/gpg.rs`, `verify_detached` / `sign_detached`, `keyring.to_string_lossy().as_ref()`.  
**Defect:** `to_string_lossy` can mangle non-UTF8 paths, potentially passing a different path to `--keyring`.  
**Patch:** Use `OsStr` directly via `.args([...])` with `keyring.as_os_str()` instead of lossy conversion.

---

## Exact patch locations (Rust)

| File | Function / anchor | Change |
|------|-------------------|--------|
| `evolution-engine/bootstrap-rust/src/gpg.rs` | `verify_detached` | Add `approved_signers` + freshness params; keyring anchor binding; pre-verify keyring contains `expected`; parse VALIDSIG creation time. |
| `evolution-engine/bootstrap-rust/src/gpg.rs` | `sign_detached` | Add receipt-key presence/capability precondition in `gpg_home` before signing. |
| `evolution-engine/bootstrap-rust/src/gpg.rs` | `ensure_keyring_permissions` | Add uid ownership and strict mode check. |
| `evolution-engine/bootstrap-rust/src/gpg.rs` | `verify_detached` / `sign_detached` | Replace `to_string_lossy().as_ref()` with `as_os_str()` for path args. |

---

## Omitted files — what to inspect / patch

- `evolution-engine/src/trust/model.py`: confirm the Python trust model imports/duplicates the same Stage A keyring anchor and approved-signer list; add validation that the keyring path is canonical and that `expected_fingerprint` is in the allowlist before verification. Do not hardcode or generate rotation keys.
- `evolution-engine/bootstrap-rust/test-stage-a.sh`: add negative cases below; assert exit code != 0 and stderr contains the rejection reason.
- `evolution-engine/bootstrap-rust/test-rotation.sh`: preserve the OLD→NEW rotation blocker; add an assertion that no new rotation material is accepted without the OLD key’s prior authorization. Do not fabricate rotation keys or signatures.
- `evolution-engine/bootstrap-rust/ROTATION.md`: document that Stage A receipt signing requires the precondition from Finding 4 and that OLD→NEW rotation remains blocked until the OLD key authorizes the NEW key.

---

## New regression test names

**Rust (`evolution-engine/bootstrap-rust/tests/` or `#[cfg(test)]` in `src/gpg.rs`)**
- `verify_detached_rejects_attacker_controlled_keyring`
- `verify_detached_rejects_keyring_missing_expected_fingerprint`
- `verify_detached_rejects_stale_or_replayed_signature`
- `verify_detached_requires_approved_signer`
- `verify_detached_rejects_unapproved_signer_with_validsig`
- `sign_detached_rejects_unknown_receipt_key`
- `sign_detached_rejects_non_signing_key`
- `ensure_keyring_permissions_rejects_group_world_writable`
- `ensure_keyring_permissions_rejects_wrong_owner`

**Python (`evolution-engine/src/trust/tests/` or `tests/trust/`)**
- `test_stage_a_rejects_wrong_keyring_path`
- `test_stage_a_rejects_stale_bootstrap_signature`
- `test_stage_a_requires_approved_signer_fingerprint`
- `test_stage_a_rejects_unapproved_signer`
- `test_receipt_signing_enforces_key_presence_precondition`

**Shell (`evolution-engine/bootstrap-rust/test-stage-a.sh`, `test-rotation.sh`)**
- `stage_a_wrong_keyring_must_fail`
- `stage_a_stale_signature_must_fail`
- `stage_a_unapproved_signer_must_fail`
- `stage_a_missing_receipt_key_precondition_must_fail`
- `rotation_old_to_new_blocker_preserved` (in `test-rotation.sh`)

Each shell test should exercise the binary with a tampered keyring, expired/replayed signature, or unapproved fingerprint and assert non-zero exit plus a deterministic rejection message.

---

## Rotation blocker constraint

Preserve the OLD→NEW rotation blocker: do not add, generate, or commit any rotation key material, fingerprints, or signatures. All new tests must use synthetic, clearly-labeled test-only keys and must assert rejection, not issuance, of rotation material.
