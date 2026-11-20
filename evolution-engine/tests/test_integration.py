"""End-to-end integration tests: discover → resolve → plan → execute → validate.

These tests exercise the CLI's helper functions across fixtures with a single
ObservedState class identity, and prove the two source paths converge on the
same target with one engine.
"""
from __future__ import annotations

import sys
import unittest
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.core import ObservedState  # noqa: E402
from src.discovery import discover  # noqa: E402
from src.target import load_target, resolve_target  # noqa: E402
from src.planner import plan as build_plan  # noqa: E402
from src.executor import execute_plan  # noqa: E402
from src.validation import validate_system  # noqa: E402

BASE = Path(__file__).resolve().parent.parent


class FakeExec:
    """Minimal injected executor that records commands and reports success."""

    def __init__(self):
        self.commands: list[str] = []

    def __call__(self, cmd: str) -> tuple[int, str, str]:
        self.commands.append(cmd)
        c = cmd.strip()
        if c.startswith("pacman -Q "):
            return 0, "1.0-1", ""
        if c.startswith("pacman -Qqdt"):
            return 0, "", ""
        if c.startswith("pacman -Qqm"):
            return 0, "", ""
        if c.startswith("systemctl is-enabled"):
            return 0, "enabled", ""
        if c.startswith("systemctl is-active"):
            return 0, "active", ""
        if c == "pacman --version":
            return 0, "Pacman v7.1.0", ""
        if c.startswith("uname"):
            return 0, "x86_64" if " -m" in c else "6.10.1-arch1-1", ""
        return 0, "", ""


def _fixture_pipeline(name: str, packages: dict[str, str] | None = None):
    root = BASE / "fixtures" / name
    fx = FakeExec()
    state = discover(root=str(root), execute=fx)
    target = load_target()
    target, decisions = resolve_target(state, target)
    plan = build_plan(state, target, decisions=decisions)
    return state, target, plan, decisions, fx


