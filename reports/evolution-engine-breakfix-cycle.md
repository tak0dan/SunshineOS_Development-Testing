# Evolution Engine — continuous break/fix cycle

This report records the **implement → test → break → fix → try to break again**
loop run against the Sunshine Evolution Engine. Every defect below was found by
an actual failing test or a live VM run, fixed, and covered with a regression
test. The engine is exercised on three fixtures (`clean-arch`, `old-sunshine`,
`arch-plasma`) and on the live `SunshineOS-Audit` VM.

Status at the end of this cycle: **56 unit/integration tests pass; all three
fixtures and the live VM complete a full `--apply --dry-run` with zero failed
operations and zero errors.**

## Cycle 1 — class identity mismatch

**Symptom.** Planner unit tests passed but integration failed with an
`isinstance` error: discovery produced `core.ObservedState`, planner expected
`src.core.ObservedState`.

**Root cause.** `src/discovery/__init__.py` imported `core` as a top-level
module while the planner used the package path `src.core`. Python created two
distinct classes with the same name.

**Fix.** Discovery now prefers the relative import (`from ..core ...`) with a
standalone-script fallback.

**Regression guard.** `test_single_class_identity` asserts
`isinstance(state, ObservedState)` across the discovery→planner boundary.

## Cycle 2 — capability names treated as component IDs

**Symptom.** A plan's component dependency edges were missing on pure Arch.

**Root cause.** `ComponentSpec.requires` contains capability names (e.g.
`unified-configuration`), but the planner looked them up as component IDs.

**Fix.** `src/planner/planner.py` now resolves a required capability to the
component that provides it before creating dependency edges.

## Cycle 3 — false network decision from unrelated evidence

**Symptom.** `clean-arch` produced a user decision: *"Observed network
'systemd' is not supported by this target."*

**Root cause.** `_observed_choice()` searched free-form evidence text. A generic
`services.systemd` observation whose evidence mentioned "network" was misread
as the network backend choice.

**Fix.** The category must appear in the observation's *identity* (key or
component), and key-suffix values are preferred over evidence tokens.
`clean-arch` now resolves `networkmanager` automatically; only the genuinely
ambiguous desktop choice requires input.

**Regression guard.** `test_network_choice_not_inferred_from_unrelated_service`.

## Cycle 4 — discovery crashed on empty successful command output

**Symptom.** Five integration tests errored with `IndexError: list index out of
range`.

**Root cause.** `lines(stdout)[0]` was evaluated before checking whether the
command produced any output. A command that exits 0 with no stdout is normal.

**Fix.** Guard both `command_ok(rc)` and a non-empty line list in
`_detect_init_system` and distribution detection.

**Regression guard.** `test_discovery_survives_empty_command_output` uses an
executor that returns success with empty output for every command.

## Cycle 5 — generic Arch capabilities mistaken for Sunshine registration

**Symptom.** The pure-Arch plan skipped introduction of boot, kernel, desktop
and recovery components (6 of 7 required components registered instead of 7).

**Root cause.** `_detect_presence()` treated *any* provider of a capability as
proof that the Sunshine component providing it was registered. Clean Arch
already has GRUB (`boot-entry-management`) and mkinitcpio
(`kernel-installation`), so the planner concluded those components existed.

**Fix.** Presence now requires an explicit Sunshine marker
(`sunshine-component:<id>`), a matching observation detected as such a marker,
or evidence naming a Sunshine registration.

**Regression guard.** `test_generic_arch_capabilities_do_not_count_as_registration`.

## Cycle 6 — transaction grouping inverted the DAG

**Symptom.** Dry-run aborted: *"operation …RegisterComponent depends on
…InstallBootEntry in a later transaction group"*.

**Root cause.** `group_for()` forced all `CreateCheckpoint` operations into the
`bootstrap` group, and a component's `RegisterComponent` was assigned to an
earlier architectural group than its own `InstallBootEntry`. Sequence ordering
therefore violated dependency edges.

