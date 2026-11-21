# SteamOS deliverable consolidation — Wave 1

## Survey and catalogue

The repository implements three relevant boundaries:

| Exact path / symbol | Existing behavior | Consolidation finding |
|---|---|---|
| `evolution-engine/src/evolution/staging.py::StagingCapability.ab_slot_possible` | Selects A/B only from observed distinct active/inactive slot IDs, inactive-slot availability, and switch capability. `assess_staging` prefers recovery reconstruction when requested. | A/B staging is capability based, consistent with mandate M-01/M-04. |
| `evolution-engine/src/evolution/staging.py::WorkflowRun` | Enforces a fixed phase prefix, including `Build → ValidateStaged → Activate → BootValidate`, and rejects skipped/forged phases. | Correct history invariants did not previously guard the activation API. |
| `evolution-engine/src/evolution/slot_activation.py::validate_slot_activation` | Checks planned candidate ID, target OS identity, staged-validation result, and retained previous-slot bootability. It is a pure qualification function. | No connection to a `WorkflowRun`; callers could invoke it before staged validation. |
| `evolution-engine/tests/test_steam_os_ab_staging.py` | `STEAMOS_AB_001`–`006` cover slot detection and phase-history invariants. | Workflow-history coverage did not exercise an activation boundary. |
| `evolution-engine/tests/test_steam_os_ab_activation.py` | `STEAMOS_ACT_001`–`007` check activation evidence in isolation. | Demonstrated the reusable leaf gate but left orchestration to callers. |
| `evolution-engine/src/evolution/steamos_workflow.py::validate_steamos_workflow_activation` | New integration gate checks A/B strategy agreement, retained previous slot, non-aborted workflow, and exact `Activate` phase after `ValidateStaged`, then delegates to the evidence gate. | Closes the sequencing gap without introducing platform commands or slot mutation. |
| `evolution-engine/tests/test_steamos_workflow.py` | New `STEAMOS_FLOW_001`–`004` cover phase ordering, abort, assessment mismatch, and bad rollback evidence. | Regression locks the integrated boundary. |

### Research source limits

The mandate calls for deep SteamOS research. Existing repository notes in `autonomy/codex/steamos-repair-wave1.md` identify the local catalogue at `reports/CROSS_DISTRO_RESEARCH_2026-11-21.md:283-310`, the reported RAUC backend path `/usr/lib/rauc/bootloader-custom-backend.sh`, and the issue-reported `/usr/lib/steamos/steamos-devmode` marker. Prior work records that there is no SteamOS source checkout or ISO available in this workspace; these are catalogue or upstream-reported paths, not locally inspected files. This change therefore consolidates the migration integration proven by repository code and makes no claim of full device or firmware qualification.

## Change summary

Added `validate_steamos_workflow_activation` to bind the existing slot activation evidence check to the workflow state machine. It blocks activation unless the workflow is an active A/B run at `Activate`, its immediately preceding completed phase is `ValidateStaged`, the assessment matches the workflow strategy, and the previous slot is retainable. The function only qualifies activation; the caller remains responsible for any external switch mechanism.

## Verification

Command, run from `evolution-engine/`:

```text
python3 -m unittest tests/test_steamos_workflow.py tests/test_steam_os_ab_activation.py tests/test_steam_os_ab_staging.py -v
```

Result: **17 tests passed**, including `STEAMOS_FLOW_001`–`004`, `STEAMOS_ACT_001`–`007`, and `STEAMOS_AB_001`–`006`.

Full transcript: `autonomy/codex/steamos-deliverable-consolidation-wave1-test.log`.
