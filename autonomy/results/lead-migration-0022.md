# lead-migration / configuration reconciliation / Arch 2015 sysvinit

- Agent: lead-migration
- Model: baidu/ernie-5.5-flash-preview:free
- Parent directive: none
- Completed: 2026-11-21 01:02

---

# Wave 1 Deepening — Arch 2015 sysvinit Configuration Reconciliation

## 1. Document control

- **Repository root**: `/home/tak_0/sunshineos-audit/SunshineOS_Development-Testing`
- **Context files**:
  - `reports/USER_MIGRATION_MANDATE_2026-11-21.md`
  - `reports/ARCHITECTURE_DECISIONS.md`
- **Deliverable scope**: Wave 1 catalogue, schema, resolver algorithm, directory layout, test IDs, and evidence paths for reconciling Arch 2015 sysvinit-era configuration into SunshineOS target state.
- **Source baseline**: `B-1-2015` — Arch 2015 recovery anchor.
- **Target profile**: `TP040` — resolved SunshineOS desired state.
- **Inventory schema**: `INV7`.
- **Transition catalog**: `TC18`.
- **Migration engine**: `ME12`.
- **Secret policy**: No passwords, tokens, keys, or credential material are included. Secret-bearing files are referenced by path only.

All repository paths below are relative to:

```text
/home/tak_0/sunshineos-audit/SunshineOS_Development-Testing
```

Paths beginning with `/etc/`, `/boot/`, or `/var/` refer to the observed target system root, not the repository.

---

## 2. Architectural invariants applied

This Wave 1 deliverable follows the migration invariants from `reports/USER_MIGRATION_MANDATE_2026-11-21.md`.

| ID | Invariant | Application to Arch 2015 sysvinit reconciliation |
|---|---|---|
| M-01 | Migration is target-state driven | Reconciliation resolves toward `TP040`, not toward “whatever Arch 2015 did”. |
| M-02 | Evolution history is immutable | Catalogue entries and transition definitions are versioned and hash-addressed. |
| M-03 | Migration intelligence is versioned independently | Resolver logic is `ME12`; catalogue is `TC18`; inventory is `INV7`. |
| M-04 | The actual installation is authoritative | Observed files under `/etc/`, `/boot/`, and `/var/` determine the inventory. |
| M-05 | Migrations are staged whenever technically possible | Configuration changes are staged under a migration plan directory before commit. |
| M-06 | Migration operations must be recoverable | Every mutation has a snapshot and compensating restore path. |
| M-07 | Historical artifacts are archived | Original Arch 2015 files are archived before transformation. |
| M-08 | Migration support is qualified, not assumed | A source state is supported only after tests and evidence exist. |
| M-09 | Migration must be repeatable | Re-running discovery, planning, or interrupted execution must be idempotent. |
| M-10 | User data and OS reconstruction are separate | User identity, home data, and local content are not blindly rewritten. |

---

## 3. Capability probes

The resolver must not assume that “Arch 2015” means a pure sysvinit system. It must probe capabilities and reconcile accordingly.

| Probe ID | Probe path or capability | Meaning | Resolver use |
|---|---|---|---|
| CAP-001 | `/etc/inittab` | sysvinit configuration is present. | Parse runlevels and init actions. |
| CAP-002 | `/etc/rc.d/` | Arch-style service script directory exists. | Inventory service scripts without executing them. |
| CAP-003 | `/etc/conf.d/` | Service configuration fragments exist. | Parse key/value configuration. |
| CAP-004 | `/etc/rc.conf` | Legacy Arch aggregate configuration may exist. | Parse known legacy keys; quarantine unknown keys. |
| CAP-005 | `/run/systemd/system` | systemd is active or partially active. | Detect hybrid init state and reconcile conflicts. |
| CAP-006 | `/usr/bin/systemctl` | systemd control binary exists. | Determine whether target mapping should use systemd units. |
| CAP-007 | `/etc/pacman.conf` | pacman configuration exists. | Reconcile package ecosystem metadata without executing package changes. |
| CAP-008 | `/etc/mkinitcpio.conf` | initramfs recipe exists. | Reconcile initramfs hooks and modules. |
| CAP-009 | `/etc/fstab` | Static filesystem table exists. | Parse, validate, and stage mount changes. |
| CAP-010 | `/etc/default/grub` or `/etc/syslinux.cfg` | Bootloader configuration exists. | Reconcile bootloader defaults without rewriting generated boot entries blindly. |

---

