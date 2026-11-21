#!/usr/bin/env python3
"""SunshineOS live maintenance toolkit.

Commands: health, sanity, update, upgrade, migrate, repair, rescue, report.

Design rules:
* read-only by default; every mutating path needs an explicit --apply
* fail closed on missing trust, missing snapshots, or contradictory evidence
* every mutation is journaled and, where possible, preceded by a snapshot
* no command invents results: unprobed state is reported as unknown
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Callable, Iterable

Runner = Callable[[list[str], int], dict[str, Any]]
STATUS_ORDER = {"pass": 0, "warn": 1, "fail": 2, "unknown": 3}
PACKAGE_NAME = re.compile(r"^[a-zA-Z0-9@._+-]+$")
ARCH_RESCUE_PROBE_COMMANDS = {
    "pacman-db-check": ("pacman", "-Dk"),
    "pacman-file-check": ("pacman", "-Qk"),
    "systemd-unit-verify": ("systemd-analyze", "verify", "default.target"),
}
ARCH_RESCUE_TIMEOUTS = {
    "pacman-db-check": 300,
    "pacman-file-check": 600,
    "systemd-unit-verify": 120,
}
REBOOT_STATE_VALUES = {"unknown": None, "settled": False, "pending": True}


def utc() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def stamp() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def state_dir() -> Path:
    return Path(os.environ.get("SUNSHINE_STATE_DIR", "/var/lib/sunshine"))


def log_dir() -> Path:
    return Path(os.environ.get("SUNSHINE_LOG_DIR", "/var/log/sunshine"))


def engine_dir() -> Path:
    return Path(os.environ.get("SUNSHINE_ENGINE_DIR", "/opt/sunshine/evolution-engine"))


def capture(argv: list[str], timeout: int = 60, cwd: Path | None = None) -> dict[str, Any]:
    """Run a command without a shell and return a structured, never-fabricated result."""
    try:
        proc = subprocess.run(
            list(argv), cwd=str(cwd) if cwd else None, capture_output=True,
            text=True, errors="replace", timeout=timeout,
        )
        return {
            "argv": list(argv), "rc": proc.returncode,
            "stdout": proc.stdout, "stderr": proc.stderr, "timed_out": False,
        }
    except subprocess.TimeoutExpired as exc:
        return {
            "argv": list(argv), "rc": 124, "stdout": exc.stdout or "",
            "stderr": (exc.stderr or "") + f"\ncommand timed out after {timeout}s",
            "timed_out": True,
        }
    except OSError as exc:
        return {
            "argv": list(argv), "rc": 127, "stdout": "",
            "stderr": f"command could not run: {exc}", "timed_out": False,
        }


def run(argv: list[str], runner: Runner | None = None, timeout: int = 60,
        cwd: Path | None = None) -> dict[str, Any]:
    if runner is not None:
        result = runner(list(argv), timeout)
        if not isinstance(result, dict):
            raise TypeError("injected runner must return a dict")
        result.setdefault("argv", list(argv))
        result.setdefault("rc", 0)
        result.setdefault("stdout", "")
        result.setdefault("stderr", "")
        result.setdefault("timed_out", False)
        return result
    return capture(argv, timeout=timeout, cwd=cwd)


def out(result: dict[str, Any]) -> str:
    return str(result.get("stdout", "")).strip()


def evidence(name: str, status: str, detail: str, remedy: str = "") -> dict[str, str]:
    if status not in STATUS_ORDER:
        status = "unknown"
    return {"name": name, "status": status, "detail": str(detail), "remedy": remedy}


def worst(items: Iterable[dict[str, str] | str]) -> str:
    states = [item.get("status", "unknown") if isinstance(item, dict) else str(item) for item in items]
    if not states:
        return "unknown"
    return max(states, key=lambda value: STATUS_ORDER.get(value, 3))


def journal(entry: dict[str, Any]) -> str | None:
    """Append a mutation or decision record. Returns the path, or None on failure."""
    path = log_dir() / "journal.jsonl"
    record = {"generated": utc(), **entry}
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, sort_keys=True) + "\n")
        return str(path)
    except OSError:
        return None


def write_report(command: str, data: dict[str, Any], out_path: str | None = None) -> str | None:
    path = Path(out_path) if out_path else log_dir() / "reports" / f"{command}-{stamp()}.json"
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return str(path)
    except OSError:
        return None


def require_root(allow_test: bool = False) -> None:
    if os.geteuid() == 0:
        return
    if allow_test and os.environ.get("SUNSHINE_ALLOW_UNPRIVILEGED_TEST") == "1":
        return
    raise PermissionError("mutating commands require root (or an explicit test override)")


def parse_os_release(root: Path) -> dict[str, str]:
    path = root / "etc" / "os-release"
    if not path.is_file():
        return {}
    values: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if "=" not in line or line.lstrip().startswith("#"):
            continue
        key, _, value = line.partition("=")
        values[key.strip()] = value.strip().strip('"')
    return values


def root_mount(root: Path, runner: Runner | None = None) -> dict[str, str]:
    result = run(["findmnt", "-no", "TARGET,SOURCE,FSTYPE,OPTIONS", "/"], runner)
    text = out(result)
    parts = text.split(maxsplit=3)
    if not parts:
        return {"target": "", "source": "", "fstype": "", "options": "", "probed": "no"}
    return {
        "target": parts[0], "source": parts[1],
        "fstype": parts[2] if len(parts) > 2 else "",
        "options": parts[3] if len(parts) > 3 else "",
        "probed": "yes",
    }


def time_sync(runner: Runner | None = None) -> dict[str, Any]:
    if shutil.which("timedatectl") is None:
        return {"available": False, "synchronized": None, "output": "timedatectl unavailable"}
    result = run(["timedatectl", "show", "-p", "NTPSynchronized", "--value"], runner)
    value = out(result).lower()
    return {
        "available": True,
        "synchronized": True if value == "yes" else False if value in {"no", "unknown"} else None,
        "output": out(result) or result.get("stderr", "").strip(),
    }


def ensure_engine_import() -> None:
    """Make the engine's ``src.*`` package importable from the staged engine dir."""
    root = str(engine_dir())
    if root not in sys.path:
        sys.path.insert(0, root)


