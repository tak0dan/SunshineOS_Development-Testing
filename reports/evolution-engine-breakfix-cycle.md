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

## Current suite

```
Ran 106 tests
OK
```

Alignment with the original specification, including the remaining Rust bootstrap gap, is tracked
in `evolution-engine/docs/SPEC_ALIGNMENT.md`.

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
