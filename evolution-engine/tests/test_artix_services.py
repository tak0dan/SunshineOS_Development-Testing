"""Regression tests for Artix OpenRC/runit service plan qualification."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.evolution.tools.artix_services import plan_artix_service  # noqa: E402


class ArtixServicePlanTests(unittest.TestCase):
    def test_ARTIX_SVC_001_openrc_enable_orders_runlevel_before_start(self) -> None:
        plan = plan_artix_service("openrc", "dbus", "enabled",
                                  observed_service_path="/etc/init.d/dbus")
        self.assertEqual(plan.commands, (
            ("rc-update", "add", "dbus", "default"),
            ("rc-service", "dbus", "start"),
        ))
        present = plan_artix_service("openrc", "dbus", "present",
                                     observed_service_path="/etc/init.d/dbus")
        self.assertEqual(present.commands, ())

    def test_ARTIX_SVC_002_runit_requires_observed_activation_path(self) -> None:
        with self.assertRaisesRegex(ValueError, "observed active service path"):
            plan_artix_service("runit", "sshd", "enabled",
                               observed_service_path="/etc/runit/sv/sshd")
        plan = plan_artix_service("runit", "sshd", "enabled",
                                  observed_service_path="/etc/runit/sv/sshd",
                                  active_service_path="/run/runit/service/sshd")
        self.assertEqual(plan.commands, (("sv", "up", "/run/runit/service/sshd"),))

    def test_ARTIX_SVC_003_unqualified_or_injected_paths_fail_closed(self) -> None:
        for kwargs in (
            {"init_system": "unknown", "service": "dbus", "path": "/etc/init.d/dbus"},
            {"init_system": "openrc", "service": "dbus;id", "path": "/etc/init.d/dbus;id"},
            {"init_system": "runit", "service": "sshd", "path": "/tmp/sshd"},
        ):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                plan_artix_service(kwargs["init_system"], kwargs["service"], "enabled",
                                   observed_service_path=kwargs["path"],
                                   active_service_path="/run/runit/service/sshd")

    def test_ARTIX_SVC_004_package_owned_runit_definition_is_not_removed(self) -> None:
        plan = plan_artix_service("runit", "sshd", "absent",
                                  observed_service_path="/etc/runit/sv/sshd")
        self.assertEqual(plan.commands, ())
        self.assertIn("package-owned", plan.rationale)

    def test_ARTIX_SVC_005_openrc_disable_stops_before_runlevel_removal(self) -> None:
        plan = plan_artix_service("openrc", "dbus", "disabled",
                                  observed_service_path="/etc/init.d/dbus")
        self.assertEqual(plan.commands, (
            ("rc-service", "dbus", "stop"),
            ("rc-update", "del", "dbus", "default"),
        ))

    def test_ARTIX_SVC_006_runit_disable_targets_only_observed_active_service(self) -> None:
        with self.assertRaisesRegex(ValueError, "observed active service path"):
            plan_artix_service("runit", "sshd", "disabled",
                               observed_service_path="/etc/runit/sv/sshd")
        plan = plan_artix_service("runit", "sshd", "disabled",
                                  observed_service_path="/etc/runit/sv/sshd",
                                  active_service_path="/run/runit/service/sshd")
        self.assertEqual(plan.commands, (("sv", "down", "/run/runit/service/sshd"),))

    def test_ARTIX_SVC_007_commands_are_argv_and_unobserved_active_paths_reject(self) -> None:
        with self.assertRaisesRegex(ValueError, "outside the supported service tree"):
            plan_artix_service("runit", "sshd", "enabled",
                               observed_service_path="/etc/runit/sv/sshd",
                               active_service_path="/tmp/sshd")
        plan = plan_artix_service("openrc", "dbus", "enabled",
                                  observed_service_path="/etc/init.d/dbus")
        self.assertTrue(all(isinstance(command, tuple) for command in plan.commands))
        self.assertTrue(all(";" not in argument for command in plan.commands for argument in command))

    def test_ARTIX_SVC_008_runit_runtime_plan_marks_persistent_activation_unresolved(self) -> None:
        running = plan_artix_service(
            "runit", "sshd", "enabled",
            observed_service_path="/etc/runit/sv/sshd",
            active_service_path="/run/runit/service/sshd",
        )
        stopped = plan_artix_service(
            "runit", "sshd", "disabled",
            observed_service_path="/etc/runit/sv/sshd",
            active_service_path="/run/runit/service/sshd",
        )
        definition = plan_artix_service(
            "runit", "sshd", "present",
            observed_service_path="/etc/runit/sv/sshd",
        )
        self.assertTrue(running.activation_transition_required)
        self.assertTrue(stopped.activation_transition_required)
        self.assertFalse(definition.activation_transition_required)

    def test_ARTIX_SVC_009_plan_serialization_preserves_unresolved_transition(self) -> None:
        plan = plan_artix_service(
            "runit", "sshd", "enabled",
            observed_service_path="/etc/runit/sv/sshd",
            active_service_path="/run/runit/service/sshd",
        )
        serialized = plan.to_dict()
        self.assertEqual(serialized["commands"], [["sv", "up", "/run/runit/service/sshd"]])
        self.assertTrue(serialized["activation_transition_required"])

    def test_ARTIX_SVC_010_openrc_rejects_runit_activation_evidence(self) -> None:
        with self.assertRaisesRegex(ValueError, "do not accept a runit active service path"):
            plan_artix_service(
                "openrc", "dbus", "enabled",
                observed_service_path="/etc/init.d/dbus",
                active_service_path="/run/runit/service/dbus",
            )


if __name__ == "__main__":
    unittest.main()
