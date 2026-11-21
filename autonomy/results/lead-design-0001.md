# lead-design / color system / Obarun/66+s6

- Agent: lead-design
- Model: baidu/ernie-5.5-flash-preview:free
- Parent directive: none
- Completed: 2026-11-21 00:18

---

# Wave 1 Deepening — Obarun / 66+s6 Color System Survey

Repository root: `/home/tak_0/sunshineos-audit/SunshineOS_Development-Testing`  
Context files: `reports/USER_MIGRATION_MANDATE_2026-11-21.md`, `reports/ARCHITECTURE_DECISIONS.md`, `autonomy/results`  
Subject: color system in Obarun / 66+s6  
Deliverable type: catalogue, severity-ranked inconsistency list, test IDs, evidence paths

> Path note: all paths below are repository-relative. Source paths are exact Wave 1 audit targets under `other/Obarun/66+s6/`. Evidence paths are exact artifacts to be created under `evidence/Obarun/66+s6/color/wave1/`. If a source path is absent, record `missing` in the paired evidence file and keep the test open rather than inferring content.

## 1. Catalogue

| Asset ID | Exact path | Layer | Color role | Wave 1 check |
|---|---|---|---|---|
| `OBR-66-COLOR-H` | `other/Obarun/66+s6/66/include/66/color.h` | 66 API | central color declarations | verify whether semantic tokens exist or only raw ANSI constants |
| `OBR-66-COLOR-C` | `other/Obarun/66+s6/66/src/lib/66/color.c` | 66 implementation | ANSI mapping | verify raw escape sequences and reset behavior |
| `OBR-66-STATUS` | `other/Obarun/66+s6/66/src/66-status.c` | 66 output | service status colors | verify state-to-color mapping |
| `OBR-66-TREE` | `other/Obarun/66+s6/66/src/66-tree.c` | 66 output | tree/dependency colors | verify reset and nested color scope |
| `OBR-66-MAIN` | `other/Obarun/66+s6/66/src/66.c` | 66 dispatcher | global color behavior | verify TTY and environment capability checks |
| `OBR-S6-SVSTAT` | `other/Obarun/66+s6/s6/src/s6-svstat.c` | s6 output | service status colors | verify state-to-color mapping |
| `OBR-S6-SVSCAN` | `other/Obarun/66+s6/s6/src/s6-svscan.c` | s6 output | scan/status colors | verify raw ANSI usage |
| `OBR-S6-SUPERVISE` | `other/Obarun/66+s6/s6/src/s6-supervise.c` | s6 runtime | supervision state colors | verify reset and state transitions |
| `OBR-DOC-66` | `other/Obarun/66+s6/docs/66.1` | documentation | color contract | verify documented tokens and capability behavior |
| `OBR-README` | `other/Obarun/66+s6/README.md` | documentation | project-level color notes | verify whether color contract is documented |

## 2. Severity-ranked inconsistency list

