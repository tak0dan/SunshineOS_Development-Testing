"""Fail-closed validation for the Wave 1 Garuda pattern catalog."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

VALID_VERDICTS = {"ADAPT", "AVOID", "COPY"}
REQUIRED_CONTROLS = {
    "ADAPT": {"plan-before-mutation", "journal-operation", "verify-postcondition"},
    "COPY": {"plan-before-mutation", "journal-operation", "verify-postcondition"},
    "AVOID": set(),
}
VALID_INVARIANTS = {f"M-{n:02d}" for n in range(1, 11)}


def load_catalog(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    validate_catalog(data)
    return data


def validate_catalog(data: dict[str, Any]) -> None:
    """Reject malformed, untraceable or insufficiently controlled findings."""
    if data.get("schema_version") != 1:
        raise ValueError("unsupported schema_version")
    source = data.get("source", {})
    if not source.get("repository") or len(source.get("revision", "")) != 40:
        raise ValueError("source must identify a repository and full commit revision")
    findings = data.get("findings")
    if not isinstance(findings, list) or not findings:
        raise ValueError("findings must be a non-empty list")
    ids: set[str] = set()
    for finding in findings:
        ident = finding.get("id", "")
        if not ident or ident in ids:
            raise ValueError(f"missing or duplicate finding id: {ident!r}")
        ids.add(ident)
        if finding.get("verdict") not in VALID_VERDICTS:
            raise ValueError(f"{ident}: invalid verdict")
        paths = finding.get("source_paths")
        if not paths or any(not isinstance(p, str) or not p for p in paths):
            raise ValueError(f"{ident}: source_paths are required")
        controls = set(finding.get("controls", []))
        missing = REQUIRED_CONTROLS[finding["verdict"]] - controls
        if missing:
            raise ValueError(f"{ident}: missing safety controls {sorted(missing)}")
        invariants = set(finding.get("invariants", []))
        if not invariants or not invariants <= VALID_INVARIANTS:
            raise ValueError(f"{ident}: invalid invariant traceability")


if __name__ == "__main__":
    catalog_path = Path(__file__).with_name("garuda-wave1-catalog.json")
    catalog = load_catalog(catalog_path)
    print(f"validated {len(catalog['findings'])} Garuda findings")
