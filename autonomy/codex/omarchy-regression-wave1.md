# Omarchy update and recovery regression survey — Wave 1

Date: 2026-11-21  
Upstream: `basecamp/omarchy`, commit `e4635a4eea887d5c8dbd70427386f570c37a2a61` (cached checkout: `/home/tak_0/.local/state/sunshine-orchestrator/iso/repos/omarchy`).  
Scope: regression conditions around update orchestration, bypass, per-user migration state, and rollback.

## Source catalogue

| Exact upstream file and evidence | Finding | SunshineOS regression control |
|---|---|---|
| `docs/update-process.md` lines 18–26, 42–61 | Update concurrency uses a runtime lock; migration completion markers are per-user under `~/.local/state/omarchy/migrations/`. | A durable journal must be paired with fresh state discovery; shared state and per-user state need explicit scope. |
| `docs/update-process.md` lines 72–103; `bin/omarchy-update-pacman-guard` | The ALPM pre-transaction hook stops direct system upgrades unless an Omarchy workflow allowance is set; an explicit escape hatch exists. | Require transaction provenance as evidence, but do not treat a guard as authoritative package inventory because it has a bypass. |
| `docs/update-process.md` lines 114–163; `bin/omarchy-update` | The documented update path sequences snapshot, package update, migrations, hooks, boot verification, and restart prompt. Migration execution occurs after pacman. | Keep stage boundaries and validate boot artifacts before declaring completion. A failed boot check blocks the reboot prompt. |
| `docs/update-process.md` lines 165–232; `bin/omarchy-migrate-notify` | Direct package upgrades have a login-time migration notification path. The notifier suppresses duplicate prompts while the main update lock is held; notification prompts rather than executing migrations invisibly. | Make notifications advisory and idempotent; don't run privileged or user-state transitions invisibly in a login hook. |
| `bin/omarchy-migrate` | Pending state is determined from per-user marker files; each migration runs before its marker is written. The script waits for a pacman lock before running. | A marker written after a step is still a claim, not proof. Re-probe effects after interruptions and root-only rollback. |
| `manual/30-updates.md` lines 33–43 | Direct pacman/yay updates can miss coordinated snapshots, migrations, and config updates; the guard directs users to the updater. | Detect bypassed workflows and leave state requiring explicit assessment rather than assume all hooks ran. |
| `manual/47-system-snapshots.md` lines 3–19 | Snapshot restore reverts root, not `/home`; per-user migration markers survive even if root effects of those migrations were reverted. | Resume/recovery must validate postconditions against observed system state, regardless of completed markers. |

The source records, SHA-256 digests, and exact commit are stored in `evolution-engine/fixtures/research/omarchy-update-recovery-wave1.json`. Hashes were compared with all six files in the cached checkout. The checkout was clean when inspected. This pins this survey's evidence to a local source snapshot; it does not establish upstream authenticity beyond the Git commit identity.

## Implemented regression coverage

Added `CAT_006` in `evolution-engine/tests/test_research_catalog.py::ResearchCatalogTests.test_CAT_006_omarchy_update_recovery_catalog_is_pinned_and_complete`. It asserts the Omarchy project identity, exact full commit ID, all six expected source paths, and successful schema validation. Existing catalogue tests `CAT_002` and `CAT_003` exercise source-hash matching and fail-closed mismatch behavior. The pinned catalog is declarative provenance; it is not executed as migration policy.

The existing recovery regressions remain relevant and are not duplicated:

- `OMR-001`, `OMR-002`: `evolution-engine/tests/test_omarchy_recovery_consistency.py`
- `OMR-003`: `evolution-engine/tests/test_executor.py`
- Implementation: `evolution-engine/src/evolution/journal_state.py::MigrationJournal.verify_completed_outputs` and `evolution-engine/src/executor/executor.py::execute_plan`

## Verification and evidence

From `evolution-engine/`:

```text
python3 -m unittest tests.test_research_catalog -v
Ran 6 tests in 0.013s
OK
```

The separate source hash check reported six matching files at the pinned commit. Captured output: `autonomy/codex/omarchy-regression-wave1-source-hashes.log`. Full test output: `autonomy/codex/omarchy-regression-wave1-test.log`.

Grounding: mandate M-04 (actual installation authoritative), M-06 (recoverable operations), M-09 (repeatability), M-10 (separate user data); architecture decisions AD-04/05/10/11/16/21/22. This change strengthens provenance and regression coverage; it does not claim Omarchy snapshot compatibility or implement snapshot discovery.
