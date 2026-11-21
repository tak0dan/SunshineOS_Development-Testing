# CachyOS deliverable consolidation — Wave 1

## Scope and grounding

Consolidates source-backed CachyOS findings into a versioned engine evidence catalogue. The user mandate's research, sustainability and reliability goals and AD-05/07/11/14 plus M-07/08 are applied as evidence rules: exact source paths, pinned source commit, SHA-256 verification, explicit adoption decisions and explicit limits. No CachyOS hooks or commands were run. The cached repository is `/home/tak_0/.local/state/sunshine-orchestrator/iso/repos/cachyos-tools`, commit `97a55536e5f756d22199f043de4aa1a0d8eebc8a`.

## Consolidated source catalogue

Catalogue artifact: `evolution-engine/fixtures/research/cachyos-wave1.json`.

| Exact path within CachyOS checkout | Catalogue ID | Consolidated finding and decision |
|---|---|---|
| `cachyos-kernel-manager/PKGBUILD` | `kernel-manager-package` | Recipe pins a signed tag and applies a local patch. Preserve recipe provenance; package presence does not identify the installed or bootable kernel. |
| `cachyos-kernel-manager/fix-installed-db.patch` | `kernel-manager-patch` | Local compatibility delta is packaged separately. Record it as distinct from upstream behavior; runtime effect is not inferred. |
| `cachy-update/PKGBUILD` | `update-helper-package` | Recipe pins a source commit and runs `make test`. Treat helper presence as workflow/UI evidence only; payload behavior is out of scope. |
| `cachyos-hooks/PKGBUILD` | `hooks-package` | Recipe pins a tag and lists payload installation inputs. The payload files are missing in this cache, so their behavior remains unverified. |
| `systemd-boot-manager/PKGBUILD` | `sdboot-package` | Recipe pins local files with SHA-512 and installs ALPM hooks. Preserve package-to-hook provenance; packaging does not prove runtime outcomes. |
| `systemd-boot-manager/sdboot-kernel-update.hook` | `kernel-update-hook` | Path trigger covers kernel image Install/Upgrade and runs `autogen` PostTransaction. Use the trigger pattern only with staged artifact checks. |
| `systemd-boot-manager/sdboot-kernel-remove.hook` | `kernel-remove-hook` | Separate path trigger handles kernel-file Remove and runs `remove` PostTransaction. Model removal separately; active kernel and recovery state must be observed. |
| `systemd-boot-manager/sdboot-systemd-update.hook` | `systemd-update-hook` | Package trigger handles systemd Upgrade and runs `autoupdate` PostTransaction. Keep it separate from kernel artifact transitions. |
| `systemd-boot-manager/sdboot-manage` | `sdboot-manager` | Selected generator failures are suppressed, with branch-specific later checks. Require per-artifact validation; static reading does not prove runtime completeness or rollback. |

The catalogue stores a SHA-256 for every listed source. Previous survey notes also reported unsupported `cachy-microcode`/scheduler hook claims; those are excluded because the named source files were not verified in this checkout. Earlier duplicate observations are consolidated above; this catalogue does not convert research into qualification or execution policy.

## Engine implementation

Added `evolution-engine/src/evolution/research_catalog.py` with immutable source/catalogue records, schema and commit validation, duplicate/path/status checks, and a local snapshot verifier. Verification refuses unsafe relative paths and reports missing or hash-mismatched source files. It never executes source files. The catalogue separates the source commit from the SunshineOS engine's own migration policy.

Regression IDs in `evolution-engine/tests/test_research_catalog.py`:

- `CAT_001`: checked-in CachyOS catalogue has nine unique, structurally valid records.
- `CAT_002`: matching source snapshot verifies.
- `CAT_003`: changed source content fails SHA-256 verification.
- `CAT_004`: parent traversal is rejected.
- `CAT_005`: unverified evidence cannot be accepted as a verified catalogue record.

## Verification and evidence

Test command, from `evolution-engine/`:

```sh
python3 -m unittest tests/test_research_catalog.py -v
```

Result: **5 tests passed**. Full output: `autonomy/codex/cachyos-deliverable-consolidation-test.log`.

Source snapshot verification command, from `evolution-engine/`:

```sh
PYTHONPATH=. python3 - <<'PY'
from pathlib import Path
from src.evolution.research_catalog import ResearchCatalog
catalog = ResearchCatalog.load('fixtures/research/cachyos-wave1.json')
errors = catalog.verify_sources(Path('/home/tak_0/.local/state/sunshine-orchestrator/iso/repos/cachyos-tools'))
print('verified source records:', len(catalog.sources))
print('errors:', errors)
raise SystemExit(bool(errors))
PY
```

Result: `verified source records: 9`; `errors: []`. The source checkout remains external to git; future verification requires that checkout or a byte-identical archived copy.
