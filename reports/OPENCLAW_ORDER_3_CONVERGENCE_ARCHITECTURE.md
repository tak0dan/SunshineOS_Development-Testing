# Order 3 — 20-year Stage A and VBox convergence architecture

- Status: done (attempts: 1)
- Agent role: architect (baidu/ernie-5.5-flash-preview:free)
- Source: OpenClaw / OpenRouter delegation from sibling session orders, 2026-11-20

---

# Proposed Stage A Traceability, Custody, and Preservation Report

Repository root: `/home/tak_0/sunshineos-audit/SunshineOS_Development-Testing`

Status: proposed design for `reports/STAGE_A_TRACEABILITY.md`.

No credentials, tokens, passwords, key values, or secrets are included. Rotation and credential references are identifier-only.

---

## 1. Source basis

Use these repository artifacts as the canonical inputs:

| Source | Purpose |
|---|---|
| `reports/ARCHITECTURE_DECISIONS.md` | Canonical AD-01..AD-30 and M-01..M-10 mapping. |
| `evolution-engine/src/evolution/invariants.py` | Machine-checkable invariants `_m01`..`_m10`. |
| `evolution-engine/tests/test_evolution.py::VersionAndSchemeTests` | Asserts invariants and scheme behavior. |
| `evolution-engine/tests/source-matrix.toml` | Source-shape matrix for btrfs/ext4/LUKS/GRUB/systemd-boot/NVIDIA/AUR. |
| `reports/VM_EVOLUTION_VALIDATION.md` | VM validation evidence. |
| `reports/cross-distro-stability.md` | Cross-distro stability evidence. |
| `evolution-engine/evolution/docs/BASELINE_ARCH_2026.md` | Baseline epoch rationale. |

Evidence path conventions:

| Evidence class | Path pattern |
|---|---|
| Stage A gate result | `evidence/stage-a/<GATE_OR_ID>.json` |
| VBox break/fix log | `logs/vbox/<TEST_ID>.log` |
| VBox structured result | `evidence/vbox/<TEST_ID>.json` |
| CI result | `logs/ci/<CI_ID>.json` |
| Quarterly preservation manifest | `reports/quarterly-preservation/Q-YYYYQn/manifest.json` |
| Rotation custody record | `evidence/custody/<ROTATION_ID>.json` |

---

## 2. Stage A gate model

Stage A gates are proposed logical gates derived from the shipped engine and AD decisions.

| Gate | Name | Pass condition | Primary evidence |
|---|---|---|---|
| SA-00 | Inventory authority | Observed installation inventory is authoritative; reported release cannot override it. | `evidence/inventory/SA-00.json`, `evolution-engine/src/evolution/invariants.py::_m04` |
| SA-01 | Baseline and scheme | Arch 2026 baseline epoch and declarative scheme are loaded and validated. | `evidence/stage-a/SA-01.json`, `evolution-engine/src/evolution/scheme.toml` |
| SA-02 | Qualification | Source capabilities are classified into a qualified support tier. | `evidence/qualification/SA-02.json`, `evolution-engine/src/evolution/qualification.py` |
| SA-03 | Target resolution | Target state is deterministic and derived from cumulative evolution records. | `evidence/target/SA-03.json`, `evolution-engine/src/evolution/target_resolver.py` |
| SA-04 | Trust and custody | Artifacts, channels, tools, and observers fail closed unless signed and verified. | `evidence/trust/SA-04.json`, `evolution-engine/src/trust/model.py` |
| SA-05 | Checkpoint and staging | Checkpoint occurs before crossing; staged migration or equivalent recovery contract exists. | `evidence/checkpoints/SA-05.json`, `evolution-engine/src/evolution/updater.py` |
| SA-06 | Recovery and data | Recovery lineage and user-data preservation plan are explicit and separate. | `evidence/recovery/SA-06.json`, `evolution-engine/src/evolution/recovery.py` |
| SA-07 | Execution, hooks, UX | Hooks are sandboxed, permission-limited, non-network, and UX helpers are wired. | `logs/hooks/SA-07.log`, `evolution-engine/src/evolution/hooks.py` |
| SA-08 | Ledger and archive | Ledger is immutable, contiguous, digest-tracked; artifacts are content-addressed. | `evidence/ledger/SA-08.json`, `evolution-engine/src/evolution/ledger.py` |
| SA-09 | Verify and tamper detection | Post-migration verification detects missing checkpoints and changed managed paths. | `evidence/verify/SA-09.json`, `src/verify.py` |
| SA-10 | Release and preservation | Release gate and quarterly preservation rules are satisfied. | `reports/quarterly-preservation/Q-YYYYQn/manifest.json` |

