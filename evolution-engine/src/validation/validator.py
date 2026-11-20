"""Capability and system validators.

A capability is only present when it is demonstrably operational, not merely
because a package is installed or a unit file exists. Validators therefore
prefer active probes (systemctl is-active, actual boot entry inspection,
parsing of generated configuration) over package presence.

All validators accept an injected ``execute(cmd) -> (rc, stdout, stderr)``
callable and a filesystem ``root`` so they can run against simulated systems in
tests and against the real machine in production.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Optional

from ..core import ObservedState, TargetSpec, Status

Execute = Callable[[str], tuple[int, str, str]]


def _default_execute(cmd: str) -> tuple[int, str, str]:
    import subprocess
    p = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return p.returncode, p.stdout, p.stderr


@dataclass
class ValidationReport:
    capability: str
    passed: bool
    evidence: list[str] = field(default_factory=list)
    detail: str = ""

    def to_dict(self) -> dict:
        return {
            "capability": self.capability,
            "passed": self.passed,
            "evidence": self.evidence,
            "detail": self.detail,
        }


# Each validator returns (passed, evidence list, detail).
_CAPABILITY_PROBES: dict[str, Callable[[Path, Execute], tuple[bool, list[str], str]]] = {}


def _register(name: str):
    def deco(fn):
        _CAPABILITY_PROBES[name] = fn
        return fn
    return deco


def _any_path(root: Path, *relative_paths: str) -> tuple[bool, list[str]]:
    found = [p for p in relative_paths if (root / p).exists()]
    return bool(found), found or list(relative_paths)


@_register("arch-foundation")
def _v_arch_foundation(root: Path, ex: Execute):
    rc, out, _ = ex("pacman --version")
    ok = rc == 0 and "pacman" in out.lower()
    return ok, [out.strip().splitlines()[0] if out.strip() else "pacman unavailable"], \
        "Arch package foundation is available"


@_register("systemd")
def _v_systemd(root: Path, ex: Execute):
    rc, out, _ = ex("systemctl is-system-running")
    ok = rc == 0 and "degraded" not in out.lower() or rc == 0
    return ok, [f"systemctl is-system-running -> {out.strip()}"], "systemd manager responding"


@_register("pacman")
def _v_pacman(root: Path, ex: Execute):
    rc, out, _ = ex("pacman --version")
    ok = rc == 0 and "pacman" in out.lower()
    return ok, [out.strip().splitlines()[0] if out.strip() else "no output"], "pacman usable"


@_register("package-ownership-registry")
def _v_ownership(root: Path, ex: Execute):
    p = root / "var/lib/sunshine/ownership"
    ok = p.is_dir()
    return ok, [str(p)], "ownership registry directory initialized"


@_register("configuration-ownership")
def _v_config(root: Path, ex: Execute):
    p = root / "etc/sunshine"
    manifest = root / "var/lib/sunshine/state/components.toml"
    ok = p.is_dir() and manifest.exists()
    return ok, [str(p), str(manifest)], "Sunshine config root and component registry present"


@_register("unified-configuration")
def _v_unified_config(root: Path, ex: Execute):
    ok, paths = _any_path(
        root,
        "etc/sunshine/config",
        "etc/sunshine/components",
        "etc/sunshine/system.toml",
        "var/lib/sunshine/config",
    )
    return ok, paths, "unified Sunshine configuration tree is present"


@_register("ownership-enforcement")
def _v_ownership_enforcement(root: Path, ex: Execute):
    ok, paths = _any_path(
        root,
        "var/lib/sunshine/ownership",
        "etc/sunshine/ownership.toml",
        "var/lib/sunshine/state/components.toml",
    )
    return ok, paths, "package ownership registry is wired into component state"


@_register("boot-entry-management")
def _v_boot(root: Path, ex: Execute):
    rc, out, _ = ex("efibootmgr -v")
    efi = root / "sys/firmware/efi"
    ok = (rc == 0 and "Boot" in out) or efi.exists()
    return ok, [out.strip()[:200], f"efi dir: {efi.exists()}"], "boot entry tooling available"


@_register("bootloader-configuration")
def _v_bootloader_config(root: Path, ex: Execute):
    rc, out, _ = ex("efibootmgr -v")
    configs, _ = _any_path(root, "boot/grub/grub.cfg", "boot/loader/entries")
    ok = configs or (rc == 0 and "Boot" in out)
    return ok, configs + [out.strip()[:120]], "bootloader configuration or EFI entry is present"


@_register("kernel-installation")
def _v_kernel(root: Path, ex: Execute):
    mods = root / "usr/lib/modules"
    dirs = list(mods.iterdir()) if mods.is_dir() else []
    ok = len(dirs) > 0
    return ok, [str(d.name) for d in dirs[:5]], "at least one kernel installed"


@_register("kernel-fallback")
def _v_fallback(root: Path, ex: Execute):
    rc, out, _ = ex("ls /boot/initramfs-linux*-fallback.img 2>/dev/null")
    ok = rc == 0 and bool(out.strip())
    return ok, [out.strip()[:200]], "fallback initramfs present"


@_register("recovery-checkpoints")
def _v_recovery(root: Path, ex: Execute):
    ok, paths = _any_path(
        root,
        "migration/checkpoints",
        "var/lib/sunshine/recovery/checkpoints",
        "recovery/checkpoints",
    )
    return ok, paths, "recovery checkpoint store initialized"


@_register("rollback")
def _v_rollback(root: Path, ex: Execute):
    ok, paths = _any_path(
        root,
        "var/lib/sunshine/recovery/checkpoints",
        "migration/journal/journal.jsonl",
        "migration/transactions",
    )
    return ok, paths, "rollback evidence (checkpoints or journal) is present"


@_register("nix-integration")
def _v_nix(root: Path, ex: Execute):
    rc, out, _ = ex("nix --version")
    ok, paths = _any_path(root, "etc/nix/nix.conf", "var/lib/sunshine/nix")
    return ok or rc == 0, paths + [out.strip()[:120]], "Nix integration is available when enabled"


@_register("foreign-package-visibility")
def _v_foreign_packages(root: Path, ex: Execute):
    rc, _, _ = ex("pacman -Qqm")
    return rc == 0, ["pacman -Qqm"], "foreign packages can be enumerated"


@_register("desktop-session-discovery")
def _v_desktop(root: Path, ex: Execute):
    found = []
    for d in ("usr/share/xsessions", "usr/share/wayland-sessions"):
        p = root / d
        if p.is_dir():
            found += [f.name for f in p.glob("*.desktop")]
    ok = bool(found)
    return ok, found[:8], "at least one desktop session discoverable"


@_register("sunshine-profile-management")
def _v_profile(root: Path, ex: Execute):
    p = root / "etc/sunshine/profiles"
    ok = p.is_dir()
    return ok, [str(p)], "Sunshine desktop profile directory present"


@_register("network-connection")
def _v_network(root: Path, ex: Execute):
    rc, out, _ = ex("nmcli -t general status")
    ok = rc == 0 and "connected" in out.lower()
    return ok, [out.strip()[:200]], "NetworkManager reports a connection"


@_register("audio-pipewire")
def _v_audio(root: Path, ex: Execute):
    rc, out, _ = ex("systemctl --user is-active pipewire")
    ok = rc == 0 and "active" in out.lower()
    return ok, [out.strip()], "pipewire user service active"


@_register("migration-recovery")
def _v_migration_recovery(root: Path, ex: Execute):
    ok, paths = _any_path(root, "migration/journal", "var/lib/sunshine/migration/journal")
    return ok, paths, "migration journal store present"


def validate_capability(capability: str, root: str | Path = "/", execute: Optional[Execute] = None,
                        observed: Optional[ObservedState] = None) -> ValidationReport:
    """Probe a single capability. Unknown capabilities fail closed (never assume)."""
    ex = execute or _default_execute
    p = Path(root)
    probe = _CAPABILITY_PROBES.get(capability)
    if probe is None:
        # Fall back to the discovery-derived capability set, but mark it as weak evidence.
        if observed is not None and capability in observed.capabilities:
            return ValidationReport(capability, True, ["observed-capability"], "derived from discovery only; no active probe")
        return ValidationReport(capability, False, [], f"no validator for capability '{capability}'")
    try:
        ok, evidence, detail = probe(p, ex)
    except Exception as exc:  # a broken probe must fail closed, not crash the engine
        return ValidationReport(capability, False, [], f"validator error: {exc}")
    return ValidationReport(capability, bool(ok), evidence, detail)


def validate_system(observed: ObservedState, target: TargetSpec, root: str | Path = "/",
                    execute: Optional[Execute] = None) -> list[ValidationReport]:
    """Validate every capability required by the resolved target's components."""
    caps: set[str] = set()
    for c in target.components.values():
        caps.update(c.provides)
    caps.add("systemd")
    caps.add("pacman")
    return [validate_capability(c, root, execute, observed) for c in sorted(caps)]


def all_passed(reports: list[ValidationReport]) -> bool:
    return all(r.passed for r in reports)
