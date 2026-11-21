# Omarchy development leadership survey — Wave 1

Date: 2026-11-21  
Scope: migration and update reliability patterns suitable for SunshineOS.  
Primary upstream: `basecamp/omarchy`, branch `quattro` (source snapshot commit not pinned in this workspace; treat these as branch-view references, not immutable provenance).

## Source catalogue

| Upstream path | Verified observation | SunshineOS disposition |
|---|---|---|
| `docs/update-process.md` — [upstream](https://github.com/basecamp/omarchy/blob/quattro/docs/update-process.md), lines 305–306 | Per-user migration markers drive pending-work detection in some flows; direct pacman updates bypass the post-update hook. | Discovery must compare observed component state and transaction evidence; do not treat a completion marker or updater invocation as proof. |
| `docs/update-process.md`, lines 327–333 | Channel switching changes repository configuration and package selection; runtime version is derived from package or checkout state rather than a standalone version file. | Inventory the effective repository set, package state, and source identity; never infer migration eligibility from a release string alone. |
| `manual/30-updates.md` — [upstream](https://github.com/basecamp/omarchy/blob/quattro/manual/30-updates.md), lines 191–197 | The supported updater wraps snapshot, migrations, configuration updates, and package updates; direct pacman transactions bypass that workflow. Reinstall can overwrite user configuration. | Keep mutation behind a reviewed plan and journal; configuration reconciliation must preserve user-owned data and expose destructive reset semantics. |
| `manual/47-system-snapshots.md` — [upstream](https://github.com/basecamp/omarchy/blob/quattro/manual/47-system-snapshots.md), lines 170–180 | Snapshot rollback restores root but not `/home`; home-resident migration markers survive, so a completed marker can disagree with rolled-back root state. Snapshot availability is Limine-specific. | Never equate a stored completion marker with a verified postcondition. Re-discover affected state after restore; qualify rollback capability by boot/filesystem topology. |
| `manual/31-dotfiles.md` — [upstream](https://github.com/basecamp/omarchy/blob/quattro/manual/31-dotfiles.md), lines 195–223 | Hooks are user scripts at defined lifecycle points; package-owned system files are overwritten on update; the documented config resync is destructive. | Treat hooks as untrusted extension inputs with declared scope and lifecycle; track ownership and use three-way config reconciliation. |
| `docs/file-layout.md` — [upstream](https://github.com/basecamp/omarchy/blob/quattro/docs/file-layout.md), lines 176–199, 414–434 | System defaults, per-user seeding, provisioning, and migrations have distinct ownership locations. Deferred hardware provisioning has an explicit queue and retry exit behavior. | Adopt explicit ownership boundaries and resumable queued operations; avoid copying system layout as an implementation dependency. |

These paths are an upstream survey, not a local byte-for-byte source archive. The research catalog's content-hash verification therefore cannot yet validate them. Pinning a full upstream commit and storing verified source snapshots remains required before promoting these records to verified catalog evidence.

## Implemented control

`evolution-engine/src/evolution/journal_state.py::MigrationJournal.verify_completed_outputs` compares each completed operation's stored output hash with fresh observation supplied by discovery. It reports missing hashes, unobserved outputs, and mismatches. This is an explicit check for resume/recovery callers; it does not silently rewrite the journal or claim that a snapshot is valid.

Regression coverage: `evolution-engine/tests/test_omarchy_recovery_consistency.py::OmarchyRecoveryConsistencyTests.test_OMR_001_completed_operation_requires_matching_observed_output` and `test_OMR_002_missing_observation_or_recorded_hash_fails_closed`.

Exact verification command and result:

```text
$ cd evolution-engine && python3 -m unittest tests.test_omarchy_recovery_consistency
..
Ran 2 tests in 0.001s
OK
```

## Invariants and limitations

- Supports M-04 by requiring current observed state, M-06 by detecting stale completion claims during recovery, and M-09 by preventing stale markers from being accepted as sufficient evidence on retry.
- Hash creation and discovery wiring remain the caller's responsibility. Existing callers must supply canonical output hashes to gain the check; this change does not yet wire a global recovery pass.
- Snapshot availability is not assumed from Omarchy identity. The observed bootloader and filesystem capabilities determine support.
