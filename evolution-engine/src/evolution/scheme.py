"""Load and validate the declarative evolutionary scheme."""
from __future__ import annotations

import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from .milestones import MilestoneRegistry
from .versions import VersionSet

DEFAULT_SCHEME_PATH = Path(__file__).resolve().with_name("scheme.toml")


@dataclass(frozen=True)
class Scheme:
    format_version: int
    registry: MilestoneRegistry
    versions: VersionSet
    baseline_epoch: str

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "Scheme":
        if int(data.get("format_version", 0)) != 1:
            raise ValueError(f"unsupported scheme format_version {data.get('format_version')!r}")
        aliases = {
            str(entry.get("name", "")).strip().lower(): str(entry.get("version", ""))
            for entry in data.get("aliases", [])
            if isinstance(entry, Mapping) and entry.get("name")
        }
        registry = MilestoneRegistry.from_dict({
            "current": data.get("current", "0"),
            "aliases": aliases,
            "milestones": data.get("milestone", data.get("milestones", [])),
        })
        versions = VersionSet.from_dict({
            "os_evolution": f"E{int(registry.current.parts[0]):03d}",
            "migration_engine": str(data.get("engine_version", "ME1")),
            "inventory_schema": str(data.get("inventory_schema", "INV1")),
            "evolution_schema": str(data.get("evolution_schema", "EVS1")),
            "transition_catalog": str(data.get("transition_catalog", "TC1")),
            "baseline": str(data.get("baseline_epoch", "")),
        })
        return cls(
            format_version=1,
            registry=registry,
            versions=versions,
            baseline_epoch=str(data.get("baseline_epoch", "")),
        )

    def validate(self) -> list[str]:
        errors = list(self.versions.validate())
        if not self.baseline_epoch:
            errors.append("scheme has no baseline_epoch")
        return errors

    def to_dict(self) -> dict[str, Any]:
        return {
            "format_version": self.format_version,
            "baseline_epoch": self.baseline_epoch,
            "versions": self.versions.to_dict(),
            "registry": self.registry.to_dict(),
        }


def load_scheme(path: str | Path | None = None) -> Scheme:
    """Load a TOML scheme, failing closed on malformed or contradictory data."""
    source = Path(path) if path is not None else DEFAULT_SCHEME_PATH
    try:
        data = tomllib.loads(source.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValueError(f"scheme not found: {source}") from exc
    except tomllib.TOMLDecodeError as exc:
        raise ValueError(f"invalid scheme TOML {source}: {exc}") from exc
    scheme = Scheme.from_dict(data)
    errors = scheme.validate()
    if errors:
        raise ValueError("invalid evolutionary scheme: " + "; ".join(errors))
    return scheme