**Fix.** Checkpoint groups are derived from their dependencies, and a general
promotion pass moves every dependent to at least its dependency's group before
the group sequence is rebuilt (the topological order within groups is kept).

**Regression guard.** `test_executor_group_promotion_preserves_dag_order`
verifies every dependency runs before its dependent in the completed sequence.

## Cycle 7 — partial upgrades forbidden by Arch

**Symptom.** Dry-run aborted: *"repository databases changed but no foundation
full-upgrade operation (partial upgrades are refused)"*.

**Root cause.** When the repository generation changes, Arch requires one
coherent `pacman -Syu` transaction before any selective package install. The
planner emitted selective installs without a foundation upgrade.

**Fix.** The planner emits a single `foundation.full-upgrade` operation when
the repository generation changes and package installation is needed, and
makes every `InstallPackages` operation depend on it. The operation is added to
the graph first so dependency order is valid regardless of component order.

## Cycle 8 — dry-run reported changes

**Symptom.** `ExecutionResult.status == "dry_run"` but `changed == True`.

**Fix.** `result.changed` is now only set when not in dry-run mode.

**Regression guard.** `test_dry_run_execution_changes_nothing` asserts both
`changed is False` and that no state files are created.

## Cycle 9 — `--apply` blocked on already-answered decisions

**Symptom.** After adding `--decide desktop-profile=hyprland`, `--apply` still
printed "Unresolved decisions" and exited 2.

**Root cause.** The gate checked all decisions rather than only those still
requiring user input.

**Fix.** Gate on `[d for d in plan.decisions if d["requires_user_input"]]`.

## Cycle 10 — boot entry refused by the executor (live VM)

**Symptom.** Live VM dry-run failed on the 12th operation: *"refused: invalid
boot entry label or loader"*.

**Root cause.** `plan_boot_integration` passed `ctx.spec.software_version`
(`"2026.1"`) as the EFI loader path. The default label, `boot_integration`,
also contained an underscore, which the label regex rejects.

**Fix.** Emit an absolute loader path (`/boot/EFI/Linux/sunshine.efi`) and an
explicit valid label (`Sunshine OS`). Added a `label` parameter to
`ops.install_boot_entry()`.

**Regression guard.** `test_boot_entry_loader_is_an_efi_path_with_valid_label`
checks every fixture.

## Cycle 11 — ownership transfer refused on fresh installs

**Symptom.** Pure-Arch fixtures failed dry-run: *"refused: low-confidence
observations; refusing ownership transfer"*. The live VM (with existing
Sunshine state at high confidence) succeeded.

**Root cause.** The ownership strategy always emitted a *destructive*
`chown -R` even when no Sunshine tree existed. On a clean install there is
nothing to take over; assigning the intended owner to directories we create is
not destructive and must not be gated by observation confidence.

**Fix.** `transfer_ownership()` gained a `destructive` parameter. The planner
sets it from `_has_sunshine_tree()`: False for a fresh install, True when
`/etc/sunshine`, `/var/lib/sunshine` or component schemas actually exist.
The `old-sunshine` fixture was also made more faithful by adding
`etc/sunshine/config.toml`, so discovery reports a real, high-confidence tree.

**Result.** All three fixtures and the live VM now complete a full dry-run.

## Live VM evidence

Command (guest control, after copying `src/` into the guest):

```
python3 /tmp/evolution-engine/src/engine.py --root / \
  --state-root /tmp/eve-state --apply --dry-run \
  --decide desktop-profile=hyprland
```

Final result:

```
status: dry_run | changed: False | completed: 25 | failed: (none)
errors: []
```

Discovery on the VM observed distribution `sunshineos`, 1335 packages,
1 foreign package, repositories `[sunshine, core, extra, multilib,
chaotic-aur]`, 20+ capabilities, and required components across core,
configuration, ownership, kernel management, boot integration, recovery and
desktop integration.

## What is intentionally still strict

These are safety properties, not bugs; tests confirm they keep working:

- Low-confidence observations **refuse destructive operations** (ownership
  transfer, configuration replacement, service disable).
