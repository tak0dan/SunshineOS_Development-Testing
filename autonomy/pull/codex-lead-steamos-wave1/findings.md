# Findings — SteamOS Wave 1

- Repository staging selection is in `evolution-engine/src/evolution/staging.py::assess_staging`; its input is observational `Inventory.boot`.
- Cross-distro evidence at `reports/cross-distro-stability.md` describes SteamOS A/B inactive-slot updates and previous-slot retention. Research at `autonomy/results/lead-research-01.md` labels SteamOS OSTree, conflicting with that more specific report; no OSTree assumption was adopted.
- Existing inventory did not encode explicit inactive-slot and switch capability facts, so A/B staging must be opt-in by observed booleans, never distro name.
- Test IDs: STEAMOS_AB_001 through STEAMOS_AB_004. Evidence log: `autonomy/codex/steamos-development-lead-wave1-test.log`.
