# VirtualBox audit attack-surface break plan — 2026-11-21

- Source: OpenClaw task `vbox-breakplan`, researcher role, 1 attempt.
- Scope: disposable snapshots of `SunshineOS-Audit`; no credential values recorded.
- Current baseline after Stage A hardening: 163 Python engine tests, 7 Rust tests (the agent result below cites the earlier 161/5 baseline).

---

## Method (applies to every attempt)

- Disposable snapshot only: `VBoxManage snapshot "$VM" take asw-base`, run attempt, capture, `restore`. Never on the live guest holding production-pinned trust (`packages/sunshine-update/` trust material, `key_rotations: []`), and never against the real OLD root — the rotation blocker in `ROTATION.md` stands; use ephemeral OLD/NEW keys per `test-rotation.sh`.
- No credential values in commands or logs: authenticate via env/stdin (`--password-stdin`), scrub captures. The live sudo note in `reports/VM_EVOLUTION_VALIDATION.md` stays value-free.
- Baseline before each attempt: `src/milestone_cli.py --from 0 --upgrade-to 0.9 --dry-run` (`ok: true`, chain `["0.9"]`, 64-char journal id), `src/engine.py --apply --decide desktop-profile=hyprland` + `--verify` (`passed True`, `reports 18`), `vm_updater_check.py` (`rollback_ok true`, `guard_no_rollback true`, `full_digest true`), release digest `c248e20f…` for `sunshine-update-0.9.0-1`.

## Priority (likelihood of hiding a migration/trust failure)