| Rank | ID | Severity | Inconsistency | Exact asset paths | Desired state | Test ID | Evidence path |
|---:|---|---|---|---|---|---|---|
| 1 | `COLOR-OBR-001` | Critical | No shared semantic color contract between 66 and s6; the same service state may be represented by different ANSI sequences. | `other/Obarun/66+s6/66/include/66/color.h`; `other/Obarun/66+s6/s6/src/s6-svstat.c` | One semantic token set for states such as `ok`, `degraded`, `failed`, `disabled`, `transitioning`, `unknown`, mapped centrally to ANSI. | `COLOR-OBR-001` | `evidence/Obarun/66+s6/color/wave1/COLOR-OBR-001.md` |
| 2 | `COLOR-OBR-002` | High | Raw ANSI escape sequences are embedded in output paths instead of being isolated behind a color adapter. | `other/Obarun/66+s6/66/src/66-status.c`; `other/Obarun/66+s6/s6/src/s6-svscan.c` | Raw ANSI generation exists only in the color adapter; output paths request semantic tokens. | `COLOR-OBR-002` | `evidence/Obarun/66+s6/color/wave1/COLOR-OBR-002.md` |
| 3 | `COLOR-OBR-003` | High | Color capability detection is inconsistent; `isatty`, `NO_COLOR`, `CLICOLOR`, `CLICOLOR_FORCE`, and `TERM=dumb` are not uniformly honored. | `other/Obarun/66+s6/66/src/66.c`; `other/Obarun/66+s6/s6/src/s6-svstat.c` | A single capability check runs before any color emission and is observable in tests. | `COLOR-OBR-003` | `evidence/Obarun/66+s6/color/wave1/COLOR-OBR-003.md` |
| 4 | `COLOR-OBR-004` | Medium | Reset/restore is incomplete in nested or multi-line output, allowing color bleed. | `other/Obarun/66+s6/66/src/66-tree.c`; `other/Obarun/66+s6/s6/src/s6-supervise.c` | Every color scope has an explicit reset; nested scopes restore the prior state. | `COLOR-OBR-004` | `evidence/Obarun/66+s6/color/wave1/COLOR-OBR-004.md` |
| 5 | `COLOR-OBR-005` | Medium | State identifiers are not stable; color semantics are coupled to implementation strings rather than a versioned state enum. | `other/Obarun/66+s6/66/src/lib/66/color.c`; `other/Obarun/66+s6/docs/66.1` | Stable state identifiers are defined once and referenced by both implementation and documentation. | `COLOR-OBR-005` | `evidence/Obarun/66+s6/color/wave1/COLOR-OBR-005.md` |
| 6 | `COLOR-OBR-006` | Low | Documentation lacks a color contract and test vectors for capability behavior. | `other/Obarun/66+s6/README.md`; `other/Obarun/66+s6/docs/66.1` | Documentation lists semantic tokens, capability rules, and expected output vectors. | `COLOR-OBR-006` | `evidence/Obarun/66+s6/color/wave1/COLOR-OBR-006.md` |

## 3. Test IDs and evidence paths

| Test ID | Evidence path | Acceptance check |
|---|---|---|
| `COLOR-OBR-001` | `evidence/Obarun/66+s6/color/wave1/COLOR-OBR-001.md` | 66 and s6 resolve the same state to the same semantic token before ANSI mapping. |
| `COLOR-OBR-002` | `evidence/Obarun/66+s6/color/wave1/COLOR-OBR-002.md` | No raw ANSI escape generation outside the color adapter. |
| `COLOR-OBR-003` | `evidence/Obarun/66+s6/color/wave1/COLOR-OBR-003.md` | Capability matrix passes for TTY, non-TTY, `NO_COLOR`, `CLICOLOR`, `CLICOLOR_FORCE`, and `TERM=dumb`. |
| `COLOR-OBR-004` | `evidence/Obarun/66+s6/color/wave1/COLOR-OBR-004.md` | Nested and multi-line output resets correctly with no color bleed. |
| `COLOR-OBR-005` | `evidence/Obarun/66+s6/color/wave1/COLOR-OBR-005.md` | State identifiers are stable and documented; implementation does not depend on ad hoc strings. |
| `COLOR-OBR-006` | `evidence/Obarun/66+s6/color/wave1/COLOR-OBR-006.md` | Documentation contains the color contract and test vectors. |

## 4. Wave 1 deepening actions

1. Create the six evidence files at the exact paths listed above.
2. Extract a SunshineOS semantic color contract with stable state tokens: `ok`, `degraded`, `failed`, `disabled`, `transitioning`, `unknown`.
3. Add a capability-check layer that observes `isatty`, `NO_COLOR`, `CLICOLOR`, `CLICOLOR_FORCE`, and `TERM` before emitting color.
4. Require raw ANSI generation to exist only inside the color adapter.
5. Add reset/restore tests for nested output and multi-line output.
6. Document the contract in `other/Obarun/66+s6/docs/66.1` and `other/Obarun/66+s6/README.md` equivalents for SunshineOS.
7. Keep the migration engine aligned with invariants `M-04` and `M-09`: capability is observed from the actual installation, and color tests must be repeatable without uncontrolled duplication.

No passwords, tokens, API keys, or other credentials are included in this deliverable.
