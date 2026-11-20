"""Stable release identity and self-describing release metadata.

A release is identified by more than an integer: parallel channels, hotfixes
and release candidates make a bare evolution index ambiguous. Identity binds
the release version, evolution index, baseline epoch, manifest schema and a
content digest over the release's own metadata.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any, Mapping

from .milestones import MilestoneVersion


def canonical_json(value: Any) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, default=str
    ).encode("utf-8")


def content_digest(value: Any) -> str:
    return hashlib.sha256(canonical_json(value)).hexdigest()


@dataclass(frozen=True)
class ReleaseIdentity:
    release_id: str
    evolution_index: int
    baseline_epoch: str
    manifest_schema: int
    content_digest: str
    release_version: str = ""
    channel: str = "stable"
    parent_release_id: str = ""
    published_at: str = ""
    engine_compatibility: str = ">=1.0,<2.0"

    @classmethod
    def create(
        cls,
        *,
        release_id: str,
        evolution_index: int,
        baseline_epoch: str,
        manifest_schema: int,
        metadata: Mapping[str, Any],
        **extra: Any,
    ) -> "ReleaseIdentity":
        """Build an identity, computing the digest over all identity fields."""
        payload = {
            "release_id": str(release_id),
            "evolution_index": int(evolution_index),
            "baseline_epoch": str(baseline_epoch),
            "manifest_schema": int(manifest_schema),
            "release_version": str(extra.get("release_version", "")),
            "channel": str(extra.get("channel", "stable")),
            "parent_release_id": str(extra.get("parent_release_id", "")),
            "published_at": str(extra.get("published_at", "")),
            "engine_compatibility": str(extra.get("engine_compatibility", ">=1.0,<2.0")),
            "metadata": dict(metadata),
        }
        return cls(
            release_id=payload["release_id"],
            evolution_index=payload["evolution_index"],
            baseline_epoch=payload["baseline_epoch"],
            manifest_schema=payload["manifest_schema"],
            content_digest=content_digest(payload),
            release_version=payload["release_version"],
            channel=payload["channel"],
            parent_release_id=payload["parent_release_id"],
            published_at=payload["published_at"],
            engine_compatibility=payload["engine_compatibility"],
        )

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "ReleaseIdentity":
        return cls(
            release_id=str(data.get("release_id", "")),
            evolution_index=int(data.get("evolution_index", 0)),
            baseline_epoch=str(data.get("baseline_epoch", "")),
            manifest_schema=int(data.get("manifest_schema", 0)),
            content_digest=str(data.get("content_digest", "")).lower(),
            release_version=str(data.get("release_version", "")),
            channel=str(data.get("channel", "stable")),
            parent_release_id=str(data.get("parent_release_id", "")),
            published_at=str(data.get("published_at", "")),
            engine_compatibility=str(data.get("engine_compatibility", ">=1.0,<2.0")),
        )

    @property
    def milestone(self) -> MilestoneVersion:
        return MilestoneVersion((self.evolution_index,))

    def validate(self) -> list[str]:
        errors: list[str] = []
        if not self.release_id:
            errors.append("release has no release_id")
        if self.evolution_index < 0:
            errors.append(f"{self.release_id}: evolution_index must be >= 0")
        if not self.baseline_epoch:
            errors.append(f"{self.release_id}: no baseline_epoch")
        if self.manifest_schema < 1:
            errors.append(f"{self.release_id}: manifest_schema must be >= 1")
        if len(self.content_digest) != 64:
            errors.append(f"{self.release_id}: malformed content_digest")
        if not self.engine_compatibility:
            errors.append(f"{self.release_id}: no engine compatibility declaration")
        return errors

    def to_dict(self) -> dict[str, Any]:
        return {
            "release_id": self.release_id,
            "evolution_index": self.evolution_index,
            "baseline_epoch": self.baseline_epoch,
            "manifest_schema": self.manifest_schema,
            "content_digest": self.content_digest,
            "release_version": self.release_version,
            "channel": self.channel,
            "parent_release_id": self.parent_release_id,
            "published_at": self.published_at,
            "engine_compatibility": self.engine_compatibility,
        }
