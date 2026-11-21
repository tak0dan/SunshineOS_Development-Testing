"""Fail-closed qualification for switching into a staged A/B slot.

Slot names and an updater's successful write status do not prove that the
candidate contains the intended operating system or that rollback remains
possible. Call this gate immediately before activation, using fresh probes.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from .staging import StagingAssessment


@dataclass(frozen=True)
class SlotActivationEvidence:
    candidate_slot: str
    candidate_os: str
    staged_validation_passed: bool
    previous_slot_bootable: bool

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> "SlotActivationEvidence":
        return cls(
            candidate_slot=str(data.get("candidate_slot", "")),
            candidate_os=str(data.get("candidate_os", "")),
            staged_validation_passed=data.get("staged_validation_passed") is True,
            previous_slot_bootable=data.get("previous_slot_bootable") is True,
        )


def validate_slot_activation(
    assessment: StagingAssessment,
    evidence: SlotActivationEvidence | Mapping[str, Any],
    *,
    expected_os: str,
) -> None:
    """Raise ``ValueError`` unless fresh evidence permits A/B activation.

    The candidate's detected OS identity must match the requested target, the
    staged validation must have passed, and the original slot must remain
    bootable. Unknown or malformed evidence always blocks activation.
    """
    if assessment.strategy != "ab_slot":
        raise ValueError("slot activation requires an A/B staging assessment")
    if not assessment.active_slot or not assessment.candidate_slot:
        raise ValueError("A/B assessment has no active and candidate slot identities")
    if assessment.active_slot == assessment.candidate_slot:
        raise ValueError("A/B assessment slots must be distinct")
    if not expected_os.strip():
        raise ValueError("expected target OS identity is required")

    observed = (evidence if isinstance(evidence, SlotActivationEvidence)
                else SlotActivationEvidence.from_mapping(evidence))
    if observed.candidate_slot != assessment.candidate_slot:
        raise ValueError("observed candidate slot does not match the planned slot")
    if observed.candidate_os.casefold() != expected_os.strip().casefold():
        raise ValueError("candidate slot OS identity does not match the target")
    if not observed.staged_validation_passed:
        raise ValueError("candidate slot has not passed staged validation")
    if not observed.previous_slot_bootable:
        raise ValueError("previous slot is not confirmed bootable")
