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
Discover → Resolve target → Plan → Preflight → Execute (journaled) → Validate → Commit
```

## Layout

```
src/
  engine.py            orchestrator + CLI
  core.py              shared typed models (facts, target, ops, plan, journal)
  discovery/           capability & system discovery
  target/              target manifest + profile resolution
  planner/             DAG planner, typed operations, conflicts
  executor/            transactional executor, primitives, recovery
  validation/          capability and system validators
tests/                 unit + integration + idempotency tests
fixtures/              simulated source states (clean Arch, old Sunshine, etc.)
docs/                  architecture, security, testing, threat model
```

## Status

Iteration 1 — foundational engine. See `docs/ARCHITECTURE.md` and `docs/TESTING.md`.
