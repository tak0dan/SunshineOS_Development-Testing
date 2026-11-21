# Live VM validation of `sunshine-update 0.9.0-2` — 2026-11-21

## Setup

- VM: `SunshineOS-Audit` (running, UEFI, NAT SSH).
- Disposable snapshot before the test: `pre-0.9.0-2-package`, UUID `d8c2087e-9eff-412c-8912-8791f8a76757`.
- Package copied from `tak0dan/SunshineOS` `Development_Anesthesia` commit `f707d18`.
- Release asset SHA-256: `f11ab1a9a9465c5310acdb155aa08d9c121235b79e2378bd80d7fbfec7ea6152`.

## Results

| Check | Result |
|---|---|
| `pacman -U sunshine-update-0.9.0-2-x86_64.pkg.tar.zst` | upgraded `sunshine-update` to `0.9.0-2`; snapshot pre/post hooks ran |
| Installed wrapper | contains `exec pkexec sunshine-evolution "$@"` for unprivileged callers; no `sudo` fallback |
| Installed Core digest | `/usr/share/sunshine/evolution/src/trust/model.py` SHA-256 `7b4c43809cd21f67072f5938d6104b0e1efd7621a9e2902d11526f5ced3b5fbf` |
| Rust Stage A `verify` | exit 0; `passed true`; `errors []`; `artifacts_verified ["core"]`; generation `1`; target `sunshine-2026.11`; trusted keys `["2FEC611A7F97ED9A37294C90D16F3BE763A4B6BE"]`; `rotated_keys []` |
| Receipt-key custody | `sunshine-evolution --help` as root refuses to start: receipt signing key is not installed in `/etc/sunshine/trust/receipt-home` |
| Secret exposure | no private key material observed in the package or receipt home; only public keyring and trust database files present |

The receipt-home refusal is intentional for this disposable snapshot: the package ships public trust
material only, and the root-owned receipt signing key must be provisioned out of band before the
privileged handoff path can run.

## Interpretation

The Stage A verifier accepted the shipped NEW-pinned index in the live guest. The wrapper now
enforces the declared polkit channel, and a missing receipt key fails closed before any handoff.
The empty `rotated_keys` list is expected: no production OLD→NEW rotation was fabricated, and the
OLD private key remains unavailable.

## Next break attempts

From `reports/VBOX_ATTACK_SURFACE_PLAN_2026-11-21.md`, the next disposable-snapshot attempts are:
guestcontrol engine replacement, NAT SSH concurrent apply, and checkpoint removal with snapshot
restore. Any fix must preserve the signed chain and tri-pass convergence behavior.