---

## 3. VBox break/fix test catalog

These are proposed VBox test IDs. Each test should produce:

- `logs/vbox/<TEST_ID>.log`
- `evidence/vbox/<TEST_ID>.json`

| Test ID | Break/fix assertion |
|---|---|
| VBOX-INV-001 | A misleading reported release does not override observed inventory. |
| VBOX-BASE-001 | Floating “latest Arch” is rejected; baseline epoch is pinned. |
| VBOX-SCHEME-001 | Missing or altered scheme metadata is rejected or blocks migration. |
| VBOX-COMPAT-001 | Old Sunshine OS and pure Arch are classified by capability, not release age. |
| VBOX-TARGET-001 | Ambiguous target resolution fails unless `--decide` is explicit. |
| VBOX-COMP-001 | Conceptual component names resolve to real packages such as `sunshine-base` and `linux`. |
| VBOX-PROFILE-001 | `sunshine-profiles.service` is rejected; `sunshine-apps.service` is accepted. |
| VBOX-TRUST-001 | Empty digest, unknown signer, or revoked channel blocks migration. |
| VBOX-TOOLSYNC-001 | Source push alone does not update tools; signed `tak0dan/sunshine-tools` release is required. |
| VBOX-HOOK-001 | Hook using network, `shell=True`, or excessive permissions is rejected. |
| VBOX-CHECKPOINT-001 | Failure after crossing restores the pre-crossing checkpoint. |
| VBOX-STAGE-001 | btrfs staged migration is preferred; ext4 receives an equivalent recovery contract. |
| VBOX-ROLLBACK-001 | Any failed verification triggers restore. |
| VBOX-RECOVERY-001 | Recovery lineage `B-1 -> M bridge -> B0 -> target` is present and valid. |
| VBOX-DATA-001 | User-data preservation is planned separately from OS reconstruction. |
| VBOX-LEDGER-001 | Ledger gap, non-contiguous entry, or digest mismatch is rejected. |
| VBOX-ARCHIVE-001 | Historical artifact is retrievable by digest from the content-addressed archive. |
| VBOX-TRANS-001 | Retired transitions remain discoverable as knowledge. |
| VBOX-RELEASE-001 | Release missing required artifacts or qualification records fails the release gate. |
| VBOX-VERIFY-001 | `--verify` detects tampering. |
| VBOX-VERIFY-002 | Missing checkpoint is detected by verification. |
| VBOX-VERIFY-003 | Changed managed path is detected by verification. |
| VBOX-VERIFY-ROOT-001 | Root-run service probe fallbacks do not hide tampering. |
| VBOX-UI-001 | Terminal UX helpers are present and wired into install/post-install paths. |
| VBOX-OBS-001 | OpenClaw credentials remain environment-only, redacted, and absent from tasks/logs/reports. |
| VBOX-OBS-002 | Telegram reporter is a no-op until bot token and chat ID are configured. |
| VBOX-SUPPORT-001 | Support policy enforces 20-year margin and at least 40 preserved quarterly releases, with 80 as target. |
| VBOX-ROT-001 | Rotation without custody approval, revocation propagation, or post-rotation verification fails closed. |
| VBOX-RESTORE-001 | A preserved quarterly release can be restored and pass Stage A gates. |

---

## 4. CI check catalog

Existing commands from `reports/ARCHITECTURE_DECISIONS.md`:

```sh
cd evolution-engine
python3 -m unittest discover -s tests
bash test-source-matrix.sh
bash test-post-migration.sh
cd bootstrap-rust && cargo test --offline --locked
```

Proposed CI identifiers:

