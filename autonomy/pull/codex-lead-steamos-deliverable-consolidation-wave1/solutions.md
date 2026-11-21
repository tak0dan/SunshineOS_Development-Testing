# Solution

Added `evolution-engine/src/evolution/steamos_workflow.py::validate_steamos_workflow_activation`. It requires an active A/B workflow at `Activate`, immediately after `ValidateStaged`, an A/B staging assessment matching that workflow, a retained previous slot, and the existing fresh candidate evidence checks.

Regression test `evolution-engine/tests/test_steamos_workflow.py` adds IDs `STEAMOS_FLOW_001`–`004`.
