# Sunshine Evolution Engine — Architecture

## Formal definition

> **Sunshine Evolution Engine** — a repository-driven, target-state transformation and
> reconciliation system responsible for evolving supported Arch Linux installations and existing
> Sunshine OS installations into the currently published Sunshine OS architecture.
>
> The engine discovers the installed system, resolves the current target, calculates the required
> component transformations, executes them through validated operations and commits the resulting
> system state.
>
> It supports introduction, evolution, replacement, reconfiguration and retirement of components
> independently of Sunshine release history. It preserves the Arch foundation and delegates
> standard package management to pacman.

## The central decision

**Migrations depend on what the machine currently is, not which Sunshine version it came from.**

This gives one engine for both:

- `Old Sunshine OS → Current Sunshine OS`
- `Pure Arch Linux → Current Sunshine OS`

## Three separated data models

| Model | Meaning | Lifecycle |
|-------|---------|-----------|
| Observed state | Factual inventory of the machine | Rebuilt on every run |
| Desired state | Versioned target specification | Published in the repository |
| Transformation state | Generated execution plan | Created per run, journaled |

They are never combined into one configuration file. They have different trust requirements and
lifecycles.

## Pipeline stages

### A — Bootstrap and trust verification
Verify local engine version, repository signatures, artifact hashes, compatibility. No
transformation begins before trust succeeds. (Bootstrap/trust crate is a future Rust component;
the Python engine models the interface.)

### B — Discovery
Inspect distribution, packages, kernel, boot, storage, services, network, audio, desktop, users,
existing Sunshine components. Every observation carries confidence and evidence. A GRUB package
alone is MEDIUM confidence; an EFI boot entry plus configuration is HIGH. Low confidence never
authorizes destructive operations.

### C — Target resolution
Load the versioned target manifest. Choose desktop profile. Preserve compatible existing choices
(bootloader, desktop, network, audio). Ask the user only when intent cannot be safely determined.

### D — Planning
Compute missing/outdated capabilities. Build a DAG of typed operations. Detect cycles, conflicts
and missing providers. Add checkpoints before destructive operations. The planner never branches
on release versions; it compares observed state to target state.

### E — Execution
Topological execution in transaction groups, each with preflight, checkpoint, journal, validation
and commit condition. The journal is append-only and fsynced. After interruption the engine
re-discovers the machine and reconciles journal intent with actual state before resuming.

### F — Validation
Capabilities are validated with active probes, not package presence alone. Unknown capabilities
fail closed.

## Component lifecycle

| Operation | Meaning |
|-----------|---------|
| Introduce | Component absent → install and initialize |
| Evolve | Schema/capability outdated |
| Replace | Swap implementation, preserve contract |
| Reconfigure | Current component, wrong configuration |
| Retire | Remove safely after data migration |

## Typed operations

`InstallPackages`, `RemovePackages`, `TransferOwnership`, `CreateConfiguration`,
`MigrateConfiguration`, `RegisterComponent`, `EnableService`, `DisableService`, `InstallKernel`,
`GenerateInitramfs`, `InstallBootEntry`, `CreateCheckpoint`, `ValidateCapability`.

Migration manifests never contain arbitrary shell scripts. Complex cases use versioned signed
adapters running under the executor's authorization, journaling and validation model.

## Arch foundation rules

- Pacman remains the authority. No second package manager.
- A coherent full-upgrade (`pacman -Syu`) is used when repository databases change — partial
  upgrades are refused.
- Foreign/AUR packages are classified with uncertainty, never auto-removed.
- Sunshine repository config uses managed fragments; user repos, mirrors, signature settings and
  custom options are preserved. Blockers are reported, not silently deleted.
- Kernel package migration, kernel management migration and boot integration migration are
  separate components with separate schemas.

## Configuration ownership

Four categories: Sunshine-owned (auto-migrate), system-owned (explicit adapters), user-owned
(preserve), unknown (conservative). Three-way merge (old default, user current, new default)
preserves user changes and asks only on conflict.

## Security invariants

1. Trust root is pinned in the bootstrap package; keys are never fetched from the same
   unauthenticated server that serves the code.
2. Key rotation follows a verifiable chain from the previous root.
3. Every downloaded artifact is hash- and signature-verified before execution.
4. Privileged operations are narrow, authorized, journaled and validated.
5. Low-confidence observations cannot authorize destructive operations.
6. The executor, not components, controls authorization and journaling.

## Supported source profiles

A five-year guarantee applies to **supported source profiles and supported Sunshine states**, not
arbitrary Linux systems. Clean Arch with systemd/pacman/supported bootloader/filesystem is the
primary conversion target. Customized Arch is conditional. Unsupported arrangements fail preflight
with a precise explanation.

## Idempotency

Running the engine twice against an unchanged target must produce no mutating operations — only
validation. This is a fundamental property and is covered by tests.