## 4. Wave 1 catalogue

Each catalogue row is materialized as:

```text
evolution-engine/catalogs/arch-2015-sysvinit/entries/<ID>.yaml
```

The catalogue manifest is:

```text
evolution-engine/catalogs/arch-2015-sysvinit/manifest.yaml
```

### 4.1 Boot, init, and runlevel configuration

| ID | Observed path | Class | Reconciliation semantics | Test ID |
|---|---|---|---|---|
| CFG-2015-001 | `/etc/inittab` | boot/init | Parse `initdefault`, runlevels, `sysinit`, `single`, `multi`, `shutdown`, and respawn actions. Map to `TP040` init model. Preserve unknown directives as quarantined items. | TEST-ARCH2015-SYSV-001 |
| CFG-2015-002 | `/etc/rc.conf` | legacy aggregate | Parse known legacy keys such as `HOSTNAME`, `MODULES`, `DAEMONS`, `INTERFACES`, `LOCALE`, `TIMEZONE`, `KEYMAP`, `HARDWARECLOCK`. Treat as historical input, not authoritative target state. | TEST-ARCH2015-SYSV-002 |
| CFG-2015-003 | `/etc/rc.sysinit` | boot script | Extract early-boot operations. Convert deterministic operations into target boot hooks or validation requirements. Do not execute the script during migration. | TEST-ARCH2015-SYSV-003 |
| CFG-2015-004 | `/etc/rc.single` | runlevel script | Reconcile single-user/rescue semantics. Map to target rescue or maintenance mode. | TEST-ARCH2015-SYSV-004 |
| CFG-2015-005 | `/etc/rc.multi` | runlevel script | Reconcile multi-user boot semantics. Extract service startup expectations and map to target service enablement. | TEST-ARCH2015-SYSV-005 |
| CFG-2015-006 | `/etc/rc.local` | user local hook | Preserve as optional local extension. Do not auto-execute. Stage as a user-controlled hook with explicit validation. | TEST-ARCH2015-SYSV-006 |
| CFG-2015-007 | `/etc/rc.shutdown` | shutdown script | Reconcile shutdown ordering and service stop expectations. Do not execute during migration. | TEST-ARCH2015-SYSV-007 |

### 4.2 Service definitions and service configuration

| ID | Observed path | Class | Reconciliation semantics | Test ID |
|---|---|---|---|---|
| CFG-2015-008 | `/etc/rc.d/` | service definitions | Inventory executable service scripts. Hash each file. Map each service to a target service adapter or unit. Never execute scripts during discovery. | TEST-ARCH2015-SYSV-008 |
| CFG-2015-009 | `/etc/conf.d/` | service configuration | Parse shell-style key/value fragments. Preserve unknown keys. Map known keys to target environment or service configuration. | TEST-ARCH2015-SYSV-009 |
| CFG-2015-010 | `/etc/rc.d/functions` | runtime library | Treat as a runtime helper library. Archive and hash. Do not source or execute during migration. | TEST-ARCH2015-SYSV-010 |
| CFG-2015-011 | `/etc/default/` | generic defaults | Inventory generic default files. Reconcile only when a target mapping exists. Preserve unknown files as archived user/system extensions. | TEST-ARCH2015-SYSV-011 |

### 4.3 Storage, initramfs, and boot image configuration

| ID | Observed path | Class | Reconciliation semantics | Test ID |
|---|---|---|---|---|
| CFG-2015-012 | `/etc/fstab` | storage | Parse mounts, options, dump/pass fields. Validate syntax and target compatibility. Stage changes; require validation before commit. | TEST-ARCH2015-SYSV-012 |
| CFG-2015-013 | `/etc/crypttab` | storage/security | Inventory encrypted device mappings without collecting key material. Preserve only non-secret metadata such as device names and keyfile paths when safe. | TEST-ARCH2015-SYSV-013 |
| CFG-2015-014 | `/etc/mkinitcpio.conf` | initramfs | Reconcile hooks, modules, binaries, and compression settings. Rebuild initramfs only in staged target environment. | TEST-ARCH2015-SYSV-014 |
| CFG-2015-015 | `/etc/mkinitcpio.d/` | initramfs presets | Inventory preset files. Reconcile preset names and options without executing generation in the live system. | TEST-ARCH2015-SYSV-015 |
| CFG-2015-016 | `/etc/default/grub` | bootloader | Reconcile bootloader defaults. Do not blindly rewrite generated configuration. Mark generated files as derived artifacts. | TEST-ARCH2015-SYSV-016 |
| CFG-2015-017 | `/boot/grub/grub.cfg` | generated boot config | Treat as generated. Validate presence and provenance. Regenerate only through target-approved tooling. | TEST-ARCH2015-SYSV-017 |
| CFG-2015-018 | `/etc/syslinux.cfg` | bootloader | Reconcile if syslinux is present. Preserve kernel/initrd paths and menu semantics where compatible. | TEST-ARCH2015-SYSV-018 |
| CFG-2015-019 | `/etc/loader/entries/` | bootloader entries | Inventory boot entries if present. Reconcile entry names, kernel paths, and initrd paths. | TEST-ARCH2015-SYSV-019 |