def engine_health(runner: Runner | None = None) -> dict[str, Any]:
    script = engine_dir() / "src" / "engine.py"
    if not script.is_file():
        return {"available": False, "rc": 127, "report": None,
                "stderr": f"engine entrypoint not found: {script}"}
    result = run([sys.executable or "python3", str(script), "--health"],
                 runner, timeout=180, cwd=engine_dir())
    report = None
    try:
        report = json.loads(out(result))
    except (ValueError, TypeError):
        pass
    return {
        "available": True, "rc": result["rc"], "report": report,
        "stdout": result.get("stdout", "")[:4000], "stderr": result.get("stderr", "")[:2000],
    }


def gpu_busy(root: Path) -> list[dict[str, str]]:
    found: list[dict[str, str]] = []
    base = root / "sys" / "class" / "drm"
    if not base.is_dir():
        return found
    for path in sorted(base.glob("card*/device/gpu_busy_percent")):
        try:
            value = path.read_text(encoding="utf-8").strip()
        except OSError:
            continue
        found.append({"device": path.parts[-3], "busy_percent": value})
    return found


def health(root: Path, runner: Runner | None = None, deep: bool = False) -> dict[str, Any]:
    evidence_list: list[dict[str, str]] = []
    osrel = parse_os_release(root)
    uname = run(["uname", "-a"], runner)
    mount = root_mount(root, runner)
    sync = time_sync(runner)

    try:
        usage = shutil.disk_usage(str(root))
        disk = {"total": usage.total, "used": usage.used, "free": usage.free,
                "percent_free": round(100.0 * usage.free / usage.total, 2) if usage.total else 0}
        if usage.free < 1_000_000_000:
            evidence_list.append(evidence("disk-space", "fail", f"free={usage.free} bytes",
                                          "free space before any package or migration work"))
        elif usage.free < 3_000_000_000:
            evidence_list.append(evidence("disk-space", "warn", f"free={usage.free} bytes",
                                          "more free space is recommended for staged updates"))
        else:
            evidence_list.append(evidence("disk-space", "pass", f"free={usage.free} bytes"))
    except OSError as exc:
        disk = {"error": str(exc)}
        evidence_list.append(evidence("disk-space", "unknown", str(exc)))

    meminfo: dict[str, str] = {}
    mem_path = root / "proc" / "meminfo"
    if mem_path.is_file():
        for line in mem_path.read_text(encoding="utf-8", errors="replace").splitlines():
            if ":" in line:
                key, _, value = line.partition(":")
                meminfo[key.strip()] = value.strip()
    load = ""
    load_path = root / "proc" / "loadavg"
    if load_path.is_file():
        load = load_path.read_text(encoding="utf-8").split()[0]

    pacman_result = run(["pacman", "-Q"], runner, timeout=120)
    installed = 0 if pacman_result["rc"] != 0 else len(
        [line for line in out(pacman_result).splitlines() if line.strip()]
    )
    if pacman_result["rc"] == 0:
        evidence_list.append(evidence("pacman-database", "pass", f"installed={installed}"))
    else:
        evidence_list.append(evidence("pacman-database", "warn",
                                      (pacman_result.get("stderr") or "pacman -Q failed").strip()[:300],
                                      "verify the package database on the target root"))

    pkg_health = engine_health(runner) if deep else {
        "available": None, "rc": None, "report": None, "skipped": "use --deep for package integrity"
    }
    if deep and pkg_health.get("available"):
        report = pkg_health.get("report") or {}
        healthy = report.get("healthy")
        if healthy is True:
            evidence_list.append(evidence("package-integrity", "pass", "engine health report is healthy"))
        elif healthy is False:
            findings: list[str] = []
            for check in report.get("checks", []):
                findings.extend(check.get("findings", []))
            evidence_list.append(evidence("package-integrity", "warn",
                                          "; ".join(findings[:5]) or "engine reported unhealthy",
                                          "review with 'sunshine-live repair' before mutating"))
        else:
            evidence_list.append(evidence("package-integrity", "unknown",
                                          "engine health output was not a usable JSON report"))

    if sync.get("synchronized") is True:
        evidence_list.append(evidence("clock", "pass", "NTP reports synchronized"))
    elif sync.get("synchronized") is False:
        evidence_list.append(evidence("clock", "warn", "NTP reports not synchronized",
                                      "enable time sync before signed or networked operations"))
    else:
        evidence_list.append(evidence("clock", "unknown", str(sync.get("output") or "not available")))

    snapshots = snapshot_inventory(root, runner)
    if snapshots.get("available"):
        evidence_list.append(evidence("snapshots", "pass" if snapshots.get("count") else "warn",
                                      f"snapper snapshots={snapshots.get('count', 0)}",
                                      "a pre-existing snapshot improves rollback safety"))
    else:
        evidence_list.append(evidence("snapshots", "warn", snapshots.get("reason", "none detected"),
                                      "configure snapper or a btrfs snapshot directory"))

    facts = {
        "generated": utc(), "root": str(root), "os_release": osrel,
        "kernel": out(uname), "mount": mount, "disk": disk,
        "memory": {"mem_total": meminfo.get("MemTotal", ""), "mem_available": meminfo.get("MemAvailable", "")},
        "load1": load, "gpu": gpu_busy(root), "installed_packages": installed,
        "clock": sync, "snapshots": snapshots, "package_health": pkg_health,
    }
    return {"command": "health", "status": worst(evidence_list),
            "facts": facts, "evidence": evidence_list}