| CI ID | Check | Evidence |
|---|---|---|
| CI-UNIT | `cd evolution-engine && python3 -m unittest discover -s tests` | `logs/ci/CI-UNIT.json` |
| CI-INV | Invariant checks via `evolution-engine/src/evolution/invariants.py::check_invariants` and `evolution-engine/tests/test_evolution.py::VersionAndSchemeTests` | `logs/ci/CI-INV.json` |
| CI-SRC-MTX | `cd evolution-engine && bash test-source-matrix.sh` | `logs/ci/CI-SRC-MTX.json` |
| CI-POST | `bash test-post-migration.sh` | `logs/ci/CI-POST.json` |
| CI-RUST | `cd bootstrap-rust && cargo test --offline --locked` | `logs/ci/CI-RUST.json` |
| CI-TGT | `tests/test_target.py` | `logs/ci/CI-TGT.json` |
| CI-COMP | `tests/test_components.py` | `logs/ci/CI-COMP.json` |
| CI-VER | `tests/test_post_migration_verify.py` | `logs/ci/CI-VER.json` |
| CI-OPEN | `openclaw/tests/test_openrouter.py` | `logs/ci/CI-OPEN.json` |
| CI-REP | Proposed `openclaw/tests/test_reporter.py` | `logs/ci/CI-REP.json` |
| CI-TRUST | Proposed trust model tests for `evolution-engine/src/trust/model.py` | `logs/ci/CI-TRUST.json` |
| CI-SCHEME | Proposed scheme validation tests for `evolution-engine/src/evolution/scheme.toml` | `logs/ci/CI-SCHEME.json` |
| CI-LEDGER | Proposed ledger tests for `evolution-engine/src/evolution/ledger.py` | `logs/ci/CI-LEDGER.json` |
| CI-REC | Proposed recovery tests for `evolution-engine/src/evolution/recovery.py` | `logs/ci/CI-REC.json` |
| CI-STAGE | Proposed staging tests for `evolution-engine/src/evolution/staging.py` | `logs/ci/CI-STAGE.json` |
| CI-SNAP | Proposed snapshot tests for `evolution-engine/src/evolution/tools/snapshots.py` | `logs/ci/CI-SNAP.json` |
| CI-CHAN | Proposed channel tests for `evolution-engine/src/evolution/tools/channels.py` | `logs/ci/CI-CHAN.json` |
| CI-HOOK | Proposed hook sandbox tests for `evolution-engine/src/evolution/hooks.py` | `logs/ci/CI-HOOK.json` |
| CI-JRN | Proposed journal tests for `evolution-engine/src/evolution/journal_state.py` | `logs/ci/CI-JRN.json` |
| CI-ART | Proposed archive tests for `evolution-engine/src/evolution/artifacts.py` | `logs/ci/CI-ART.json` |
| CI-QUAL | Proposed qualification/release-gate tests for `evolution-engine/src/evolution/qualification.py::release_gate` | `logs/ci/CI-QUAL.json` |
| CI-TRANS | Proposed transition tests for `evolution-engine/src/evolution/transitions.py` | `logs/ci/CI-TRANS.json` |
| CI-BASE | Proposed baseline tests for `evolution-engine/src/evolution/baseline.py` | `logs/ci/CI-BASE.json` |
| CI-TOOL | Proposed tests for `profile/airootfs/usr/local/bin/sunshine-toolsync` | `logs/ci/CI-TOOL.json` |
| CI-UI | Proposed tests for `profile/airootfs/usr/local/lib/sunshine/ui.sh` | `logs/ci/CI-UI.json` |

---

## 5. Traceability matrix: M-01..M-10

| ID | Stage A gate | VBox break/fix test | CI check | Evidence |
|---|---|---|---|---|
| M-01 | SA-03 | VBOX-TARGET-001 | CI-TGT, CI-UNIT | `evolution-engine/src/evolution/target_resolver.py::TargetResolver`; `evidence/target/M-01.json` |
| M-02 | SA-08 | VBOX-LEDGER-001 | CI-LEDGER, CI-INV | `evolution-engine/src/evolution/ledger.py::EvolutionLedger`; `evidence/ledger/M-02.json` |
| M-03 | SA-01, SA-10 | VBOX-BASE-001, VBOX-SUPPORT-001 | CI-BASE, CI-QUAL | `evolution-engine/src/evolution/versions.py`; `reports/quarterly-preservation/` |
| M-04 | SA-00 | VBOX-INV-001 | CI-INV | `evolution-engine/src/evolution/invariants.py::_m04`; `evidence/inventory/M-04.json` |
| M-05 | SA-05 | VBOX-STAGE-001 | CI-STAGE, CI-SRC-MTX | `evolution-engine/src/evolution/staging.py`; `evidence/staging/M-05.json` |
| M-06 | SA-05, SA-06 | VBOX-ROLLBACK-001, VBOX-RECOVERY-001 | CI-REC, CI-STAGE | `evolution-engine/src/evolution/updater.py::EvolutionUpdater.upgrade`; `evidence/recovery/M-06.json` |
| M-07 | SA-08 | VBOX-ARCHIVE-001 | CI-ART | `evolution-engine/src/evolution/artifacts.py::ContentAddressedArchive`; `evidence/archive/M-07.json` |
| M-08 | SA-02 | VBOX-COMPAT-001 | CI-QUAL, CI-SRC-MTX | `evolution-engine/src/evolution/qualification.py::SourceCapabilities.tier`; `evidence/qualification/M-08.json` |
| M-09 | SA-09 | VBOX-VERIFY-001 | CI-VER, CI-POST | `src/engine.py`; `evidence/verify/M-09.json` |
| M-10 | SA-06 | VBOX-DATA-001 | CI-REC | `evolution-engine/src/evolution/recovery.py::DataPreservationPlan`; `evidence/recovery/M-10.json` |

