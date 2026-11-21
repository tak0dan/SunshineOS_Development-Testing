"""Native Arch Linux rescue assessment.

This rewrites the read-only intent of Windows DISM/SFC servicing checks and WinRE
recovery checks as Arch-native evidence: pacman database/file verification,
systemd unit verification, boot artifacts, transaction locks, snapshots and
reboot state. It consumes already-captured observations and never executes a
repair, removes a lock, rewrites a unit, or updates a boot entry.

Attribution: the lock-state vocabulary is adapted from the read-only
``autonomy/codex/pacman_lock_repair.py`` pull; boot-artifact evidence follows
``src/evolution/tools/boot_artifact_repair.py``. Research provenance is pinned in
``fixtures/research/native-arch-rescue-wave1.json``.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

PACKAGE_TRANSACTION_NAMES = frozenset({
    "pacman", "yay", "paru", "pamac", "garuda-update", "packagekitd",
})

REQUIRED_PROBES: dict[str, tuple[str, ...]] = {
    "pacman-db-check": ("pacman", "-Dk"),
    "pacman-file-check": ("pacman", "-Qk"),
    "systemd-unit-verify": ("systemd-analyze", "verify", "default.target"),
}

WINDOWS_COUNTERPARTS: dict[str, str] = {
    "pacman-database": "DISM /Online /Cleanup-Image /CheckHealth",
    "pacman-owned-files": "DISM /ScanHealth; SFC /verifyonly",
    "systemd-units": "WinRE startup repair",
    "boot-artifacts": "WinRE boot repair",
    "transaction-lock": "Windows servicing transaction state",
    "snapshot-readiness": "System Restore",
    "reboot-state": "pending servicing reboot",
}

_MISSING_FILES = re.compile(r"(\d+)\s+missing files", re.IGNORECASE)
_SYSTEMD_PROBLEM = ("error", "failed", "not found", "invalid", "warning")


@dataclass(frozen=True)
class LockAssessment:
    state: str  # missing | active-owner | owner-unknown | stale-candidate
    lock_path: str
    owners: tuple[int, ...] = ()
    detail: str = ""

    @property
    def repair_allowed(self) -> bool:
        """No observed lock state authorizes automatic deletion."""
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
            # A process that exited during inspection is no longer lock evidence.
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


@dataclass(frozen=True)
class ArchRescueProbe:
    name: str
    command: tuple[str, ...]
    return_code: int | None
    output: str = ""
    timed_out: bool = False


@dataclass(frozen=True)
class ArchRescueFinding:
    check: str
    status: str  # healthy | degraded | unknown | blocked
    detail: str
    native_command: tuple[str, ...] = ()
    windows_counterpart: str = ""

    def to_dict(self) -> dict[str, object]:
        return {
            "check": self.check,
            "status": self.status,
            "detail": self.detail,
            "native_command": list(self.native_command),
            "windows_counterpart": self.windows_counterpart,
        }


@dataclass(frozen=True)
class ArchRescueReport:
    findings: tuple[ArchRescueFinding, ...]

    @property
    def healthy(self) -> bool:
        return bool(self.findings) and all(item.status == "healthy" for item in self.findings)

    @property
    def degraded(self) -> bool:
        return any(item.status == "degraded" for item in self.findings)

    @property
    def blocked(self) -> bool:
        return any(item.status in {"unknown", "blocked"} for item in self.findings)

    @property
    def safe_to_mutate(self) -> bool:
        return self.healthy and not self.blocked and not self.degraded

    def to_dict(self) -> dict[str, object]:
        return {
            "healthy": self.healthy,
            "degraded": self.degraded,
            "blocked": self.blocked,
            "safe_to_mutate": self.safe_to_mutate,
            "findings": [item.to_dict() for item in self.findings],
        }


def _is_file(path: Path) -> bool:
    try:
        return path.is_file()
    except OSError:
        return False


def observe_arch_rescue_root(root: str | Path) -> dict[str, Any]:
    """Collect read-only boot artifacts from a target root; unknown on I/O errors."""
    base = Path(root)
    boot = base / "boot"
    try:
        kernel = any((boot.glob("vmlinuz-*"))) or _is_file(boot / "vmlinuz-linux")
        initramfs = any(boot.glob("initramfs-*.img"))
        loader_config = _is_file(boot / "loader" / "loader.conf")
        grub_config = _is_file(boot / "grub" / "grub.cfg")
        syslinux_config = _is_file(boot / "syslinux" / "syslinux.cfg")
        entries = any((boot / "loader" / "entries").glob("*.conf"))
    except OSError:
        return {
            "kernel_present": None, "initramfs_present": None,
            "bootloader_config_present": None, "boot_entries_present": None,
        }
    return {
        "kernel_present": bool(kernel),
        "initramfs_present": bool(initramfs),
        "bootloader_config_present": bool(loader_config or grub_config or syslinux_config),
        "boot_entries_present": bool(entries or grub_config or syslinux_config),
    }


def _finding(check: str, status: str, detail: str,
             command: tuple[str, ...] = ()) -> ArchRescueFinding:
    return ArchRescueFinding(
        check, status, detail, command, WINDOWS_COUNTERPARTS.get(check, ""),
    )


def _classify_probe(check: str, probe: ArchRescueProbe | None) -> ArchRescueFinding:
    command = REQUIRED_PROBES[check_to_key(check)]
    if probe is None:
        return _finding(check, "unknown", "required probe is missing", command)
    if probe.name != check_to_key(check):
        return _finding(check, "blocked", "probe identity does not match its evidence key", probe.command)
    if tuple(probe.command) != command:
        return _finding(check, "blocked", "probe command is not the required read-only check", probe.command)
    if probe.timed_out:
        return _finding(check, "blocked", "probe timed out; result is unusable", command)
    if probe.return_code is None or probe.return_code == 127:
        return _finding(check, "unknown", "probe result is unavailable", command)
    if probe.return_code != 0:
        return _finding(check, "degraded", f"probe exited with status {probe.return_code}", command)
    text = probe.output.casefold()
    if check == "pacman-database":
        if "checking dependencies" in text and not any(
            token in text for token in ("error", "warning", "failed", "unresolved", "missing")
        ):
            return _finding(check, "healthy", "pacman reported clean dependency state", command)
        return _finding(check, "unknown", "pacman output does not contain a recognized clean result", command)
    if check == "pacman-owned-files":
        counts = [int(value) for value in _MISSING_FILES.findall(text)]
        if counts and all(value == 0 for value in counts):
            return _finding(check, "healthy", "all checked packages reported zero missing files", command)
        if counts or "no such file" in text or "missing file" in text:
            return _finding(check, "degraded", "pacman reported missing owned files", command)
        return _finding(check, "unknown", "pacman output does not contain a recognized clean result", command)
    if check == "systemd-units":
        output = probe.output.strip()
        if not output:
            return _finding(check, "healthy", "systemd-analyze produced no unit verification problems", command)
        if any(token in text for token in _SYSTEMD_PROBLEM):
            return _finding(check, "degraded", "systemd-analyze reported a unit problem", command)
        return _finding(check, "unknown", "systemd-analyze output is not a recognized clean result", command)
    return _finding(check, "unknown", "unsupported native check", command)


def check_to_key(check: str) -> str:
    return {
        "pacman-database": "pacman-db-check",
        "pacman-owned-files": "pacman-file-check",
        "systemd-units": "systemd-unit-verify",
    }[check]


def _observation_finding(check: str, value: Any, command: tuple[str, ...] = ()) -> ArchRescueFinding:
    if check == "boot-artifacts":
        if not isinstance(value, Mapping):
            return _finding(check, "unknown", "boot artifact observations are missing", command)
        keys = ("kernel_present", "initramfs_present", "bootloader_config_present")
        states = [value.get(key) for key in keys]
        if any(state is None for state in states):
            return _finding(check, "unknown", "one or more boot artifact observations are unavailable", command)
        missing = [key for key, state in zip(keys, states) if state is not True]
        if missing:
            return _finding(check, "degraded", f"missing boot artifacts: {', '.join(missing)}", command)
        return _finding(check, "healthy", "kernel, initramfs and bootloader configuration were observed", command)
    if check == "transaction-lock":
        state = value
        if state == "missing":
            return _finding(check, "healthy", "no package database lock was observed", command)
        if state == "stale-candidate":
            return _finding(check, "degraded", "lock has no observed owner; recheck before any repair", command)
        if state == "active-owner":
            return _finding(check, "blocked", "a package transaction owner is present; preserve the lock", command)
        return _finding(check, "unknown", f"lock state is not trusted: {state!r}", command)
    if check == "snapshot-readiness":
        if value is True:
            return _finding(check, "healthy", "a rollback snapshot was observed", command)
        if value is False:
            return _finding(check, "degraded", "no rollback snapshot was observed", command)
        return _finding(check, "unknown", "snapshot readiness was not observed", command)
    if check == "reboot-state":
        if value is True:
            return _finding(check, "blocked", "a pending reboot leaves servicing state unsettled", command)
        if value is False:
            return _finding(check, "healthy", "no pending reboot was observed", command)
        return _finding(check, "unknown", "pending-reboot state was not observed", command)
    return _finding(check, "unknown", "unsupported observation", command)


def assess_arch_rescue(
    probes: Mapping[str, ArchRescueProbe], *, observed: Mapping[str, Any]
) -> ArchRescueReport:
    """Classify captured Arch-native rescue evidence without making changes."""
    findings = [
        _classify_probe("pacman-database", probes.get("pacman-db-check")),
        _classify_probe("pacman-owned-files", probes.get("pacman-file-check")),
        _classify_probe("systemd-units", probes.get("systemd-unit-verify")),
        _observation_finding("boot-artifacts", observed.get("boot-artifacts", observed)),
        _observation_finding("transaction-lock", observed.get("lock_state")),
        _observation_finding("snapshot-readiness", observed.get("snapshot_available")),
        _observation_finding("reboot-state", observed.get("pending_reboot")),
    ]
    return ArchRescueReport(tuple(findings))
