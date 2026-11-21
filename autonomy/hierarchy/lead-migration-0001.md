# lead-migration-0001 -> hierarchy

# Wave 1 Deepening — 40–80 Milestone Ledger for Obarun/66+s6

**Repository root:** `/home/tak_0/sunshineos-audit/SunshineOS_Development-Testing`  
**Context files:** `reports/USER_MIGRATION_MANDATE_2026-11-21.md`, `reports/ARCHITECTURE_DECISIONS.md`, `autonomy/results/`  
**Subject:** 40–80 milestone ledger in Obarun/66+s6  
**Wave:** 1 of deepening  
**Deliverable path:** `reports/WAVE1_OBARUN_66_S6_LEDGER.md`  
**Agent result path:** `autonomy/results/wave1-obarun-66-s6-ledger.md`  
**No credentials, tokens, passwords, or key material are included.**

---

## 1. Scope and invariants

The ledger must be a **cumulative declarative ledger**, not a replay of release scripts. It must preserve historical anchors, evolutionary states, migration intelligence, and execution separately.

| Invariant | Ledger enforcement |
|---|---|
| M-01 target-state driven | Resolver selects events by target profile, not release number. |
| M-02 immutable evolution history | Event directories are content-hashed and signed; no silent edits. |
| M-03 migration intelligence versioned independently | `EVS4` schema and `ME12` engine are separate identities. |
| M-04 installation is authoritative | Inventory snapshot drives event selection. |
| M-05 staged migration | Planner emits staged operations before commit. |
| M-06 recoverable operations | Every service/filesystem/boot operation has a recovery or compensating action. |
| M-07 historical artifacts archived | Baselines and old catalogs remain under `evolution-engine/ledger/archive/`. |
| M-08 migration support qualified | Compatibility metadata gates event applicability. |
| M-09 repeatable | Journal fingerprint prevents duplicate execution. |
| M-10 user data separate | OS reconstruction plan excludes user data by default. |

Key identities: `B0-2026`, `B-1-2015`, `E001`–`E080`, `ME12`, `INV7`, `EVS4`, `TC18`, `TP040`.

---

## 2. Obarun/66+s6 survey catalogue

Host paths below are the Wave 1 capture set. If a path is absent on a given image, record `ABSENT` in the evidence file; do not infer presence.

| ID | Host path(s) to capture | Repository evidence path | Ledger hook |
|---|---|---|---|
| OB-01 | `/usr/bin/66` | `evidence/obarun-66-s6/OB-01-66-cli.txt` | `services.manager=66` |
| OB-02 | `/etc/66/` | `evidence/obarun-66-s6/OB-02-etc-66-tree.txt` | `services.definitions_root=/etc/66` |
| OB-03 | `/etc/66/service/` | `evidence/obarun-66-s6/OB-03-66-service-tree.txt` | `services.service_root=/etc/66/service` |
| OB-04 | `/etc/66/bundle/` | `evidence/obarun-66-s6/OB-04-66-bundle-tree.txt` | `services.bundle_root=/etc/66/bundle` |
| OB-05 | `/etc/s6-overlay/s6-rc.d/` | `evidence/obarun-66-s6/OB-05-s6-rc-d-tree.txt` | `supervisor.s6_rc_d=/etc/s6-overlay/s6-rc.d` |
| OB-06 | `/etc/s6-overlay/s6-rc.user/` | `evidence/obarun-66-s6/OB-06-s6-rc-user-tree.txt` | `supervisor.s6_rc_user=/etc/s6-overlay/s6-rc.user` |
| OB-07 | `/run/service/` | `evidence/obarun-66-s6/OB-07-run-service-tree.txt` | `supervisor.scan_dir=/run/service` |
| OB-08 | `/run/s6/` | `evidence/obarun-66-s6/OB-08-run-s6-tree.txt` | `supervisor.runtime_root=/run/s6` |
| OB-09 | `/var/lib/66/` | `evidence/obarun-66-s6/OB-09-var-lib-66-tree.txt` | `state.root=/var/lib/66` |
| OB-10 | `/var/log/` | `evidence/obarun-66-s6/OB-10-var-log-tree.txt` | `logging.root=/var/log` |
| OB-11 | `/sbin/init` | `evidence/obarun-66-s6/OB-11-init-path.txt` | `boot.init=/sbin/init` |
| OB-12 | `/var/lib/pacman/local/` | `evidence/obarun-66-s6/OB-12-package-ownership.txt` | `packages.owner_db=/var/lib/pacman/local` |
| OB-13 | `/usr/lib/66/` | `evidence/obarun-66-s6/OB-13-usr-lib-66-tree.txt` | `services.library_root=/usr/lib/66` |

