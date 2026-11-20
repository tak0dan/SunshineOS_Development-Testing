"""Evolution updater: one implementation for bootstrap and evolution sources.

The milestone chain is a set of *logical gates*. The updater does not replay every
historical release as an execution script: it checkpoints once, runs the declared
pre hooks for the gates being crossed, applies the engine transformation once to
the resolved target, verifies convergence, runs post hooks, then commits. Any
failure runs on-failure hooks and restores the checkpoint.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

from .hooks import HookOutcome, HookRunner
from .journal_state import MigrationJournal
from .release import content_digest
from .scheme import Scheme

ApplyFn = Callable[[], tuple[bool, str]]
VerifyFn = Callable[[], tuple[bool, str]]
CheckpointFn = Callable[[], str]
CheckpointVerifyFn = Callable[[str], tuple[bool, str]]
RestoreFn = Callable[[str], tuple[bool, str]]


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

    def upgrade(
        self, source: str, target: str | None = None, *, dry_run: bool = False
    ) -> UpgradeReport:
        target_version = target if target is not None else self.scheme.registry.current
        try:
            milestones = self.scheme.registry.chain(source, target_version)
        except ValueError as exc:
            return UpgradeReport(source, str(target_version), (), False, error=str(exc))

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

        checkpoint_ref = ""
        try:
            journal.transition("Planning", "chain resolved")
            journal.transition("PlanReview", "plan reviewed")
            self._check_execution_preconditions(milestones)
            report.steps.append({"phase": "Preconditions", "detail": "validated"})
            journal.transition("Prepared", "checkpoint requested")
            if self.checkpoint_fn is not None:
                checkpoint_ref = self.checkpoint_fn()
                journal.add_checkpoint(checkpoint_ref)
            else:
                journal.add_checkpoint("journal-only", "checkpoint")
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
