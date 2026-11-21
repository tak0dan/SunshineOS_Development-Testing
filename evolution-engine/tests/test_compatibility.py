"""Tests for source compatibility profiles (TODO_Migration.md §14)."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.core import Confidence, ObservedState, Status, observation  # noqa: E402
from src.target.compatibility import (  # noqa: E402
    classify_source,
    preflight_source,
)


def _obs(component, detected, confidence, status):
    return observation(component, detected, confidence, status, [f"{component}: fixture"])


def _arch(**overrides) -> ObservedState:
    state = ObservedState(
        distribution=overrides.get("distribution", "arch"),
        architecture=overrides.get("architecture", "x86_64"),
        init_system=overrides.get("init_system", "systemd"),
        package_manager=overrides.get("package_manager", "pacman"),
    )
    state.observe(_obs("pacman.query", "pacman-database-ok", "high", "functional"))
    state.observe(_obs("bootloader", "grub", "high", "configured"))
    state.observe(_obs("kernel.running", "6.10.1-arch1-1", "high", "running"))
    state.observe(_obs("kernel.installed", "6.10.1-arch1-1", "high", "installed"))
    if overrides.get("foreign"):
        state.foreign_packages = ["custom-aur-tool"]
    if overrides.get("luks"):
        state.observe(_obs("capability.luks", "luks", "medium", "configured"))
    if overrides.get("partial"):
        state.observe(_obs("sunshine.partial-installation", "partial", "medium", "installed"))
    if overrides.get("broken_db"):
        state.observe(_obs("pacman.query", "broken", "high", "absent"))
    if overrides.get("no_bootloader"):
        state.observations.pop("bootloader", None)
        state.observe(_obs("bootloader", "none", "high", "absent"))
    return state


class CompatibilityTests(unittest.TestCase):
    def test_clean_arch_is_official(self):
        report = classify_source(_arch())
        self.assertEqual(report.profile, "arch-standard")
        self.assertEqual(report.support_level, "official")
        self.assertTrue(report.supported)
        self.assertEqual(report.blockers, [])

    def test_endeavouros_with_arch_lineage_is_conditional(self):
        """T-ENDEAVOUR-COMP-001: derive support from observed os-release lineage."""
        state = _arch(distribution="endeavouros")
        state.observe(_obs("system.os-release", "os-release-parsed", "high", "configured"))
        state.observations["system.os-release"].evidence.append("ID_LIKE=arch")
        report = classify_source(state)
        self.assertTrue(report.supported)
        self.assertEqual(report.profile, "arch-customized")
        self.assertEqual(report.support_level, "conditional")
        self.assertIn("os-release ID_LIKE includes arch", report.evidence)

    def test_endeavouros_without_arch_lineage_is_blocked(self):
        """T-ENDEAVOUR-COMP-002: do not infer lineage from distro name alone."""
        report = classify_source(_arch(distribution="endeavouros"))
        self.assertFalse(report.supported)
        self.assertTrue(any("ID_LIKE=arch" in b for b in report.blockers))

    def test_endeavouros_unconfigured_os_release_evidence_is_blocked(self):
        """T-ENDEAVOUR-COMP-003: stale evidence cannot qualify source lineage."""
        state = _arch(distribution="endeavouros")
        state.observe(_obs("system.os-release", "os-release-parsed", "high", "absent"))
        state.observations["system.os-release"].evidence.append("ID_LIKE=arch")
        report = classify_source(state)
        self.assertFalse(report.supported)
        self.assertTrue(any("lacks corroborating ID_LIKE=arch" in b for b in report.blockers))

    def test_endeavouros_lineage_requires_exact_arch_token(self):
        """T-ENDEAVOUR-COMP-004: similar strings are not Arch lineage."""
        state = _arch(distribution="endeavouros")
        state.observe(_obs("system.os-release", "os-release-parsed", "high", "configured"))
        state.observations["system.os-release"].evidence.append("ID_LIKE=archlinux")
        report = classify_source(state)
        self.assertFalse(report.supported)
        self.assertTrue(any("lacks corroborating ID_LIKE=arch" in b for b in report.blockers))

    def test_garuda_with_arch_lineage_is_conditional(self):
        """T-GARUDA-COMP-001: Garuda lineage requires observed os-release evidence."""
        state = _arch(distribution="garuda")
        state.observe(_obs("system.os-release", "os-release-parsed", "high", "configured"))
        state.observations["system.os-release"].evidence.append("ID_LIKE=arch")
        report = classify_source(state)
        self.assertTrue(report.supported)
        self.assertEqual(report.profile, "arch-customized")
        self.assertEqual(report.support_level, "conditional")
        self.assertIn("os-release ID_LIKE includes arch", report.evidence)

    def test_garuda_without_arch_lineage_is_blocked(self):
        """T-GARUDA-COMP-002: distro branding alone must not qualify lineage."""
        report = classify_source(_arch(distribution="garuda"))
        self.assertFalse(report.supported)
        self.assertTrue(any("garuda source lacks corroborating ID_LIKE=arch" in b for b in report.blockers))

    def test_garuda_stale_arch_lineage_is_blocked(self):
        """T-GARUDA-COMP-003: failed os-release discovery cannot authorize migration."""
        state = _arch(distribution="garuda")
        state.observe(_obs("system.os-release", "os-release-parsed", "high", "absent"))
        state.observations["system.os-release"].evidence.append("ID_LIKE=arch")
        report = classify_source(state)
        self.assertFalse(report.supported)
        self.assertTrue(any("garuda source lacks corroborating ID_LIKE=arch" in b for b in report.blockers))

    def test_garuda_lineage_requires_exact_arch_token(self):
        """T-GARUDA-COMP-004: lookalike ID_LIKE values are not accepted."""
        state = _arch(distribution="garuda")
        state.observe(_obs("system.os-release", "os-release-parsed", "high", "configured"))
        state.observations["system.os-release"].evidence.append("ID_LIKE=archlinux")
        report = classify_source(state)
        self.assertFalse(report.supported)
        self.assertTrue(any("garuda source lacks corroborating ID_LIKE=arch" in b for b in report.blockers))

    def test_garuda_conditional_profile_respects_strict_policy(self):
        """T-GARUDA-COMP-005: strict preflight may reject conditional Garuda."""
        state = _arch(distribution="garuda")
        state.observe(_obs("system.os-release", "os-release-parsed", "high", "configured"))
        state.observations["system.os-release"].evidence.append("ID_LIKE=arch")
        report = preflight_source(state, allow_conditional=False)
        self.assertFalse(report.supported)
        self.assertEqual(report.support_level, "unsupported")
        self.assertTrue(any("conditional source profile" in b for b in report.blockers))

    def test_foreign_packages_make_conditional_not_unsupported(self):
        report = classify_source(_arch(foreign=True))
        self.assertEqual(report.profile, "arch-customized")
        self.assertEqual(report.support_level, "conditional")
        self.assertTrue(report.supported)
        self.assertTrue(any("foreign" in w for w in report.warnings))

    def test_incomplete_package_ownership_inventory_blocks_source(self):
        """T-ENDEAVOUR-PKG-002: uncertain foreign ownership blocks migration."""
        state = _arch(distribution="endeavouros")
        state.observe(_obs("system.os-release", "os-release-parsed", "high", "configured"))
        state.observations["system.os-release"].evidence.append("ID_LIKE=arch")
        state.observe(_obs("packages.ownership-inventory", "package-ownership-inventory", "low", "absent"))
        report = classify_source(state)
        self.assertFalse(report.supported)
        self.assertTrue(any("ownership inventory is incomplete" in b for b in report.blockers))

    def test_luks_and_partial_sunshine_are_conditional(self):
        report = classify_source(_arch(luks=True, partial=True))
        self.assertEqual(report.profile, "arch-customized")
        self.assertTrue(report.supported)
        self.assertGreaterEqual(len(report.warnings), 2)

    def test_installed_sunshine_is_supported(self):
        state = _arch(distribution="sunshineos")
        state.observe(_obs("sunshine.installation", "complete", "high", "configured"))
        report = classify_source(state)
        self.assertEqual(report.profile, "sunshine-installed")
        self.assertTrue(report.supported)

    def test_non_arch_distribution_is_blocked(self):
        report = classify_source(_arch(distribution="debian"))
        self.assertFalse(report.supported)
        self.assertTrue(any("unsupported distribution" in b for b in report.blockers))

    def test_non_systemd_is_blocked(self):
        report = classify_source(_arch(init_system="openrc"))
        self.assertFalse(report.supported)
        self.assertTrue(any("init system" in b for b in report.blockers))

    def test_arch_2015_sysvinit_requires_recovery_bridge(self):
        """T-ARCH2015-SYSV-003: never run the ordinary transformer on SysV."""
        from src.evolution.recovery import (
            BASELINE_ID,
            BRIDGE_ID,
            RECOVERY_BASELINE_ID,
            recovery_path,
        )

        report = classify_source(_arch(init_system="sysvinit"))
        self.assertFalse(report.supported)
        self.assertTrue(any("sysvinit" in blocker for blocker in report.blockers))
        self.assertEqual(
            recovery_path(RECOVERY_BASELINE_ID, "E040"),
            [RECOVERY_BASELINE_ID, BRIDGE_ID, BASELINE_ID, "E040"],
        )

    def test_non_pacman_is_blocked(self):
        report = classify_source(_arch(package_manager="apt"))
        self.assertFalse(report.supported)
        self.assertTrue(any("package manager" in b for b in report.blockers))

    def test_unsupported_architecture_is_blocked(self):
        report = classify_source(_arch(architecture="riscv64"))
        self.assertFalse(report.supported)
        self.assertTrue(any("architecture" in b for b in report.blockers))

    def test_broken_database_is_blocked(self):
        report = classify_source(_arch(broken_db=True))
        self.assertFalse(report.supported)
        self.assertTrue(any("database" in b for b in report.blockers))

    def test_no_bootloader_is_blocked(self):
        report = classify_source(_arch(no_bootloader=True))
        self.assertFalse(report.supported)
        self.assertTrue(any("bootloader" in b for b in report.blockers))

    def test_strict_policy_rejects_conditional_source(self):
        report = preflight_source(_arch(foreign=True), allow_conditional=False)
        self.assertFalse(report.supported)
        self.assertTrue(any("conditional source" in b for b in report.blockers))

    def test_report_is_json_serialisable(self):
        import json
        json.dumps(classify_source(_arch()).to_dict())

    def test_repository_rollback_is_refused(self):
        from dataclasses import replace
        from src.target import load_target
        from src.planner import plan
        state = _arch()
        state.repository_generation = 99
        target = replace(load_target(), repository_generation=7)
        with self.assertRaises(ValueError) as ctx:
            plan(state, target)
        self.assertIn("repository rollback refused", str(ctx.exception))

    def test_same_generation_is_accepted(self):
        from dataclasses import replace
        from src.target import load_target
        from src.planner import plan
        state = _arch()
        state.repository_generation = 7
        target = replace(load_target(), repository_generation=7)
        result = plan(state, target)
        self.assertTrue(result.operations)


if __name__ == "__main__":
    unittest.main()