class IntegrationTests(unittest.TestCase):
    def test_single_class_identity(self):
        state = discover(root=str(BASE / "fixtures" / "clean-arch"), execute=FakeExec())
        self.assertIsInstance(state, ObservedState)

    def test_clean_arch_pipeline_introduces_every_required_component(self):
        state, target, plan, decisions, fx = _fixture_pipeline("clean-arch", {"base": "1"})
        self.assertGreater(len(plan.operations), 0)
        registered = [o for o in plan.operations if o.type.value == "RegisterComponent"]
        self.assertGreaterEqual(len(registered), len(target.required_components()),
                                "every required component must be introduced on pure Arch")
        self.assertTrue(any(o.type.value == "CreateCheckpoint" for o in plan.operations))

    def test_old_sunshine_and_clean_arch_share_one_pipeline(self):
        old = _fixture_pipeline("old-sunshine")
        new = _fixture_pipeline("clean-arch")
        types_old = Counter(o.type.value for o in old[2].operations)
        types_new = Counter(o.type.value for o in new[2].operations)
        self.assertEqual(
            set(types_old), set(types_new),
            "both source paths must use the same operation vocabulary",
        )

    def test_decisions_are_focused_not_a_questionnaire(self):
        for fixture in ("clean-arch", "old-sunshine", "arch-plasma"):
            _, _, _, decisions, _ = _fixture_pipeline(fixture)
            user_questions = [d for d in decisions if d.get("requires_user_input")]
            self.assertLessEqual(len(user_questions), 3,
                                 f"{fixture} asked {len(user_questions)} questions")

    def test_dry_run_execution_changes_nothing(self):
        import tempfile
        from src.core import Plan, Operation, OpType
        # Use a minimal non-destructive plan: a plan built from sparse fixture
        # observations correctly refuses destructive ops, which is a feature.
        op = Operation(id="dry-register", type=OpType.REGISTER_COMPONENT,
                       component="core",
                       params={"component_id": "core", "schema": 3})
        plan = Plan(id="dry-plan", source={}, target={}, operations=[op])
        root = Path(tempfile.mkdtemp())
        result = execute_plan(plan, root, FakeExec(), dry_run=True)
        self.assertEqual(result.status, "dry_run", result.errors)
        self.assertFalse(result.changed)
        self.assertEqual(list(root.iterdir()), [], "dry-run must not create state files")

    def test_validation_fails_closed_for_unknown_capability(self):
        from src.validation import validate_capability
        r = validate_capability("totally-made-up-capability", "/", lambda c: (0, "", ""))
        self.assertFalse(r.passed)

    # ---- Regressions found during live VM dry-run ------------------------ #

    def test_boot_entry_loader_is_an_efi_path_with_valid_label(self):
        """software_version must never be used as a boot loader path."""
        import re
        for fixture in ("clean-arch", "old-sunshine", "arch-plasma"):
            _, _, plan, _, _ = _fixture_pipeline(fixture)
            entries = [o for o in plan.operations if o.type.value == "InstallBootEntry"]
            self.assertTrue(entries, f"{fixture} emitted no boot entry")
            for entry in entries:
                self.assertTrue(entry.params["loader"].startswith("/"),
                                f"{fixture}: loader={entry.params['loader']!r}")
                self.assertRegex(entry.params["label"], r"^[A-Za-z0-9][A-Za-z0-9 _.-]{0,63}$")

    def test_generic_arch_capabilities_do_not_count_as_registration(self):
        """GRUB/kernel capabilities must not skip component introduction."""
        from src.core import ComponentSpec, Lifecycle
        from src.planner.strategies import _detect_presence
        from src.discovery import discover
        state = discover(str(BASE / "fixtures" / "clean-arch"), execute=FakeExec())
        spec = ComponentSpec(id="boot_integration", schema=2, required=True,
                             software_version="2026.1", lifecycle=Lifecycle.EVOLVE,
                             provides=["boot-entry-management", "bootloader-configuration"],
                             requires=[])
        self.assertFalse(_detect_presence(state, spec),
                         "generic Arch boot capability was mistaken for a Sunshine component")

    def test_full_clean_arch_plan_dry_runs_end_to_end(self):
        """The whole fixture pipeline must survive a dry-run apply."""
        import tempfile
        state, target, plan, decisions, fx = _fixture_pipeline("clean-arch")
        result = execute_plan(plan, Path(tempfile.mkdtemp()), fx, dry_run=True)
        self.assertEqual(result.status, "dry_run", result.errors)
        self.assertEqual(len(result.completed_ops), len(plan.operations))
        self.assertFalse(result.changed)

    def test_discovery_survives_empty_command_output(self):
        """A command exiting 0 with no stdout must not crash discovery."""
        class EmptyExec(FakeExec):
            def __call__(self, cmd):
                return 0, "", ""
        discover(str(BASE / "fixtures" / "clean-arch"), execute=EmptyExec())

    def test_network_choice_not_inferred_from_unrelated_service(self):
        """services.systemd evidence must not become a 'systemd' network choice."""
        from src.target.resolver import _observed_choice
        from src.discovery import discover
        state = discover(str(BASE / "fixtures" / "clean-arch"), execute=FakeExec())
        choice = _observed_choice(state, "network")
        self.assertIsNotNone(choice)
        self.assertEqual(choice[0], "networkmanager")

    def test_executor_group_promotion_preserves_dag_order(self):
        """A RegisterComponent depending on InstallBootEntry must run after it."""
        import tempfile
        _, _, plan, _, fx = _fixture_pipeline("clean-arch")
        result = execute_plan(plan, Path(tempfile.mkdtemp()), fx, dry_run=True)
        self.assertEqual(result.status, "dry_run", result.errors)
        positions = {oid: i for i, oid in enumerate(result.completed_ops)}
        for op in plan.operations:
            for dep in op.requires:
                self.assertIn(dep, positions, f"{op.id} ran without dependency {dep}")
                self.assertLess(positions[dep], positions[op.id],
                                f"{op.id} ran before its dependency {dep}")


if __name__ == "__main__":
    unittest.main()
