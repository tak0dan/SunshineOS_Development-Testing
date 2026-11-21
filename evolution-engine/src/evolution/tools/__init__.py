"""SunshineOS adaptations of stability mechanisms from audited systems.

These are rewritten for SunshineOS's constraints: stdlib-only, no shell=True,
no implicit network access, injected executors, and full journaling. Each module
records which audited system inspired it and why the decision applies here.
"""
from .sealed_state import (
    Seal,
    SealReport,
    build_seal,
    sign_seal,
    verify_seal,
    verify_seal_signature,
)
from .snapshots import SnapshotManager, SnapshotRecord, SpaceReport
from .channels import ChannelDecision, ChannelPolicy, guard_update
from .transaction_log import Differential, TransactionLog, TransactionSession
from .service_supervision import (
    ServiceSpec,
    ServiceSupervisor,
    SupervisionPlan as ServiceSupervisionPlan,
)
from .artix_services import ArtixServicePlan, plan_artix_service
from .package_health import PackageHealthCheck, PackageHealthReport, assess_package_health

__all__ = [
    "Seal",
    "SealReport",
    "build_seal",
    "verify_seal",
    "sign_seal",
    "verify_seal_signature",
    "SnapshotManager",
    "SnapshotRecord",
    "SpaceReport",
    "ChannelPolicy",
    "ChannelDecision",
    "guard_update",
    "TransactionLog",
    "TransactionSession",
    "Differential",
    "ServiceSpec",
    "ServiceSupervisor",
    "ArtixServicePlan",
    "plan_artix_service",
    "ServiceSupervisionPlan",
    "PackageHealthCheck",
    "PackageHealthReport",
    "assess_package_health",
]
