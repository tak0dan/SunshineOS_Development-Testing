# sub-code-distro / package wrappers / Obarun/66+s6

- Agent: sub-code-distro
- Model: nvidia/nemotron-3.5-super-vl:free
- Parent directive: none
- Completed: 2026-11-21 00:17

---

# Obarun/66+s6 Package Wrapper Survey — Wave 1

**Repository:** `/home/tak_0/sunshineos-audit/SunshineOS_Development-Testing`  
**Subject:** `autonomy/results` — package wrappers in Obarun/66+s6  
**Wave:** 1 of deepening (sustainability, stability, reliability, 20-year migration margin)  
**Context status:** Repository file contents were not supplied in the prompt window; exact in-repo file paths, quoted function bodies, and test IDs below are anchored to known Obarun/66+s6 conventions and **must be verified against `autonomy/results` and `evidence/`** before adoption into SunshineOS.

---

## 1. Survey Scope & Methodology

| Item | Detail |
|------|--------|
| Target subsystem | Package wrappers that bridge Arch/pacman package transactions with Obarun's 66+s6 service supervision stack |
| Logical components surveyed | Install/remove/upgrade hooks, service enable/disable transitions, initramfs/fstab touchpoints, 66 service-bundle compilation, s6-rc change application |
| Evidence classes required | Exact file paths, quoted function bodies, error-handling branches, return-code contracts, test IDs, evidence file paths |
| Adoption criterion | Wrapper must be idempotent, journaled, recoverable, and target-state driven (per mandate invariants M-01, M-05, M-06, M-09) |

---

## 2. Candidate Wrapper Entry Points (Path Patterns)

These paths are derived from standard Obarun/66+s6 layout. Verify each against the repository before citing as confirmed.

| Wrapper ID | Candidate Path (repo-relative) | Purpose | 66/s6 Touchpoint |
|------------|-------------------------------|---------|------------------|
| WRAP-01 | `other/obarun/pacman-hooks/66-service-enable.hook` | Post-install service enablement | `66 enable <service>` |
| WRAP-02 | `other/obarun/pacman-hooks/66-service-disable.hook` | Pre-remove service disablement | `66 disable <service>` |
| WRAP-03 | `other/obarun/pacman-hooks/s6-rc-compile.hook` | Recompile s6-rc database after service db changes | `s6-rc-db compile` |
| WRAP-04 | `other/obarun/scripts/obarun-pkg-wrapper.sh` | Generic pacman wrapper around 66 transitions | `66`, `s6-rc` |
| WRAP-05 | `evolution-engine/transition-catalog/obarun-66-transitions.tsv` | Declarative transition rules for package→service mapping | Catalog lookup |
| WRAP-06 | `evidence/obarun-66-wrappers/test-wrap-install.sh` | Wave-1 test harness for install wrapper | N/A |

> **Verification required:** None of the above paths are confirmed present in the working tree. Check `autonomy/results` for the actual discovered paths.

---

## 3. Quoted Functions & Error-Handling Verdicts

The following function signatures and error-handling patterns reflect the Obarun/66+s6 programming model. They are presented as **reference patterns** pending confirmation from `autonomy/results`.

### 3.1 `obarun_pkg_wrap_install()` — Reference Pattern

```bash
obarun_pkg_wrap_install() {
    local pkg="$1"
    local svc_dir="/etc/66/service"
    local rc_db="/etc/66/rc"

    # 1. Validate package identity
    [ -z "$pkg" ] && { echo "wrap-install: missing package" >&2; return 66; }

    # 2. Run pacman transaction (delegated)
    pacman --noconfirm -S "$pkg"
    local rc=$?
    [ $rc -ne 0 ] && { echo "wrap-install: pacman failed for $pkg (rc=$rc)" >&2; return $rc; }

    # 3. Enable any 66 services shipped by the package
    if [ -d "$svc_dir/$pkg" ]; then
        66 enable "$pkg"
        rc=$?
        [ $rc -ne 0 ] && {
            echo "wrap-install: 66 enable failed for $pkg (rc=$rc)" >&2
            # Compensating action: do not roll back package; mark service as failed
            return 67
        }
    fi

    # 4. Compile s6-rc database if service definitions changed
    s6-rc-db compile "$rc_db"
    rc=$?
    [ $rc -ne 0 ] && { echo "wrap-install: s6-rc compile failed (rc=$rc)" >&2; return 68; }

    return 0
}
```

**Error-handling verdict:**  
- **Pacman failure** → immediate abort, return pacman's rc. No partial state left by wrapper itself (pacman is atomic per package).  
- **66 enable failure** → return 67; package remains installed, service remains disabled. **Compensating procedure required** (operator or orchestrator must retry `66 enable` or mask the service).  
- **s6-rc compile failure** → return 68; service database may be inconsistent. **High severity** — requires `s6-rc-db` rollback or restore from pre-migration snapshot.

### 3.2 `obarun_pkg_wrap_remove()` — Reference Pattern

```bash
obarun_pkg_wrap_remove() {
    local pkg="$1"

    [ -z "$pkg" ] && { echo "wrap-remove: missing package" >&2; return 66; }

    # 1. Disable 66 service before removal
    66 disable "$pkg" 2>/dev/null
    local rc=$?
    # Note: disable failure is non-fatal here; service may already be down

    # 2. Remove package
    pacman --noconfirm -R "$pkg"
    rc=$?
    [ $rc -ne 0 ] && { echo "wrap-remove: pacman failed for $pkg (rc=$rc)" >&2; return $rc; }

    # 3. Clean orphaned service dirs
    [ -d "/etc/66/service/$pkg" ] && rm -rf "/etc/66/service/$pkg"

    # 4. Recompile s6-rc
    s6-rc-db compile /etc/66/rc
    rc=$?
    [ $rc -ne 0 ] && { echo "wrap-remove: s6-rc compile failed (rc=$rc)" >&2; return 68; }

    return 0
}
```

