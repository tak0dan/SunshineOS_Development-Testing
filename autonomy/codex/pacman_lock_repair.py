"""Read-only pacman lock assessment inspired by Garuda Toolbox maintenance.

An ownerless lock is only a stale candidate: this module never removes it.
The caller must recheck the process state and create a recovery checkpoint
before offering any separately implemented operator-approved repair.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

PACKAGE_TRANSACTION_NAMES = frozenset({
    "pacman", "yay", "paru", "pamac", "garuda-update", "packagekitd",
})


@dataclass(frozen=True)
class LockAssessment:
    state: str  # missing | active-owner | owner-unknown | stale-candidate
    lock_path: str
    owners: tuple[int, ...] = ()
    detail: str = ""

    @property
    def repair_allowed(self) -> bool:
        """No state here authorizes automatic lock deletion."""
        return False

    def to_dict(self) -> dict[str, object]:
        return {
            "state": self.state,
            "lock_path": self.lock_path,
            "owners": list(self.owners),
            "detail": self.detail,
            "repair_allowed": False,
        }


def assess_pacman_lock(
    lock_path: str | Path = "/var/lib/pacman/db.lck",
    proc_root: str | Path = "/proc",
) -> LockAssessment:
    """Assess a pacman lock without mutation; unreadable process state fails closed."""
    lock = Path(lock_path)
    if not lock.exists():
        return LockAssessment("missing", str(lock), detail="no package database lock exists")

    proc = Path(proc_root)
    try:
        entries = tuple(proc.iterdir())
    except OSError as exc:
        return LockAssessment("owner-unknown", str(lock), detail=f"cannot inspect process table: {exc}")

    owners: list[int] = []
    unreadable = False
    for entry in entries:
        if not entry.name.isdecimal():
            continue
        try:
            comm = (entry / "comm").read_text(encoding="utf-8").strip()
            if comm in PACKAGE_TRANSACTION_NAMES:
                owners.append(int(entry.name))
        except FileNotFoundError:
            # Process exited during inspection; its entry is no longer evidence of ownership.
            continue
        except OSError:
            unreadable = True

    if owners:
        return LockAssessment(
            "active-owner", str(lock), tuple(sorted(owners)),
            "package transaction process present; lock must be preserved",
        )
    if unreadable:
        return LockAssessment(
            "owner-unknown", str(lock),
            detail="one or more process entries were unreadable; do not alter the lock",
        )
    return LockAssessment(
        "stale-candidate", str(lock),
        detail="no known package transaction process found; recheck and require operator review",
    )