- A repository-generation change **refuses partial upgrades**.
- A plan with dependency cycles or missing edges is rejected at build time.
- Validation of an unknown capability fails closed.
- Dry-run never writes state.

## Next break attempts

1. Interrupt a real apply mid-transaction and verify journal resume.
2. Inject a conflicting package state after planning and verify re-discovery
   invalidates the stale plan.
3. Feed deliberately contradictory observations (two desktop sessions, two
   bootloaders) and confirm the decision gate asks rather than guesses.
4. Run the engine against a minimal Arch ISO with no `/etc/sunshine`, then
   re-run it to prove convergence is idempotent.

---

## Cycle 12 — fixture CLI used the real host as an oracle

**Symptom.** `sunshine-evolve --fixture clean-arch --check` reported the developer's host
distribution and package set in some paths, even though the filesystem root was a fixture.

**Root cause.** Only discovery's filesystem reads were redirected. External commands still went
through `subprocess.run`, so a fake Arch tree was combined with real host command output.

**Fix.** `src/fixtures.py` now owns a reusable `FixtureExecutor`. The CLI injects it into both
discovery and execution; unknown commands fail instead of silently falling back to the host.

**Regression guard.** `tests/test_cli.py::test_plan_is_faithful_without_host_subprocess_leakage`
and `test_check_uses_fixture_distribution_not_host`.

## Cycle 13 — dry-run apply returned exit code 1

**Symptom.** A successful offline dry-run printed `status: dry_run` but `main()` returned 1.

**Root cause.** The success status whitelist used old names (`completed`, `no-op`) that the
executor never emits; it now emits `success` or `dry_run`.

**Fix.** CLI accepts `success`, `no-op` and `dry_run`.

**Regression guard.** `test_dry_run_apply_completes_offline` and
`test_real_apply_and_repeat_are_idempotent`.

## Cycle 14 — `--fixture` and `--root /` looked equivalent

**Symptom.** Passing both flags could be read as "fixture filesystem with live host commands",
and fixture `--apply` defaulted to the real `/var/lib/sunshine` state root.

**Root causes.** The mutual-exclusion check compared against a mutable default, and argparse's
error path raised `SystemExit` in in-process CLI tests. The sandbox default was unsafe.

**Fix.** `--root` defaults to `None`; fixture mode rejects an explicit root with a normal exit 2.
Fixture apply refuses the live state root unless the operator passes an explicit sandbox.

**Regression guard.** `test_fixture_and_root_are_mutually_exclusive`,
`test_fixture_apply_refuses_live_state_root`.

## Cycle 15 — detected desktops created a dependency cycle

**Symptom.** `--fixture arch-hyprland --plan` failed with
`component dependency cycle detected among: desktop_integration`.

**Root cause.** Resolver appended a profile's `required_capabilities` to the component's
`requires` list, even though those capabilities are also in the component's own `provides`.

**Fix.** Requirements already provided by the same component are filtered out. The reasoning is
documented in `src/target/resolver.py`.

**Regression guard.** `test_profile_capabilities_do_not_create_self_dependency`; all desktop
fixtures now plan and dry-run.

## Cycle 16 — contradictory bootloaders were silently resolved

**Symptom.** A machine with GRUB and systemd-boot evidence inherited whichever observation was
iterated first.

**Root cause.** `_observed_choice()` returned a single first match without checking whether other
observations disagreed.

**Fix.** `_observed_choices()` collects all distinct signals; `_preserve_choice()` emits one
focused question when they disagree or when one is unsupported.

**Regression guard.** `test_conflicting_bootloaders_ask_one_question` and the contradictory-state
tests in `tests/test_target.py`.

## Cycle 17 — PipeWire compatibility looked like PulseAudio

**Symptom.** A normal PipeWire system produced a false "Which audio should Sunshine use?" decision
because `pactl info` succeeded through `pipewire-pulse`.

**Root cause.** Discovery treated `pactl` output as evidence of a legacy PulseAudio daemon.

**Fix.** When PipeWire is present and the only Pulse evidence mentions PipeWire compatibility, the
Pulse observation is downgraded and recorded as a compatibility layer, not a competing backend.

