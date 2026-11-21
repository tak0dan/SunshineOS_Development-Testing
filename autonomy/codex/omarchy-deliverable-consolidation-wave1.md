# Omarchy deliverable consolidation — Wave 1

## Survey and provenance

The local source checkout is `basecamp/omarchy` at commit `e4635a4eea887d5c8dbd70427386f570c37a2a61` (`/home/tak_0/.local/state/sunshine-orchestrator/iso/repos/omarchy`). The existing research fixture `evolution-engine/fixtures/research/omarchy-update-recovery-wave1.json` pins six source files and their SHA-256 values; its validation is covered by `CAT_006` in `evolution-engine/tests/test_research_catalog.py`. I rechecked the fixture's source hashes locally and additionally hashed `bin/omarchy-update` and `bin/omarchy-apply-pacman` against the same checkout.

| Exact source path | Finding grounded in source | SunshineOS implication |
|---|---|---|
| `docs/update-process.md` | Describes the update ordering, lock, guard, per-user migration markers, notification behavior, and final boot verification. | Keep transaction, migration, and boot-validation evidence distinct; a login notification is advisory. |
| `bin/omarchy-update` | Runs system packages before per-user migrations and AUR work. Boot verification runs after these and gates the reboot prompt; failure exits nonzero. | Update completion must require successful boot verification after package and migration stages. |
| `bin/omarchy-migrate` | Executes user-scoped migrations recorded under the user's state directory. | User markers are claims and must reconcile with journal and freshly observed system postconditions. |
| `bin/omarchy-update-pacman-guard` | The ALPM guard restricts direct full upgrades, while an explicit environment override can bypass it. | Guard status is not transaction proof; inventory and transaction evidence remain necessary. |
| `manual/30-updates.md` | Documents the blessed update sequence and warns direct pacman transactions can skip orchestration. | Preserve explicit transaction plans and configuration ownership. |
| `manual/47-system-snapshots.md` | Documents root restore behavior that can leave `/home` markers behind; described support is setup-dependent. | Re-probe after restore; do not generalize snapshot support to other layouts. |
| `bin/omarchy-apply-pacman` | Validates channel and region values, renders both pacman files before replacement, and retains backups on explicit refresh. | Validate bounded configuration inputs and prepare related files together before installation. |

Additional checked hashes: `bin/omarchy-update` is `d59539590ff3b20282c1fb6b05a8f506ec931d098a358282f1521a41131634b3`; `bin/omarchy-apply-pacman` is `9108ae817b0af37fa27e3fde3b2be583d1d9eab008461b032603d5625f058718`. The six catalogue values are retained in the fixture. These are source observations, not evidence of behavior on a qualified live installation.

## Implementation and regression coverage

Added `evolution-engine/src/evolution/update_evidence.py::validate_update_completion_evidence`. It blocks update completion when any required stage is absent or failed, or when package transaction, migrations, and boot verification are out of order or duplicated. It is a pure validator: it neither executes updates nor triggers reboot. This encodes the terminal boot gate observed in `bin/omarchy-update` while keeping execution with the orchestrator.

Regression tests in `evolution-engine/tests/test_omarchy_update_completion.py`:

- `OMR-011`: accepts package, migration, and boot evidence in order, with optional AUR work between migration and boot verification.
- `OMR-012`: failed boot verification blocks completion.
- `OMR-013`: missing boot evidence blocks completion.
- `OMR-014`: duplicate and out-of-order required evidence blocks completion.

Related existing controls: `OMR-001/002` in `test_omarchy_recovery_consistency.py`; `OMR-005..010` in `test_omarchy_marker_reconciliation.py`; catalogue provenance `CAT_006` in `test_research_catalog.py`. Architecture grounding: mandate priorities for stability, recoverability, and installation-state authority; `reports/ARCHITECTURE_DECISIONS.md` AD-05, AD-11, AD-16, and AD-21.

## Verification

Exact command, run from `evolution-engine/`:

```text
python3 -m unittest tests.test_omarchy_update_completion tests.test_omarchy_marker_reconciliation tests.test_omarchy_recovery_consistency tests.test_research_catalog -v
```

Result: **Ran 19 tests in 0.017s — OK**. Full output: `autonomy/codex/omarchy-deliverable-consolidation-wave1-test.log`.

## Change summary and evidence

- Implementation: `evolution-engine/src/evolution/update_evidence.py`.
- Regression tests: `evolution-engine/tests/test_omarchy_update_completion.py`.
- Test output: `autonomy/codex/omarchy-deliverable-consolidation-wave1-test.log`.
- Pull notes: `autonomy/pull/codex-lead-omarchy-deliverable-consolidation-wave1/`.
- This consolidated survey and change summary: `autonomy/codex/omarchy-deliverable-consolidation-wave1.md`.
