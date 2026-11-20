# Sunshine Evolution Engine

A repository-driven, target-state transformation and reconciliation system that evolves both
supported Arch Linux installations and existing Sunshine OS installations into the currently
published Sunshine OS architecture.

## Core idea

Sunshine OS is a **target state**, not a prerequisite. The same engine must handle:

```
Old Sunshine OS  ──> Current Sunshine OS
Pure Arch Linux  ──> Current Sunshine OS
```

The engine never asks "which Sunshine version is installed?" as its primary question. It asks
"what does this machine actually have, and what must it have?".

## Five principles

1. **Desired-state convergence** — describe the target, reconcile the machine with it.
2. **Capability discovery** — inspect the actual machine; don't assume installation history.
3. **Evolutionary components** — introduce, evolve, replace, reconfigure, retire independently.
4. **Declarative transformation plans** — compute operations, including never-before-seen ones.
5. **Upstream preservation** — Arch stays the foundation; pacman remains the package authority.

## Pipeline

```
Stage A trust → Discover → Resolve target → Plan → Preflight → Execute (journaled) → Validate → Commit
```

Stage A is optional in the offline test CLI but mandatory in production. Supply
`--trust-index`, `--trust-policy` and `--trust-keyring` to verify signed metadata, artifact
digests, chained key rotation, protocol compatibility and the signed Core handoff before any
discovery or mutation. See `docs/SPEC_ALIGNMENT.md` for the remaining Rust-bootstrap gap.

## Layout

```
src/
  engine.py            orchestrator + CLI
  core.py              shared typed models (facts, target, ops, plan, journal)
  discovery/           capability & system discovery
  target/              target manifest, profiles, component contracts
  trust/               Stage A: signed index, rotation, artifacts, handoff
  components.py        component contract loader/validator
  adapters.py          signed, versioned Rust adapter contracts
  fixtures.py          offline host-independent CLI executor
  planner/             DAG planner, typed operations, conflicts
  executor/            transactional executor, primitives, recovery
  validation/          capability and system validators
tests/                 unit + integration + idempotency + trust tests
fixtures/              simulated source states (clean Arch, old Sunshine, etc.)
docs/                  architecture, security, testing, threat model
```

## Status

Foundational engine with 106 offline tests, Stage A protocol verification, signed adapter
contracts, source compatibility profiles, host-independent fixture CLI and documented break/fix
cycles. The production Rust bootstrap is the next architecture step. See `docs/ARCHITECTURE.md`,
`docs/SPEC_ALIGNMENT.md`, `docs/TESTING.md` and `../reports/evolution-engine-breakfix-cycle.md`.