**Regression guard.** Full suite plus `tests/test_integration.py` compatibility assertions.

## Cycle 18 — no tamper check existed between plan and execute

**Symptom.** A plan built against one machine state could be executed after packages changed.

**Fix.** `state_fingerprint()` stores a stable digest in `Plan.source`. When current discovery is
supplied, a mismatch aborts with `stale plan` before any command runs.

**Regression guard.** `test_stale_plan_is_refused_after_state_changes` asserts zero commands run.

## Cycle 19 — trust and component metadata were only documentation

**Symptom.** The spec required signed metadata, chained rotation, handoff verification and
component contracts, but the engine had no typed implementation to test.

**Fix.** Added `src/trust` (signed index, artifact digests, chained key rotation, self-signed-key
rejection, protocol/core compatibility, signed handoff), `src/components` (contracts validated
against target) and `src/adapters` (Rust-only signed adapters with narrow permissions and typed
parameters). CLI accepts `--trust-index`, `--trust-policy` and `--trust-keyring` and blocks all
commands when Stage A fails.

**Regression guard.** `tests/test_trust.py` and `tests/test_components.py`, plus
`test_failed_stage_a_blocks_apply_before_discovery`.

## Cycle 20 — repeated apply changed files again

**Symptom.** A second real fixture apply reported `changed: true`, violating the five-year
convergence contract.

**Root causes.** Ownership records were rewritten with a fresh timestamp, and the fixture executor
did not remember installed packages between CLI invocations.

**Fix.** Ownership transfer is now content-addressed and reuses an identical record. Fixture
executor state is persisted inside the caller's sandbox, and dry-run/read-only commands get no
sandbox state at all.

**Regression guard.** `test_real_apply_and_repeat_are_idempotent` and
`test_dry_run_does_not_create_state`.

## Cycle 21 — live VM exposed false bootloader/network conflicts

**Symptom.** After stricter contradiction detection, the live VM reported
`Conflicting bootloader choices: grub, refind` and `Conflicting network choices:
networkmanager, systemd-networkd`, blocking dry-run with two extra questions.

**Root cause.** Installed-but-unused packages were treated as equally strong evidence as running
backends. GRUB had an EFI entry and configuration; rEFInd was only installed. NetworkManager had
active units; systemd-networkd was only installed.

**Fix.** Observations now carry a signal-strength tier: running/configured + corroborating
evidence outranks mere installation. Only equally strong signals compete; a weaker alternative is
recorded but does not force a user decision.

**Regression guard.**
`test_installed_only_alternative_does_not_create_conflict`; live VM check now reports a single
legitimate desktop-profile question instead of three.

## Cycle 22 — the trust root was only a Python protocol

**Symptom.** The specification required a small Rust bootstrap with a pinned root and a verified
handoff. The engine had typed trust rules, but Python itself was still the entrypoint and no signed
handoff receipt existed.

**Root cause.** Stage A was modeled as data validation inside Core. Nothing established a
trustworthy boundary between "verify" and "transform", and nothing bound the Core artifact digest
to the transformation that followed.

**Fix.** Added `bootstrap-rust/`: a std-only Rust binary with SHA-256, canonical JSON and GPG
verification. It verifies the signed index, rotations, artifacts and handoff descriptor, writes a
signed receipt, and `exec()`s the verified Core with `--trust-report` and `--trust-receipt`. Core
re-verifies the receipt, including the Stage A report digest, before discovery or mutation.

**Regression guards.** `cargo test` (4 tests), `test-stage-a.sh` (real GPG key, handoff, tampered
receipt rejection) and Python `tests/test_bootstrap.py`. A new CLI test proves `--trust-report`
without a receipt is refused.

## Cycle 23 — a key in the keyring was still being treated as trusted

**Symptom.** The 2026-11-20 tools rotation replaced a local keyring file out-of-band. Nothing in the
release proved that the new key could be reached from the root an existing install already trusted.
The rotation payload also carried `valid_after` without enforcing it.

