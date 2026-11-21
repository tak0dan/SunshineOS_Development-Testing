"""Regression coverage for conservative systemd unit inventory assessment."""
from __future__ import annotations

import unittest

from src.evolution.tools.systemd_inventory import (
    assess_unit_inventory,
    parse_unit_file_inventory,
)
from src.evolution.tools.service_supervision import ServiceSpec, ServiceSupervisor


class SystemdUnitInventoryTests(unittest.TestCase):
    def test_T_ARCH2026_SYSTEMD_001_parses_states_and_skips_header(self):
        inventory = parse_unit_file_inventory(
            "sshd.service enabled enabled\nfoo.timer static -\n",
            command_succeeded=True,
        )
        self.assertTrue(inventory.complete)
        self.assertEqual(inventory.units, {"sshd.service": "enabled", "foo.timer": "static"})

    def test_T_ARCH2026_SYSTEMD_002_failed_probe_is_unknown(self):
        inventory = parse_unit_file_inventory("", command_succeeded=False)
        finding, = assess_unit_inventory(inventory, {"sshd.service": "enabled"})
        self.assertEqual((finding.observed, finding.action), ("unknown", "block"))

    def test_T_ARCH2026_SYSTEMD_003_masked_desired_service_blocks(self):
        inventory = parse_unit_file_inventory("sshd.service masked -\n", command_succeeded=True)
        finding, = assess_unit_inventory(inventory, {"sshd.service": "enabled"})
        self.assertEqual(finding.action, "block")

    def test_T_ARCH2026_SYSTEMD_004_malformed_inventory_is_incomplete(self):
        inventory = parse_unit_file_inventory("sshd.service ???\nmalformed\n", command_succeeded=True)
        self.assertFalse(inventory.complete)
        self.assertEqual(len(inventory.errors), 2)
        finding, = assess_unit_inventory(inventory, {"sshd.service": "enabled"})
        self.assertEqual(finding.action, "block")

    def test_T_ARCH2026_SYSTEMD_005_invalid_desired_unit_rejected(self):
        inventory = parse_unit_file_inventory("", command_succeeded=True)
        with self.assertRaises(ValueError):
            assess_unit_inventory(inventory, {"../../bad.service": "enabled"})

    def test_T_ARCH2026_SYSTEMD_006_legacy_unit_types_remain_observable(self):
        inventory = parse_unit_file_inventory(
            "org.example.Legacy.busname static -\n"
            "pre-upgrade.snapshot static -\n",
            command_succeeded=True,
        )
        self.assertTrue(inventory.complete)
        self.assertEqual(
            inventory.units,
            {"org.example.Legacy.busname": "static", "pre-upgrade.snapshot": "static"},
        )

    def test_T_ARCH2026_SYSTEMD_007_duplicate_unit_makes_snapshot_incomplete(self):
        inventory = parse_unit_file_inventory(
            "sshd.service enabled enabled\nsshd.service disabled disabled\n",
            command_succeeded=True,
        )
        self.assertFalse(inventory.complete)
        self.assertTrue(any("duplicate unit sshd.service" in error for error in inventory.errors))
        finding, = assess_unit_inventory(inventory, {"sshd.service": "disabled"})
        self.assertEqual((finding.observed, finding.action), ("unknown", "block"))

    def test_T_ARCH2026_SYSTEMD_008_unknown_state_makes_snapshot_incomplete(self):
        inventory = parse_unit_file_inventory(
            "known.service enabled enabled\nfuture.service newly-added -\n",
            command_succeeded=True,
        )
        self.assertFalse(inventory.complete)
        finding, = assess_unit_inventory(inventory, {"known.service": "enabled"})
        self.assertEqual((finding.observed, finding.action), ("unknown", "block"))

    def test_T_ARCH2026_SYSTEMD_009_enabled_alias_states_are_satisfied(self):
        inventory = parse_unit_file_inventory(
            "one.service enabled enabled\n"
            "two.service enabled-runtime enabled\n"
            "three.service linked linked\n"
            "four.service linked-runtime linked\n"
            "five.service alias -\n",
            command_succeeded=True,
        )
        self.assertTrue(inventory.complete)
        findings = assess_unit_inventory(
            inventory,
            {name: "enabled" for name in inventory.units},
        )
        self.assertEqual({finding.action for finding in findings}, {"satisfied"})

    def test_T_ARCH2026_SYSTEMD_010_masked_runtime_blocks_present(self):
        inventory = parse_unit_file_inventory(
            "critical.service masked-runtime -\n",
            command_succeeded=True,
        )
        finding, = assess_unit_inventory(inventory, {"critical.service": "present"})
        self.assertEqual((finding.observed, finding.action), ("masked-runtime", "block"))

    def test_T_ARCH2026_SYSTEMD_011_absent_desired_state_is_idempotently_satisfied(self):
        inventory = parse_unit_file_inventory("sshd.service enabled enabled\n", command_succeeded=True)
        findings = assess_unit_inventory(
            inventory,
            {"missing.service": "absent", "sshd.service": "absent"},
        )
        self.assertEqual(
            [(finding.observed, finding.action) for finding in findings],
            [("absent", "satisfied"), ("enabled", "review-remove")],
        )

    def test_T_ARCH2026_SYSTEMD_012_invalid_desired_state_rejected(self):
        inventory = parse_unit_file_inventory("sshd.service enabled enabled\n", command_succeeded=True)
        with self.assertRaises(ValueError):
            assess_unit_inventory(inventory, {"sshd.service": "masked"})

    def test_T_ARCH2026_SYSTEMD_013_checked_plan_blocks_masked_unit(self):
        inventory = parse_unit_file_inventory(
            "sunshine-apps.service masked -\n", command_succeeded=True
        )
        with self.assertRaisesRegex(ValueError, "does not authorize.*masked"):
            ServiceSupervisor().plan_checked(
                [ServiceSpec("sunshine-apps.service")], inventory
            )

    def test_T_ARCH2026_SYSTEMD_014_checked_plan_blocks_incomplete_inventory(self):
        inventory = parse_unit_file_inventory("", command_succeeded=False)
        with self.assertRaisesRegex(ValueError, "does not authorize.*unknown"):
            ServiceSupervisor().plan_checked(
                [ServiceSpec("sunshine-apps.service")], inventory
            )

    def test_T_ARCH2026_SYSTEMD_015_checked_plan_requires_package_stage_for_absent_unit(self):
        inventory = parse_unit_file_inventory("sshd.service enabled enabled\n", command_succeeded=True)
        with self.assertRaisesRegex(ValueError, "review-install"):
            ServiceSupervisor().plan_checked(
                [ServiceSpec("sunshine-apps.service")], inventory
            )

    def test_T_ARCH2026_SYSTEMD_017_bad_unit_blocks_checked_plan(self):
        inventory = parse_unit_file_inventory(
            "sunshine-apps.service bad -\n", command_succeeded=True
        )
        finding, = assess_unit_inventory(
            inventory, {"sunshine-apps.service": "enabled"}
        )
        self.assertEqual((finding.observed, finding.action), ("bad", "block"))
        with self.assertRaisesRegex(ValueError, "does not authorize.*bad"):
            ServiceSupervisor().plan_checked(
                [ServiceSpec("sunshine-apps.service")], inventory
            )

    def test_T_ARCH2026_SYSTEMD_016_checked_plan_allows_disabled_existing_unit(self):
        inventory = parse_unit_file_inventory(
            "sunshine-apps.service disabled disabled\n", command_succeeded=True
        )
        plans = ServiceSupervisor().plan_checked(
            [ServiceSpec("sunshine-apps.service")], inventory
        )
        self.assertEqual(plans[0].commands[0], ("systemctl", "enable", "sunshine-apps.service"))


if __name__ == "__main__":
    unittest.main()
