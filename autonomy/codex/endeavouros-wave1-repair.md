# EndeavourOS repair-tool survey and SunshineOS adaptation — Wave 1

Date: 2026-11-21  
Scope: survey verifiable EndeavourOS repair and maintenance tools, catalogue their paths and boundaries, and implement a safe configuration-drift assessment. The source checkout and test fixture do not qualify real-host repair or migration.

## EndeavourOS survey

Upstream source reviewed: [`endeavouros-team/eos-bash-shared`](https://github.com/endeavouros-team/eos-bash-shared), the shared tools repository. Its README catalogs `eos-pacdiff` as the EndeavourOS pacdiff utility, `eos-update` as a package updater using pacman and optionally yay, and `paccache-service-manager` for managing the package-cache service. The repository's `eos-pacdiff` implementation calls `/usr/bin/pacdiff -s`, can make backups of candidate files, and contains a safety warning naming `/etc/passwd`, `/etc/group`, and `/etc/shadow` as files that need particular care. These are source-reviewed behaviors; I did not execute those utilities on a host.

| Exact upstream path / command | Observed repair or maintenance behavior | SunshineOS treatment |
|---|---|---|
| `endeavouros-team/eos-bash-shared/eos-pacdiff` | Wraps `pacdiff` for interactive `.pacnew`/`.pacsave` reconciliation; supports backups and warns about sensitive account files. | Adopt candidate discovery and explicit review. Do not auto-merge, overwrite, or delete. |
| `endeavouros-team/eos-bash-shared/eos-update` (repository README entry) | Package updater with EndeavourOS/Arch options; uses pacman and optionally yay. | Treat as update workflow, not a repair authority. Package-health checks remain read-only and preserve foreign package ownership. |
| `endeavouros-team/eos-bash-shared/paccache-service-manager` (repository README entry) | Manages the paccache service that limits package-cache growth. | Potential later cache-maintenance adapter; no automatic cache deletion added here. |
| EndeavourOS ISO `/arch/x86_64/airootfs.sfs` | Compressed live root; existing local ISO survey identifies it, but this wave did not extract it. | No claim that these utilities are installed in this particular ISO or comprise its complete repair toolkit. |

Official source references: [shared tools repository and README](https://github.com/endeavouros-team/eos-bash-shared), [eos-pacdiff source](https://github.com/endeavouros-team/eos-bash-shared/blob/main/eos-pacdiff), [eos-packagelist documentation](https://github.com/endeavouros-team/PKGBUILDS/tree/master/eos-packagelist). The package-list tool is a profile package list handler with an optional pacman install mode; it is not itself a repair or validation mechanism.

## SunshineOS changes

- Added `evolution-engine/src/evolution/tools/config_drift.py::assess_config_drift`, a read-only, rooted scanner for regular `.pacnew` and `.pacsave` candidates below `/etc`.
- The scanner returns deterministic candidate paths, original paths, type, and a review disposition. It marks `/etc/fstab`, `/etc/crypttab`, account databases, and sudoers candidates for manual review.
- Symlink directories and symlink candidates are not followed. Missing/unreadable configuration roots report an incomplete assessment instead of a clean result.
- Added `evolution-engine/tests/test_config_drift.py` with `T-EOS-REPAIR-001` (candidate classification and no mutation), `T-EOS-REPAIR-002` (missing evidence fails closed), and `T-EOS-REPAIR-003` (symlink boundary).
- Existing `evolution-engine/src/evolution/tools/package_health.py::assess_package_health` is also catalogued as the read-only package repair assessment path: pacman dependency checks, installed-file checks, and orphan candidates are advisory; this work did not alter that concurrently present file.

This follows mandate M-04/M-06/M-08 and architecture decisions AD-04/AD-05/AD-14: observed state governs, repair must be recoverable, and a source profile or tool presence is not migration qualification. The assessment generates no mutation operations; any future reconciliation needs a checkpoint, explicit plan, and validation before enabling writes.

## Regression evidence

Command from `evolution-engine/`:

```text
python3 -m unittest tests.test_config_drift tests.test_package_health
Ran 6 tests — OK
```

Test IDs: `T-EOS-REPAIR-001`–`003`, plus the three existing `PackageHealthTests`. Full output: [`endeavouros-wave1-repair-test.log`](endeavouros-wave1-repair-test.log).

## Qualification limits

This is a source survey and offline unit-tested assessment, not a copied EndeavourOS implementation or host repair qualification. The EndeavourOS ISO's compressed root and installer were not extracted; installed defaults, exact package versions, repository/keyring recovery, service repair, and crash recovery remain unverified. The `.pacnew` assessment is observational only and deliberately leaves merges to a qualified later workflow.
