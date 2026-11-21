# SteamOS repair tooling survey — Wave 1

## Catalogue and evidence

| Exact path / symbol | Finding | SunshineOS implication |
|---|---|---|
| `reports/CROSS_DISTRO_RESEARCH_2026-11-21.md:283-310` | Local SteamOS research catalogue describes read-only root operation, `steamos-readonly`, developer mode, RAUC/Casync slot updates and previous-slot rollback. This is a research summary, not a checked-out SteamOS source tree. | Treat root writable state and boot-slot state as separate observed facts. |
| `reports/cross-distro-stability.md:19,106-110,147` | Cross-distro catalogue records the RAUC/Casync update design, keeplist and evidence-source caveat. S13 is the strongest technical source cited; several neighboring details use secondary sources. | Borrow plan/verify/recover invariants, not undocumented implementation details. |
| `/usr/lib/rauc/bootloader-custom-backend.sh` | Path named by the local SteamOS research catalogue for custom RAUC bootloader state handling. No local copy exists in this repository. | Do not treat slot names or update success as proof of bootability; use the separate candidate validation gate. |
| `/usr/lib/steamos/steamos-devmode` | Valve issue #1654 reports a `steamos-devmode enable` failure while creating this marker, despite `steamos-readonly status` reporting disabled. This is a reported failure mode, not a locally inspected script. | Detect contradictory readonly, mount and devmode observations; do not blindly retry package operations. |
| `evolution-engine/src/evolution/tools/steamos_repair.py::assess_steamos_repair` | New pure assessment of root mount readonly state, tool status and devmode marker state. | Unknown or contradictory observations block package repair and point to recovery. |
| `evolution-engine/src/evolution/slot_activation.py::validate_slot_activation` | Existing adjacent A/B gate checks candidate OS identity, validation and prior-slot bootability. | A diagnosis does not authorize activation; slot switching remains a separate gated operation. |
| `evolution-engine/tests/test_steamos_repair.py` | `T_STEAMOS_REPAIR_001`–`008` cover coherent state, protected root, contradictory state, partial devmode, missing marker, incomplete evidence, unknown status and unclassified writable state. | Regressions guarantee assessment fails closed and never claims a mutation occurred. |

### Upstream grounding

SteamOS update mechanics are grounded in the Collabora technical account of SteamOS 3.6 RAUC/Casync update changes: [Collabora — SteamOS 3.6 atomic updates](https://www.collabora.com/news-and-blog/news-and-events/steamos-3-6-how-the-steam-deck-atomic-updates-are-improving.html). A concrete developer-mode partial failure is recorded by [ValveSoftware/SteamOS issue #1654](https://github.com/ValveSoftware/SteamOS/issues/1654): the report says readonly status was `disable`, while developer-mode marker creation failed and package operations still encountered read-only errors. These are not equivalent to source-code inspection. The SteamOS checkout/ISO is unavailable in this workspace, so file paths above are catalogue/reported paths and were not opened from an image.

## Change summary

Added a read-only repair assessment for a known SteamOS failure class. It distinguishes a protected root, internally consistent developer mode, incomplete developer mode, contradictory observations and insufficient evidence. Contradictions stop the flow and recommend the vendor recovery path or retained known-good slot. The assessment does not run `steamos-readonly`, `steamos-devmode`, `pacman`, RAUC, mount operations or any other command.

This is diagnostic qualification, not an automatic repair or end-to-end SteamOS support claim. Callers must supply fresh, trusted probe results; no live probe adapter is wired yet.

## Verification

From `evolution-engine/`:

```text
python3 -m unittest tests/test_steamos_repair.py -v
```

Result: **8 tests passed** (`T_STEAMOS_REPAIR_001`–`008`). Full transcript: `autonomy/codex/steamos-repair-wave1-test.log`.
