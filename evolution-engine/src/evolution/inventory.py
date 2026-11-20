"""Canonical, versioned, observational system inventory.

The migration engine never compares raw source-distro output with evolution
YAML. Both actual and desired state are expressed in this stable schema. The
inventory is *observational*: it records what exists and never decides what is
permitted, removed or changed -- those are planner policy decisions.

Inventory schema versioning is independent of release numbers: releases 1-5
may use schema 1, releases 6-20 schema 2, and so on. Old inventory records are
converted through explicit inventory-schema converters, never through release
evolution records.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Mapping

INVENTORY_SCHEMA = 1

DOMAINS = (
    "identity", "hardware", "storage", "boot", "packages", "repositories",
    "services", "configuration", "users", "network", "desktop", "security",
    "runtime", "migration_metadata",
)


@dataclass
class Inventory:
    """One normalized observation of a machine."""

    schema: int = INVENTORY_SCHEMA
    identity: dict[str, Any] = field(default_factory=dict)
    hardware: dict[str, Any] = field(default_factory=dict)
    storage: dict[str, Any] = field(default_factory=dict)
    boot: dict[str, Any] = field(default_factory=dict)
    packages: dict[str, Any] = field(default_factory=dict)
    repositories: dict[str, Any] = field(default_factory=dict)
    services: dict[str, Any] = field(default_factory=dict)
    configuration: dict[str, Any] = field(default_factory=dict)
    users: dict[str, Any] = field(default_factory=dict)
    network: dict[str, Any] = field(default_factory=dict)
    desktop: dict[str, Any] = field(default_factory=dict)
    security: dict[str, Any] = field(default_factory=dict)
    runtime: dict[str, Any] = field(default_factory=dict)
    migration_metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "Inventory":
        return cls(
            schema=int(data.get("schema", INVENTORY_SCHEMA)),
            **{
                domain: dict(data.get(domain) or {})
                for domain in DOMAINS
            },
        )

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {"schema": self.schema}
        for domain in DOMAINS:
            result[domain] = dict(getattr(self, domain))
        return result

    def domain(self, name: str) -> dict[str, Any]:
        if name not in DOMAINS:
            raise ValueError(f"unknown inventory domain {name!r}")
        return getattr(self, name)


def from_observed(observed: Any) -> Inventory:
    """Normalize an :class:`~core.ObservedState` without changing its meaning.

    This function is deliberately lossless in spirit but not authoritative:
    unrecognized facts remain in ``runtime.extra`` so later schema versions can
    interpret them. It never sets a policy or removal decision.
    """
    inv = Inventory(schema=INVENTORY_SCHEMA)
    inv.identity = {
        "distribution": getattr(observed, "distribution", "unknown"),
        "architecture": getattr(observed, "architecture", "unknown"),
        "init_system": getattr(observed, "init_system", "unknown"),
        "package_manager": getattr(observed, "package_manager", "unknown"),
    }
    inv.packages = {
        "installed": dict(getattr(observed, "packages", {})),
        "foreign": list(getattr(observed, "foreign_packages", [])),
    }
    inv.repositories = {
        "configured": list(getattr(observed, "repositories", [])),
        "generation": int(getattr(observed, "repository_generation", 0)),
    }
    capabilities = sorted(getattr(observed, "capabilities", set()))
    inv.runtime = {
        "capabilities": capabilities,
        "observations": {
            key: {
                "detected": getattr(value, "detected", ""),
                "confidence": str(getattr(value, "confidence", "low")),
                "status": str(getattr(value, "status", "absent")),
                "evidence": list(getattr(value, "evidence", [])),
            }
            for key, value in sorted(
                getattr(observed, "observations", {}).items()
            )
        },
    }
    inv.users = {
        "accounts": list(getattr(observed, "users", [])),
        "groups": dict(getattr(observed, "groups", {})),
        "home_directories": list(getattr(observed, "home_directories", [])),
    }
    # Domains not yet surfaced by discovery stay observational placeholders.
    inv.boot = {"capabilities": [c for c in capabilities if "boot" in c]}
    inv.services = {"capabilities": [c for c in capabilities if "service" in c]}
    inv.desktop = {"capabilities": [c for c in capabilities if "desktop" in c]}
    inv.storage = {"capabilities": [c for c in capabilities if "storage" in c]}
    inv.configuration = {"managed_resources": []}
    inv.network = {"capabilities": [c for c in capabilities if "network" in c]}
    inv.hardware = {"architecture": inv.identity["architecture"]}
    inv.security = {"require_signed_packages": "signed" in capabilities}
    inv.migration_metadata = {"sunshine_adopted": "sunshine" in capabilities}
    return inv


# Inventory-schema converters. These are independent of release evolution.
Converter = Callable[[Inventory], Inventory]


def _v1_to_v2(inv: Inventory) -> Inventory:
    """Example forward converter: split repository signing into its own key."""
    upgraded = Inventory.from_dict(inv.to_dict())
    upgraded.schema = 2
    configured = upgraded.repositories.get("configured", [])
    upgraded.repositories["signing"] = {
        "verified": [r for r in configured if str(r).endswith("[signed]")],
    }
    return upgraded


INVENTORY_CONVERTERS: dict[int, Converter] = {
    1: _v1_to_v2,
}


def upgrade_inventory(inv: Inventory, target_schema: int = INVENTORY_SCHEMA) -> Inventory:
    """Convert an old inventory record forward using schema converters only."""
    if target_schema < inv.schema:
        raise ValueError(
            f"refusing inventory downgrade {inv.schema} -> {target_schema}"
        )
    current = inv
    while current.schema < target_schema:
        converter = INVENTORY_CONVERTERS.get(current.schema)
        if converter is None:
            raise ValueError(
                f"no inventory converter from schema {current.schema}; "
                "release evolution cannot convert inventory schemas"
            )
        current = converter(current)
    return current
