# Solution — SteamOS Wave 1

Added `ab_slot` staging strategy in `evolution-engine/src/evolution/staging.py`. It requires both explicit inventory capabilities, retains a previous slot, and defers to recovery reconstruction when needed. Forced unavailable A/B and staged-root strategies fail closed. Regression coverage is in `evolution-engine/tests/test_steam_os_ab_staging.py`.
