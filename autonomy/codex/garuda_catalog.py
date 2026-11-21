"""Fail-closed validation for the Wave 1 Garuda pattern catalog."""
from __future__ import annotations

import json
import re
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
    if not isinstance(data, dict):
        raise ValueError("catalog must be an object")
    if data.get("schema_version") != 1:
        raise ValueError("unsupported schema_version")
    source = data.get("source", {})
    if not isinstance(source, dict):
        raise ValueError("source must be an object")
    revision = source.get("revision", "")
    if not isinstance(source.get("repository"), str) or not source["repository"].strip() or not isinstance(revision, str) or not re.fullmatch(r"[0-9a-f]{40}", revision):
        raise ValueError("source must identify a repository and full commit revision")
    invariant_refs = data.get("invariants")
    if not isinstance(invariant_refs, list) or not invariant_refs or any(not isinstance(item, str) for item in invariant_refs) or not set(invariant_refs) <= VALID_INVARIANTS:
        raise ValueError("catalog invariants are invalid")
    findings = data.get("findings")
    if not isinstance(findings, list) or not findings:
        raise ValueError("findings must be a non-empty list")
    ids: set[str] = set()
    for finding in findings:
        if not isinstance(finding, dict):
            raise ValueError("finding must be an object")
        ident = finding.get("id", "")
        if not isinstance(ident, str):
            raise ValueError("finding id must be a string")
        if not ident or ident in ids:
            raise ValueError(f"missing or duplicate finding id: {ident!r}")
        ids.add(ident)
        if finding.get("verdict") not in VALID_VERDICTS:
            raise ValueError(f"{ident}: invalid verdict")
        paths = finding.get("source_paths")
        if not isinstance(paths, list) or not paths or any(not isinstance(p, str) or not p or p.startswith("/") or ".." in Path(p).parts for p in paths):
            raise ValueError(f"{ident}: source_paths are required")
        controls_list = finding.get("controls", [])
        if not isinstance(controls_list, list) or any(not isinstance(item, str) for item in controls_list):
            raise ValueError(f"{ident}: controls must be a list of strings")
        controls = set(controls_list)
        missing = REQUIRED_CONTROLS[finding["verdict"]] - controls
        if missing:
            raise ValueError(f"{ident}: missing safety controls {sorted(missing)}")
        refs = finding.get("invariants", [])
        if not isinstance(refs, list) or any(not isinstance(item, str) for item in refs):
            raise ValueError(f"{ident}: invariants must be a list of strings")
        invariants = set(refs)
        if not invariants or not invariants <= VALID_INVARIANTS:
            raise ValueError(f"{ident}: invalid invariant traceability")


if __name__ == "__main__":
    catalog_path = Path(__file__).with_name("garuda-wave1-catalog.json")
    catalog = load_catalog(catalog_path)
    checkout = Path(catalog["source"].get("checkout", ""))
    if checkout.is_dir():
        missing = sorted({path for item in catalog["findings"] for path in item["source_paths"] if not (checkout / path).is_file()})
        if missing:
            raise SystemExit(f"source paths missing from pinned checkout: {missing}")
    print(f"validated {len(catalog['findings'])} Garuda findings")
