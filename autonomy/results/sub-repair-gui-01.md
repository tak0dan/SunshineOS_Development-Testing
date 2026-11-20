# Sunshine Toolbox repair integration

- Agent: sub-repair-gui
- Model: nvidia/nemotron-3.5-lightning:free
- Completed: 2026-11-21 00:15

---

# Sunshine Toolbox Repair Engine Exposure Design
*Based on `reports/USER_MIGRATION_MANDATE_2026-11-21.md` invariants and `/home/tak_0/sunshine-toolbox` (Electron/Angular fork)*

---

## 1. Module Structure
Engine exposed via dedicated renderer process, isolated from main UI unless polkit-verified. All paths rooted at `app/repair-engine/`.

```
sunshine-toolbox/
├── src/
│   └── repair-engine/
│       ├── core/                    # Immutable state tree, journal schema (M-09)
│       │   ├── state-inventory.ts   # Normalized system snapshot (M-04)
│       │   ├── target-resolver.ts   # Evolutionary ledger navigator (M-01, M-03)
│       │   ├── transition-catalog.ts # Semantic rules per mandate §3 (M-07)
│       │   ├── migration-planner.ts # Dependency graph, risk scoring
│       │   ├── artifact-manager.ts  # Hash/verify/signature check (M-08, M-10)
│       │   ├── migration-executor.ts# Adaptors, staging area, compensating ops (M-05, M-06)
│       │   └── validation-recovery.ts# Verification loops, rollback triggers
│       ├── ui/
│       │   ├── progress/
│       │   │   └── progress-indicator.tsx  # %/step journal, M-09 repeatable
│       │   ├── actions/
│       │   │   └── polkit-requester.tsx
│       │   └── confirmations/
│       │       └── fail-closed-dialog.tsx
│       └── index.ts                   # Engine bootstrap, exports typed API
└── electron/main/                     # Only loads repair-engine on explicit user opt-in
```

**Key invariants enforced at module boundary:**
- M-01: Target-state driven — resolver never emits “next release” steps; always resolves toward `TP040`-style profile
- M-03: Migration logic versioned independently — engine publishes `ME12`-style identifier, decoupled from OS release `E040`
- M-06: Recoverable — every executor operation returns a `journal_id`; UI must display “Compensating action available” on failure
- M-10: User data / OS reconstruction separate — artifact manager never auto-migrates personal configs without explicit map

---

## 2. Task Progress Exposure
Progress is **event-driven**, **percentage-based**, and **journal-anchored**. No imperatival “step X of Y” polling.

| Feature | Implementation | Mandate Reference |
|---------|----------------|-------------------|
| Step index | `progress.currentStep` incremented only after `validation-recovery` passes | M-05: staged whenever technically possible |
| Percentage | `progress.percent` = `(completedOps / totalOps) * 100`, rounded to integer | M-09: repeatable — re-running discovery must not duplicate |
| Journal ID | Each op emits `journal_id: uuid`; stored in `~/.sunshineos/repair-journal/` | M-06: recoverable; M-07: historical artifacts archived |
| Interruption | On process kill, UI restores last `journal_id`; offers “Resume from journal” | M-09: re-running must not produce uncontrolled duplication |
| Fail state | `progress.error` contains `op_id`, `hash`, and “recover?” CTA | M-06: operations must be recoverable |

Progress component subscribes to `engine/events/progress`; renderer displays:
```
[===               ] 42% • Step 7/12 • Journal: j-3f9a1...
```
Clicking “Details” reveals hash, dependency graph, and compensating action preview.

---

## 3. Polkit Actions
All privilege escalation funneled through **two dedicated actions**. No ad-hoc `sudo` in renderer.

| Action ID | Description | Auth Type | UI Trigger |
|-----------|-------------|-----------|------------|
| `sunshineos.repair.engine.modify` | Executes migration-executor ops: package install, service enable, fstab edit, initramfs regeneration | `pkexec` with timeout 300s | Any `migration-executor` op that mutates filesystem/services |
| `sunshineos.repair.engine.restore` | Triggers validation-recovery: rollback, journal replay, compensating ops | `pkexec` with timeout 600s | Error state CTA, manual rollback initiation |