def snapshot_inventory(root: Path, runner: Runner | None = None) -> dict[str, Any]:
    if shutil.which("snapper") is None:
        return {"available": False, "count": 0, "reason": "snapper is not installed"}
    result = run(["snapper", "-c", "root", "list", "-t", "single", "--columns", "number"], runner)
    if result["rc"] != 0:
        return {"available": False, "count": 0,
                "reason": (result.get("stderr") or "snapper list failed").strip()[:300]}
    lines = [line for line in out(result).splitlines() if line.strip().isdigit()]
    return {"available": True, "count": len(lines)}


def sanity(root: Path, runner: Runner | None = None, *,
           require_snapshot: bool = False, require_time: bool = False,
           expected_os: str = "", trust: dict[str, str] | None = None,
           require_trust: bool = False) -> dict[str, Any]:
    result_evidence: list[dict[str, str]] = []
    mount = root_mount(root, runner)
    if mount.get("probed") != "yes":
        result_evidence.append(evidence("root-mount", "unknown", "findmnt did not return root mount data"))
    elif "ro" in mount.get("options", "").split(","):
        result_evidence.append(evidence("root-mount", "fail", "root is mounted read-only",
                                        "remount read-write or operate from the live environment"))
    else:
        result_evidence.append(evidence("root-mount", "pass", f"fstype={mount.get('fstype')}"))

    try:
        usage = shutil.disk_usage(str(root))
        if usage.free >= 3_000_000_000:
            result_evidence.append(evidence("free-space", "pass", f"free={usage.free}"))
        elif usage.free >= 1_000_000_000:
            result_evidence.append(evidence("free-space", "warn", f"free={usage.free}"))
        else:
            result_evidence.append(evidence("free-space", "fail", f"free={usage.free}",
                                            "free at least 1 GiB before applying changes"))
    except OSError as exc:
        result_evidence.append(evidence("free-space", "unknown", str(exc)))

    boot = root / "boot"
    if boot.is_dir():
        result_evidence.append(evidence("boot", "pass", f"{boot} exists"))
    else:
        result_evidence.append(evidence("boot", "fail", f"{boot} is missing",
                                        "mount or create the boot partition before changing the bootloader"))

    if shutil.which("pacman") is None:
        result_evidence.append(evidence("pacman", "fail", "pacman not found on PATH"))
    else:
        result_evidence.append(evidence("pacman", "pass", "pacman is available"))

    lock = root / "var" / "lib" / "pacman" / "db.lck"
    if lock.exists():
        holder = ""
        try:
            holder = lock.read_text(encoding="utf-8", errors="replace").splitlines()[0].strip()
        except (OSError, IndexError):
            pass
        alive = False
        if holder.isdigit():
            try:
                os.kill(int(holder), 0)
                alive = True
            except OSError:
                alive = False
        if alive:
            result_evidence.append(evidence("pacman-lock", "fail", f"held by live PID {holder}",
                                            "wait for the running pacman process"))
        else:
            result_evidence.append(evidence("pacman-lock", "warn",
                                            f"stale-looking lock: {lock} (holder={holder or 'unknown'})",
                                            "inspect, then use 'repair --fix-lock' with --apply"))
    else:
        result_evidence.append(evidence("pacman-lock", "pass", "no database lock"))

    pgrep = run(["pgrep", "-x", "pacman"], runner)
    if pgrep["rc"] == 0:
        result_evidence.append(evidence("running-transaction", "fail", "pacman is running",
                                        "do not start a second package transaction"))
    elif pgrep["rc"] == 1:
        result_evidence.append(evidence("running-transaction", "pass", "no pacman process"))
    else:
        result_evidence.append(evidence("running-transaction", "unknown",
                                        (pgrep.get("stderr") or "pgrep failed").strip()[:200]))

    sync = time_sync(runner)
    if sync.get("synchronized") is True:
        result_evidence.append(evidence("clock", "pass", "NTP reports synchronized"))
    elif require_time:
        result_evidence.append(evidence("clock", "fail", str(sync.get("output") or "not synchronized"),
                                        "signed/networked work requires a synchronized clock"))
    else:
        result_evidence.append(evidence("clock", "warn", str(sync.get("output") or "not synchronized"),
                                        "enable time sync for signed or networked operations"))

    snapshots = snapshot_inventory(root, runner)
    if snapshots.get("available") and snapshots.get("count"):
        result_evidence.append(evidence("snapshot-capability", "pass",
                                        f"snapshots={snapshots['count']}"))
    elif require_snapshot:
        result_evidence.append(evidence("snapshot-capability", "fail",
                                        snapshots.get("reason", "no snapshot capability"),
                                        "configure snapper/btrfs or pass --allow-no-snapshot explicitly"))
    else:
        result_evidence.append(evidence("snapshot-capability", "warn",
                                        snapshots.get("reason", "no snapshot capability")))

    osrel = parse_os_release(root)
    identity = osrel.get("ID", "")
    id_like = osrel.get("ID_LIKE", "")
    if expected_os:
        if identity == expected_os or expected_os in id_like.split():
            result_evidence.append(evidence("os-identity", "pass", f"ID={identity} ID_LIKE={id_like}"))
        else:
            result_evidence.append(evidence("os-identity", "fail",
                                            f"expected {expected_os!r}, got ID={identity!r}",
                                            "mount the correct root or choose the matching source profile"))

    if require_trust or (trust and any(trust.values())):
        trust = trust or {}
        for label, key in (("trust-index", "index"), ("trust-policy", "policy"),
                           ("trust-keyring", "keyring")):
            value = trust.get(key, "")
            if not value:
                result_evidence.append(evidence(label, "fail", "not supplied",
                                                "signed Stage A inputs are mandatory for apply"))
            elif not Path(value).is_file():
                result_evidence.append(evidence(label, "fail", f"missing file: {value}"))
            else:
                result_evidence.append(evidence(label, "pass", value))

    return {"command": "sanity", "generated": utc(), "root": str(root),
            "status": worst(result_evidence), "evidence": result_evidence,
            "os_release": osrel, "mount": mount, "snapshots": snapshots}


