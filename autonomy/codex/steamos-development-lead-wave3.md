# SteamOS regression survey — Wave 3

## Survey and catalogue

Grounding: `reports/USER_MIGRATION_MANDATE_2026-11-21.md` sets the target-state and recoverability requirements (M-01, M-05, M-06, M-09). `reports/ARCHITECTURE_DECISIONS.md` maps these to AD-05 (inventory authority), AD-11 (checkpoint and restore), AD-12 (staging), AD-14 (qualified support), AD-16 (post-migration verification), and AD-30 (long support margin).

SteamOS-specific evidence in `reports/cross-distro-stability.md:19` identifies an image-based A/B update model: prepare the inactive root slot, retain a previous known-good slot, validate written chunks, and use update channels. The source catalogue is at `reports/cross-distro-stability.md:106-110`: S13 is Collabora's SteamOS 3.6 account of RAUC/Casync and seed validation; S14-S17 are a man-page mirror and community/secondary sources. The report itself cautions at line 147 that some SteamOS details come from secondary sources. This implementation uses the general invariant of a retained previous slot and makes no dependency on a particular SteamOS update client or exact slot mechanics.

Repository locations and existing regression coverage:

- `evolution-engine/src/evolution/inventory.py::Inventory` carries observed boot facts; slot behavior is not inferred from a SteamOS distro label.
- `evolution-engine/src/evolution/staging.py::StagingCapability.from_inventory` and `ab_slot_possible` require explicit candidate availability, switching support, and distinct non-empty active/candidate identifiers. `assess_staging` selects the plan and gives recovery reconstruction precedence. `WorkflowRun` sequences the 14 phases, including `ValidateStaged` immediately before `Activate`.
- `evolution-engine/tests/test_steam_os_ab_staging.py` holds the SteamOS A/B regression IDs: `STEAMOS_AB_001` named candidate/retained slots; `STEAMOS_AB_002` incomplete or ambiguous evidence is rejected; `STEAMOS_AB_003` recovery precedes A/B activation; `STEAMOS_AB_004` forced staged-root requires capability; `STEAMOS_AB_005` invalid workflow strategies are rejected and an aborted validation phase cannot progress to activation.
- `evolution-engine/tests/test_evolution.py::EvolutionTests.test_staging_and_workflow_phases` covers shared strategy and ordered-phase behavior.

## Change

`WorkflowRun` previously relied on callers going through `plan_workflow()` to validate strategy names. Direct construction accepted arbitrary names and still allowed phase progression. Added constructor validation against `STRATEGIES`. The new STEAMOS_AB_005 test covers direct invalid construction and the fail-closed behavior after validation aborts, ensuring `Activate` cannot be reached.

## Verification

From `evolution-engine/`:

```text
python3 -m unittest discover -s tests -p 'test_steam_os_ab_staging.py'
.....
----------------------------------------------------------------------
Ran 5 tests in 0.004s

OK
python3 -m unittest discover -s tests -p 'test_evolution.py'
..............................
----------------------------------------------------------------------
Ran 30 tests in 0.096s

OK
```

Captured output: `autonomy/codex/steamos-development-lead-wave3-test.log`.
