# Findings — SteamOS migration engine, Wave 1 deepening

- `reports/cross-distro-stability.md:19,106-110,147` catalogs A/B updates and states its source-quality caveats; Collabora [S13] is the strongest source cited there.
- `evolution-engine/src/evolution/staging.py::assess_staging` only chooses a slot strategy from observed slot IDs/capabilities. `evolution-engine/src/evolution/inventory.py::from_observed` does not currently probe slot topology.
- Candidate slot identity and successful write do not prove expected OS contents or that rollback is bootable. Valve tracker issue #1213 records an opposite slot unexpectedly containing Windows: https://github.com/ValveSoftware/SteamOS/issues/1213.
- Relevant mandate invariants: M-05/M-06/M-08/M-09. Decisions: AD-11/12/14/16/30.