def snapshot_create(label: str, root: Path, runner: Runner | None = None) -> dict[str, Any]:
    if shutil.which("snapper") is not None:
        result = run(["snapper", "-c", "root", "create", "-t", "single", "-d", label], runner)
        if result["rc"] == 0:
            numbers = re.findall(r"\b(\d+)\b", out(result))
            return {"ok": True, "type": "snapper", "id": numbers[-1] if numbers else None,
                    "output": out(result), "argv": result["argv"]}
        return {"ok": False, "type": "snapper", "error": (result.get("stderr") or out(result)).strip()[:400]}

    mount = root_mount(root, runner)
    if mount.get("fstype") == "btrfs":
        directory = Path(os.environ.get("SUNSHINE_SNAPSHOT_DIR", str(root / ".sunshine-snapshots")))
        target = directory / f"{label}-{stamp()}"
        result = run(["btrfs", "subvolume", "snapshot", "-r", str(root), str(target)], runner)
        if result["rc"] == 0:
            return {"ok": True, "type": "btrfs", "id": str(target),
                    "output": out(result), "argv": result["argv"]}
        return {"ok": False, "type": "btrfs", "error": (result.get("stderr") or out(result)).strip()[:400]}

    return {"ok": False, "type": "none", "error": "neither snapper nor a btrfs root snapshot path is available"}


def trust_args(args: argparse.Namespace) -> dict[str, str]:
    return {
        "index": getattr(args, "trust_index", "") or "",
        "policy": getattr(args, "trust_policy", "") or "",
        "keyring": getattr(args, "trust_keyring", "") or "",
        "report": getattr(args, "trust_report", "") or "",
        "receipt": getattr(args, "trust_receipt", "") or "",
        "adapter_dir": getattr(args, "adapter_dir", "") or "",
        "adapter_artifact_root": getattr(args, "adapter_artifact_root", "") or "",
    }


def engine_argv(args: argparse.Namespace, mode: str) -> tuple[list[str], Path]:
    directory = Path(getattr(args, "engine_dir", "")) if getattr(args, "engine_dir", "") else engine_dir()
    script = directory / "src" / "engine.py"
    argv = [sys.executable or "python3", str(script),
            "--state-root", getattr(args, "state_root", "") or str(state_dir())]
    if getattr(args, "fixture", ""):
        argv += ["--fixture", args.fixture]
    else:
        argv += ["--root", getattr(args, "root", "/") or "/"]
    argv += [f"--{mode}"]
    trust = trust_args(args)
    mapping = (
        ("--trust-index", "index"), ("--trust-policy", "policy"),
        ("--trust-keyring", "keyring"), ("--trust-report", "report"),
        ("--trust-receipt", "receipt"), ("--adapter-dir", "adapter_dir"),
        ("--adapter-artifact-root", "adapter_artifact_root"),
    )
    for flag, key in mapping:
        if trust.get(key):
            argv += [flag, trust[key]]
    for decision in getattr(args, "decide", []) or []:
        argv += ["--decide", decision]
    return argv, directory


def run_engine(args: argparse.Namespace, mode: str, runner: Runner | None = None) -> dict[str, Any]:
    argv, directory = engine_argv(args, mode)
    script = Path(argv[1])
    if not script.is_file():
        return {"ok": False, "command": mode, "argv": shlex.join(argv), "rc": 127,
                "stdout": "", "stderr": f"engine entrypoint missing: {script}"}
    result = run(argv, runner, timeout=600, cwd=directory)
    return {"ok": result["rc"] == 0, "command": mode, "argv": shlex.join(argv),
            "rc": result["rc"], "stdout": result.get("stdout", "")[:20000],
            "stderr": result.get("stderr", "")[:10000], "timed_out": result.get("timed_out", False)}


def guarded_apply(args: argparse.Namespace, runner: Runner | None, *, expected_os: str = "") -> tuple[dict[str, Any], dict[str, Any] | None, dict[str, Any]]:
    """Common root/sanity/snapshot gate for every mutating command."""
    root = Path(getattr(args, "root", "/") or "/")
    try:
        require_root(True)
    except PermissionError as exc:
        check = {"command": "sanity", "generated": utc(), "status": "fail",
                 "evidence": [evidence("authorization", "fail", str(exc), "run as root with --apply")]}
        return check, None, {"ok": False, "reason": str(exc)}
    check = sanity(root, runner, require_snapshot=not args.allow_no_snapshot,
                   require_time=True, expected_os=expected_os, trust=trust_args(args),
                   require_trust=getattr(args, "command_name", "") in {"upgrade", "migrate"})
    if check["status"] == "fail":
        return check, None, {"ok": False, "reason": "sanity checks failed; no mutation attempted"}
    snap = snapshot_create(f"sunshine-{getattr(args, 'command_name', 'apply')}", root, runner)
    if not snap["ok"] and not args.allow_no_snapshot:
        return check, snap, {"ok": False, "reason": "snapshot gate failed; no mutation attempted"}
    return check, snap, {"ok": True}