### 4.4 Kernel, modules, and system tuning

| ID | Observed path | Class | Reconciliation semantics | Test ID |
|---|---|---|---|---|
| CFG-2015-020 | `/etc/modprobe.d/` | kernel/module options | Parse module option fragments. Preserve unknown options. Map to target module configuration. | TEST-ARCH2015-SYSV-020 |
| CFG-2015-021 | `/etc/modules-load.d/` | kernel/module loading | Parse module load lists. Reconcile with target module loading mechanism. | TEST-ARCH2015-SYSV-021 |
| CFG-2015-022 | `/etc/sysctl.d/` | kernel tuning | Parse sysctl fragments. Validate key names and value types. Stage changes. | TEST-ARCH2015-SYSV-022 |

### 4.5 Identity, locale, time, and network configuration

| ID | Observed path | Class | Reconciliation semantics | Test ID |
|---|---|---|---|---|
| CFG-2015-023 | `/etc/hostname` | identity | Reconcile hostname. If legacy `rc.conf` also defines hostname, resolve conflict using target profile and observed authority. | TEST-ARCH2015-SYSV-023 |
| CFG-2015-024 | `/etc/hosts` | network/name resolution | Preserve static host entries. Validate syntax. Do not overwrite without explicit plan. | TEST-ARCH2015-SYSV-024 |
| CFG-2015-025 | `/etc/resolv.conf` | network/resolver | Detect regular file versus symlink. Preserve valid resolver configuration. Stage changes carefully. | TEST-ARCH2015-SYSV-025 |
| CFG-2015-026 | `/etc/locale.conf` | localization | Reconcile locale settings. Validate locale availability in target environment. | TEST-ARCH2015-SYSV-026 |
| CFG-2015-027 | `/etc/vconsole.conf` | localization/console | Reconcile console font, keymap, and related settings. | TEST-ARCH2015-SYSV-027 |
| CFG-2015-028 | `/etc/timezone` | time | Reconcile timezone. Validate against target timezone database. | TEST-ARCH2015-SYSV-028 |
| CFG-2015-029 | `/etc/adjtime` | time/hardware clock | Reconcile RTC mode. Preserve hardware clock semantics unless target profile requires change. | TEST-ARCH2015-SYSV-029 |

### 4.6 Package ecosystem and security policy

| ID | Observed path | Class | Reconciliation semantics | Test ID |
|---|---|---|---|---|
| CFG-2015-030 | `/etc/pacman.conf` | package manager | Reconcile repository configuration, hooks, and architecture settings. Do not execute package operations during configuration reconciliation. | TEST-ARCH2015-SYSV-030 |
| CFG-2015-031 | `/etc/pacman.d/` | package manager data | Inventory mirrorlists and related files. Archive and validate. Do not treat mirror availability as permanent. | TEST-ARCH2015-SYSV-031 |
| CFG-2015-032 | `/etc/sudoers` | security policy | Validate syntax in staging. Preserve policy unless target profile explicitly replaces it. | TEST-ARCH2015-SYSV-032 |
| CFG-2015-033 | `/etc/sudoers.d/` | security policy fragments | Inventory fragments. Validate syntax. Preserve unknown fragments as quarantined or archived. | TEST-ARCH2015-SYSV-033 |
| CFG-2015-034 | `/etc/udev/rules.d/` | device rules | Parse udev rules. Preserve device semantics. Stage changes and validate rule syntax. | TEST-ARCH2015-SYSV-034 |

### 4.7 Identity and secret-sensitive files

These files are inventoried by path, metadata, and hash only. Their contents are not copied into evidence unless explicitly required by a reviewed recovery procedure.