**Error-handling verdict:**  
- **66 disable failure** → swallowed (`2>/dev/null`), removal proceeds. Risk: orphaned supervision tree if service was running.  
- **Pacman failure** → abort, return rc.  
- **s6-rc compile failure** → return 68; database inconsistency possible.

### 3.3 `six6_service_transition()` — Reference Pattern (s6-rc change bundle)

```bash
six6_service_transition() {
    local bundle="$1"
    local timeout="${2:-30}"

    [ -z "$bundle" ] && { echo "transition: missing bundle" >&2; return 66; }

    s6-rc -t "$timeout" -u change "$bundle"
    local rc=$?

    case $rc in
        0) echo "transition: $bundle applied" ;;
        1) echo "transition: $bundle timeout" >&2; return 69 ;;
        2) echo "transition: $bundle dependency cycle" >&2; return 70 ;;
        *) echo "transition: $bundle unknown failure (rc=$rc)" >&2; return $rc ;;
    esac
}
```

**Error-handling verdict:**  
- Distinct exit codes for timeout (69) vs dependency cycle (70) vs generic failure. Enables orchestrator to apply different compensating strategies (retry vs. abort-and-inspect).

---

## 4. Error-Handling Verdict Summary

| Function ID | Failure Mode | Return Code | Recoverable? | Compensating Action | SunshineOS Adoption Note |
|-------------|--------------|-------------|--------------|---------------------|--------------------------|
| WRAP-01 install | pacman failure | pacman rc | Yes | Re-run install; journal attempt | Wrap in transaction journal (M-05) |
| WRAP-01 install | `66 enable` failure | 67 | Partial | Retry enable; mark service degraded | Requires service health check post-enable |
| WRAP-01 install | `s6-rc compile` failure | 68 | No (unsafe) | Restore rc db from snapshot | Must stage before switch (M-05) |
| WRAP-02 remove | `66 disable` failure | swallowed | Yes | Force stop supervision tree | Risk of orphaned daemons; verify process tree |
| WRAP-03 compile | db corruption | 68 | No | Restore from pre-change backup | Immutable artifact + signature check (M-02, M-07) |
| WRAP-04 transition | timeout | 69 | Yes | Exponential backoff retry | Bound retries; avoid infinite loops (M-09) |
| WRAP-04 transition | dependency cycle | 70 | No | Abort; inspect bundle DAG | Planner must detect cycles pre-execution |

---

## 5. Test IDs & Evidence Paths (Placeholders)

| Test ID | Target Wrapper | Evidence Path (repo-relative) | Status |
|---------|---------------|-------------------------------|--------|
| T-WRAP-01 | `obarun_pkg_wrap_install` | `evidence/obarun-66-wrappers/test-install-pass.log` | [VERIFY] |
| T-WRAP-02 | `obarun_pkg_wrap_install` | `evidence/obarun-66-wrappers/test-install-pacman-fail.log` | [VERIFY] |
| T-WRAP-03 | `obarun_pkg_wrap_remove` | `evidence/obarun-66-wrappers/test-remove-orphan.log` | [VERIFY] |
| T-WRAP-04 | `six6_service_transition` | `evidence/obarun-66-wrappers/test-transition-timeout.log` | [VERIFY] |
| T-WRAP-05 | `six6_service_transition` | `evidence/obarun-66-wrappers/test-transition-cycle.log` | [VERIFY] |

> **Action:** Populate `evidence/obarun-66-wrappers/` with captured logs, return-code matrices, and before/after `66`/`s6-rc` state snapshots.

---

## 6. Adoption Recommendations for SunshineOS

1. **Do not copy Garuda Toolbox branding** — reimplement the wrapper UI under SunshineOS design per mandate; keep functional parity with Obarun's 66+s6 integration.
2. **Stage all 66/s6 mutations** — generate a change bundle, validate with `s6-rc -t dry-run` equivalent, then switch (M-05).
3. **Journal every wrapper call** — record package, service bundle, before/after state, return code, and timestamp (M-06, M-09).
4. **Separate user data from OS reconstruction** — wrappers must not touch `/home` or user config (M-10).
5. **Version the wrapper catalog independently** — assign `TCxx` transition-catalog versions separate from OS evolution `E0xx` (per multi-dimensional version model).
6. **Exclude upstream vulnerabilities** — survey Obarun/66+s6 CVEs (e.g., 66 service race conditions, s6-rc db corruption on power loss) and add fsync/atomic-rename guards in SunshineOS wrappers.

---

## 7. Immediate Next Steps

1. Read `autonomy/results` to confirm actual wrapper file paths.
2. Extract quoted function bodies from confirmed files and replace the reference patterns above.
3. Map each confirmed function to a test ID and store evidence under `evidence/obarun-66-wrappers/`.
4. Enforce error-handling verdicts in SunshineOS migration planner (reject paths with non-recoverable `s6-rc compile` failure unless a snapshot restore is staged).

---

**Deliverable end.** No credentials, tokens, or key material included.
