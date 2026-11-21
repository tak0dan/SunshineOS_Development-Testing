# SteamOS development leadership — Wave 1

## Survey and catalogue

Repository grounding checked `reports/USER_MIGRATION_MANDATE_2026-11-21.md` (migration invariants M-01–M-10 and the target-state architecture) and `reports/ARCHITECTURE_DECISIONS.md` (AD-01, AD-03, AD-05, AD-11, AD-12, AD-14, AD-17, AD-20, AD-30). The implementation point is `evolution-engine/src/evolution/staging.py::StagingCapability` and `assess_staging`, the engine’s capability-driven pre-activation strategy selector. Its inventory source is `evolution-engine/src/evolution/inventory.py::Inventory.boot`.

SteamOS research already in the repository:

- `reports/cross-distro-stability.md` §SteamOS says updates prepare the inactive A/B partition, retain a previous slot, validate chunks, and use update channels. The report cites Collabora for the technical A/B mechanism; it also records that some supporting sources are secondary.
- `autonomy/results/lead-research-02.md` describes A/B root replacement and retention as a reusable invariant, but contains claims about firmware switching and “SteamOS Architecture Docs, 2024” without an exact archived source path. I treated these as hypothesis, not implementation facts.
- `autonomy/results/lead-research-01.md` calls SteamOS “OSTree + atomic updates,” which conflicts with the more specific RAUC/Casync account in `reports/cross-distro-stability.md`. No OSTree dependency was introduced.
- `autonomy/results/surge-20-0020.md`, `autonomy/results/sub-code-distro-01.md`, and `autonomy/results/sub-research-hooks-0023.md` also contain broad SteamOS adoption proposals. They do not establish available A/B fields in the engine inventory, so the integration is gated on explicit observations.

## Change made

`evolution-engine/src/evolution/staging.py` now supports the `ab_slot` strategy. The selector requires both `boot.inactive_slot_available is True` and `boot.slot_switch_supported is True`; it never infers capability from distribution identity. If recovery reconstruction is requested, it takes precedence over A/B activation. Forced A/B or staged-root selection fails closed when required inventory facts are missing. The strategy reports workspace `inactive-slot` and previous-state retention.

Regression tests in `evolution-engine/tests/test_steam_os_ab_staging.py`:

- `STEAMOS_AB_001`: complete observed capability selects A/B staging.
- `STEAMOS_AB_002`: partial, string-valued, or absent capability cannot select A/B; forced selection is rejected.
- `STEAMOS_AB_003`: recovery reconstruction precedes activation.
- `STEAMOS_AB_004`: forced staged-root requires capability.

## Verification

From `evolution-engine/`:

```text
python3 -m unittest discover -s tests -p 'test_steam_os_ab_staging.py'
....
----------------------------------------------------------------------
Ran 4 tests in 0.002s

OK

python3 -m unittest discover -s tests -p 'test_evolution.py'
..............................
----------------------------------------------------------------------
Ran 30 tests in 0.099s

OK
```

Full captured output: `autonomy/codex/steamos-development-lead-wave1-test.log`.