def cmd_update(args: argparse.Namespace, runner: Runner | None = None) -> dict[str, Any]:
    root = Path(args.root or "/")
    data: dict[str, Any] = {"command": "update", "generated": utc(), "root": str(root),
                            "apply": bool(args.apply)}
    if not args.apply:
        check = run(["pacman", "-Qu"], runner, timeout=180)
        data.update({"status": "preview", "upgrade_list": out(check),
                     "rc": check["rc"], "stdout": check.get("stdout", "")[:20000],
                     "stderr": check.get("stderr", "")[:4000],
                     "remedy": "pass --apply to execute after sanity and snapshot gates"})
        return data
    args.command_name = "update"
    check, snap, gate = guarded_apply(args, runner)
    data.update({"sanity": check, "snapshot": snap, "gate": gate})
    if not gate["ok"]:
        data["status"] = "blocked"
        return data
    action = run(["pacman", "-Syu", "--noconfirm", "--needed"], runner, timeout=1800)
    post = health(root, runner, deep=False)
    data.update({"status": "pass" if action["rc"] == 0 else "fail", "action": action,
                 "post_health_status": post["status"]})
    journal({"command": "update", "apply": True, "snapshot": snap, "action": action,
             "status": data["status"]})
    return data


def cmd_upgrade(args: argparse.Namespace, runner: Runner | None = None) -> dict[str, Any]:
    root = Path(args.root or "/")
    data: dict[str, Any] = {"command": "upgrade", "generated": utc(), "root": str(root),
                            "apply": bool(args.apply), "trust": trust_args(args)}
    mode = "apply" if args.apply else "plan"
    if args.apply:
        args.command_name = "upgrade"
        check, snap, gate = guarded_apply(args, runner)
        data.update({"sanity": check, "snapshot": snap, "gate": gate})
        if not gate["ok"]:
            data["status"] = "blocked"
            return data
    result = run_engine(args, mode, runner)
    data.update({"status": "pass" if result["ok"] else "fail", "engine": result})
    verification = run_engine(args, "verify", runner) if (args.apply and args.verify) else None
    if verification is not None:
        data["verification"] = verification
        if not verification["ok"]:
            data["status"] = "fail"
    journal({"command": "upgrade", "apply": bool(args.apply), "snapshot": data.get("snapshot"),
             "engine": result, "status": data["status"]})
    return data


def cmd_migrate(args: argparse.Namespace, runner: Runner | None = None) -> dict[str, Any]:
    root = Path(args.root or "/")
    osrel = parse_os_release(root)
    identity = osrel.get("ID", "")
    id_like = osrel.get("ID_LIKE", "").split()
    source = args.source or "auto"
    data: dict[str, Any] = {"command": "migrate", "generated": utc(), "root": str(root),
                            "source": source, "detected_id": identity,
                            "detected_id_like": id_like, "target_manifest": args.target_manifest or ""}
    accepted = {
        "auto": True,
        "arch": identity == "arch" or "arch" in id_like or identity in {"garuda", "cachyos", "artix", "endeavouros"},
        "sunshine": identity in {"sunshine", "sunshineos"}
                    or "sunshine" in id_like or "sunshineos" in id_like,
    }
    if source not in accepted:
        data.update({"status": "fail", "reason": f"unknown source profile: {source!r}"})
        return data
    if not accepted[source]:
        data.update({"status": "fail", "reason": f"source {source!r} does not match detected identity"})
        return data
    if args.target_manifest and not Path(args.target_manifest).is_file():
        data.update({"status": "fail", "reason": f"target manifest missing: {args.target_manifest}"})
        return data

    check = run_engine(args, "check", runner)
    data["engine_check"] = check
    if not check["ok"]:
        data["status"] = "fail"
        return data
    expected_os = {"sunshine": "sunshine", "arch": "arch"}.get(source, "")
    if args.apply:
        args.command_name = "migrate"
        sanity_check, snap, gate = guarded_apply(args, runner, expected_os=expected_os)
        data.update({"sanity": sanity_check, "snapshot": snap, "gate": gate})
        if not gate["ok"]:
            data["status"] = "blocked"
            return data
    result = run_engine(args, "apply" if args.apply else "plan", runner)
    data.update({"status": "pass" if result["ok"] else "fail", "engine": result})
    if args.apply and args.verify:
        verification = run_engine(args, "verify", runner)
        data["verification"] = verification
        if not verification["ok"]:
            data["status"] = "fail"
    journal({"command": "migrate", "apply": bool(args.apply), "source": source,
             "detected_id": identity, "snapshot": data.get("snapshot"), "status": data["status"]})
    return data


def _servicing_assessment(directory: str | None) -> dict[str, Any]:
    if not directory:
        return {"collected": False, "reason": "no --servicing-dir evidence supplied"}
    base = Path(directory)
    if not base.is_dir():
        return {"collected": False, "reason": f"missing servicing evidence directory: {base}"}
    try:
        ensure_engine_import()
        from src.evolution.tools.windows_servicing import ServicingProbe, assess_windows_servicing
    except ImportError as exc:
        return {"collected": False, "reason": f"assessment module unavailable: {exc}"}
    probes: dict[str, Any] = {}
    for name in ("dism-checkhealth", "dism-scanhealth", "sfc-verifyonly"):
        path = base / f"{name}.json"
        if not path.is_file():
            continue
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
            probes[name] = ServicingProbe(
                name=str(payload.get("name", "")),
                command=tuple(payload.get("command", ())),
                return_code=payload.get("return_code"),
                output=str(payload.get("output", "")),
            )
        except (ValueError, TypeError, OSError) as exc:
            probes[name] = ServicingProbe(name="", command=(), return_code=127, output=str(exc))
    reboot_file = base / "reboot-pending.json"
    reboot: bool | None = None
    if reboot_file.is_file():
        try:
            value = json.loads(reboot_file.read_text(encoding="utf-8")).get("pending")
            reboot = value if isinstance(value, bool) else None
        except (ValueError, OSError):
            reboot = None
    report = assess_windows_servicing(probes, reboot_pending=reboot)
    return {"collected": True, "healthy": report.healthy, "blocked": report.blocked,
            "findings": [item.__dict__ for item in report.findings]}


