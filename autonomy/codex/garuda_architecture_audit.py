"""Verify the pinned Garuda Toolbox architecture observations used by Wave 1.

This is a read-only source audit. It records evidence and fails closed if a
catalogued behavior disappears or the checkout no longer matches its pin.
"""
from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path
from typing import Any

CATALOG = Path(__file__).with_name("garuda-wave1-catalog.json")
CHECKS = {
    "GARUDA-ARCH-001": ("packages/renderer/src/app/components/maintenance/maintenance.component.ts", r"garuda-update --skip-mirrorlist[\s\S]{0,180}pacman -Syu", "Updater fallback crosses updater/pacman paths"),
    "GARUDA-ARCH-002": ("packages/renderer/src/app/components/maintenance/maintenance.component.ts", r"pacman --noconfirm -Rns", "Orphan cleanup uses automatic confirmation and recursive removal"),
    "GARUDA-ARCH-003": ("packages/renderer/src/app/components/maintenance/maintenance.component.ts", r"executeAndWaitBashTerminal\(", "Renderer invokes a shell-command execution API for maintenance actions"),
    "GARUDA-ARCH-004": ("packages/renderer/src/app/components/maintenance/maintenance.component.ts", r"const cmd = `cp -r \$\{file\}", "Config reset interpolates paths into a shell command"),
    "GARUDA-ARCH-005": ("packages/renderer/src/app/components/boot-repair/boot-repair.service.ts", r"dd if=\"\$\{filename\}" , "Boot repair constructs a raw-device write using dd"),
    "GARUDA-ARCH-006": ("packages/main/src/modules/ShellModule.ts", r"ipcMain\.handle\('shell:spawnStreaming'[\s\S]{0,500}spawn\(command, args", "Shell IPC accepts command and argv from its caller"),
    "GARUDA-ARCH-007": ("packages/main/src/modules/AutoUpdater.ts", r"checkForUpdatesAndNotify\(this\.#notification\)", "Desktop application updater checks packaged app releases"),
    "GARUDA-ARCH-008": ("packages/main/src/modules/AutoUpdater.ts", r"this\.logger\.error\([\s\S]{0,240}return null", "Application updater errors are logged and suppressed so the app continues"),
    "GARUDA-ARCH-009": ("packages/renderer/src/app/components/system-status/system-status.component.ts", r"garuda-update --skip-mirrorlist[\s\S]{0,100}pacman -Syu", "System update flow selects Garuda updater or falls back to pacman"),
}


def audit(checkout: Path, expected_revision: str) -> dict[str, Any]:
    actual = subprocess.run(
        ["git", "-C", str(checkout), "rev-parse", "HEAD"],
        check=True, capture_output=True, text=True,
    ).stdout.strip()
    if actual != expected_revision:
        raise ValueError(f"checkout revision mismatch: expected {expected_revision}, got {actual}")
    findings = []
    for ident, (relative, pattern, description) in CHECKS.items():
        path = checkout / relative
        if not path.is_file():
            raise ValueError(f"{ident}: missing source file {relative}")
        lines = path.read_text(encoding="utf-8").splitlines()
        content = "\n".join(lines)
        match = re.search(pattern, content)
        if not match:
            raise ValueError(f"{ident}: expected source behavior not found in {relative}")
        line = content.count("\n", 0, match.start()) + 1
        excerpt = match.group(0).replace("\n", " ").strip()
        findings.append({"id": ident, "source_path": relative, "line": line,
                         "description": description, "evidence": excerpt})
    return {"checkout": str(checkout), "revision": actual, "findings": findings}


def main() -> int:
    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
    source = catalog["source"]
    result = audit(Path(source["checkout"]), source["revision"])
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
