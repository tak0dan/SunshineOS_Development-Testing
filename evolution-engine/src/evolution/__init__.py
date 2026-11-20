"""Evolutionary milestones: versioned, verifiable convergence steps.

Milestone 0 is current vanilla Arch Linux. Milestone 0.9 is the current
SunshineOS release (which does not yet ship the migration mechanism). Every
later Arch-based SunshineOS release is the next milestone.

The registry describes an ordered chain of declarative steps. The updater
applies every missing step, verifying after each one and rolling back on
failure, so an upgrade from any historical state converges on the current
target regardless of how much time has passed.
"""
from .milestones import (
    HookSpec,
    Milestone,
    MilestoneRegistry,
    MilestoneVersion,
)
from .scheme import DEFAULT_SCHEME_PATH, load_scheme
from .repository import MilestoneRepository
from .hooks import HookOutcome, HookPhase, run_hooks
from .updater import EvolutionUpdater, UpgradeReport
from .tools import (
    ChannelDecision,
    ChannelPolicy,
    Differential,
    Seal,
    SealReport,
    ServiceSpec,
    ServiceSupervisor,
    ServiceSupervisionPlan,
    SnapshotManager,
    SnapshotRecord,
    SpaceReport,
    TransactionLog,
    TransactionSession,
    build_seal,
    guard_update,
    sign_seal,
    verify_seal,
    verify_seal_signature,
)

__all__ = [
    "HookSpec",
    "HookOutcome",
    "HookPhase",
    "Milestone",
    "MilestoneRegistry",
    "MilestoneVersion",
    "MilestoneRepository",
    "EvolutionUpdater",
    "UpgradeReport",
    "DEFAULT_SCHEME_PATH",
    "load_scheme",
    "run_hooks",
    "ChannelDecision",
    "ChannelPolicy",
    "Differential",
    "Seal",
    "SealReport",
    "ServiceSpec",
    "ServiceSupervisor",
    "ServiceSupervisionPlan",
    "SnapshotManager",
    "SnapshotRecord",
    "SpaceReport",
    "TransactionLog",
    "TransactionSession",
    "build_seal",
    "guard_update",
    "sign_seal",
    "verify_seal",
    "verify_seal_signature",
]