def _native_lock_assessment(root: Path) -> dict[str, Any] | None:
    """Return the engine's fail-closed pacman lock state, or None if unavailable."""
    try:
        ensure_engine_import()
        from src.evolution.tools.arch_rescue import assess_pacman_lock
    except ImportError:
        return None
    lock = assess_pacman_lock(root / "var" / "lib" / "pacman" / "db.lck", root / "proc")
    return lock.to_dict()


def _arch_rescue_assessment(root: Path, runner: Runner | None,
                            reboot_state: str = "unknown") -> dict[str, Any]:
    """Collect Arch-native rescue evidence and classify it in the engine.

    The live command only observes. It cannot remove a lock, rewrite a unit,
    regenerate a boot entry, or create a snapshot.
    """
    try:
        ensure_engine_import()
        from src.evolution.tools.arch_rescue import (
            ArchRescueProbe,
            assess_arch_rescue,
            observe_arch_rescue_root,
        )
    except ImportError as exc:
        return {"collected": False, "reason": f"assessment module unavailable: {exc}"}

    probes: dict[str, Any] = {}
    for name, command in ARCH_RESCUE_PROBE_COMMANDS.items():
        result = run(list(command), runner, timeout=ARCH_RESCUE_TIMEOUTS[name])
        probes[name] = ArchRescueProbe(
            name=name,
            command=tuple(command),
            return_code=None if result.get("timed_out") else result.get("rc"),
            output=(out(result) + "\n" + str(result.get("stderr", ""))).strip(),
            timed_out=bool(result.get("timed_out")),
        )

    observed = observe_arch_rescue_root(root)
    lock = _native_lock_assessment(root)
    snapshots = snapshot_inventory(root, runner)
    observed.update({
        "lock_state": (lock or {}).get("state"),
        "lock": lock or {"state": "unknown", "lock_path": str(
            root / "var" / "lib" / "pacman" / "db.lck"), "detail": "assessor unavailable"},
        "snapshot_available": snapshots.get("available"),
        "pending_reboot": REBOOT_STATE_VALUES.get(
            str(reboot_state).lower(), REBOOT_STATE_VALUES["unknown"]
        ),
    })
    report = assess_arch_rescue(probes, observed=observed)
    return {
        "collected": True,
        "assessment": report.to_dict(),
        "observed": observed,
        "probes": {
            name: {"command": list(probe.command), "return_code": probe.return_code,
                   "timed_out": probe.timed_out}
            for name, probe in probes.items()
        },
    }


def _steamos_assessment(root: Path, runner: Runner | None) -> dict[str, Any]:
    observed: dict[str, Any] = {}
    mount = root_mount(root, runner)
    observed["root_mount_readonly"] = "ro" in mount.get("options", "").split(",")

    readonly = run(["steamos-readonly", "status"], runner)
    text = (out(readonly) + " " + readonly.get("stderr", "")).strip().lower()
    observed["readonly_status"] = "enabled" if "enabled" in text else "disabled" if "disabled" in text else "unknown"

    devmode = run(["steamos-devmode", "status"], runner)
    text = (out(devmode) + " " + devmode.get("stderr", "")).strip().lower()
    observed["devmode_status"] = "enabled" if "enabled" in text else "disabled" if "disabled" in text else "unknown"

    observed["devmode_marker_present"] = any(
        path.exists() for path in (
            root / "etc" / "steamos" / "devmode-enabled",
            root / "var" / "lib" / "steamos" / "developer-mode",
        )
    )
    try:
        ensure_engine_import()
        from src.evolution.tools.steamos_repair import assess_steamos_repair
    except ImportError as exc:
        return {"observed": observed, "assessment": None, "reason": f"module unavailable: {exc}"}
    return {"observed": observed, "assessment": assess_steamos_repair(observed).to_dict()}


def _slot_assessment(evidence_path: str | None, staging_path: str | None,
                     workflow_path: str | None, expected_os: str) -> dict[str, Any]:
    if not (evidence_path and staging_path and workflow_path):
        return {"evaluated": False, "reason": "slot evidence requires --slot-evidence, --slot-assessment and --slot-workflow"}
    try:
        payload = json.loads(Path(evidence_path).read_text(encoding="utf-8"))
        staging_payload = json.loads(Path(staging_path).read_text(encoding="utf-8"))
        workflow_payload = json.loads(Path(workflow_path).read_text(encoding="utf-8"))
        ensure_engine_import()
        from src.evolution.slot_activation import SlotActivationEvidence
        from src.evolution.staging import StagingAssessment, WorkflowRun
        from src.evolution.steamos_workflow import validate_steamos_workflow_activation
        assessment = StagingAssessment(
            strategy=str(staging_payload["strategy"]), workspace=str(staging_payload["workspace"]),
            reasons=tuple(staging_payload.get("reasons", ())),
            can_retain_previous=staging_payload.get("can_retain_previous") is True,
            active_slot=staging_payload.get("active_slot"), candidate_slot=staging_payload.get("candidate_slot"),
        )
        workflow = WorkflowRun(
            strategy=str(workflow_payload["strategy"]),
            completed=list(workflow_payload.get("completed", ())),
            current=workflow_payload.get("current"),
            aborted=workflow_payload.get("aborted") is True,
        )
        validate_steamos_workflow_activation(
            workflow, assessment, SlotActivationEvidence.from_mapping(payload), expected_os=expected_os
        )
        return {"evaluated": True, "allowed": True, "detail": "fresh evidence qualifies activation only; no slot was switched"}
    except Exception as exc:  # fail closed on any malformed evidence
        return {"evaluated": True, "allowed": False, "reason": f"{type(exc).__name__}: {exc}"}