**Root cause.** A rotation record and a public-key file are different trust statements. The old
protocol accepted any well-formed record from an already-trusted signer but did not prove the
release pipeline order, and the signed date was only metadata.

**Fix.** Added `bootstrap-rust/test-rotation.sh` and `bootstrap-rust/ROTATION.md`: OLD pins the
package, OLD signs the index and OLD→NEW rotation, NEW signs Core. A third key is deliberately
present in the keyring but rejected because the signed chain does not promote it. Rust and Python
now reject future or malformed `valid_after` values before adding the key to the trust set.

**Regression guards.** Chained rotation verify, self-signed rotation rejection, untrusted-signer
rejection, rotation-disabled rejection, unapproved-artifact rejection, plus
`test_future_rotation_date_is_rejected` and Rust `rotation_dates_use_utc_calendar_days`.

## Cycle 24 — adapter contracts could be honored without launching anything

**Symptom.** `src/adapters.py` validated manifests but `dispatch()` still routed every
`MigrateConfiguration`-style operation to built-in primitives. A plan could name an adapter without
a registry, and no invocation reached the journal.

**Root cause.** The adapter interface existed only as data. There was no registry bound to Stage A,
no launch boundary and no audit trail for adapter processes.

**Fix.** `AdapterRegistry` verifies manifest and artifact signatures plus the Stage A artifact set,
and rechecks the digest before launch. `execute_adapter()` refuses unregistered adapters and
builds a shell-free `systemd-run --scope` command with no network, no capabilities, explicit
read/write paths and memory/CPU/process/time limits. Journal entries now carry the invocation ID,
artifact digest, permissions, limits and parameter names on both success and failure.

**Regression guards.** `tests/test_adapter_runtime.py` covers registry verification, TOCTOU
tampering, sandbox command construction, successful and failed journaling, and refusal without a
registry. A regression in manifest parsing was found during this cycle when a table-form
`[signature]` was read as a string; the parser now handles both legacy and signed forms.

## Cycle 25 — storage/boot capabilities did not drive recovery tooling

**Symptom.** Building the source matrix exposed that the published target installed `btrfs-progs`
on a plain ext4/LUKS root and `os-prober` on a systemd-boot system, while a LUKS root got no
`cryptsetup` and no explicit header/crypttab recovery intent. The plan was "correct" only by
accident of the conservative default package set.

**Root cause.** `current.toml` lists recovery/boot tools unconditionally. The resolver only
specialised desktop/network/audio/Nix choices, so it never narrowed or extended tooling from
observed storage and bootloader capabilities.

**Fix.** `_resolve_storage_providers()` now removes `btrfs-progs` when the btrfs capability is
absent, removes `os-prober` for systemd-boot, adds `cryptsetup` when LUKS is present, and records a
`storage-providers` decision with the evidence. `plan_recovery()` adds an explicit "back up LUKS
headers and /etc/crypttab before boot changes" intent to pre-boot checkpoints on encrypted roots.
The ext4/LUKS fixture now reports `cryptsetup` as installed.

**Regression guards.** `test_source_matrix.py` asserts forbidden/required install packages per case
and the LUKS checkpoint markers; the fixture apply is idempotent. A first implementation silently
kept the empty `boot_integration` set because it only persisted on change — fixed with explicit
`boot_changed`/`recovery_changed` flags and covered by the plan assertions.

## Cycle 26 — the matrix tested code paths, not declared source shapes

**Symptom.** Five hand-written fixture tests existed, but there was no single declarative matrix
that said which filesystem/bootloader/encryption/AUR axes were covered or what each convergence
plan must contain. A new source shape could be added without a matching expectation.

**Root cause.** Fixtures were discovered ad hoc in individual tests; expectations were implicit in
assertions scattered across the suite.

**Fix.** Added `tests/source-matrix.toml` as the single source of truth: each case names its
fixture, axes, source profile, observed filesystem/LUKS/btrfs/bootloader/AUR/foreign packages,
forbidden installs and checkpoint markers; `[convergence]` lists required/forbidden operation types
and the mandatory full-upgrade foundation operation. `tests/test_source_matrix.py` turns the data
into discovery, plan and apply/idempotency assertions; `./test-source-matrix.sh` is the CI proof.

