# SteamOS migration engine survey — Wave 1 deepening

## Source survey and catalogue

| Exact source path | Verified finding | Engine implication |
|---|---|---|
| `reports/cross-distro-stability.md:19` | Catalogues SteamOS image based atomic A/B updates, inactive slot writes and retention of the previous known-good slot. | Preserve a bootable prior state, and gate activation on candidate validation. |
| `reports/cross-distro-stability.md:106-110,147` | [S13] is the stronger Collabora technical account; other listed channel and update details include community/vendor and secondary sources. The report explicitly limits claim strength. | Treat A/B as an architectural pattern; do not import SteamOS-specific updater assumptions as a SunshineOS contract. |
| `evolution-engine/src/evolution/inventory.py::Inventory.boot` | Boot inventory is an observational domain; `from_observed()` currently only fills boot capabilities and does not discover slot topology. | Current A/B facts need to arrive from a future trusted probe; distro name alone is not evidence. |
| `evolution-engine/src/evolution/staging.py::StagingCapability.from_inventory`, `ab_slot_possible`, `assess_staging` | Selection requires distinct observed active/inactive IDs, explicit candidate availability, and switch support; a plan records active/candidate IDs. Recovery reconstruction is preferred when requested. | Candidate identifiers are necessary but do not establish the candidate's contents or prior-slot bootability. |
| `evolution-engine/src/evolution/staging.py::WorkflowRun`, `PHASES` | `ValidateStaged` precedes `Activate`, followed by `BootValidate`, `Commit`, and `Retain`. The current uncommitted edit additionally constrains phase history to a canonical prefix. | Enforce candidate identity and retained-slot evidence at the boundary immediately before activation. |
| `evolution-engine/src/evolution/slot_activation.py::validate_slot_activation` | New pure, fail-closed pre-activation gate checks the planned slot identity, expected OS identity, successful staged validation, and bootability of the original slot. | Caller must supply fresh probe results; no host mutation or slot switch is performed by this gate. |
| `evolution-engine/tests/test_steam_os_ab_activation.py` | Regression IDs `STEAMOS_ACT_001`–`007` cover acceptance and wrong OS, missing identity, failed validation, unavailable rollback, wrong candidate and non-A/B plan. | A foreign OS in the inactive partition cannot be mistaken for an update candidate. |

SteamOS source grounding: the Collabora account describes RAUC/Casync atomic A/B updates ([SteamOS 3.6 update mechanics](https://www.collabora.com/news-and-blog/news-and-events/steamos-3-6-how-the-steam-deck-atomic-updates-are-improving.html)). Valve's community tracker records an update failure where the opposite slot unexpectedly contained a Windows installation ([ValveSoftware/SteamOS issue #1213](https://github.com/ValveSoftware/SteamOS/issues/1213)). This supports verifying candidate contents rather than trusting slot naming. The local source-quality caveat remains the one recorded in `reports/cross-distro-stability.md:147`.

## Mandate and architecture alignment

This work supports mandate invariants M-05 (stage before activation), M-06 (recoverability), M-08 (qualify support), and M-09 (repeatability), in `reports/USER_MIGRATION_MANDATE_2026-11-21.md:30-34`. It aligns with AD-11, AD-12, AD-14, AD-16, and AD-30 in `reports/ARCHITECTURE_DECISIONS.md:30-49`.

## Change and boundary

Added `evolution-engine/src/evolution/slot_activation.py`. The function is a pre-activation qualification contract, not an updater. The current engine does not discover slot topology or connect an activation executor to this gate; a future trusted probe/executor integration must call it with fresh evidence before any switch. No SteamOS labels, RAUC commands, external updater code, or source claims are treated as executable policy.

Regression tests: `STEAMOS_ACT_001`–`007` in `evolution-engine/tests/test_steam_os_ab_activation.py`.

## Verification

From `evolution-engine/`, exact command:

```sh
python3 -m unittest discover -s tests -p 'test_steam_os_ab_activation.py'
python3 -m unittest discover -s tests -p 'test_steam_os_ab_staging.py'
python3 -m unittest discover -s tests -p 'test_evolution.py'
```

Results: 7 activation tests, 6 A/B staging tests, and 30 evolution tests passed. Full output: `autonomy/codex/steamos-wave1-deepening-tests.log`.
