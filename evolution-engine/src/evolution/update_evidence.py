"""Fail-closed validation of terminal update completion evidence.

Update orchestration can finish package and migration work while boot artifacts
remain unusable. A caller must not publish update completion until the required
stages have succeeded in order and boot verification has observed its result.
This module validates evidence only; it performs no update or reboot action.
"""
from __future__ import annotations

from collections.abc import Sequence


REQUIRED_UPDATE_STAGES = ("package_transaction", "migrations", "boot_verification")


def validate_update_completion_evidence(
    completed_stages: Sequence[str],
    failed_stages: Sequence[str] = (),
) -> list[str]:
    """Return blockers to declaring an update complete.

    Extra stages are allowed, but required stages must occur in canonical
    order. A stage recorded as failed blocks completion even if a later retry
    also appears in the sequence; callers should supply the reconciled journal
    view rather than an append-only event history.
    """
    errors: list[str] = []
    positions: dict[str, int] = {}
    for index, stage in enumerate(completed_stages):
        if stage in REQUIRED_UPDATE_STAGES:
            if stage in positions:
                errors.append(f"required update stage {stage!r} is recorded more than once")
            else:
                positions[stage] = index

    for stage in REQUIRED_UPDATE_STAGES:
        if stage not in positions:
            errors.append(f"required update stage {stage!r} was not completed")
        if stage in failed_stages:
            errors.append(f"required update stage {stage!r} has a failed result")

    present = [stage for stage in REQUIRED_UPDATE_STAGES if stage in positions]
    if present != sorted(present, key=positions.__getitem__):
        errors.append("required update stages are out of order")
    return errors