| ID | Observed path | Class | Reconciliation semantics | Test ID |
|---|---|---|---|---|
| CFG-2015-035 | `/etc/passwd` | identity/user data | Validate structure. Do not blindly merge. Preserve user identity unless target profile requires migration. | TEST-ARCH2015-SYSV-035 |
| CFG-2015-036 | `/etc/group` | identity/user data | Validate structure. Preserve group mappings unless target profile requires change. | TEST-ARCH2015-SYSV-036 |
| CFG-2015-037 | `/etc/shadow` | secret-sensitive | Inventory path, mode, owner, and hash only. Do not include credential material in evidence. | TEST-ARCH2015-SYSV-037 |
| CFG-2015-038 | `/etc/gshadow` | secret-sensitive | Inventory path, mode, owner, and hash only. Do not include credential material in evidence. | TEST-ARCH2015-SYSV-038 |

### 4.8 Hybrid init detection

| ID | Observed path | Class | Reconciliation semantics | Test ID |
|---|---|---|---|---|
| CFG-2015-039 | `/etc/systemd/system/` | parallel init | Detect systemd unit presence. Reconcile conflicts between sysvinit scripts and systemd units. Prefer target profile decision, not implicit precedence. | TEST-ARCH2015-SYSV-039 |

---

## 5. Repository directory layout for Wave 1

```text
/home/tak_0/sunshineos-audit/SunshineOS_Development-Testing/
├── evolution-engine/
│   ├── catalogs/
│   │   └── arch-2015-sysvinit/
│   │       ├── manifest.yaml
│   │       └── entries/
│   │           ├── CFG-2015-001.yaml
│   │           ├── CFG-2015-002.yaml
│   │           ├── CFG-2015-003.yaml
│   │           ├── CFG-2015-004.yaml
│   │           ├── CFG-2015-005.yaml
│   │           ├── CFG-2015-006.yaml
│   │           ├── CFG-2015-007.yaml
│   │           ├── CFG-2015-008.yaml
│   │           ├── CFG-2015-009.yaml
│   │           ├── CFG-2015-010.yaml
│   │           ├── CFG-2015-011.yaml
│   │           ├── CFG-2015-012.yaml
│   │           ├── CFG-2015-013.yaml
│   │           ├── CFG-2015-014.yaml
│   │           ├── CFG-2015-015.yaml
│   │           ├── CFG-2015-016.yaml
│   │           ├── CFG-2015-017.yaml
│   │           ├── CFG-2015-018.yaml
│   │           ├── CFG-2015-019.yaml
│   │           ├── CFG-2015-020.yaml
│   │           ├── CFG-2015-021.yaml
│   │           ├── CFG-2015-022.yaml
│   │           ├── CFG-2015-023.yaml
│   │           ├── CFG-2015-024.yaml
│   │           ├── CFG-2015-025.yaml
│   │           ├── CFG-2015-026.yaml
│   │           ├── CFG-2015-027.yaml
│   │           ├── CFG-2015-028.yaml
│   │           ├── CFG-2015-029.yaml
│   │           ├── CFG-2015-030.yaml
│   │           ├── CFG-2015-031.yaml
│   │           ├── CFG-2015-032.yaml
│   │           ├── CFG-2015-033.yaml
│   │           ├── CFG-2015-034.yaml
│   │           ├── CFG-2015-035.yaml
│   │           ├── CFG-2015-036.yaml
│   │           ├── CFG-2015-037.yaml
│   │           ├── CFG-2015-038.yaml
│   │           └── CFG-2015-039.yaml
│   ├── schemas/
│   │   └── config-reconciliation.schema.yaml
│   ├── resolvers/
│   │   └── arch2015_sysvinit_resolver.pseudo.md
│   └── tests/
│       └── test_arch2015_sysvinit_reconciliation.py
├── evidence/
│   └── arch-2015-sysvinit/
│       ├── inventory/
│       ├── plans/
│       └── tests/
├── logs/
│   └── migration/
│       └── arch-2015-sysvinit/
└── reports/
    ├── USER_MIGRATION_MANDATE_2026-11-21.md
    └── ARCHITECTURE_DECISIONS.md
```

---

## 6. Configuration reconciliation schema

Schema file:

```text
evolution-engine/schemas/config-reconciliation.schema.yaml
```

Conceptual schema:

