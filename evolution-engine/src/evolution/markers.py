"""Fail-closed reconciliation for persisted per-user migration markers.

Some update systems store migration completion in user state while snapshots
restore only the root filesystem. A marker is therefore a claim, not proof.
This module compares each claim with both the migration journal and fresh
observations before callers may treat it as complete.
"""
from __future__ import annotations

import re
from typing import Mapping

_SHA256 = re.compile(r"^[0-9a-f]{64}$")


def _is_sha256(value: str) -> bool:
    return bool(_SHA256.fullmatch(value))


def validate_user_completion_markers(
    markers: Mapping[str, str],
    journal_outputs: Mapping[str, str],
    observed_outputs: Mapping[str, str],
) -> list[str]:
    """Return inconsistencies between per-user markers and current root state.

    ``markers`` maps operation IDs to the output hash recorded by the user's
    migration marker. ``journal_outputs`` contains hashes for journaled,
    completed operations only. ``observed_outputs`` must come from fresh system
    discovery. Any missing or mismatched evidence is an error; this function
    never changes markers or journal state.
    """
    errors: list[str] = []
    for operation_id in sorted(markers):
        marker_hash = markers[operation_id]
        prefix = f"user marker {operation_id}"
        if not operation_id:
            errors.append("user marker has an empty operation ID")
            continue
        if not _is_sha256(marker_hash):
            errors.append(f"{prefix}: completion marker has an invalid SHA-256 output hash")
            continue

        journal_hash = journal_outputs.get(operation_id)
        if not journal_hash:
            errors.append(f"{prefix}: no matching completed journal operation")
            continue
        if not _is_sha256(journal_hash):
            errors.append(f"{prefix}: completed journal record has an invalid SHA-256 output hash")
            continue
        if marker_hash != journal_hash:
            errors.append(f"{prefix}: output hash differs from completed journal record")

        observed_hash = observed_outputs.get(operation_id)
        if not observed_hash:
            errors.append(f"{prefix}: current system output was not observed")
        elif not _is_sha256(observed_hash):
            errors.append(f"{prefix}: current system output has an invalid SHA-256 hash")
        elif observed_hash != journal_hash:
            errors.append(f"{prefix}: current system output differs from completed journal record")
    return errors
