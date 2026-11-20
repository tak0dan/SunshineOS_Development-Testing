# Order 1 — VBox guest attack-surface threat sweep

- Status: done (attempts: 1)
- Agent role: researcher (nvidia/nemotron-3.5-lightning:free)
- Note: first delegation (ling-3.2-flash) returned tool-call markup instead of the requested table; retried with a stricter prompt and the supplied key after a 429.
- Source: OpenClaw / OpenRouter delegation from sibling session orders, 2026-11-20

---

| surface | vulnerability class | concrete SunshineOS test step | expected fail-closed signal | evidence artifact path |
|---|---|---|---|---|
| guest additions | guest auth bypass | `src/engine.py --verify` guest session authentication probe | `status failed`; probe denied on guest account password mismatch | `reports/screenshots/vm-evolution-validation-2026-11-20.png` |
| VMSVGA/3D | driver state anomaly | `src/milestone_cli.py --milestones` under UEFI/OVMF hyprland desktop profile | `errors []`; no unexpected GPU/3D driver modules in artifact inventory | `reports/screenshots/vm-evolution-validation-2026-11-20.png` |
| VNC | session eavesdropping | `--apply --decide desktop-profile=hyprland` with VNC console attachment | `journal_status completed`; no plaintext credentials in journal | `reports/screenshots/vm-evolution-validation-2026-11-20.png` |
| serial TCP | command injection | `vm_updater_check.py` rollback injection test | `rollback_ok true`; `journal_state RolledBack`; `restore_calls ["checkpoint-ref"]` | `reports/screenshots/vm-evolution-validation-2026-11-20.png` |
| NAT SSH | port conflict escalation | `VBoxManage guestcontrol` host-to-guest copy workflow (tar extraction, copyto, extraction) | `status success`; `errors []`; full 64-char journal id validated | `reports/VM_EVOLUTION_VALIDATION.md` |
| shared folders/clipboard | mount escalation | extracted module inventory check (`artifacts.py`, `baseline.py`, `compatibility.py`, `hooks.py`, `invariants.py`, `repository.py`, `updater.py`, `tools/`) | all artifacts present; no unauthorized mounts or clipboard agents detected | `reports/screenshots/vm-evolution-validation-2026-11-20.png` |
| snapshots | rollback gap | checkpoint tamper: move `migration/checkpoints` away, then restore | `passed False`; only failing capability: `recovery-checkpoints`; after restore: `passed True`, `reports 18` | `reports/VM_EVOLUTION_VALIDATION.md` |
| guestcontrol | command injection | `VBoxManage guestcontrol` workflow as documented in host procedure | `status success`; `changed false` on consecutive applies; journal id validated | `reports/screenshots/vm-evolution-validation-2026-11-20.png` |
