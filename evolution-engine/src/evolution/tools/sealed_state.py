"""Signed sealed-state verification, adapted from macOS SSV/APFS.

macOS Big Sur introduced a Signed System Volume whose every byte is hashed into
a Merkle tree and verified on read and at boot, with APFS snapshots allowing a
previous system version to be restored without reinstallation. SunshineOS uses
the same *decision* at a smaller scale: managed state is sealed with a SHA-256
Merkle root, the seal is signed by the Stage A trust chain, and verification
detects added, removed and modified files before a milestone is committed.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping

from ..release import canonical_json

Signer = Callable[[str, bytes], str]
Verifier = Callable[[str, bytes, str], bool]


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _merkle(leaves: Iterable[str]) -> str:
    layer = [bytes.fromhex(h) for h in leaves]
    if not layer:
        return _sha256(b"")
    while len(layer) > 1:
        if len(layer) % 2:
            layer.append(layer[-1])
        layer = [
            hashlib.sha256(layer[i] + layer[i + 1]).digest()
            for i in range(0, len(layer), 2)
        ]
    return layer[0].hex()


@dataclass(frozen=True)
class Seal:
    root: str
    files: Mapping[str, str]
    signature: str = ""
    signed_by: str = ""

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "Seal":
        return cls(
            root=str(data.get("root", "")),
            files={
                str(k): str(v) for k, v in (data.get("files") or {}).items()
            },
            signature=str(data.get("signature", "")),
            signed_by=str(data.get("signed_by", "")),
        )

    def payload(self) -> dict[str, Any]:
        return {
            "root": self.root,
            "files": {k: self.files[k] for k in sorted(self.files)},
        }

    def to_dict(self) -> dict[str, Any]:
        return {**self.payload(), "signature": self.signature, "signed_by": self.signed_by}


@dataclass(frozen=True)
class SealReport:
    passed: bool
    errors: tuple[str, ...] = ()
    added: tuple[str, ...] = ()
    removed: tuple[str, ...] = ()
    modified: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "passed": self.passed, "errors": list(self.errors),
            "added": list(self.added), "removed": list(self.removed),
            "modified": list(self.modified),
        }


def build_seal(
    root: str | Path, *, exclude: Iterable[str] = ("hooks.jsonl", "*.tmp")
) -> Seal:
    base = Path(root)
    if not base.is_dir():
        raise ValueError(f"seal root is not a directory: {base}")
    files: dict[str, str] = {}
    for path in sorted(base.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(base).as_posix()
        if any(rel.endswith(pattern.lstrip("*")) or rel == pattern for pattern in exclude):
            continue
        files[rel] = _sha256(path.read_bytes())
    root_hash = _merkle(files[k] for k in sorted(files))
    return Seal(root=root_hash, files=files)


def verify_seal(root: str | Path, seal: Seal) -> SealReport:
    base = Path(root)
    errors: list[str] = []
    if not base.is_dir():
        return SealReport(False, (f"seal root is not a directory: {base}",))
    actual = build_seal(base).files
    expected = dict(seal.files)
    added = tuple(sorted(set(actual) - set(expected)))
    removed = tuple(sorted(set(expected) - set(actual)))
    modified = tuple(sorted(
        name for name in set(actual) & set(expected) if actual[name] != expected[name]
    ))
    if added:
        errors.append("unexpected files: " + ", ".join(added))
    if removed:
        errors.append("missing files: " + ", ".join(removed))
    if modified:
        errors.append("modified files: " + ", ".join(modified))
    if _merkle(actual[k] for k in sorted(actual)) != seal.root:
        errors.append("Merkle root mismatch")
    return SealReport(not errors, tuple(errors), added, removed, modified)


def sign_seal(seal: Seal, signed_by: str, sign: Signer) -> Seal:
    payload = canonical_json(seal.payload())
    return Seal(
        root=seal.root, files=seal.files,
        signature=sign(signed_by, payload), signed_by=signed_by,
    )


def verify_seal_signature(
    seal: Seal, trusted_keys: set[str], verifier: Verifier
) -> SealReport:
    errors: list[str] = []
    if seal.signed_by not in trusted_keys:
        errors.append(f"seal signer {seal.signed_by or '(empty)'} is not trusted")
    if not seal.signature:
        errors.append("seal has no signature")
    if not errors:
        try:
            ok = verifier(seal.signed_by, canonical_json(seal.payload()), seal.signature)
        except Exception as exc:
            ok, = (False,)
            errors.append(f"seal verifier error: {exc}")
        if not ok:
            errors.append("invalid seal signature")
    return SealReport(not errors, tuple(errors))