**Survey notes for 66+s6:**

- `66` is the service manager; `s6` is the supervision layer.
- Service state is filesystem-backed: `up`, `down`, `once`, `absent`.
- `66` bundles group services; `s6-rc` compiled trees and user trees define supervision topology.
- The ledger must store **desired service state**, not `66` command scripts.
- Package ownership must be captured to map package transitions to service transitions.
- Boot transition must record init path and boot-system semantics.

---

## 3. Ledger schema

Schema path: `evolution-engine/ledger/schemas/EVS4/event.schema.yaml`  
Event path pattern: `evolution-engine/ledger/events/E001/event.yaml`  
Signature path pattern: `evolution-engine/ledger/events/E001/signature.asc`  
Hash path pattern: `evolution-engine/ledger/events/E001/hash.txt`

| Field | Type | Required | Notes |
|---|---|---|---|
| `event_id` | string | yes | `E001`–`E080`; stable immutable identifier. |
| `schema_version` | string | yes | `EVS4`. |
| `baseline` | string | yes | `B0-2026` or `B-1-2015`. |
| `target_profile` | string | yes | e.g. `TP040`. |
| `content_hash` | string | yes | Hash of canonical event content. |
| `signature` | string | yes | Signature over `content_hash`. |
| `dependencies` | list | yes | Prior event IDs or catalog IDs. |
| `compatibility` | object | yes | Inventory/engine/catalog compatibility gates. |
| `publication` | object | yes | Publication metadata. |
| `deprecation` | object | no | Deprecation metadata. |
| `changes` | object | yes | Semantic changes only. |

`changes` sub-schema:

| Section | Purpose |
|---|---|
| `packages` | add/remove/replace with capability checks. |
| `services` | 66/s6 desired-state transitions. |
| `configuration` | create/modify/retire with semantic intent. |
| `boot` | init and boot-system transition. |
| `filesystem` | fstab/initramfs/mount transition. |
| `security` | policy changes. |
| `migration_metadata` | recovery, preconditions, validation hooks. |

Service transition fields:

| Field | Example |
|---|---|
| `manager` | `66` |
| `supervisor` | `s6` |
| `service_path` | `/etc/66/service/<name>` |
| `bundle` | `<bundle-name>` |
| `from_state` | `down` |
| `to_state` | `up` |
| `desired_state` | `up` / `down` / `once` / `absent` |
| `dependencies` | service or package dependencies |
| `recovery` | compensating action or `rebuild-from-catalog` |

Catalog path: `evolution-engine/ledger/catalogs/TC18/services/66-s6.yaml`

---

## 4. Directory layout

```text
evolution-engine/
  ledger/
    baselines/
      B0-2026/
        baseline.yaml
      B-1-2015/
        baseline.yaml
    events/
      E001/
        event.yaml
        hash.txt
        signature.asc
      E002/
        event.yaml
        hash.txt
        signature.asc
      ...
      E080/
        event.yaml
        hash.txt
        signature.asc
    schemas/
      EVS4/
        event.schema.yaml
    catalogs/
      TC18/
        packages/
        services/
          66-s6.yaml
        boot/
        filesystem/
        security/
    archive/
      EVS3/
      TC17/
  resolver/
    resolve.py
    plan.py
    validate.py
  artifact-manager/
  executor/
  orchestrator/
  inventory/
  tests/
    test_ledger_schema.py
    test_ledger_immutability.py
    test_resolver_idempotence.py
    test_66_s6_transitions.py
    test_baseline_reconstruction.py
    test_target_profile.py
    test_recovery.py
    test_milestone_coverage.py
    test_secret_scan.py

evidence/
  obarun-66-s6/
    OB-01-66-cli.txt
    OB-02-etc-66-tree.txt
    OB-03-66-service-tree.txt
    OB-04-66-bundle-tree.txt
    OB-05-s6-rc-d-tree.txt
    OB-06-s6-rc-user-tree.txt
    OB-07-run-service-tree.txt
    OB-08-run-s6-tree.txt
    OB-09-var-lib-66-tree.txt
    OB-10-var-log-tree.txt
    OB-11-init-path.txt
    OB-12-package-ownership.txt
    OB-13-usr-lib-66-tree.txt
  migration-ledger/
    T-LEDGER-001.txt
    T-LEDGER-002.txt
    T-LEDGER-003.txt
    T-LEDGER-004.txt
    T-LEDGER-005.txt
    T-LEDGER-006.txt
    T-LEDGER-007.txt
    T-LEDGER-008.txt
    T-LEDGER-009.txt
    T-LEDGER-010.txt

reports/
  WAVE1_OBARUN_66_S6_LEDGER.md

autonomy/results/
  wave1-obarun-66-s6-ledger.md

TODO/
  wave1-obarun-66-s6-ledger.md

prs/
  wave1-obarun-66-s6-ledger.md

logs/
  wave1-obarun-66-s6-ledger.log
```

