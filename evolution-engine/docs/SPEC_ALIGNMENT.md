# Alignment with `TODO/TODO_Migration.md`

This document maps the remote architecture specification to the current prototype. It is
intentionally blunt about what is implemented, what is specified but not production-hardened,
and what remains a real gap.

## Summary

| Spec area | Status here | Notes |
|-----------|-------------|-------|
| §1 Target-state construction | Implemented | `src/target/current.toml`, resolver, capability planner. No release-version branching. |
| §2 Bootstrap package `sunshine-update` | Protocol only | This repo models Stage A inputs; installation/packaging stays in `SunshineOS`. |
| §2.2 Pinned trust root | Implemented in protocol | `src/trust` accepts pinned roots and refuses unsigned metadata. |
| §2.3 Upgradeable bootstrap/handoff | Implemented in protocol | Compatibility checks plus a signed handoff artifact requirement. Rust binary still pending. |
| §3 Stage B discovery | Implemented | Typed observations with confidence/evidence, including users/groups/home directories without secrets. |
| §3 Stage C resolution | Implemented | Automatic single-profile selection; one focused question for ambiguity or conflict. |
| §3 Stage D / §4 planning | Implemented | DAG, typed operations, dependency/conflict checks, full-upgrade rule. |
| §4.3 Typed operations | Implemented | No arbitrary shell in plans; adapters are the only extension point. |
| §5 Component lifecycle | Implemented | Introduce/evolve/replace/reconfigure/retire decisions from observed vs target capability state. |
| §5.1 Component contracts | Implemented | `src/target/contracts/*.toml`, validated against the published target on every apply. |
| §6 Arch foundation | Implemented | Pacman authority, foreign-package uncertainty, managed repository fragments, rollback refusal. |
| §7 Kernel/boot | Implemented | Separate kernel, initramfs and boot-entry operations; checkpoints required before boot work. |
| §8 Configuration ownership | Implemented | Three-way merge, ownership registry, non-destructive fresh-install assignment. |
| §9 Execution/journal | Implemented | Append-only fsynced journal, transaction groups, actual-state reconciliation on resume. |
| §9.4 Reconciliation after interruption | Implemented | Journal entries are hints; probes decide what can be skipped. |
| §11 Repository generations | Implemented in planner | Monotonic generation, no silent rollback, coherent `pacman -Syu`. |
| §13.1 Component bundles | Implemented as data | Profiles and component contracts are versioned TOML; adapters are separate signed units. |
| §13.2 Signed adapters | Implemented in contract layer | Rust-only, signed artifact, narrow permissions, typed parameters, forbidden escape keys. |
| §14 Source-profile limits | Implemented | `arch-standard`, `arch-customized`, `sunshine-installed`, `unsupported`; apply exits 3 for unsupported. |
| §16 Recommended structure | Partially implemented | Python prototype mirrors module boundaries; small Rust bootstrap crate not yet present. |

## Detailed gap register

### G1 — Rust bootstrap is not yet the production entrypoint

The specification asks for a small, self-sufficient bootstrap with a pinned trust root, ideally
written in Rust. `src/trust` implements the *protocol*, and `gpg_verifier()` allows real signature
checking without adding Python crypto dependencies, but the actual trusted binary has not been
built. The Python CLI is a reference implementation and test harness, not the final trust root.

**Exit criterion:** a static Rust binary verifies Stage A, downloads verified Core, and hands off
without relying on Python, Nix, Flatpak or desktop components.

### G2 — Handoff is verified, not yet executed

`verify_stage_a()` requires the handoff descriptor to name a verified artifact and checks protocol
compatibility. It does not spawn the Core entrypoint or record a signed handoff receipt.

**Exit criterion:** Stage A writes a signed receipt containing bootstrap version, Core artifact
digest, protocol version and repository generation; Core refuses to start without it.

### G3 — Artifact signature transport is still deployment-dependent

The current `sunshine-tools` manifest/signature delivery uses the same release server and a local
keyring. The trust model rejects same-server *automatic key trust*, but the release pipeline still
needs a chained rotation document for full alignment. See `docs/SECURITY.md`.

**Exit criterion:** release repository ships a chained rotation record signed by the previous key,
and the bootstrap ships only the first pinned root.

### G4 — Adapter runtime is a contract, not an execution sandbox

`src/adapters.py` validates manifests, permissions, declared parameters and Stage A verification.
It does not load or run Rust adapter binaries. There is no seccomp/landlock policy or process
supervision yet.

**Exit criterion:** executor launches only signed Rust adapters with the declared permission set,
under resource limits, and journals every invocation.

### G5 — Five-year source matrix is representative, not exhaustive

Fixtures cover clean Arch, Plasma, Hyprland, GNOME, XFCE, Sway, a five-year-old Arch state and old
Sunshine. They do not cover every storage/encryption/bootloader/DKMS permutation.

**Exit criterion:** CI matrix includes btrfs/ext4, LUKS, GRUB/systemd-boot, NVIDIA and mixed
AUR states, each with an explicit expected convergence plan.

### G6 — Validation probes are active but deployment coverage is incomplete

Every required capability now has a probe. Unknown capabilities fail closed. However, the probes
are tested mostly against injected executors and fixture sandboxes; live VM validation after a
real migration is still pending.

**Exit criterion:** `--verify` passes on a real migrated system, and deliberate tampering of each
managed capability is detected.

## Implemented safeguards that answer earlier gaps

- `src/fixtures.py` routes both discovery and execution through one injected executor. CLI
  fixture mode can no longer mix fake filesystem state with real host command output.
- `--fixture ... --apply` refuses the live `/var/lib/sunshine` state root; an explicit sandbox is
  mandatory.
- A plan carries `source.observed_fingerprint`. If current discovery differs, execution aborts
  before any command (`stale plan`).
- Conflicting observations for bootloader/network/audio produce one user decision instead of a
  silent first-match guess. PipeWire's Pulse compatibility layer no longer looks like a second
  audio daemon.
- A selected desktop profile can no longer add its own capabilities as prerequisites, which used
  to create a `desktop_integration` dependency cycle.
- Repeated CLI apply is proven idempotent with a persistent fixture sandbox.
- Trust failures block check/plan/apply/verify before discovery or execution starts.
- Component contracts and adapter manifests are validated as data, not trusted implicitly.

## Continuous-loop position

The loop is currently at: **implement → test → break → repair → document → restart with a harder
scenario**. Cycles 12–20 are recorded in `../reports/evolution-engine-breakfix-cycle.md`.
The next hard scenario is G1: build the Rust Stage A bootstrap and make the Python engine the
verified Core it hands off to.
