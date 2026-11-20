#!/usr/bin/env python3
"""Milestone CLI: inspect the evolutionary scheme and drive verified upgrades.

    python3 src/milestone_cli.py --milestones
    python3 src/milestone_cli.py --from 0 --upgrade-to 0.9 --dry-run
    python3 src/milestone_cli.py --upgrade-to 0.9
    python3 src/milestone_cli.py --milestone-verify --manifest path.json
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.evolution.repository import MilestoneRepository  # noqa: E402
from src.evolution.scheme import load_scheme  # noqa: E402
from src.evolution.updater import EvolutionUpdater  # noqa: E402


def _json(obj: object) -> str:
    if hasattr(obj, "to_dict"):
        obj = obj.to_dict()
    return json.dumps(obj, indent=2, ensure_ascii=False, default=str)


def _verifier_factory(keyring: str | None):
    if not keyring:
        return None
    from src.trust import gpg_verifier
    return gpg_verifier(keyring)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="SunshineOS evolutionary milestone tool")
    parser.add_argument("--scheme", help="path to scheme.toml (default: bundled)")
    parser.add_argument("--state-root", default="/var/lib/sunshine/evolution")
    parser.add_argument("--milestones", action="store_true", help="list registered milestones")
    parser.add_argument("--upgrade-to", metavar="VERSION", help="target milestone/release")
    parser.add_argument("--from", dest="source", metavar="VERSION", default="0",
                        help="source milestone/release (default: 0)")
    parser.add_argument("--dry-run", action="store_true", help="show chain, do not execute")
    parser.add_argument("--milestone-verify", action="store_true",
                        help="verify a signed milestone manifest")
    parser.add_argument("--manifest", help="milestone manifest for --milestone-verify")
    parser.add_argument("--trusted-key", action="append", default=[],
                        help="trusted signing fingerprint (repeatable)")
    parser.add_argument("--trust-keyring", help="GPG keyring for signature verification")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    scheme = load_scheme(args.scheme)

    if args.milestones:
        print(_json({
            "current": str(scheme.registry.current),
            "aliases": {k: str(v) for k, v in scheme.registry.aliases.items()},
            "milestones": [m.to_dict() for m in scheme.registry.milestones],
            "versions": scheme.versions.to_dict(),
        }))
        return 0

    if args.milestone_verify:
        if not args.manifest:
            print("--milestone-verify requires --manifest", file=sys.stderr)
            return 2
        if not args.trusted_key or not args.trust_keyring:
            print("--milestone-verify requires --trusted-key and --trust-keyring", file=sys.stderr)
            return 2
        repo = MilestoneRepository(args.manifest)
        manifest, report = repo.verify_file(
            trusted_keys=set(args.trusted_key),
            verifier=_verifier_factory(args.trust_keyring),
            expected_scheme=scheme,
        )
        print(_json(report))
        return 0 if report.passed else 1

    if args.upgrade_to:
        # A CLI dry run is a chain preview; it has no live transformation to
        # validate. Programmatic dry runs keep the strict preconditions.
        dry_placeholders = (
            {"apply_fn": lambda: (True, "dry-run placeholder"),
             "verify_fn": lambda: (True, "dry-run placeholder")}
            if args.dry_run else {}
        )
        updater = EvolutionUpdater(scheme, args.state_root, **dry_placeholders)
        report = updater.upgrade(args.source, args.upgrade_to, dry_run=args.dry_run)
        print(_json(report))
        return 0 if report.ok else 1

    print("nothing to do: use --milestones, --upgrade-to, or --milestone-verify", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