def parse_missing_packages(text: str) -> list[str]:
    names: list[str] = []
    for line in text.splitlines():
        match = re.match(r"^([a-zA-Z0-9@._+-]+):", line)
        lowered = line.lower()
        suspicious = "warning" in lowered or "no such file" in lowered or "missing" in lowered
        if match and PACKAGE_NAME.fullmatch(match.group(1)) and suspicious:
            names.append(match.group(1))
    return sorted(set(names))


def cmd_repair(args: argparse.Namespace, runner: Runner | None = None) -> dict[str, Any]:
    root = Path(args.root or "/")
    # 'sunshine-report' reuses this assessment with a smaller argument set.
    apply = bool(getattr(args, "apply", False))
    servicing_dir = getattr(args, "servicing_dir", None)
    slot_evidence = getattr(args, "slot_evidence", None)
    slot_assessment = getattr(args, "slot_assessment", None)
    slot_workflow = getattr(args, "slot_workflow", None)
    target_os = getattr(args, "target_os", "") or "SunshineOS"
    fix_lock = bool(getattr(args, "fix_lock", False))
    reinstall_missing = bool(getattr(args, "reinstall_missing", False))
    pkg = engine_health(runner)
    checks = (pkg.get("report") or {}).get("checks", [])
    findings = [item for check in checks for item in check.get("findings", [])]
    integrity = run(["pacman", "-Qk"], runner, timeout=600)
    missing = parse_missing_packages(integrity.get("stdout", "") + "\n" + integrity.get("stderr", ""))
    lock = root / "var" / "lib" / "pacman" / "db.lck"
    lock_state = _native_lock_assessment(root) or {
        "state": "unknown", "lock_path": str(lock), "detail": "assessor unavailable",
    }

    report: dict[str, Any] = {
        "command": "repair", "generated": utc(), "root": str(root),
        "apply": apply,
        "assessment": {
            "package_health": pkg,
            "engine_findings": findings[:50],
            "missing_file_packages": missing,
            "lock": lock_state,
            "snapshots": snapshot_inventory(root, runner),
            "steamos": _steamos_assessment(root, runner),
            "arch_native_rescue": _arch_rescue_assessment(
                root, runner, getattr(args, "reboot_state", "unknown")
            ),
            "windows_servicing": _servicing_assessment(servicing_dir),
            "slot_activation": _slot_assessment(
                slot_evidence, slot_assessment, slot_workflow, target_os
            ),
        },
        "actions": [],
        "status": "assessment",
    }
    if not apply:
        report["remedy"] = "review the assessment; pass --apply with an explicit repair flag to mutate"
        return report

    args.command_name = "repair"
    check, snap, gate = guarded_apply(args, runner)
    report.update({"sanity": check, "snapshot": snap, "gate": gate})
    if not gate["ok"]:
        report["status"] = "blocked"
        return report

    if fix_lock:
        # An ownerless lock is only a stale candidate. The assessor never
        # authorizes deletion, so no code path here may remove db.lck.
        report["actions"].append({
            "name": "remove-stale-lock", "skipped": True,
            "reason": "lock deletion is not authorized by read-only evidence; recheck and use a separately approved recovery procedure",
            "observed_state": lock_state.get("state"),
        })
        report["status"] = "blocked"
        report["reason"] = "automatic lock removal is disabled by the native rescue safety rule"
        journal({"command": "repair", "apply": True, "snapshot": snap,
                 "actions": report["actions"], "status": report["status"]})
        return report
    if reinstall_missing and missing:
        action = run(["pacman", "-S", "--noconfirm", "--needed", *missing], runner, timeout=1800)
        report["actions"].append({"name": "reinstall-missing-packages", "packages": missing, "action": action})
    if not report["actions"]:
        report["status"] = "pass"
        report["reason"] = "apply requested but no authorized repair action matched the evidence"
    else:
        report["status"] = "pass" if all(
            item.get("skipped") or item.get("action", {}).get("rc") == 0 for item in report["actions"]
        ) else "fail"
    journal({"command": "repair", "apply": True, "snapshot": snap,
             "actions": report["actions"], "status": report["status"]})
    return report


def cmd_rescue(args: argparse.Namespace, runner: Runner | None = None) -> dict[str, Any]:
    """Read-only Arch-native rescue assessment; no repair action is available here."""
    root = Path(args.root or "/")
    result = _arch_rescue_assessment(root, runner, getattr(args, "reboot_state", "unknown"))
    assessment = result.get("assessment") or {}
    if assessment.get("healthy"):
        status = "pass"
    elif assessment.get("blocked") or assessment.get("degraded"):
        status = "blocked"
    else:
        status = "assessment"
    return {
        "command": "rescue", "generated": utc(), "root": str(root),
        "status": status, "apply": False,
        "remedy": "assessment only; use sunshine-repair with explicit flags after review",
        **result,
    }


def cmd_report(args: argparse.Namespace, runner: Runner | None = None) -> dict[str, Any]:
    root = Path(args.root or "/")
    health_report = health(root, runner, deep=args.deep)
    sanity_report = sanity(root, runner, require_snapshot=False)
    repair_report = cmd_repair(args, runner)
    return {
        "command": "report", "generated": utc(), "root": str(root),
        "status": worst([health_report["status"], sanity_report["status"]]),
        "health": health_report, "sanity": sanity_report, "repair": repair_report,
    }


def print_summary(data: dict[str, Any]) -> None:
    status = str(data.get("status", "unknown")).upper()
    print(f"{data.get('command', 'command').upper()} [{status}]")
    for item in data.get("evidence", []) or []:
        print(f"  {item.get('status', 'unknown'):>7}  {item.get('name')}: {item.get('detail')}")
    if "reason" in data:
        print(f"  reason: {data['reason']}")
    if "remedy" in data:
        print(f"  remedy: {data['remedy']}")
    for key in ("engine", "action", "verification"):
        value = data.get(key)
        if isinstance(value, dict):
            print(f"  {key}: rc={value.get('rc')} ok={value.get('ok')} argv={value.get('argv', '')}")
            if value.get("stderr"):
                print(f"    stderr: {str(value['stderr']).strip()[:500]}")