---

## 5. Resolver algorithm

Resolver path: `evolution-engine/resolver/resolve.py`  
Planner path: `evolution-engine/resolver/plan.py`  
Validator path: `evolution-engine/resolver/validate.py`

### 5.1 High-level algorithm

1. Verify ledger signatures and content hashes.
2. Load inventory snapshot `INV7`.
3. Load baseline anchor `B0-2026` or `B-1-2015`.
4. Load target profile `TP040`.
5. Select compatible events from `E001`–`E080`.
6. Build dependency graph.
7. Topologically order operations.
8. Apply `TC18` semantic transition rules.
9. Add capability checks and preconditions.
10. Add recovery/compensating actions.
11. Fingerprint plan and check journal for idempotence.
12. Stage, validate, then commit or recover.

### 5.2 Resolver pseudocode

```text
function resolve(inventory, baseline, target_profile, ledger, catalog):
    assert verify_signatures(ledger)
    assert verify_hashes(ledger)

    events = select_events(inventory, baseline, target_profile, ledger)
    graph = build_dependency_graph(events)
    plan = topological_order(graph)

    plan = apply_catalog(plan, catalog)
    plan = add_capability_checks(plan, inventory)
    plan = add_preconditions(plan, inventory)
    plan = add_recovery(plan)

    fingerprint = hash(plan)
    if journal.contains(fingerprint):
        return journal.get(fingerprint)

    journal.put(fingerprint, plan)
    return plan
```

### 5.3 Event selection

```text
function select_events(inventory, baseline, target_profile, ledger):
    events = []
    for e in ledger.events:
        if e.baseline != baseline.id:
            continue
        if e.target_profile != target_profile.id:
            continue
        if not e.compatible_with(inventory):
            continue
        events.append(e)
    return events
```

### 5.4 Catalog application

```text
function apply_catalog(plan, catalog):
    for op in plan.operations:
        if op.kind == "service":
            rule = catalog.services.lookup(
                op.manager,
                op.supervisor,
                op.from_state,
                op.to_state
            )
            op.implementation = rule.semantic_transition
            op.recovery = rule.recovery
    return plan
```

### 5.5 66/s6 semantic transition

```text
function transition_service(svc, desired):
    if desired == "up":
        ensure_bundle(svc.bundle)
        ensure_service(svc.service_path)
        set_state(svc.service_path, "up")
    elif desired == "down":
        set_state(svc.service_path, "down")
    elif desired == "once":
        set_state(svc.service_path, "once")
    elif desired == "absent":
        remove_service(svc.service_path)
    else:
        fail("unsupported desired state")
```

The ledger stores `desired_state`; `66`/`s6` commands are implementation details owned by the executor.

### 5.6 Validation and recovery

```text
function validate(staged, target_profile):
    check_packages(staged, target_profile.packages)
    check_services(staged, target_profile.services)
    check_boot(staged, target_profile.boot)
    check_filesystem(staged, target_profile.filesystem)
    check_security(staged, target_profile.security)

    if not ok:
        return recover(staged)

    return commit(staged)
```

---

## 6. Test matrix

