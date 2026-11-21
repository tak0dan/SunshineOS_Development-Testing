# Findings — SteamOS architecture enforcement, Wave 1 deepening

- Research is catalogued at `reports/cross-distro-stability.md:19,106,110,147`; that report explicitly distinguishes stronger Collabora source S13 from secondary channel/source claims.
- Existing engine gates A/B strategy on observed slot IDs and switch capability in `evolution-engine/src/evolution/staging.py::StagingCapability.ab_slot_possible`.
- `WorkflowRun` previously accepted caller-supplied completed history and abort locations without ensuring they matched the canonical phase cursor. This could bypass `ValidateStaged` before `Activate`.
- Mandate mapping: M-05, M-06, M-08, M-09. Architecture mapping: AD-05, AD-11, AD-12, AD-14, AD-16, AD-30.