def add_common(parser: argparse.ArgumentParser, *, suppress: bool = False) -> None:
    """Add options accepted both before and after the subcommand.

    Subparser copies use SUPPRESS so an omitted option cannot erase a value
    supplied before the subcommand (important for the generated wrappers).
    """
    def kw(default: Any) -> dict[str, Any]:
        return {"default": argparse.SUPPRESS} if suppress else {"default": default}

    parser.add_argument("--json", action="store_true", help="emit JSON only", **kw(False))
    parser.add_argument("--out", metavar="PATH", help="write the full report to PATH", **kw(None))
    parser.add_argument("--root", metavar="PATH", help="target root (default: /)", **kw("/"))
    parser.add_argument("--state-root", metavar="PATH", help="engine state directory", **kw(str(state_dir())))
    parser.add_argument("--engine-dir", metavar="PATH", help="evolution-engine directory", **kw(""))
    parser.add_argument("--fixture", metavar="NAME", help="offline engine fixture for planning", **kw(""))
    parser.add_argument("--trust-index", metavar="PATH", **kw(""))
    parser.add_argument("--trust-policy", metavar="PATH", **kw(""))
    parser.add_argument("--trust-keyring", metavar="PATH", **kw(""))
    parser.add_argument("--trust-report", metavar="PATH", **kw(""))
    parser.add_argument("--trust-receipt", metavar="PATH", **kw(""))
    parser.add_argument("--adapter-dir", metavar="PATH", **kw(""))
    parser.add_argument("--adapter-artifact-root", metavar="PATH", **kw(""))
    parser.add_argument("--decide", action="append", metavar="ID=VALUE", **kw([]))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="sunshine-live", description=__doc__)
    add_common(parser)
    sub = parser.add_subparsers(dest="subcommand", required=True)

    p = sub.add_parser("health", help="read-only system health facts")
    add_common(p, suppress=True)
    p.add_argument("--deep", action="store_true", help="include package integrity probes")
    p.set_defaults(func=cmd_health)

    p = sub.add_parser("sanity", help="fail-closed preflight checks")
    add_common(p, suppress=True)
    p.add_argument("--require-snapshot", action="store_true")
    p.add_argument("--require-time", action="store_true")
    p.add_argument("--expected-os", default="")
    p.set_defaults(func=cmd_sanity)

    for name, func, help_text in (
        ("update", cmd_update, "package index and package update"),
        ("upgrade", cmd_upgrade, "target-state convergence via evolution engine"),
        ("migrate", cmd_migrate, "source discovery and migration planning/application"),
        ("repair", cmd_repair, "assess and, with explicit flags, repair"),
        ("report", cmd_report, "combined health, sanity and repair assessment"),
    ):
        p = sub.add_parser(name, help=help_text)
        add_common(p, suppress=True)
        if name != "report":
            p.add_argument("--apply", action="store_true", help="authorize mutation")
            p.add_argument("--allow-no-snapshot", action="store_true",
                           help="explicitly proceed when no rollback snapshot can be made")
            p.add_argument("--verify", action="store_true", help="run engine verification after apply")
        p.add_argument("--deep", action="store_true")
        if name == "migrate":
            p.add_argument("--source", choices=("auto", "arch", "sunshine"), default="auto")
            p.add_argument("--target-manifest", metavar="PATH")
        if name in {"repair", "report"}:
            p.add_argument("--servicing-dir", metavar="PATH")
            p.add_argument("--slot-evidence", metavar="PATH")
            p.add_argument("--slot-assessment", metavar="PATH")
            p.add_argument("--slot-workflow", metavar="PATH")
            p.add_argument("--target-os", default="SunshineOS")
            p.add_argument("--reboot-state", choices=tuple(REBOOT_STATE_VALUES), default="unknown",
                           help="observed servicing reboot state (default: unknown)")
        if name == "repair":
            p.add_argument("--fix-lock", action="store_true")
            p.add_argument("--reinstall-missing", action="store_true")
        p.set_defaults(func=func)

    p = sub.add_parser("rescue", help="read-only Arch-native rescue assessment")
    add_common(p, suppress=True)
    p.add_argument("--reboot-state", choices=tuple(REBOOT_STATE_VALUES), default="unknown",
                   help="observed servicing reboot state (default: unknown)")
    p.set_defaults(func=cmd_rescue)
    return parser


def cmd_health(args: argparse.Namespace, runner: Runner | None = None) -> dict[str, Any]:
    return health(Path(args.root or "/"), runner, deep=args.deep)


def cmd_sanity(args: argparse.Namespace, runner: Runner | None = None) -> dict[str, Any]:
    return sanity(Path(args.root or "/"), runner,
                  require_snapshot=args.require_snapshot, require_time=args.require_time,
                  expected_os=args.expected_os, trust=trust_args(args))


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        data = args.func(args)
    except (PermissionError, ValueError) as exc:
        payload = {"command": args.subcommand, "status": "fail", "generated": utc(),
                   "reason": f"{type(exc).__name__}: {exc}"}
        print(json.dumps(payload, indent=2) if args.json else f"{args.subcommand.upper()} [FAIL] {exc}")
        return 2
    path = write_report(args.subcommand, data, args.out)
    if path:
        data = {**data, "report_path": path}
    print(json.dumps(data, indent=2, sort_keys=True) if args.json else "")
    if not args.json:
        print_summary(data)
        if path:
            print(f"  report: {path}")
    status = str(data.get("status", "pass"))
    return 1 if status in {"fail", "blocked"} else 0


if __name__ == "__main__":
    raise SystemExit(main())
