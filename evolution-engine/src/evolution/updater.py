"""Evolution updater: one implementation for bootstrap and evolution sources.

The milestone chain is a set of *logical gates*. The updater does not replay every
historical release as an execution script: it checkpoints once, runs the declared
pre hooks for the gates being crossed, applies the engine transformation once to
the resolved target, verifies convergence, runs post hooks, then commits. Any
failure runs on-failure hooks and restores the checkpoint.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Mapping

from .baseline import BASELINE_ID
from .hooks import HookOutcome, HookRunner
from .journal_state import MigrationJournal
from .recovery import RECOVERY_BASELINE_ID, recovery_path
from .release import content_digest
from .scheme import Scheme

ApplyFn = Callable[[], tuple[bool, str]]
VerifyFn = Callable[[], tuple[bool, str]]
CheckpointFn = Callable[[], str]
CheckpointVerifyFn = Callable[[str], tuple[bool, str]]
RestoreFn = Callable[[str], tuple[bool, str]]

MAJOR_UPDATE_SCOPE = ("base", "kernel", "packages")
_YEAR = re.compile(r"(?:19|20)\d{2}")
_RELEASE_ALIASES = {
    "b-1": RECOVERY_BASELINE_ID,
    "b-1-2015": RECOVERY_BASELINE_ID,
    "arch-2015": RECOVERY_BASELINE_ID,
    "archlinux-2015": RECOVERY_BASELINE_ID,
    "b0": BASELINE_ID,
    "b0-2026": BASELINE_ID,
    "b0-arch-2026": BASELINE_ID,
    "vanilla-arch": BASELINE_ID,
}


def _canonical_release(value: Any, baseline_epoch: str) -> str:
    text = str(value or "").strip().lower()
    if not text:
        return ""
    if text in _RELEASE_ALIASES:
        return _RELEASE_ALIASES[text]
    if re.fullmatch(r"e\d+", text):
        return str(baseline_epoch or BASELINE_ID).strip().lower()
    return text


def _major_epoch(value: Any, baseline_epoch: str) -> str:
    """Return the OS major epoch without treating evolution indices as majors."""
    canonical = _canonical_release(value, baseline_epoch)
    match = _YEAR.search(canonical)
    return match.group() if match else canonical


@dataclass(frozen=True)
class AutomaticMigrationPlan:
    """Read-only lineage plan for a major release transition.

    An automatic migration is part of every ordinary upgrade: it records what
    convergence must do, never performs it. Mutation stays behind the existing
    explicit apply/trust gates, and no lock is ever deleted by this plan.
    """

    required: bool
    reason: str
    lineage: tuple[str, ...] = ()
    update_scope: tuple[str, ...] = ()
    recovery_inputs: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "required": self.required,
            "reason": self.reason,
            "lineage": list(self.lineage),
            "update_scope": list(self.update_scope),
            "recovery_inputs": self.recovery_inputs,
            "mutation_authorized": False,
            "commands": [],
            "lock_deletion": "never",
        }


def plan_automatic_migration(
    source: Any,
    target: Any,
    *,
    baseline_epoch: str = BASELINE_ID,
    current_state: Mapping[str, Any] | None = None,
) -> AutomaticMigrationPlan:
    """Plan the B-1 -> M -> B0 -> target lineage for a major release jump.

    Same-major upgrades return ``required=False`` with no lineage. Evidence or
    context is recorded, not acted on; the caller's explicit apply gate alone
    may authorize mutation. Broken upgrades reuse the B-1 base plus current
    state merged over the B0 baseline, then continue evolutionary steps.
    """
    baseline = str(baseline_epoch or BASELINE_ID)
    source_epoch = _major_epoch(source, baseline)
    target_epoch = _major_epoch(target, baseline)
    if not source_epoch or not target_epoch or source_epoch == target_epoch:
        return AutomaticMigrationPlan(
            False,
            "same major release; ordinary package and convergence steps apply",
        )

    canonical_source = _canonical_release(source, baseline)
    old_base = canonical_source == RECOVERY_BASELINE_ID
    bridge_path = recovery_path(
        RECOVERY_BASELINE_ID if old_base else BASELINE_ID, str(target),
    )
    current = dict(current_state or {})
    recovery_inputs = {
        "base": RECOVERY_BASELINE_ID,
        "current_state": current,
        "merge_with": BASELINE_ID,
        "merge_policy": "current-state-over-B0-baseline; preserve user data",
        "lineage": list(bridge_path),
        "continue_with": "evolutionary upgrade steps after reconstructed baseline validates",
        "mutation_authorized": False,
        "commands": [],
    }
    return AutomaticMigrationPlan(
        True,
        f"major release transition {source_epoch} -> {target_epoch}",
        tuple(bridge_path),
        MAJOR_UPDATE_SCOPE,
        recovery_inputs,
    )


@dataclass
class UpgradeReport:
    source: str
    target: str
    chain: tuple[str, ...]
    ok: bool
    dry_run: bool = False
    steps: list[dict[str, Any]] = field(default_factory=list)
    hook_outcomes: list[dict[str, Any]] = field(default_factory=list)
    error: str = ""
    rolled_back: bool = False
    journal_id: str = ""
    migration_required: bool = False
    migration_lineage: tuple[str, ...] = ()
    migration_plan: dict[str, Any] = field(default_factory=dict)
    recovery_inputs: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "source": self.source,
            "target": self.target,
            "chain": list(self.chain),
            "ok": self.ok,
            "dry_run": self.dry_run,
            "steps": self.steps,
            "hook_outcomes": self.hook_outcomes,
            "error": self.error,
            "rolled_back": self.rolled_back,
            "journal_id": self.journal_id,
            "migration_required": self.migration_required,
            "migration_lineage": list(self.migration_lineage),
            "migration_plan": self.migration_plan,
            "recovery_inputs": self.recovery_inputs,
        }


class EvolutionUpdater:
    """Orchestrate a verified, recoverable milestone upgrade."""

    def __init__(
        self,
        scheme: Scheme,
        state_root: str | Path,
        *,
        hook_runner: HookRunner | None = None,
        apply_fn: ApplyFn | None = None,
        verify_fn: VerifyFn | None = None,
        checkpoint_fn: CheckpointFn | None = None,
        checkpoint_verify_fn: CheckpointVerifyFn | None = None,
        restore_fn: RestoreFn | None = None,
    ) -> None:
        self.scheme = scheme
        self.state_root = Path(state_root)
        self.state_root.mkdir(parents=True, exist_ok=True)
        self.hooks = hook_runner or HookRunner(self.state_root)
        self.apply_fn = apply_fn
        self.verify_fn = verify_fn
        self.checkpoint_fn = checkpoint_fn
        self.checkpoint_verify_fn = checkpoint_verify_fn
        self.restore_fn = restore_fn

    def chain(self, source: str, target: str | None = None) -> list[str]:
        milestones = self.scheme.registry.chain(
            source, target if target is not None else self.scheme.registry.current
        )
        return [str(m.version) for m in milestones]

    def _release_label(self, value: Any) -> str:
        """Resolve a milestone to its release label, keeping explicit anchors."""
        text = str(value or "").strip()
        if (_YEAR.search(text) or re.fullmatch(r"e\d+", text, re.IGNORECASE)
                or text.lower() in _RELEASE_ALIASES):
            return text
        try:
            version = self.scheme.registry.resolve_version(text)
        except ValueError:
            return text
        milestone = self.scheme.registry.get(version)
        if milestone is not None and milestone.target_release:
            return milestone.target_release
        return str(version)

    def _check_execution_preconditions(self, milestones: list[Any]) -> None:
        """Validate non-mutating requirements before a checkpoint is taken."""

        if self.apply_fn is None:
            raise RuntimeError("no transformation apply function is configured")
        if self.verify_fn is None:
            raise RuntimeError("no verification function is configured")
        for milestone in milestones:
            for hook in milestone.hooks:
                if hook.command:
                    errors = self.hooks.validate_command(hook.command)
                    if errors and hook.required:
                        raise RuntimeError(
                            f"{milestone.version}/{hook.id}: invalid required hook: "
                            + "; ".join(errors)
                        )
                elif not hook.adapter:
                    raise RuntimeError(f"{milestone.version}/{hook.id}: hook has no command or adapter")

    @staticmethod
    def _attach_migration(report: UpgradeReport, migration: AutomaticMigrationPlan) -> None:
        report.migration_required = migration.required
        report.migration_lineage = migration.lineage
        report.migration_plan = migration.to_dict()
        report.recovery_inputs = migration.recovery_inputs
        if migration.required:
            report.steps.append({
                "phase": "AutomaticMigration",
                "detail": migration.reason,
                "lineage": list(migration.lineage),
                "update_scope": list(migration.update_scope),
                "mutation_authorized": False,
            })

    def upgrade(
        self, source: str, target: str | None = None, *, dry_run: bool = False
    ) -> UpgradeReport:
        target_version = target if target is not None else self.scheme.registry.current
        migration = plan_automatic_migration(
            self._release_label(source),
            self._release_label(target_version),
            baseline_epoch=self.scheme.baseline_epoch,
            current_state={"source": str(source), "target": str(target_version)},
        )
        try:
            milestones = self.scheme.registry.chain(source, target_version)
        except ValueError as exc:
            report = UpgradeReport(source, str(target_version), (), False, error=str(exc))
            report.steps.append({"phase": "Discover", "detail": f"source={source}"})
            self._attach_migration(report, migration)
            return report

        chain = [str(m.version) for m in milestones]
        # Full digest: a truncated identifier becomes a collision risk across
        # decades of quarterly releases and repeated recovery attempts.
        journal_id = content_digest({
            "source": str(source), "target": str(target_version), "chain": chain,
        })
        journal = MigrationJournal(
            migration_id=journal_id,
            versions=self.scheme.versions,
            target_manifest_hash=content_digest(self.scheme.to_dict()),
        )
        report = UpgradeReport(
            source=str(source), target=str(target_version), chain=tuple(chain),
            ok=True, dry_run=dry_run, journal_id=journal_id,
        )
        report.steps.append({"phase": "Discover", "detail": f"source={source}"})
        migration = plan_automatic_migration(
            self._release_label(source),
            self._release_label(target_version),
            baseline_epoch=self.scheme.baseline_epoch,
            current_state={
                "source": str(source), "target": str(target_version),
                "chain": chain, "journal_id": journal_id,
            },
        )
        self._attach_migration(report, migration)
        if dry_run:
            try:
                self._check_execution_preconditions(milestones)
            except Exception as exc:
                report.ok = False
                report.error = str(exc)
                return report
            report.steps.append({
                "phase": "PlanReview",
                "detail": "dry run: preconditions validated; no hooks or operations executed",
            })
            return report

        # A journal records what happened; it cannot restore system state.
        # Never begin a mutating migration unless the caller has provided both
        # sides of the recovery contract.  This check is intentionally after
        # dry-run planning so offline plan review remains possible.
        if self.checkpoint_fn is None or self.restore_fn is None:
            report.ok = False
            report.error = (
                "recoverable execution requires both checkpoint and restore backends"
            )
            return report

        checkpoint_ref = ""
        try:
            journal.transition("Planning", "chain resolved")
            journal.transition("PlanReview", "plan reviewed")
            self._check_execution_preconditions(milestones)
            report.steps.append({"phase": "Preconditions", "detail": "validated"})
            journal.transition("Prepared", "checkpoint requested")
            checkpoint_ref = str(self.checkpoint_fn() or "").strip()
            if not checkpoint_ref:
                raise RuntimeError("checkpoint backend returned an empty reference")
            journal.add_checkpoint(checkpoint_ref)
            journal.transition("Executing", "apply transformation")

            for milestone in milestones:
                outcomes: list[HookOutcome] = self.hooks.run(
                    milestone.hooks, "pre_upgrade"
                )
                report.hook_outcomes.extend(o.to_dict() for o in outcomes)
                failed = [o for o in outcomes if o.phase == "pre_upgrade" and not o.ok]
                if failed:
                    raise RuntimeError(
                        f"pre_upgrade hook failed for milestone {milestone.version}: "
                        + failed[0].output
                    )
                report.steps.append({
                    "phase": "pre_upgrade", "milestone": str(milestone.version),
                    "hooks": [o.hook_id for o in outcomes],
                })

            applied, apply_detail = self.apply_fn()
            if not applied:
                raise RuntimeError(f"transformation failed: {apply_detail}")
            report.steps.append({"phase": "Build", "detail": apply_detail})

            verified, verify_detail = self.verify_fn()
            if not verified:
                raise RuntimeError(f"post-migration verification failed: {verify_detail}")
            journal.add_validation("post-migration-verify", True, verify_detail)
            report.steps.append({"phase": "ValidateStaged", "detail": verify_detail})

            for milestone in milestones:
                outcomes = self.hooks.run(milestone.hooks, "post_milestone")
                report.hook_outcomes.extend(o.to_dict() for o in outcomes)
                failed = [o for o in outcomes if o.phase == "post_milestone" and not o.ok]
                if failed:
                    raise RuntimeError(
                        f"post_milestone hook failed for {milestone.version}: "
                        + failed[0].output
                    )
                report.steps.append({
                    "phase": "post_milestone", "milestone": str(milestone.version),
                    "hooks": [o.hook_id for o in outcomes],
                })

            journal.transition("Validation", "verification passed")
            journal.transition("CommitReady", "all gates passed")
            journal.transition("Committed", "upgrade committed")
            report.steps.append({"phase": "Commit", "detail": "committed"})
            journal.save(self.state_root / f"journal-{journal_id}.json")
            return report
        except Exception as exc:
            report.ok = False
            report.error = str(exc)
            if migration.required:
                report.steps.append({
                    "phase": "RecoveryPlan",
                    "detail": f"rebuild from {RECOVERY_BASELINE_ID} plus current state "
                              f"merged with {BASELINE_ID}",
                    "lineage": list(migration.lineage),
                    "mutation_authorized": False,
                })
            try:
                journal.transition("Failed", str(exc))
            except ValueError:
                pass
            for milestone in reversed(milestones):
                outcomes = self.hooks.run(milestone.hooks, "on_failure")
                report.hook_outcomes.extend(o.to_dict() for o in outcomes)
            if checkpoint_ref and self.restore_fn is not None:
                restore_detail = ""
                checkpoint_ok = True
                if self.checkpoint_verify_fn is not None:
                    checkpoint_ok, checkpoint_detail = self.checkpoint_verify_fn(checkpoint_ref)
                    journal.add_validation(
                        "checkpoint-integrity", checkpoint_ok, checkpoint_detail
                    )
                    if not checkpoint_ok:
                        report.error += (
                            "; rollback refused: checkpoint integrity failed: "
                            + checkpoint_detail
                        )
                if checkpoint_ok:
                    restored, restore_detail = self.restore_fn(checkpoint_ref)
                    if restored:
                        report.rolled_back = True
                        journal.add_checkpoint(restore_detail, "restored")
                        try:
                            journal.transition("RolledBack", restore_detail)
                        except ValueError:
                            pass
                    else:
                        journal.add_validation("rollback", False, restore_detail)
                        report.error += f"; rollback failed: {restore_detail}"
            journal.save(self.state_root / f"journal-{journal_id}.json")
            return report