| # | Surface | Hiding mechanism |
|---|---|---|
| 1 | Snapshots | Rollback resurrects pre-tamper state; fakes `changed false` convergence; erases journal/checkpoint evidence |
| 2 | guestcontrol | Artifact-injection channel; patched engine or mid-apply mutation fakes verify |
| 3 | Shared folders | Overlay of state root, `migration/checkpoints`, `/etc/sunshine/trust/receipt-home`, or the dedicated GPG keyring |
| 4 | NAT SSH | Remote kill mid-apply leaves partial journal; concurrent apply bypasses the decision gate |
| 5 | Guest additions | Clock skew breaks journal ordering; fake guest properties; root-level module can hide files |
| 6 | VMSVGA/3D | Screenshot is the published evidence; stale/corrupt framebuffer shows success over a failed verify |
| 7 | VNC | Console keystrokes repair state outside the journal (sudo accepts the account's own password → effective root) |
| 8 | Serial TCP | Secret leak + unjournaled console shell |
| 9 | Clipboard / DnD | Exfiltrates digests/fingerprints; injects files outside the journal |

## Per-surface break attempts

**1. Snapshots** — Attempt: apply → `changed false`; snapshot S1; move `migration/checkpoints` away; `--verify` (expect `passed False`, only `recovery-checkpoints`); restore S1; `--verify` again. Variant: snapshot mid-apply, restore, re-apply. Fail-closed: convergence must not come from file presence alone; journal generation/64-char id must be checked against a host-side or receipt copy; restore must surface as generation rollback or verify failure, never silent `passed True`. Evidence: `evidence/vm-attack-surface/01-snapshots/{showvminfo.txt,snapshot-list.txt,journal-before.json,journal-after-restore.json,verify.json,state-root-digest.txt,host-journal-copy.json}`.

**2. guestcontrol** — Attempt: rebuild the tarball with `evolution-engine/src/engine.py` patched to force `passed True` / skip the checkpoint guard; `copyto` over `/tmp/eve/evolution-engine`; run CLI. Also a second `guestcontrol execute` touching `/tmp/eve-state` during apply. Fail-closed: source digest must match the pinned release digest; mismatch → refusal or recorded rejection; forced-pass must not yield `reports 18` with real probe output; guard still fires. Evidence: `02-guestcontrol/{tarball-sha256-host.txt,tarball-sha256-guest.txt,copyto-log.txt,engine-diff.txt,cli-output.txt,journal.json,verify.json,vm_updater_check.txt}`.

**3. Shared folders** — Attempt: `sharedfolder add` over `/tmp/eve-state`; over `/etc/sunshine/trust/receipt-home` with a forged receipt; over the GPG home with a substitute keyring; run apply/verify. Fail-closed: engine refuses or records `vboxsf` state root; receipt check fails closed (receipt-home must contain the policy fingerprint); verification with per-invocation `GNUPGHOME` + dedicated keyring requires `VALIDSIG` naming the declared fingerprint — substitute keyring yields "No public key", not success. Evidence: `03-shared-folders/{showvminfo.txt,guest-mount.txt,apply-stderr.txt,verify.json,receipt-check.log,gpg-verify.log,journal.json}`.

**4. NAT SSH** — Attempt: `modifyvm --natpf1 ssh,tcp,,2222,,22`; during apply, kill the engine PID or start a concurrent apply with a different `--decide` value. Fail-closed: interrupted apply leaves `journal_state ≠ completed`; verify fails; next apply converges from checkpoint (`restore_calls ["checkpoint-ref"]`); concurrent apply rejected by single-writer lock; decision change requires a new journaled decision. Evidence: `04-nat-ssh/{natpf.txt,session-log.txt (no credentials),journal.json,verify.json,concurrent-stderr.txt,ps-tree.txt}`.

**5. Guest additions** — Attempt: skew guest clock ±hours; set fake guestproperty `migration/completed`; run apply/verify. Fail-closed: journal timestamps monotonic and cross-checked; chain ordered by generation, not wall clock; verify ignores guest properties; skew → precondition failure, not silent success. Evidence: `05-guest-additions/{VBoxService-version.txt,guestproperty-list.txt,time-delta.txt,journal-timestamps.txt,verify.json}`.

**6. VMSVGA/3D** — Attempt: `modifyvm --accelerate3d on --vram 128`; run a deliberately failing apply (tamper checkpoints); capture screenshot; diff against terminal transcript. Fail-closed: PNG is never the trust anchor; CLI exit code + journal + verify are authoritative; pixel/journal mismatch must be reported as evidence failure. Evidence: `06-vmsvga-3d/{modifyvm.log,screenshot.png,transcript.txt,journal.json,verify.json,pixel-vs-journal-diff.txt}`.

**7. VNC** — Attempt: `modifyvm --vnc on --vncport 5900 --vncpassword "$VNC_PASS"` (value never logged); capture console; inject keystrokes to manually restore `migration/checkpoints` after tamper; run verify. Fail-closed: VNC off in the audit VM config by default; manual repair without a journal entry must not yield `passed True` — state is bound to journal/receipt digest, not file presence. Evidence: `07-vnc/{vnc-config.txt (no password),capture.png,journal.json,verify.json,checkpoint-digest.txt}`.

**8. Serial TCP** — Attempt: `modifyvm --uart1 0x3F8 4 --uartmode1 tcpserver 5001`; capture output during apply; attempt to drive a getty shell. Fail-closed: no secret material on serial (grep scan shows zero matches, values never recorded); unjournaled console commands treated like VNC; engine logs to journal files only. Evidence: `08-serial-tcp/{capture.log,secret-scan.txt (counts only),journal.json,verify.json}`.

**9. Clipboard / DnD** — Attempt: `modifyvm --clipboard bidirectional --draganddrop hosttoguest`; drag a forged checkpoints/receipt file in; read clipboard after an apply that prints the journal id. Fail-closed: DnD/clipboard never in the trust path; forged file rejected by digest; clipboard may carry public digests only and authorizes nothing. Evidence: `09-clipboard-dnd/{clipboard.txt,dnd-files.txt,journal.json,verify.json,trust-dir-listing.txt}`.

## Invariants every capture must assert

- 64-char journal id; `full_digest true`; `journal_state completed` only after all probes; steady-state convergence = three consecutive applies, first may change, later no-ops (`evolution-engine/tests/test_cli.py`).
- Tamper → `passed False` with only `recovery-checkpoints` failing; restore → `passed True`, `reports 18`; rollback injection → `rollback_ok true`, `restore_calls ["checkpoint-ref"]`.
- GPG: per-invocation `GNUPGHOME`, dedicated keyring only, `VALIDSIG` names the declared fingerprint (Rust and Python verifiers, per `reports/STAGE-A-DEPLOYMENT-2026-11-20.md`).

## Close-out

After each attempt restore the snapshot and re-run the baseline set (161 Python tests, 5 Rust tests, `test-stage-a.sh`, `test-rotation.sh`) to prove no residual trust damage. File captures under `evidence/vm-attack-surface/<nn>-<surface>/` and link them from a new `reports/VM-ATTACK-SURFACE-<date>.md`. Any resulting fix must not fabricate the OLD-signed rotation record.