---

## 6. Traceability matrix: AD-01..AD-30

| ID | Stage A gate | VBox break/fix test | CI check | Evidence |
|---|---|---|---|---|
| AD-01 | SA-01 | VBOX-BASE-001 | CI-BASE | `evolution-engine/src/evolution/baseline.py::ARCH_2026_BASELINE`; `evolution-engine/evolution/docs/BASELINE_ARCH_2026.md`; `evidence/stage-a/AD-01.json` |
| AD-02 | SA-01 | VBOX-SCHEME-001 | CI-SCHEME | `evolution-engine/src/evolution/milestones.py::MilestoneRegistry.chain`; `evolution-engine/src/evolution/scheme.toml`; `evidence/stage-a/AD-02.json` |
| AD-03 | SA-03 | VBOX-TARGET-001 | CI-TGT | `evolution-engine/src/evolution/target_resolver.py::TargetResolver`; `src/planner.py`; `evidence/target/AD-03.json` |
| AD-04 | SA-02 | VBOX-COMPAT-001 | CI-SRC-MTX | `evolution-engine/src/evolution/compatibility.py::CompatibilityEngine`; `evolution-engine/src/evolution/inventory.py::from_observed`; `evidence/qualification/AD-04.json` |
| AD-05 | SA-00 | VBOX-INV-001 | CI-INV | `evolution-engine/src/evolution/invariants.py::_m04`; `src/context.py::ExecutionContext`; `evidence/inventory/AD-05.json` |
| AD-06 | SA-04 | VBOX-TRUST-001 | CI-TRUST | `evolution-engine/src/trust/model.py`; `evolution-engine/src/evolution/repository.py`; `evolution-engine/src/evolution/tools/channels.py`; `evidence/trust/AD-06.json` |
| AD-07 | SA-01 | VBOX-SCHEME-001 | CI-SCHEME | `evolution-engine/src/evolution/scheme.toml`; `evolution-engine/src/evolution/scheme.py`; `evidence/stage-a/AD-07.json` |
| AD-08 | SA-04, SA-07 | VBOX-HOOK-001 | CI-HOOK | `src/adapters/runtime.py`; `evolution-engine/src/evolution/hooks.py`; `evidence/hooks/AD-08.json` |
| AD-09 | SA-07 | VBOX-HOOK-001 | CI-HOOK, CI-UNIT | `src/engine.py`; `evolution-engine/src/evolution/hooks.py::HookRunner.validate_command`; `evidence/hooks/AD-09.json` |
| AD-10 | SA-05 | VBOX-STAGE-001 | CI-JRN | `src/context.py::ExecutionContext`; `evolution-engine/src/evolution/journal_state.py`; `evidence/journal/AD-10.json` |
| AD-11 | SA-05 | VBOX-CHECKPOINT-001, VBOX-ROLLBACK-001 | CI-POST | `evolution-engine/src/evolution/updater.py::EvolutionUpdater.upgrade`; `evidence/checkpoints/AD-11.json` |
| AD-12 | SA-05 | VBOX-STAGE-001, VBOX-MATRIX-EXT4-001 | CI-STAGE, CI-SNAP | `evolution-engine/src/evolution/staging.py`; `evolution-engine/src/evolution/tools/snapshots.py`; `evidence/staging/AD-12.json` |
| AD-13 | SA-06 | VBOX-RECOVERY-001 | CI-REC | `evolution-engine/src/evolution/recovery.py::recovery_path`; `RecoveryBridge`; `evidence/recovery/AD-13.json` |
| AD-14 | SA-02 | VBOX-COMPAT-001 | CI-QUAL | `evolution-engine/src/evolution/qualification.py::SourceCapabilities.tier`; `CompatibilityEngine.classify`; `evidence/qualification/AD-14.json` |
| AD-15 | SA-02 | VBOX-MATRIX-BTRFS-001, VBOX-MATRIX-EXT4-001, VBOX-MATRIX-LUKS-001, VBOX-MATRIX-GRUB-001, VBOX-MATRIX-SDBOOT-001, VBOX-MATRIX-NVIDIA-001, VBOX-MATRIX-AUR-001 | CI-SRC-MTX | `evolution-engine/tests/source-matrix.toml`; `evolution-engine/tests/test_source_matrix.py`; `evidence/matrix/AD-15.json` |
| AD-16 | SA-09 | VBOX-VERIFY-001, VBOX-VERIFY-002, VBOX-VERIFY-003 | CI-VER | `src/engine.py`; `tests/test_post_migration_verify.py`; `evolution-engine/src/evolution/tools/sealed_state.py`; `evidence/verify/AD-16.json` |
| AD-17 | SA-08 | VBOX-LEDGER-001 | CI-LEDGER | `evolution-engine/src/evolution/ledger.py::EvolutionLedger`; `evidence/ledger/AD-17.json` |
| AD-18 | SA-03 | VBOX-TRANS-001 | CI-TRANS | `evolution-engine/src/evolution/transitions.py::TransitionRegistry.any_for`; `evidence/transitions/AD-18.json` |
| AD-19 | SA-10 | VBOX-RELEASE-001 | CI-QUAL | `evolution-engine/src/evolution/qualification.py::release_gate`; `evidence/release/AD-19.json` |
| AD-20 | SA-08 | VBOX-ARCHIVE-001 | CI-ART | `evolution-engine/src/evolution/artifacts.py::ContentAddressedArchive`; `evidence/archive/AD-20.json` |
| AD-21 | SA-06 | VBOX-DATA-001 | CI-REC | `evolution-engine/src/evolution/recovery.py::DataPreservationPlan`; `evidence/recovery/AD-21.json` |
| AD-22 | SA-03 | VBOX-TARGET-001 | CI-TGT | `src/target.py`; `tests/test_target.py`; `evidence/target/AD-22.json` |
| AD-23 | SA-03 | VBOX-COMP-001 | CI-COMP | `evolution-engine/src/components/`; `src/target.py`; `tests/test_components.py`; `evidence/components/AD-23.json` |
| AD-24 | SA-03 | VBOX-PROFILE-001 | CI-COMP | `src/target.py`; `tests/test_components.py`; `evolution-engine/src/evolution/tools/service_supervision.py`; `evidence/components/AD-24.json` |
| AD-25 | SA-09 | VBOX-VERIFY-ROOT-001 | CI-VER | `src/verify.py`; `tests/test_post_migration_verify.py`; `evidence/verify/AD-25.json` |
| AD-26 | SA-04 | VBOX-TOOLSYNC-001 | CI-TOOL | `profile/airootfs/usr/local/bin/sunshine-toolsync`; `reports/`; `evidence/tools/AD-26.json` |
| AD-27 | SA-07 | VBOX-UI-001 | CI-UI | `profile/airootfs/usr/local/lib/sunshine/ui.sh`; `reports/`; `evidence/ui/AD-27.json` |
| AD-28 | SA-04 | VBOX-OBS-001 | CI-OPEN | `openclaw/backends.py::OpenRouterBackend`; `openclaw/tests/test_openrouter.py`; `evidence/observers/AD-28.json` |
| AD-29 | SA-10 | VBOX-OBS-002 | CI-REP | `openclaw/reporter.py::TelegramReporter`; `openclaw/cli.py::configured_reporters`; `evidence/observers/AD-29.json` |
| AD-30 | SA-10 | VBOX-SUPPORT-001, VBOX-RESTORE-001 | CI-QUAL, CI-TRANS | `evolution-engine/src/evolution/compatibility.py::SupportPolicy`; `evolution-engine/src/evolution/versions.py`; `evolution-engine/src/evolution/transitions.py`; `reports/quarterly-preservation/`; `evidence/preservation/AD-30.json` |