**Regression guards.** Two more failure modes were found and fixed while making the matrix pass:
the new/aged fixtures had no Wayland session file, so the decided Hyprland profile failed
post-apply validation; and the test looked for `foundation.full-upgrade` as a package name when it
is the id of the full-upgrade operation. Both are now covered by the five matrix cases.

## Cycle 27 — `--verify` checked the pristine fixture, not the migrated system

**Symptom.** After a successful fixture apply, `--verify` passed even though it never inspected the
sandbox where the migration wrote its configuration, components and journals. Serialized reports
were Python `ValidationReport(...)` repr strings, not JSON objects. Bootloader validation accepted
the presence of an EFI directory without proving boot entries could be enumerated, and optional
Nix produced a permanent failure on plain Arch.

**Root cause.** In fixture CLI mode the root was always the source fixture. There was no link
between a state root and the source it came from, so verification had no migrated filesystem to
probe. Report serialization used the dataclass directly; validator logic conflated "firmware
exists" with "tooling works" and optional components with required promises.

**Fix.** `write_apply_marker()` materializes the fixture into the state root (without overwriting
apply-created files) and records its origin; `--verify` and `--repair` detect the marker and probe
the migrated root with the matching injected executor. `cmd_verify()` serializes `r.to_dict()`.
`materialize_fixture()` no longer re-seeds files into an already-migrated sandbox. Boot-entry
validation now requires `efibootmgr` output; only `target.required_components()` provide validated
capabilities; network/audio validators are added from the *active* package sets rather than the
supported-choice catalogue.

**Regression guards.** `tests/test_post_migration_verify.py` asserts structured JSON, ≥18
capability reports, and a pass after apply. Bootloader-configuration tampering removes
`boot/grub/grub.cfg` as well as the boot marker so the real file-backed validator is exercised.

## Cycle 28 — a passing `--verify` proved nothing about tampering

**Symptom.** There was no proof that verification detects damage to a migrated system. Several
capabilities were backed by the injected executor, so deleting their files would never fail, and
some capabilities depended on the same underlying probe, making "one capability broke" ambiguous.

**Root cause.** Tamper markers did not exist, executor methods always returned success, and there
was no systematic mapping from each validated capability to a way to break exactly it.

**Fix.** `FixtureExecutor.tampered(name)` reads markers from
`<state_root>/migration/tamper/<name>`; `systemd`, `pacman`, `boot` and `network` probes and the
pipewire audio probe now fail when their marker exists. `TAMPER_CASES` in
`tests/test_post_migration_verify.py` enumerates a break for every managed capability — markers
for command-backed ones, file/directory/glob removal for filesystem-backed ones. A guard asserts
the union of broken capabilities covers all reported capabilities, so a newly added validator must
also gain a tamper case. `cmd_verify()` refuses to probe at all when Stage A fails.

**Regression guards.** `./test-post-migration.sh` proves baseline verification passes, then that
each tamper case fails verification, names its capability, and includes a detail string.

## Current suite

```
Python: 126 tests — OK
Rust:   5 tests — OK
Stage A end-to-end: verify OK, handoff OK, receipt OK, tamper rejected
Chained rotation: OK; self-signed/untrusted/disabled/unapproved rejected
Adapter runtime: sandbox command OK; success/failure journaled; registry-less refused
Source matrix: 5 cases across btrfs/ext4/LUKS/GRUB/systemd-boot/NVIDIA/DKMS/mixed-AUR/aged/old-sunshine — OK
Post-migration: verify passes after apply; every managed capability tamper detected — OK
```

Alignment with the original specification is tracked in `evolution-engine/docs/SPEC_ALIGNMENT.md`;
all architecture gaps G1–G6 are closed at the protocol/offline level. Live GUI-VM verification and
packaging remain as deployment work, not protocol gaps.

