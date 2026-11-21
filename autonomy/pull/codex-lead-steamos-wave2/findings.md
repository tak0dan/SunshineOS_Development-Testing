# Findings — SteamOS integration Wave 2

- Research catalogue: `reports/cross-distro-stability.md` §1, SteamOS row and Sources [S13]–[S17]. [S13] is the stronger technical account (Collabora, RAUC/Casync); other cited material includes community/secondary references.
- Engine staging is in `evolution-engine/src/evolution/staging.py`; current discovery in `evolution-engine/src/evolution/inventory.py::from_observed` does not observe slot layout. Therefore this integration is capability gated and not an end-to-end SteamOS updater.
- Re-read constraints: `reports/USER_MIGRATION_MANDATE_2026-11-21.md` M-05/M-06/M-09 and `reports/ARCHITECTURE_DECISIONS.md` AD-05/11/12/14/16/20.
