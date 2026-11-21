"""Fail-closed service plans for Artix OpenRC and runit inventories.

These plans describe argv only; they never execute commands.  Callers must
provide an observed init system and service path so a marker file cannot turn
an unrelated installation into an assumed Artix service layout.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

SERVICE_NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.@+-]*$")
OPENRC_ROOT = "/etc/init.d"
RUNIT_ROOT = "/etc/runit/sv"
RUNIT_ACTIVE_ROOT = "/run/runit/service"


@dataclass(frozen=True)
class ArtixServicePlan:
    init_system: str
    service: str
    desired: str
    commands: tuple[tuple[str, ...], ...]
    rationale: str
    activation_transition_required: bool = False

    def to_dict(self) -> dict[str, object]:
        """Return a stable, JSON-compatible representation of this plan."""
        return {
            "init_system": self.init_system,
            "service": self.service,
            "desired": self.desired,
            "commands": [list(command) for command in self.commands],
            "rationale": self.rationale,
            "activation_transition_required": self.activation_transition_required,
        }


def plan_artix_service(
    init_system: str,
    service: str,
    desired: str,
    *,
    observed_service_path: str,
    active_service_path: str | None = None,
) -> ArtixServicePlan:
    """Render a conservative OpenRC/runit plan from exact observed paths.

    ``desired`` is one of enabled/disabled/present/absent. ``present`` and
    ``absent`` concern installed service definitions and are deliberately not
    mutated by this runtime-only planner.
    """
    init = init_system.lower()
    if init not in ("openrc", "runit"):
        raise ValueError(f"unsupported Artix init system {init_system!r}")
    if not SERVICE_NAME.fullmatch(service):
        raise ValueError(f"invalid service name {service!r}")
    if desired not in ("enabled", "disabled", "present", "absent"):
        raise ValueError(f"invalid desired state {desired!r}")

    if init == "openrc":
        if active_service_path is not None:
            raise ValueError("OpenRC plans do not accept a runit active service path")
        expected = f"{OPENRC_ROOT}/{service}"
        if observed_service_path != expected:
            raise ValueError("OpenRC service path is not the exact observed init.d entry")
        if desired == "enabled":
            commands = (("rc-update", "add", service, "default"), ("rc-service", service, "start"))
        elif desired == "disabled":
            commands = (("rc-service", service, "stop"), ("rc-update", "del", service, "default"))
        else:
            commands = ()
        return ArtixServicePlan(
            init,
            service,
            desired,
            commands,
            "OpenRC runlevel membership and runtime state are separate operations",
        )

    expected = f"{RUNIT_ROOT}/{service}"
    if observed_service_path != expected:
        raise ValueError("runit service path is not the exact observed service definition")
    if active_service_path not in (None, f"{RUNIT_ACTIVE_ROOT}/{service}"):
        raise ValueError("runit active path is outside the supported service tree")
    if desired in ("present", "absent"):
        commands = ()
        rationale = "runit service definition installation is package-owned"
    elif desired == "enabled":
        if active_service_path is None:
            raise ValueError("runit enablement requires an observed active service path")
        commands = (("sv", "up", active_service_path),)
        rationale = "operate on the observed runsv service path; enablement link is inventory-owned"
    else:
        if active_service_path is None:
            raise ValueError("runit disablement requires an observed active service path")
        commands = (("sv", "down", active_service_path),)
        rationale = "stop the observed runsv service; do not remove its activation link implicitly"
    return ArtixServicePlan(
        init,
        service,
        desired,
        commands,
        rationale,
        # This planner deliberately controls only runtime state. The runit
        # activation link is an independent persistent policy that must be
        # inventoried and changed by a qualified, recoverable adapter.
        activation_transition_required=desired in ("enabled", "disabled"),
    )
