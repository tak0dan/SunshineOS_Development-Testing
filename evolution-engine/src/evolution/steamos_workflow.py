"""SteamOS-inspired A/B staging and activation integration.

The staging choice, phase history, and fresh candidate evidence are separate
inputs. This adapter binds them at the activation boundary so an otherwise
valid slot report cannot bypass the migration workflow's validation phase.
It only qualifies activation; it never switches firmware or writes a slot.
"""
from __future__ import annotations

from typing import Any, Mapping

from .slot_activation import SlotActivationEvidence, validate_slot_activation
from .staging import StagingAssessment, WorkflowRun


def validate_steamos_workflow_activation(
    workflow: WorkflowRun,
    assessment: StagingAssessment,
    evidence: SlotActivationEvidence | Mapping[str, Any],
    *,
    expected_os: str,
) -> None:
    """Allow the activation caller to proceed only at the qualified phase.

    The workflow must be an A/B run whose completed history ends immediately
    before ``Activate``. Candidate and rollback evidence is then checked by
    the shared slot activation gate.
    """
    if workflow.strategy != "ab_slot":
        raise ValueError("SteamOS workflow activation requires an A/B strategy")
    if assessment.strategy != workflow.strategy:
        raise ValueError("workflow strategy does not match the staging assessment")
    if not assessment.can_retain_previous:
        raise ValueError("A/B workflow has no retained previous slot")
    if workflow.aborted:
        raise ValueError("aborted workflow cannot activate a slot")
    if workflow.current != "Activate" or not workflow.completed or workflow.completed[-1] != "ValidateStaged":
        raise ValueError("workflow must pass staged validation before slot activation")
    validate_slot_activation(assessment, evidence, expected_os=expected_os)
