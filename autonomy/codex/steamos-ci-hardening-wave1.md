# SteamOS CI hardening — Wave 1

## Survey catalogue

The local corpus contains no SteamOS source checkout or SteamOS-owned GitHub Actions workflow. The SteamOS facts below are therefore repository-catalogued research, not direct inspection of Valve's current source. The repository explicitly marks some SteamOS evidence as secondary in `reports/cross-distro-stability.md:147`.

| Exact path / symbol | Catalogue finding | CI implication |
|---|---|---|
| `reports/cross-distro-stability.md:19` | SteamOS is catalogued as image-based A/B updates, inactive-slot preparation, retained previous state, read-only root, and explicit keep-list. | Keep regressions for candidate-slot identity, retention and staging in CI. |
| `reports/CROSS_DISTRO_RESEARCH_2026-11-21.md:283-310` | The research records read-only root/developer mode, systemd, signed package/tooling claims, slot updates and a seed-index desynchronization failure mode. These are corpus claims; no ISO/source tree was present to independently inspect. | Run safety regressions for slot qualification and read-only/devmode evidence. Do not treat this as a direct SteamOS build. |
| `evolution-engine/src/evolution/staging.py::StagingCapability.from_inventory`, `assess_staging`, `WorkflowRun` | A/B staging is selected only from observed slot capability; ordered staging phases include staged validation before activation. | Execute A/B staging regressions on every push and pull request. |
| `evolution-engine/src/evolution/slot_activation.py::validate_slot_activation` | Activation qualification checks planned candidate identity, expected OS, staged validation and previous-slot bootability. | Keep activation regressions in the CI job. |
| `evolution-engine/src/evolution/tools/steamos_repair.py::assess_steamos_repair` | Repair assessment is read-only and fails closed on missing or contradictory rootfs/devmode observations. | Keep readonly/devmode repair regressions in CI. |
| `.github/workflows/steamos-regressions.yml` (added) | No prior SteamOS-specific workflow existed under `.github/workflows/`; this workflow uses read-only token permissions, a full-SHA checkout pin, focused tests and the repository workflow audit. | Make current SteamOS-inspired safety regressions part of push/PR CI. |

## Change and regression IDs

Added `.github/workflows/steamos-regressions.yml` to run the existing staging/activation and repair tests, then audit workflow trust policy. Added `evolution-engine/tests/test_steamos_ci.py` to prevent removal of those suites or weakening the workflow's permissions/action pin without an explicit test update.

- `STEAMOS_CI_001` — required staging, activation, and repair test patterns are present.
- `STEAMOS_CI_002` — contents permission is read-only and checkout is pinned to a 40-character commit SHA.
- `STEAMOS_CI_003` — the workflow invokes the repository CI trust-policy audit.
- Existing covered IDs: `STEAMOS_AB_001`–`006`, `STEAMOS_ACT_001`–`007`, `T_STEAMOS_REPAIR_001`–`008`.

This adds CI for SunshineOS's SteamOS-inspired safety controls; it does not claim to build or test SteamOS itself. It implements the mandate's stability/reliability priorities and AD-06/AD-09, while preserving AD-05/11/12/14 through existing tested logic.

## Verification

From the repository root, ran:

```sh
python3 -m unittest discover -s evolution-engine/tests -p 'test_steam_os_ab_*.py' -v && python3 -m unittest discover -s evolution-engine/tests -p 'test_steamos_repair.py' -v && python3 -m unittest discover -s evolution-engine/tests -p 'test_steamos_ci.py' -v && python3 autonomy/codex/ci_policy_audit.py .
```

Result: A/B staging + activation 13 tests passed; repair 8 passed; CI workflow guard 3 passed; audit scanned 5 workflows and returned `NO_DETECTED_POLICY_FINDINGS`. Full transcript: `autonomy/codex/steamos-ci-hardening-wave1-test.log`.
