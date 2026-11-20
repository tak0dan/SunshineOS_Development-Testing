"""Declarative service supervision plans.

Service state is part of the desired target, not an installer side effect. The
supervisor converts validated specs into argv commands and idempotent drop-in
configuration. It does not execute anything itself and never invokes a shell.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Iterable, Mapping, Sequence

UNIT_RE = re.compile(r"^[A-Za-z0-9@._-]+\.(service|socket|timer|target|path)$")
DESIRED = ("enabled", "disabled", "present", "absent")
RESTART = ("no", "on-success", "on-failure", "on-abnormal", "on-watchdog", "on-abort", "always")
CLASSIFICATIONS = ("essential", "standard", "best-effort")


@dataclass(frozen=True)
class ServiceSpec:
    """One supervised unit and its declared operational contract."""

    unit: str
    desired: str = "enabled"
    runtime: str = "systemd"
    restart: str = "on-failure"
    classification: str = "standard"
    start_limit_burst: int = 5
    start_limit_interval_sec: int = 60
    timeout_start_sec: int = 90
    dependencies: tuple[str, ...] = ()
    environment: Mapping[str, str] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "ServiceSpec":
        return cls(
            unit=str(data.get("unit", "")),
            desired=str(data.get("desired", "enabled")),
            runtime=str(data.get("runtime", "systemd")),
            restart=str(data.get("restart", "on-failure")),
            classification=str(data.get("classification", "standard")),
            start_limit_burst=int(data.get("start_limit_burst", 5)),
            start_limit_interval_sec=int(data.get("start_limit_interval_sec", 60)),
            timeout_start_sec=int(data.get("timeout_start_sec", 90)),
            dependencies=tuple(str(d) for d in data.get("dependencies", [])),
            environment={
                str(k): str(v) for k, v in (data.get("environment") or {}).items()
            },
        )

    def validate(self) -> list[str]:
        errors: list[str] = []
        if not UNIT_RE.match(self.unit):
            errors.append(f"invalid systemd unit name {self.unit!r}")
        if self.desired not in DESIRED:
            errors.append(f"{self.unit}: invalid desired state {self.desired!r}")
        if self.runtime != "systemd":
            errors.append(f"{self.unit}: unsupported runtime {self.runtime!r}")
        if self.restart not in RESTART:
            errors.append(f"{self.unit}: invalid restart policy {self.restart!r}")
        if self.classification not in CLASSIFICATIONS:
            errors.append(f"{self.unit}: invalid classification {self.classification!r}")
        if self.start_limit_burst < 0 or self.start_limit_interval_sec <= 0:
            errors.append(f"{self.unit}: start-limit values are out of range")
        if self.timeout_start_sec <= 0:
            errors.append(f"{self.unit}: timeout_start_sec must be positive")
        if len(set(self.dependencies)) != len(self.dependencies):
            errors.append(f"{self.unit}: duplicate dependencies")
        return errors

    def to_dict(self) -> dict[str, Any]:
        return {
            "unit": self.unit,
            "desired": self.desired,
            "runtime": self.runtime,
            "restart": self.restart,
            "classification": self.classification,
            "start_limit_burst": self.start_limit_burst,
            "start_limit_interval_sec": self.start_limit_interval_sec,
            "timeout_start_sec": self.timeout_start_sec,
            "dependencies": list(self.dependencies),
            "environment": dict(sorted(self.environment.items())),
        }


@dataclass(frozen=True)
class SupervisionPlan:
    unit: str
    desired: str
    commands: tuple[tuple[str, ...], ...]
    drop_in: str
    rationale: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "unit": self.unit,
            "desired": self.desired,
            "commands": [list(command) for command in self.commands],
            "drop_in": self.drop_in,
            "rationale": self.rationale,
        }


class ServiceSupervisor:
    """Validate specs and render deterministic supervision plans."""

    def plan(self, specs: Iterable[ServiceSpec]) -> list[SupervisionPlan]:
        unique: dict[str, ServiceSpec] = {}
        for spec in specs:
            errors = spec.validate()
            if errors:
                raise ValueError("; ".join(errors))
            if spec.unit in unique:
                raise ValueError(f"duplicate service spec {spec.unit}")
            unique[spec.unit] = spec

        plans: list[SupervisionPlan] = []
        for unit in sorted(unique):
            spec = unique[unit]
            if spec.desired in ("enabled", "present"):
                commands: tuple[tuple[str, ...], ...] = (
                    ("systemctl", "enable", unit),
                    ("systemctl", "start", unit),
                )
            else:
                commands = (
                    ("systemctl", "stop", unit),
                    ("systemctl", "disable", unit),
                )
            plans.append(SupervisionPlan(
                unit=unit,
                desired=spec.desired,
                commands=commands,
                drop_in=self.render_drop_in(spec),
                rationale=(
                    f"{spec.classification} unit with restart={spec.restart} "
                    f"and timeout={spec.timeout_start_sec}s"
                ),
            ))
        return plans

    @staticmethod
    def render_drop_in(spec: ServiceSpec) -> str:
        lines = [
            f"# SunshineOS managed supervision for {spec.unit}",
            "[Unit]",
            f"StartLimitBurst={spec.start_limit_burst}",
            f"StartLimitIntervalSec={spec.start_limit_interval_sec}",
            "",
            "[Service]",
            f"Restart={spec.restart}",
            f"TimeoutStartSec={spec.timeout_start_sec}",
        ]
        for key in sorted(spec.environment):
            lines.append(f"Environment={key}={spec.environment[key]}")
        return "\n".join(lines) + "\n"

    @staticmethod
    def validate_coverage(
        desired_services: Iterable[str],
        plans: Iterable[SupervisionPlan],
        *,
        essential_services: Iterable[str] = (),
    ) -> list[str]:
        planned = {plan.unit: plan for plan in plans}
        errors: list[str] = []
        for service in desired_services:
            if service not in planned:
                errors.append(f"no supervision plan for desired service {service}")
            elif planned[service].desired == "disabled":
                errors.append(f"desired service {service} is planned as disabled")
        for service in essential_services:
            plan = planned.get(service)
            if plan is None:
                errors.append(f"no supervision plan for essential service {service}")
            elif "Restart=no" in plan.drop_in:
                errors.append(f"essential service {service} has Restart=no")
        return errors