```yaml
apiVersion: sunshineos.evolution/v1
kind: ConfigReconciliationEntry
metadata:
  id: CFG-2015-001
  sourceBaseline: B-1-2015
  targetProfile: TP040
  inventorySchema: INV7
  transitionCatalog: TC18
  migrationEngine: ME12
spec:
  observedPath: /etc/inittab
  pathType: file
  parser: inittab-v1
  capabilityProbe: CAP-001
  classification: boot-init
  authority: observed
  conflictPolicy: staged-review
  preserve:
    - comments
    - unknown-directives
  targetMapping:
    initSystem: "{{ target_profile.init.system }}"
    defaultRunlevel: "{{ target_profile.boot.default }}"
  validation:
    - syntax
    - semantic
    - target-profile-conformance
  recovery:
    snapshot: true
    compensatingAction: restore-archived-file
  evidence:
    inventory: evidence/arch-2015-sysvinit/inventory/CFG-2015-001.normalized.yaml
    plan: evidence/arch-2015-sysvinit/plans/CFG-2015-001.plan.yaml
    test: evidence/arch-2015-sysvinit/tests/TEST-ARCH2015-SYSV-001/result.md
```

### 6.1 Required schema fields

| Field | Purpose |
|---|---|
| `metadata.id` | Stable catalogue identifier. |
| `metadata.sourceBaseline` | Source anchor, normally `B-1-2015`. |
| `metadata.targetProfile` | Desired target profile, normally `TP040`. |
| `metadata.inventorySchema` | Inventory representation version, normally `INV7`. |
| `metadata.transitionCatalog` | Transition knowledge version, normally `TC18`. |
| `metadata.migrationEngine` | Resolver implementation version, normally `ME12`. |
| `spec.observedPath` | Exact path observed on the source system. |
| `spec.pathType` | `file`, `directory`, `symlink`, or `generated`. |
| `spec.parser` | Parser identifier used to normalize content. |
| `spec.capabilityProbe` | Probe that must succeed before applying the entry. |
| `spec.classification` | Semantic class, such as `boot-init`, `service-config`, `user-data`, or `secret-sensitive`. |
| `spec.authority` | Whether observed content is authoritative, advisory, or derived. |
| `spec.conflictPolicy` | How conflicts are handled: `target-wins`, `staged-review`, `preserve-user`, or `quarantine`. |
| `spec.preserve` | Elements that must not be silently discarded. |
| `spec.targetMapping` | Mapping rules from source semantics to target semantics. |
| `spec.validation` | Required validation stages. |
| `spec.recovery` | Snapshot and compensating behavior. |
| `spec.evidence` | Repository evidence paths. |

---

## 7. Resolver algorithm

Resolver specification file:

```text
evolution-engine/resolvers/arch2015_sysvinit_resolver.pseudo.md
```

### 7.1 High-level flow

1. Load target profile `TP040`.
2. Probe source capabilities.
3. Build an `INV7` inventory snapshot.
4. Load catalogue entries from `TC18`.
5. Normalize each observed configuration item.
6. Classify each item.
7. Resolve conflicts using target profile and observed authority.
8. Generate a staged migration plan.
9. Validate staged state.
10. Commit only if validation passes.
11. Recover from snapshot if validation fails.
12. Write evidence and journal entries.

### 7.2 Resolver pseudocode

```text
procedure reconcile_arch2015_sysvinit(root, target_profile, catalog, journal):

    caps = probe_capabilities(root)

    inventory = load_inventory(root, caps)

    plan = new MigrationPlan(
        source_baseline = "B-1-2015",
        target_profile = target_profile,
        inventory_schema = "INV7",
        transition_catalog = "TC18",
        migration_engine = "ME12"
    )

    for entry in catalog:

        if not caps.supports(entry.spec.capabilityProbe):
            plan.skip(entry, reason = "capability-missing")
            continue

        observed = inventory.read(entry.spec.observedPath)

        if observed.exists:
            parsed = entry.spec.parser.parse(observed.bytes)
            normalized = normalize(parsed, entry.spec)
            inventory.record(
                id = entry.metadata.id,
                path = entry.spec.observedPath,
                normalized = normalized,
                hash = hash(observed.bytes)
            )
        else:
            normalized = empty(entry.spec)

        decision = decide(entry, normalized, target_profile, caps)

        plan.add(decision)

    plan.sort_by_dependencies()

    staged = stage_plan(plan, root)

    report = validate_staged(staged, target_profile)

    if report.ok:
        commit(staged, journal)
    else:
        recover(staged, journal)

    write_evidence(plan, staged, report)

    return report
```

### 7.3 Decision function

```text
function decide(entry, normalized, target_profile, caps):

    class = entry.spec.classification

    if class == "s…
