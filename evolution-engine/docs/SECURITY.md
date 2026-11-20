# Security model and threat analysis

## Trust chain

1. The user obtains and installs a genuine, signed `sunshine-update` package through pacman.
   Package authenticity comes from Arch's existing signature trust — not from anything downloaded
   later.
2. That package contains a pinned Sunshine repository trust root (`repository-root.pub`).
3. The bootstrap verifies signed repository metadata before retrieving anything else.
4. The metadata names the current target and required artifacts with digests.
5. Every artifact is hash- and signature-verified before installation or execution.
6. Key rotation is chained: a new key is signed by the previous root, or by an out-of-band
   verified procedure recorded in the repository. **A key is never fetched from the same
   unauthenticated server that serves the code it signs.**

The protocol-level implementation is in `src/trust`: a downloaded key is only trusted after a
rotation record verifies against a key that was already trusted, self-signed rotations are
rejected, artifacts must match signed SHA-256 digests, and the Core handoff must name a verified
artifact.

> Known production gap: the current `sunshine-toolsync` fetches its manifest and signature from
> the same GitHub release and trusts a local GPG keyring file. Rotation therefore still requires
> updating that keyring out-of-band (as done in the 2026-11-20 rotation). The release must ship a
> chained rotation document signed by the previous key, and the pinned root must live inside a
> small Rust bootstrap rather than the Python CLI.

## Privilege model

- Avoid broad sudoers rules. Use narrow, polkit-authorized privileged helpers.
- The bootstrap Critical logic must not depend on Python/Nix/Flatpak/desktop components it is
  supposed to install.
- Components cannot modify the trust root, bypass journaling, or self-authorize privileged
  operations. Typed operations run under the executor's security model; signed Rust adapters may
  extend primitives but remain inside the same authorization and validation boundaries.

## Threats and mitigations

| Threat | Mitigation |
|--------|------------|
| Malicious repository serves trojaned tools | Detached signature + per-file SHA-256 from signed manifest; path allow-list; rollback refusal |
| Downgrade to vulnerable release | Repository generation monotonicity; version comparison refuses older releases |
| Key substitution | Pinned root in package; chained rotation; keyring updated only out-of-band |
| TOCTOU on downloaded archive | Extract to private temp dir, verify each file before install, use realpath checks, reject symlinks |
| Privilege escalation via component metadata | Metadata signed; operation parameters validated; no arbitrary shell in manifests |
| Destructive action from bad discovery | Confidence levels; low-confidence observations cannot authorize destructive ops |
| Interrupted transformation corrupts system | Append-only fsynced journal, transaction checkpoints, re-discovery before resume |
| Partial-upgrade breakage | Coherent full-upgrade transactions; refuse partial upgrades |
| Loss of user configuration | Ownership classification; three-way merge; preserve user/system/unknown conservatively |
| Boot failure after kernel migration | Install alongside existing kernel, keep previous entry, validate before committing |
| Reviewed plan executed against mutated machine | `source.observed_fingerprint` mismatch aborts as `stale plan` before any command |
| Contradictory discovery guesses user intent | Distinct bootloader/network/audio signals force one focused decision |
| Fixture/demo leaks real host state | Single injected executor for discovery and execution; live state root refused |

## Fail-closed rules

- Unknown capability → validation failure.
- Missing provider or dependency cycle → plan rejected.
- Invalid/unsigned metadata → abort before any transformation.
- Ambiguous source profile → preflight failure with precise explanation.
- Low-confidence destructive operation → refused.