**Action definition** (placed in `sunshine-toolbox/electron/main/polkit-actions.d/`, loaded at startup):
```json
{
  "id": "sunshineos.repair.engine.modify",
  "description": "Apply staged migration operations to system state",
  "vendor": "SunshineOS",
  "allowed_users": ["sunshine-user"],
  "some_restrictions": []
}
```
```json
{
  "id": "sunshineos.repair.engine.restore",
  "description": "Recover system to last validated state via journal",
  "vendor": "SunshineOS",
  "allowed_users": ["sunshine-user"],
  "some_restrictions": []
}
```
**Renderer never calls `child_process.exec`** — always routes through `electron.ipcMain` handler that validates `journal_id` and op-type against allowlist before invoking `pkexec`.

---

## 4. Fail-Closed Confirmations
Every high-impact operation passes through a **fail-closed dialog** that defaults to **safe abort**. Branding: SunshineOS sun-icon, teal-orange palette, no system branding.

### Dialog Flow (TypeScript/Angular component `fail-closed-dialog.tsx`)

1. **Title**: “System modification requires confirmation”
2. **Primary CTA**: “Continue” (destructive, labeled in **orange**)
3. **Secondary CTA**: “Cancel” (safe, labeled in **teal**)
4. **Footer text**: “This action cannot be undone automatically. A journal entry will be created. See details.”
5. **Conditional risk list** (populated from `operation.risk assessment`):
   - “Will modify `/etc/fstab`”
   - “Will regenerate `initramfs`”
   - “Will replace 3 packages”
6. **Hash verification**: Shows `SHA-256 of staged artifacts`; user must verify against expected if known.

```tsx
<dialog role="alert" class="sunshine-fail-closed">
  <h2>System modification requires confirmation</h2>
  <p>This action will modify system state. A journal entry <code>j-{id}</code> will be created for recovery.</p>
  <div class="risk-list">
    <ul>
      <li>Modify /etc/fstab</li>
      <li>Regenerate initramfs</li>
      <li>Replace 3 packages</li>
    </ul>
  </div>
  <div class="hash-verification">
    <p>Staged artifact hash: <code>e3b0c44298fc1c149afbf4c8996fb924</code></p>
    <p>Verify against known good if available.</p>
  </div>
  <footer>
    <button class="btn-cancel">Cancel</button>
    <button class="btn-continue">Continue</button>
  </footer>
</dialog>
```

**Behavior:**
- “Cancel” closes dialog, emits `progress.event = "aborted"` → UI logs “Repair engine: operation aborted by user” (M-09 repeatable)
- “Continue” validates polkit auth, dispatches to `migration-executor`, starts progress stream
- If auth fails or executor throws: dialog re-presents “Recovery available from journal `j-{id}`” — primary CTA “Restore”, secondary “Exit”
- **Default**: dialog closes on escape key → abort (fail-closed)

---

## 5. Branding Enforcement
- All strings, colors, icons sourced from `sunshine-toolbox/src/themes/sunshineos/`
- No references to parent project, Electron, or Angular in user-facing text
- Font: `SunshineOS Sans` (defined in `src/themes/fonts.ts`)
- Color palette variables:
  ```css
  :root {
    --sun-primary: #ff6b35;    /* orange — CTA actions */
    --sun-secondary: #1976d2;  /* teal — secondary actions */
    --sun-bg: #fafafa;
    --sun-on-bg: #212121;
    --sun-warning: #ffb300;
  }
  ```
- Component class prefix: `sun-` (e.g., `sun-progress-bar`, `sun-dialog`, `sun-polkit-wrapper`)
- Any third-party logo (e.g., polkit) must be replaced with SunshineOS sun-icon (`/usr/share/icons/sunshineos/sun-256.svg`)

---

## 6. Mandate-Aligned Initialization
On first launch, engine boots with:
1. **Inventory scan** → creates `~/.sunshineos/system-snapshot.json` (M-04: actual installation authoritative)
2. **Target resolver** → loads `TP040` profile from `evolution-engine/ledger/`, cross-references `B0-2026` baseline
3. **Progress panel** mounts showing “Discovery: 0% — scanning system state”
4. **Polkit prompt** for `sunshineos.repair.engine.modify` if user attempts manual repair

All bootstrap logic lives at `sunshine-toolbox/src/repair-engine/core/boot.ts`; exits gracefully if invariants fail (M-02: evolution history immutable — if ledger hash mismatch, UI shows “Unsupported historical state” and offers “Contact maintainer” rather than proceeding).

---
*Design cites exact paths: `reports/USER_MIGRATION_MANDATE_2026-11-21.md`, `/home/tak_0/sunshine-toolbox`, `evolution-engine/`. All architectural decisions grounded in mandate invariants M-01 through M-10.*
