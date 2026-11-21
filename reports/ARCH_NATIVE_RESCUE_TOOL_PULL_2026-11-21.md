# Native Arch rescue tool pull — 2026-11-21

## Scope

This record completes the research/tool pull from the Arch-family ISO and source
corpus and the Windows 11 servicing research already collected in this repo. The
Windows read-only checks are **rewritten as Arch-native evidence**; no Windows
command is executed and no Windows ISO or VM is claimed as tested. No credential
material is included, and the 20-year migration margin and Stage A trust rules are
unchanged.

## Source basis

The pull is pinned in
`evolution-engine/fixtures/research/native-arch-rescue-wave1.json` and verified by
`test_CAT_007`. Pinned evidence includes:

- the cached ISO/repository manifest snapshot (6 Arch-family ISO downloads, 4
  successful repository pulls);
- the cumulative cross-distro research and stability decision records;
- the Windows servicing wave notes and the existing exact-argv DISM/SFC assessor;
- Arch-family pull modules for pacman lock assessment, ALPM hook validation,
  boot-generation suppression auditing, and traceable pattern catalogs.

The catalog records SHA-256 for every source file and fails closed on changed or
missing content. Windows 11 and SteamOS remain documentation/research sources
because the corpus records no stable direct ISO URL for them.

## Windows-to-Arch mapping

| Windows concept (research only) | Native Arch evidence | Result |
|---|---|---|
| DISM `/CheckHealth` component-store check | `pacman -Dk` dependency/database check | exact argv allowlist; recognized clean output only |
| DISM `/ScanHealth` + SFC `/verifyonly` protected-file check | `pacman -Qk` owned-file check | zero missing files is healthy; missing files degrade |
| WinRE startup repair | `systemd-analyze verify default.target` | silence is healthy; error/failed/not-found/invalid/warning degrades |
| WinRE boot repair | kernel, initramfs and bootloader configuration under the target root | missing artifacts degrade; unobserved facts are unknown |
| Servicing transaction state | pacman lock state with process-table ownership | active owner blocks; stale candidate degrades; unknown unreadable state blocks |
| System Restore | observed rollback snapshot | absence degrades; absence of observation is unknown |
| Pending servicing reboot | explicit observed reboot state | pending blocks; settled is healthy; default unknown blocks |

All checks are read-only. The engine assessor accepts only captured probe results
and filesystem observations; it never executes a repair. A mutating command must
still go through the existing root, `--apply`, sanity, snapshot, journal and, for
upgrade/migration, signed Stage A gates.

## Published integrations

- `evolution-engine/src/evolution/tools/arch_rescue.py` — fail-closed native
  assessor with Windows counterparts recorded on every finding.
- `evolution-engine/src/evolution/tools/__init__.py` — public engine exports.
- `iso/tools/sunshine_live.py` — collects native probes, embeds assessment in
  `repair`/`report`, and adds read-only `sunshine-rescue`.
- `iso/tools/stage_profile.py` — generates the `sunshine-rescue` wrapper and
  includes it in build metadata.
- `iso/profile/sunshine/profiledef.sh` — file metadata for the wrapper.
- `iso/profile/sunshine/airootfs/etc/motd` — operator entry point.
- `iso/README.md` — command and safety documentation.

### Lock safety change

The old `sunshine-repair --apply --fix-lock` path could delete `db.lck` when a PID
recorded in the lockfile looked dead. That is no longer accepted as proof. The
native lock assessor classifies an ownerless lock only as `stale-candidate`, and
`--fix-lock` now records a blocked, skipped action with no `rm` call. Automatic
lock deletion was removed from every code path.

## Verification

Run from the repository root:

- `python3 -m unittest discover -s evolution-engine/tests -p 'test_*.py'` —
  **325 tests OK**.
- `python3 -m unittest discover -s iso/tests -p 'test_*.py'` — **28 tests OK**.
- Focused native rescue tests: 7 engine tests OK.
- Focused provenance test: `test_CAT_007` verifies all 10 pinned source hashes.
- `shellcheck iso/build.sh iso/verify.sh iso/tools/sunshine-live iso/profile/sunshine/profiledef.sh` — clean.
- `python3 autonomy/codex/ci_policy_audit.py .` — `WORKFLOWS: 6`,
  `RESULT: NO_DETECTED_POLICY_FINDINGS`.
- `bash iso/build.sh --check --skip-tests` — staged profile validated, no missing
  files, `profiledef.sh` syntax OK, `sunshine-rescue` wrapper generated.

These are source and staged-profile checks. The rebuilt image produced by CI after
this change is recorded separately in `reports/ISO_ARTIFACT_2026-11-21.md`.

## Limits

- No Windows servicing mutation, Windows VM, or Windows ISO was used.
- The engine has a deterministic rule-based assessor, not a learned planner.
- `sunshine-rescue` is assessment-only and never mutates state.
- Boot, installation and booted-toolkit validation of the rebuilt image remain
  separate claims and are not asserted by this record.