---

## 7. Cross-distro / cross-shape VBox matrix

Required shapes: btrfs, ext4, LUKS, GRUB, systemd-boot, NVIDIA, AUR.

| Shape | Stage A gates | Break/fix test | Break condition | Fix / pass condition | CI checks | Evidence |
|---|---|---|---|---|---|---|
| btrfs | SA-05, SA-09 | VBOX-MATRIX-BTRFS-001 | Snapshot/subvolume staging unavailable or rollback path broken. | Staged root migration or equivalent recovery completes; verify passes. | CI-SRC-MTX, CI-STAGE | `logs/vbox/VBOX-MATRIX-BTRFS-001.log`; `evidence/vbox/VBOX-MATRIX-BTRFS-001.json` |
| ext4 | SA-05, SA-06 | VBOX-MATRIX-EXT4-001 | No native staged snapshot path; in-place recovery contract missing. | In-place recovery preserves data and reaches target. | CI-SRC-MTX, CI-REC | `logs/vbox/VBOX-MATRIX-EXT4-001.log`; `evidence/vbox/VBOX-MATRIX-EXT4-001.json` |
| LUKS | SA-05, SA-06 | VBOX-MATRIX-LUKS-001 | Encrypted root cannot be unlocked or recovery lineage is absent. | Recovery lineage and data preservation plan complete; target boots. | CI-SRC-MTX, CI-SNAP | `logs/vbox/VBOX-MATRIX-LUKS-001.log`; `evidence/vbox/VBOX-MATRIX-LUKS-001.json` |
| GRUB | SA-05, SA-09 | VBOX-MATRIX-GRUB-001 | Bootloader entry missing, stale, or unverifiable. | GRUB entry regenerated and verified; tamper checks pass. | CI-POST, CI-VER | `logs/vbox/VBOX-MATRIX-GRUB-001.log`; `evidence/vbox/VBOX-MATRIX-GRUB-001.json` |
| systemd-boot | SA-05, SA-09 | VBOX-MATRIX-SDBOOT-001 | Loader entry missing or not aligned with target state. | systemd-boot entry regenerated and verified. | CI-POST, CI-VER | `logs/vbox/VBOX-MATRIX-SDBOOT-001.log`; `evidence/vbox/VBOX-MATRIX-SDBOOT-001.json` |
| NVIDIA | SA-02, SA-07 | VBOX-MATRIX-NVIDIA-001 | NVIDIA/DKMS hook fails or module load is not verified. | Hook rebuild completes; module presence and boot state verified. | CI-SRC-MTX, CI-HOOK | `logs/vbox/VBOX-MATRIX-NVIDIA-001.log`; `evidence/vbox/VBOX-MATRIX-NVIDIA-001.json` |
| AUR | SA-02, SA-03 | VBOX-MATRIX-AUR-001 | Mixed AUR provenance is ambiguous or unsupported. | Qualification tier and target resolution account for AUR shape. | CI-SRC-MTX, CI-QUAL | `logs/vbox/VBOX-MATRIX-AUR-001.log`; `evidence/vbox/VBOX-MATRIX-AUR-001.json` |

---

## 8. Rotation custody gates

Rotation applies to trust anchors, signing identities, channel metadata, tool-release acceptance, and credential references. No secret values are recorded.

| Gate | Custody object | Pass criteria | Fail-closed link | Evidence |
|---|---|---|---|---|
| RC-01 | Rotation scope declaration | Rotation request lists artifact IDs, channels, signers, affected releases, and reason without secret values. | AD-06, AD-17 | `evidence/custody/RC-01.json` |
| RC-02 | Dual-control approval | Two authorized custodians approve; approval record is signed and journaled. | AD-06, AD-08 | `evidence/custody/RC-02.json` |
| RC-03 | Pre-rotation state check | Ledger is contiguous, checkpoints exist, current artifacts verify, and no active migration is mid-crossing. | M-02, M-06, AD-11 | `evidence/custody/RC-03.json` |
| RC-04 | Shadow acceptance | New signer/channel is accepted in shadow mode while old signer remains valid until propagation completes. | AD-06, AD-26 | `evidence/custody/RC-04.json` |
| RC-05 | Revocation propagation | Revoked signers/channels…
