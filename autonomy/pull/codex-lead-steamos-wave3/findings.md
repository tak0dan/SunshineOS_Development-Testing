# Findings — SteamOS regression survey, Wave 3

- `reports/cross-distro-stability.md:19` catalogs SteamOS A/B inactive-slot updates and retention; source quality details are at lines 106-110 and caveats at line 147.
- Engine decision points: `evolution-engine/src/evolution/staging.py::StagingCapability`, `assess_staging`, and `WorkflowRun`; observed inputs reside in `evolution-engine/src/evolution/inventory.py::Inventory`.
- `WorkflowRun` could be constructed directly with an unknown strategy, bypassing `plan_workflow()` validation. The phase sequence itself already placed `ValidateStaged` before `Activate` and disallowed advance after abort.
- Mandate alignment: M-05/M-06/M-09; architecture decisions AD-05/11/12/14/16/30.
