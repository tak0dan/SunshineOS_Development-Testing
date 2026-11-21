"""Read-only pacman health assessment for repair planning.

Inspired by the package-integrity and maintenance checks exposed by Arch-based
systems. The probe only observes: missing files and dependency errors become
findings, while orphan candidates are informational and are never removed.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Callable, Sequence

ExecuteArgv = Callable[[Sequence[str]], tuple[int, str, str]]
PACKAGE_NAME = re.compile(r"^[a-zA-Z0-9@._+-]+$")


@dataclass(frozen=True)
class PackageHealthCheck:
    name: str
    status: str  # healthy | degraded | unknown
    command: tuple[str, ...]
    return_code: int | None
    findings: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, object]:
        return {
            "name": self.name,
            "status": self.status,
            "command": list(self.command),
            "return_code": self.return_code,
            "findings": list(self.findings),
        }


@dataclass(frozen=True)
class PackageHealthReport:
    checks: tuple[PackageHealthCheck, ...]

    @property
    def healthy(self) -> bool:
        return all(check.status == "healthy" for check in self.checks)

    def to_dict(self) -> dict[str, object]:
        return {
            "healthy": self.healthy,
            "checks": [check.to_dict() for check in self.checks],
            "policy": "read-only; orphan candidates require explicit operator review",
        }


def _run_check(name: str, argv: tuple[str, ...], execute: ExecuteArgv,
               indicators: tuple[str, ...] = ()) -> PackageHealthCheck:
    try:
        code, stdout, stderr = execute(argv)
    except Exception as exc:
        return PackageHealthCheck(name, "unknown", argv, None,
                                  (f"probe could not run: {exc}",))
    output = "\n".join(part for part in (stdout, stderr) if part).strip()
    if code == 127:
        return PackageHealthCheck(name, "unknown", argv, code,
                                  ("pacman is unavailable in this environment",))
    findings_list: list[str] = []
    for line in output.splitlines():
        lowered = line.lower()
        if name == "installed-file-integrity":
            missing = re.search(r"\b(\d+) missing files?\b", lowered)
            if missing and int(missing.group(1)) > 0:
                findings_list.append(line.strip())
            elif "warning:" in lowered and not missing:
                findings_list.append(line.strip())
        elif any(token in lowered for token in indicators):
            findings_list.append(line.strip())
    findings = tuple(findings_list)
    if code != 0:
        findings = findings + (f"command exited with status {code}",)
        status = "degraded"
    else:
        status = "degraded" if findings else "healthy"
    return PackageHealthCheck(name, status, argv, code, findings)


def assess_package_health(execute: ExecuteArgv) -> PackageHealthReport:
    """Run database, file-integrity and orphan-candidate probes without mutation."""
    database = _run_check(
        "dependency-database", ("pacman", "-Dk"), execute,
        ("error:", "warning:"),
    )
    files = _run_check(
        "installed-file-integrity", ("pacman", "-Qk"), execute,
        ("warning:",),
    )
    orphan_command = ("pacman", "-Qdtq")
    try:
        code, stdout, stderr = execute(orphan_command)
    except Exception as exc:
        orphans = PackageHealthCheck(
            "orphan-candidates", "unknown", orphan_command, None,
            (f"probe could not run: {exc}",),
        )
    else:
        if code == 127:
            orphans = PackageHealthCheck(
                "orphan-candidates", "unknown", orphan_command, code,
                ("pacman is unavailable in this environment",),
            )
        elif code != 0:
            orphans = PackageHealthCheck(
                "orphan-candidates", "unknown", orphan_command, code,
                ((stderr.strip() or f"command exited with status {code}"),),
            )
        else:
            names = tuple(sorted({line.strip() for line in stdout.splitlines() if line.strip()}))
            invalid = tuple(name for name in names if not PACKAGE_NAME.fullmatch(name))
            if invalid:
                orphans = PackageHealthCheck(
                    "orphan-candidates", "unknown", orphan_command, code,
                    ("pacman returned malformed package names",),
                )
            else:
                orphans = PackageHealthCheck(
                    "orphan-candidates", "healthy", orphan_command, code,
                    tuple(f"review candidate: {name}" for name in names),
                )
    return PackageHealthReport((database, files, orphans))
