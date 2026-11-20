"""Machine-checkable architectural invariants M-01 .. M-10.

These are not aspirations in a document. Each invariant has an identifier, a
check function and a registry; the qualification gate evaluates every invariant
against the shipped architecture and refuses to publish a release that violates
one. Tests call the same functions directly.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Iterable, Mapping

Check = Callable[[Mapping[str, Any]], tuple[bool, str]]


@dataclass(frozen=True)
class Invariant:
    id: str
    summary: str
    check: Check


def _m01(ctx: Mapping[str, Any]) -> tuple[bool, str]:
    ok = ctx.get("target_state_driven", False) and not ctx.get("mandatory_sequential_replay", True)
    return bool(ok), "migration must converge on a resolved target without mandatory release replay"


def _m02(ctx: Mapping[str, Any]) -> tuple[bool, str]:
    ok = (
        ctx.get("ledger_immutable", False)
        and ctx.get("ledger_digest", "")
        and not ctx.get("ledger_mutated", False)
    )
    return bool(ok), "published evolution definitions must be immutable and digest-tracked"


def _m03(ctx: Mapping[str, Any]) -> tuple[bool, str]:
    ok = ctx.get("engine_version", "") and ctx.get("engine_version") != ctx.get("os_evolution", "")
    return bool(ok), "migration engine must be versioned independently of the OS release"


def _m04(ctx: Mapping[str, Any]) -> tuple[bool, str]:
    ok = ctx.get("installation_authoritative", False) and bool(ctx.get("inventory_hash", ""))
    return bool(ok), "the observed installation, not a release number, must drive the plan"


def _m05(ctx: Mapping[str, Any]) -> tuple[bool, str]:
    ok = ctx.get("staging_when_possible", False) or ctx.get("staging_not_applicable", False)
    return bool(ok), "migrations must be staged when storage permits"


def _m06(ctx: Mapping[str, Any]) -> tuple[bool, str]:
    ok = ctx.get("all_operations_recoverable", False)
    return bool(ok), "every operation must declare recovery or a compensating procedure"


def _m07(ctx: Mapping[str, Any]) -> tuple[bool, str]:
    ok = ctx.get("historical_artifacts_archived", False)
    return bool(ok), "historical artifacts must be archived independently of live repositories"


def _m08(ctx: Mapping[str, Any]) -> tuple[bool, str]:
    ok = ctx.get("support_qualified", False) and not ctx.get("support_assumed", True)
    return bool(ok), "support requires a qualified, tested path"


def _m09(ctx: Mapping[str, Any]) -> tuple[bool, str]:
    ok = ctx.get("repeatable", False) and ctx.get("idempotency_policies", False)
    return bool(ok), "discovery/planning/execution must be repeatable with explicit idempotency"


def _m10(ctx: Mapping[str, Any]) -> tuple[bool, str]:
    ok = ctx.get("user_data_separate", False)
    return bool(ok), "user-data preservation must be separate from OS reconstruction"


INVARIANTS: tuple[Invariant, ...] = (
    Invariant("M-01", "Target-state driven migration", _m01),
    Invariant("M-02", "Evolution history is immutable", _m02),
    Invariant("M-03", "Migration intelligence versioned independently", _m03),
    Invariant("M-04", "Actual installation is authoritative", _m04),
    Invariant("M-05", "Migrations staged when possible", _m05),
    Invariant("M-06", "Operations are recoverable", _m06),
    Invariant("M-07", "Historical artifacts archived", _m07),
    Invariant("M-08", "Support is qualified, not assumed", _m08),
    Invariant("M-09", "Migration is repeatable", _m09),
    Invariant("M-10", "User data and OS reconstruction are separate", _m10),
)


@dataclass(frozen=True)
class InvariantReport:
    results: tuple[dict[str, Any], ...]
    passed: bool

    def to_dict(self) -> dict[str, Any]:
        return {"passed": self.passed, "results": list(self.results)}


def check_invariants(ctx: Mapping[str, Any]) -> InvariantReport:
    results: list[dict[str, Any]] = []
    for invariant in INVARIANTS:
        ok, requirement = invariant.check(ctx)
        results.append({
            "id": invariant.id,
            "passed": bool(ok),
            "requirement": requirement,
            "summary": invariant.summary,
        })
    return InvariantReport(tuple(results), all(r["passed"] for r in results))
