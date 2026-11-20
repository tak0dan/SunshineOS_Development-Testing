# SunshineOS evolutionary migration: architecture decisions

Status: canonical mapping, derived from the shipped engine and audit evidence.
Scope: `Old Sunshine OS -> current SunshineOS`, `nearly pure Arch Linux -> current
SunshineOS`, and every later Arch-based SunshineOS release.

The identifiers AD-01..AD-30 were referenced in the project brief but no earlier
machine-readable list existed in this repository. A repository-wide search
confirmed this; related but unnumbered decision registers exist in
`SunshineOS/docs/ARCHITECTURE.md` section 14 and
`TODO/TODO_Migration.md` section 18. This document establishes the canonical
AD meanings. The machine-checkable invariants M-01..M-10 already live in
`evolution-engine/src/evolution/invariants.py` and are asserted by the test
suite; AD decisions are design policy, with the code path that implements each.

## Decisions

| ID | Decision | Implementing code / artifact |
|---|---|---|
| AD-01 | Freeze an Arch 2026 baseline epoch instead of tracking floating "latest Arch". | `evolution-engine/src/evolution/baseline.py::ARCH_2026_BASELINE`, `evolution/docs/BASELINE_ARCH_2026.md` |
| AD-02 | Milestones are logical gates and preserved knowledge, not release scripts. | `evolution-engine/src/evolution/milestones.py::MilestoneRegistry.chain`, `evolution-engine/src/evolution/scheme.toml` |
| AD-03 | A complete desired target is resolved from cumulative evolution records; the planner derives per-machine operations from inventory. | `evolution-engine/src/evolution/target_resolver.py::TargetResolver`, `src/planner.py` |
| AD-04 | One implementation covers Old Sunshine OS and pure Arch through capability discovery, not two migration programs. | `evolution-engine/src/evolution/compatibility.py::CompatibilityEngine`, `evolution-engine/src/evolution/inventory.py::from_observed` |
| AD-05 | The observed installation is authoritative; a reported release number cannot override inventory. | `evolution-engine/src/evolution/invariants.py::_m04`, `src/context.py::ExecutionContext` |
| AD-06 | Trust fails closed: empty digests, unknown signers, revoked channels, and unverified artifacts block migration. | `evolution-engine/src/trust/model.py`, `evolution-engine/src/evolution/repository.py`, `evolution-engine/src/evolution/tools/channels.py` |
| AD-07 | Declarative scheme data owns hooks, invariants, rollback strategy and milestone metadata. | `evolution-engine/src/evolution/scheme.toml`, `evolution-engine/src/evolution/scheme.py` |
| AD-08 | Adaptors are signed, sandboxed, permission-limited, journaled, and rechecked before invocation. | `src/adapters/runtime.py`, `evolution-engine/src/evolution/hooks.py` |
| AD-09 | Engine code is stdlib-only, dataclass-based, typed, and uses argv with no `shell=True`; hooks never use the network. | `src/engine.py`, `evolution-engine/src/evolution/hooks.py::HookRunner.validate_command` |
| AD-10 | Live and fixture execution are separated by `fs_root`/`system_root`; all journals and checkpoints remain under `state_root`. | `src/context.py::ExecutionContext`, `evolution-engine/src/evolution/journal_state.py` |
| AD-11 | Every crossing checkpoints first and restores on any failure, including failed verification. | `evolution-engine/src/evolution/updater.py::EvolutionUpdater.upgrade` |
| AD-12 | Staged root migration is preferred where supported; ext4/LUKS systems get an equivalent contract through in-place recovery. | `evolution-engine/src/evolution/staging.py`, `evolution-engine/src/evolution/tools/snapshots.py` |
| AD-13 | Recovery lineage is independent: `B-1 (Arch 2015) -> M bridge -> B0 (Arch 2026) -> target`. | `evolution-engine/src/evolution/recovery.py::recovery_path`, `RecoveryBridge` |
| AD-14 | Support is a qualified capability tier, never an assumption based on release age. | `evolution-engine/src/evolution/qualification.py::SourceCapabilities.tier`, `CompatibilityEngine.classify` |
| AD-15 | Qualification spans btrfs, ext4, LUKS, GRUB, systemd-boot, NVIDIA, DKMS, mixed AUR and old Sunshine shapes. | `evolution-engine/tests/source-matrix.toml`, `test_source_matrix.py` |
| AD-16 | `--verify` checks the migrated system and detects tampering, including missing checkpoints and changed managed paths. | `src/engine.py`, `tests/test_post_migration_verify.py`, `evolution-engine/src/evolution/tools/sealed_state.py` |
| AD-17 | The evolution ledger is immutable, contiguous, digest-tracked and validated at construction. | `evolution-engine/src/evolution/ledger.py::EvolutionLedger` |
| AD-18 | Retired transitions remain discoverable as knowledge; they are not silently deleted from the catalog. | `evolution-engine/src/evolution/transitions.py::TransitionRegistry.any_for` |
| AD-19 | A release must carry all twelve migration artifacts and qualified records for B0, E001, E039 and external Arch. | `evolution-engine/src/evolution/qualification.py::release_gate` |
| AD-20 | Historical artifacts are content-addressed and archived separately from live repositories. | `evolution-engine/src/evolution/artifacts.py::ContentAddressedArchive` |
| AD-21 | User-data preservation is planned separately from OS reconstruction. | `evolution-engine/src/evolution/recovery.py::DataPreservationPlan`, M-10 |
| AD-22 | Resolution is deterministic; ambiguous operator choices are explicit `--decide` answers, never guesses. | `evolution-engine/src/target.py`, `tests/test_target.py`, `src/engine.py` |
| AD-23 | Conceptual component names map to real published packages and kernels (`sunshine-base`, `linux`). | `evolution-engine/src/components/`, `src/target.py`, `tests/test_components.py` |
| AD-24 | Profile management is declarative; `sunshine-profiles.service` is rejected and `sunshine-apps.service` is the real target. | `evolution-engine/src/target.py`, `tests/test_components.py`, `evolution-engine/src/evolution/tools/service_supervision.py` |
| AD-25 | Root-run service probes use narrow fallbacks so tamper tests still fail closed. | `src/verify.py`, `tests/test_post_migration_verify.py` |
| AD-26 | Tools are delivered only through signed `tak0dan/sunshine-tools` releases consumed by `sunshine-toolsync`; source pushes alone do not update installations. | `profile/airootfs/usr/local/bin/sunshine-toolsync`, audit evidence in `reports/` |
| AD-27 | Terminal UX helpers are centralized (password prompts, progress graphs, logo animation, day/night messages) and must be wired into install/post-install paths. | `profile/airootfs/usr/local/lib/sunshine/ui.sh`, `reports/` deployment-gap audit |
| AD-28 | OpenClaw credentials are environment-only, free-model-only, redacted, network-injectable and never written to tasks, logs or reports. | `openclaw/backends.py::OpenRouterBackend`, `openclaw/tests/test_openrouter.py` |
| AD-29 | Telegram reporting is an observer and a no-op until bot token and chat ID are configured. | `openclaw/reporter.py::TelegramReporter`, `openclaw/cli.py::configured_reporters` |
| AD-30 | Support margin is 20 years with at least 40 quarterly releases (80 target); preservation of migration knowledge outlives any single script. | `evolution-engine/src/evolution/compatibility.py::SupportPolicy`, `evolution-engine/src/evolution/versions.py`, `evolution-engine/src/evolution/transitions.py` |

## Machine-checkable invariants

| ID | Invariant | Check |
|---|---|---|
| M-01 | Target-state driven migration | `invariants.py::_m01` |
| M-02 | Evolution history is immutable | `invariants.py::_m02` |
| M-03 | Migration intelligence versioned independently | `invariants.py::_m03` |
| M-04 | Actual installation is authoritative | `invariants.py::_m04` |
| M-05 | Migrations staged when possible | `invariants.py::_m05` |
| M-06 | Operations are recoverable | `invariants.py::_m06` |
| M-07 | Historical artifacts archived | `invariants.py::_m07` |
| M-08 | Support qualified, not assumed | `invariants.py::_m08` |
| M-09 | Migration is repeatable | `invariants.py::_m09` |
| M-10 | User data separate from OS reconstruction | `invariants.py::_m10` |

All ten are evaluated by `check_invariants()` and asserted in
`evolution-engine/tests/test_evolution.py::VersionAndSchemeTests`.

## Verification of this mapping

```sh
cd evolution-engine
python3 -m unittest discover -s tests
bash test-source-matrix.sh
bash test-post-migration.sh
cd bootstrap-rust && cargo test --offline --locked
```
