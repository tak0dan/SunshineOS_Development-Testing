"""Signed, versioned adapters for nonstandard privileged operations.

Spec §13.2 forbids a plugin free-for-all.  Adapters may only expand the set of
typed operations through a narrow interface: Rust runtime, signed artifact,
declared permissions, declared parameters, and a verified trust chain.  They
can never modify the trust root, write sudoers policy, or disable validation.
"""
from __future__ import annotations

import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping

from .core import OpType, Operation

ALLOWED_OPERATIONS = frozenset({
    OpType.MIGRATE_CONFIGURATION,
    OpType.TRANSFER_OWNERSHIP,
    OpType.ENABLE_SERVICE,
    OpType.DISABLE_SERVICE,
    OpType.GENERATE_INITRAMFS,
    OpType.INSTALL_BOOT_ENTRY,
    OpType.VALIDATE_CAPABILITY,
})
ALLOWED_PERMISSIONS = frozenset({
    "read-configuration",
    "write-managed-configuration",
    "read-package-database",
    "manage-own-service",
    "write-owned-state",
    "read-boot-configuration",
    "write-boot-entry",
    "run-validation",
})
FORBIDDEN_PERMISSIONS = frozenset({
    "modify-trust-root",
    "write-sudoers",
    "disable-validation",
    "execute-arbitrary-shell",
    "bypass-migration-journal",
})
FORBIDDEN_PARAM_KEYS = frozenset({
    "command", "cmd", "shell", "script", "sudoers", "trust_root", "signature", "verifier",
})


@dataclass(frozen=True)
class AdapterManifest:
    id: str
    component: str
    version: str
    runtime: str
    operation: OpType
    artifact: str
    artifact_sha256: str
    signature: str
    signed_by: str
    source_schema: int
    target_schema: int
    permissions: tuple[str, ...] = ()
    declared_params: tuple[str, ...] = ()
    provides: tuple[str, ...] = ()
    description: str = ""

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "AdapterManifest":
        artifact = dict(data.get("artifact") or {})
        schema = dict(data.get("schema") or {})
        return cls(
            id=str(data.get("id", "")),
            component=str(data.get("component", "")),
            version=str(data.get("version", "")),
            runtime=str(data.get("runtime", "")).lower(),
            operation=OpType(str(data.get("operation", ""))),
            artifact=str(artifact.get("name", "")),
            artifact_sha256=str(artifact.get("sha256", "")).lower(),
            signature=str(data.get("signature", "")),
            signed_by=str(data.get("signed_by", "")).upper(),
            source_schema=int(schema.get("from", 0)),
            target_schema=int(schema.get("to", 0)),
            permissions=tuple(str(p) for p in data.get("permissions", [])),
            declared_params=tuple(str(p) for p in data.get("parameters", [])),
            provides=tuple(str(p) for p in data.get("provides", [])),
            description=str(data.get("description", "")),
        )

    def to_operation(self, params: Mapping[str, Any] | None = None,
                     *, operation_id: str | None = None) -> Operation:
        """Build a typed operation after :func:`validate_adapter` has passed."""
        supplied = dict(params or {})
        forbidden = FORBIDDEN_PARAM_KEYS.intersection(supplied)
        if forbidden:
            raise ValueError(
                "adapter parameters reject privileged escape keys: " + ", ".join(sorted(forbidden))
            )
        unknown = set(supplied) - set(self.declared_params)
        if unknown:
            raise ValueError(
                f"adapter {self.id}: undeclared parameters: " + ", ".join(sorted(unknown))
            )
        merged = dict(supplied)
        merged.update({
            "adapter_id": self.id,
            "adapter_version": self.version,
            "adapter_artifact": self.artifact,
            "source_schema": self.source_schema,
            "target_schema": self.target_schema,
        })
        return Operation(
            id=operation_id or f"adapter-{self.id}",
            type=self.operation,
            component=self.component,
            params=merged,
        )


def validate_adapter(
    manifest: AdapterManifest,
    *,
    verified_artifacts: set[str] | frozenset[str],
    contract_component_ids: set[str],
) -> list[str]:
    """Return validation errors; empty means the adapter may be used."""
    errors: list[str] = []
    if not manifest.id or not manifest.component:
        errors.append("adapter must declare id and component")
    if manifest.component not in contract_component_ids:
        errors.append(f"adapter {manifest.id}: component '{manifest.component}' has no contract")
    if manifest.runtime != "rust":
        errors.append(
            f"adapter {manifest.id}: privileged adapters must be Rust, got '{manifest.runtime}'"
        )
    if manifest.operation not in ALLOWED_OPERATIONS:
        errors.append(f"adapter {manifest.id}: operation {manifest.operation.value} is not an approved interface")
    if manifest.source_schema >= manifest.target_schema:
        errors.append(f"adapter {manifest.id}: schema transition must increase")
    if manifest.artifact not in verified_artifacts:
        errors.append(f"adapter {manifest.id}: artifact '{manifest.artifact}' was not verified by Stage A")
    if not manifest.signature or not manifest.signed_by:
        errors.append(f"adapter {manifest.id}: missing signature metadata")
    bad = FORBIDDEN_PERMISSIONS.intersection(manifest.permissions)
    if bad:
        errors.append(f"adapter {manifest.id}: forbidden permissions: " + ", ".join(sorted(bad)))
    unknown = set(manifest.permissions) - ALLOWED_PERMISSIONS - FORBIDDEN_PERMISSIONS
    if unknown:
        errors.append(f"adapter {manifest.id}: unknown permissions: " + ", ".join(sorted(unknown)))
    if any(key in FORBIDDEN_PARAM_KEYS for key in manifest.declared_params):
        errors.append(f"adapter {manifest.id}: declares forbidden parameter keys")
    return errors


def load_manifest(path: str | Path) -> AdapterManifest:
    path = Path(path)
    try:
        data = tomllib.loads(path.read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError) as exc:
        raise ValueError(f"cannot load adapter manifest {path}: {exc}") from exc
    return AdapterManifest.from_dict(data)


def load_manifests(directory: str | Path) -> dict[str, AdapterManifest]:
    base = Path(directory)
    manifests: dict[str, AdapterManifest] = {}
    if not base.is_dir():
        return manifests
    for path in sorted(base.glob("*.toml")):
        manifest = load_manifest(path)
        if manifest.id in manifests:
            raise ValueError(f"duplicate adapter id {manifest.id}")
        manifests[manifest.id] = manifest
    return manifests
