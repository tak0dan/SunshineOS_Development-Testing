"""Fail-closed CachyOS kernel transition policy for migration planning.

The package inventory is observational. This module never invokes pacman and
never removes a package; it reports when a planner needs explicit policy.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class KernelMigrationReview:
    source_kernels: tuple[str, ...]
    retained_kernels: tuple[str, ...]
    blockers: tuple[str, ...]
    decisions: tuple[str, ...]

    @property
    def ready(self) -> bool:
        return not self.blockers


def review_kernel_transition(
    installed_packages: Iterable[str],
    *,
    target_kernels: Iterable[str] = (),
    fallback_kernels: Iterable[str] = (),
    active_kernel_package: str = "",
) -> KernelMigrationReview:
    """Review a kernel package transition without authorizing removals.

    CachyOS kernel variants are treated as provider-specific packages. A
    target must name replacements explicitly, preserve one source kernel or
    name an existing fallback, and must never remove the active kernel before
    a validated target boot. All package identities remain literal strings;
    no name rewriting or presumed equivalence is performed.
    """
    installed = set(installed_packages)
    target_values = tuple(target_kernels)
    fallback_values = tuple(fallback_kernels)
    targets = set(target_values)
    fallbacks = set(fallback_values)
    source = tuple(sorted(p for p in installed if p == "linux" or p.startswith("linux-")))
    cachy = tuple(p for p in source if p.startswith("linux-cachyos"))
    blockers: list[str] = []
    decisions: list[str] = []

    if not source:
        blockers.append("KERNEL_SOURCE_UNKNOWN: no installed kernel package was observed")
    if cachy and not targets:
        blockers.append("CACHY_KERNEL_MAPPING_REQUIRED: CachyOS kernel variants require an explicit target mapping")
    if any(not isinstance(p, str) or not p.strip() for p in (*target_values, *fallback_values)):
        blockers.append("KERNEL_TARGET_INVALID: target kernel identities are invalid")

    surviving = (set(source) & targets) if targets else set(source)
    if not surviving and not (fallbacks & installed):
        blockers.append("KERNEL_FALLBACK_REQUIRED: keep an installed source kernel or identify an installed fallback")
    if active_kernel_package and active_kernel_package not in installed:
        blockers.append("ACTIVE_KERNEL_UNCORROBORATED: active kernel package is absent from inventory")
    elif active_kernel_package and active_kernel_package not in surviving and active_kernel_package not in (fallbacks & installed):
        blockers.append("ACTIVE_KERNEL_RETIREMENT_BLOCKED: active kernel cannot be retired before target boot validation")

    if cachy:
        decisions.append("CachyOS kernel identities are preserved verbatim pending qualified target-provider evidence")
    if source:
        decisions.append("kernel packages are observations; this review does not authorize package removal")
    return KernelMigrationReview(source, tuple(sorted(surviving | (fallbacks & installed))), tuple(blockers), tuple(decisions))