| Test ID | Assertion | Test path | Evidence path |
|---|---|---|---|
| T-LEDGER-001 | `EVS4` schema validates `E001`–`E080`. | `evolution-engine/tests/test_ledger_schema.py` | `evidence/migration-ledger/T-LEDGER-001.txt` |
| T-LEDGER-002 | Content hashes and signatures verify. | `evolution-engine/tests/test_ledger_immutability.py` | `evidence/migration-ledger/T-LEDGER-002.txt` |
| T-LEDGER-003 | Resolver is idempotent under journal replay. | `evolution-engine/tests/test_resolver_idempotence.py` | `evidence/migration-ledger/T-LEDGER-003.txt` |
| T-LEDGER-004 | 66/s6 service transitions resolve to desired state. | `evolution-engine/tests/test_66_s6_transitions.py` | `evidence/migration-ledger/T-LEDGER-004.txt` |
| T-LEDGER-005 | s6 scan/service/log topology validates. | `evolution-engine/tests/test_66_s6_transitions.py` | `evidence/migration-ledger/T-LEDGER-005.txt` |
| T-LEDGER-006 | `B0-2026` and `B-1-2015` reconstruct correctly. | `evolution-engine/tests/test_baseline_reconstruction.py` | `evidence/migration-ledger/T-LEDGER-006.txt` |
| T-LEDGER-007 | `TP040` resolves without release-history replay. | `evolution-engine/tests/test_target_profile.py` | `evidence/migration-ledger/T-LEDGER-007.txt` |
| T-LEDGER-008 | Failed validation triggers recovery. | `evolution-engine/tests/test_recovery.py` | `evidence/migration-ledger/T-LEDGER-008.txt` |
| T-LEDGER-009 | 40 minimum and 80 ideal milestone coverage. | `evolution-engine/tests/test_milestone_coverage.py` | `evidence/migration-ledger/T-LEDGER-009.txt` |
| T-LEDGER-010 | No secrets, tokens, or key material in ledger/evidence. | `evolution-engine/tests/test_secret_scan.py` | `evidence/migration-ledger/T-LEDGER-010.txt` |

---

## 7. Wave 1 exit criteria

- `EVS4` schema accepted at `evolution-engine/ledger/schemas/EVS4/event.schema.yaml`.
- `E001`–`E040` drafted; `E041`–`E080` reserved.
- Resolver pseudocode implemented at `evolution-engine/resolver/resolve.py`.
- Obarun/66+s6 catalogue captured under `evidence/obarun-66-s6/`.
- Tests `T-LEDGER-001` through `T-LEDGER-010` pass.
- Evidence files populated under `evidence/migration-ledger/`.
- No credentials or key material present.
- Findings appended to `FINDINGS.md`.

---

## 8. Wave 2 candidates

- Capture live Obarun/66+s6 VM evidence for OB-01 through OB-13.
- Expand `TC18` with package-to-service ownership mappings.
- Add signature ceremony procedure without storing secrets in the repository.
- Add recovery drills for fstab, initramfs, boot, and service failures.
- Add 80-milestone coverage matrix and deprecation tests.

---

## 9. Risks and mitigations

| Risk | Mitigation |
|---|---|
| Host path drift across Obarun releases | Record presence/absence per image; use capability checks. |
| 66/s6 semantic changes | Store desired state and semantic transition IDs, not commands. |
| Signature management | Keep keys outside repository; verify hashes and signatures only. |
| Evidence bloat | Store normalized trees and hashes, not full filesystem dumps. |
| Resolver complexity | Keep orchestrator thin; domain logic stays in catalog and executor. |

---

## 10. References

- `reports/USER_MIGRATION_MANDATE_2026-11-21.md`
- `reports/ARCHITECTURE_DECISIONS.md`
- `autonomy/results/`
- `evolution-engine/`
- `evidence/obarun-66-s6/`
- `evidence/migration-ledger/`
- `reports/WAVE1_OBARUN_66_S6_LEDGER.md`
- `autonomy/results/wave1-obarun-66-s6-ledger.md`
- `TODO/wave1-obarun-66-s6-ledger.md`
- `prs/wave1-obarun-66-s6-ledger.md`
- `logs/wave1-obarun-66-s6-ledger.log`
- `FINDINGS.md`
