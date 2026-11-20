"""Release-channel admission control for evolutionary upgrades.

A published milestone is not sufficient authority to cross it. The guard also
requires signed artifacts, a minimum soak time, verified recovery, and a
compatible support tier. Every missing fact fails closed; no field defaults to
"safe" merely because it was omitted.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping


@dataclass(frozen=True)
class ChannelPolicy:
    """Rules a release must satisfy before an updater may cross a milestone."""

    allowed_channels: tuple[str, ...] = ("stable",)
    signed_required: bool = True
    verification_required: bool = True
    minimum_age_days: int = 3
    require_recovery: bool = True
    require_rollback: bool = True
    require_qualified_support: bool = True
    allow_unpublished: bool = False
    allow_dirty_state: bool = False
    allow_unknown_channel: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "allowed_channels": list(self.allowed_channels),
            "signed_required": self.signed_required,
            "verification_required": self.verification_required,
            "minimum_age_days": self.minimum_age_days,
            "require_recovery": self.require_recovery,
            "require_rollback": self.require_rollback,
            "require_qualified_support": self.require_qualified_support,
            "allow_unpublished": self.allow_unpublished,
            "allow_dirty_state": self.allow_dirty_state,
            "allow_unknown_channel": self.allow_unknown_channel,
        }


@dataclass(frozen=True)
class ChannelDecision:
    allowed: bool
    channel: str
    reasons: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {"allowed": self.allowed, "channel": self.channel, "reasons": list(self.reasons)}


def guard_update(context: Mapping[str, Any], policy: ChannelPolicy | None = None) -> ChannelDecision:
    """Evaluate a migration context against a channel policy, failing closed."""

    policy = policy or ChannelPolicy()
    reasons: list[str] = []
    channel = str(context.get("channel", "")).strip().lower() or "unknown"
    allowed_channels = {name.lower() for name in policy.allowed_channels}

    if channel not in allowed_channels:
        if channel == "unknown" and policy.allow_unknown_channel:
            reasons.append("channel is unknown but policy allows the generic path")
        else:
            reasons.append(f"channel {channel!r} is not allowed")

    if policy.signed_required and not bool(context.get("signed")):
        reasons.append("artifacts are not signed")
    if policy.verification_required and not bool(context.get("verification_passed")):
        reasons.append("artifact verification has not passed")
    if policy.require_recovery and not bool(context.get("recovery_available")):
        reasons.append("no recovery environment or checkpoint is available")
    if policy.require_rollback and not bool(context.get("rollback_available")):
        reasons.append("no rollback procedure is available")

    try:
        age_days = int(context.get("artifact_age_days", -1))
    except (TypeError, ValueError):
        age_days = -1
    if age_days < policy.minimum_age_days:
        reasons.append(f"artifact age {age_days}d is below soak minimum {policy.minimum_age_days}d")

    if not policy.allow_unpublished and bool(context.get("unpublished")):
        reasons.append("target milestone is unpublished")
    if not policy.allow_dirty_state and bool(context.get("dirty_state")):
        reasons.append("working state is dirty")

    support_tier = str(context.get("support_tier", "")).strip().lower() or "unsupported"
    if policy.require_qualified_support and support_tier not in ("qualified", "qualified_with_intervention"):
        reasons.append(f"support tier {support_tier!r} is not qualified")

    if not bool(context.get("published", True)):
        reasons.append("release is not published")
    if bool(context.get("revoked", False)):
        reasons.append("release has been revoked")

    return ChannelDecision(not reasons, channel, tuple(reasons))
