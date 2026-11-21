# SunshineOS infrastructure index — migration senior developer

This is the single entry point for the migration senior developer. It maps the
whole autonomous development infrastructure and, more importantly, tells you
**where to look for updates, live work, logs, findings and code**.

Nothing in this file contains credentials. Keys live only in external env files
under the orchestrator state directory and must never be copied into the repo.

---

## 1. Where to look RIGHT NOW (live state)

| Need | Go here |
|---|---|
| **What every agent is doing now** | `autonomy/SUPERVISION_LOG.md` — appended every 5 min by the supervisor |
| **Live task queue / status / retries / cooldowns** | `/home/tak_0/.local/state/sunshine-orchestrator/backlog2.json` (JSON: `tasks[]`, each with `status`, `slot`, `model`, `retry_count`, `cooldown_until`) |
| **Live orchestrator decisions** | `/home/tak_0/.local/state/sunshine-orchestrator/logs/orchestrator.out` then `orchestrator.log` — `ASSIGN`, `DONE`, `RETRY`, `FAIL`, `QUALITY-GATE`, `PUBLISHED` events |
| **Per-agent raw model output** | `/home/tak_0/.local/state/sunshine-orchestrator/logs/<task-id>.log` |
| **Per-task structured work (result/log/findings/solutions/code)** | `autonomy/pull/<task-id>/` — `result.md`, `log.txt`, `findings.md`, `solutions.md`, `code/block-NN.txt` |
| **Master pull index (all agents, chronological)** | `autonomy/pull/GLOBAL_PULL.md` |
| **Chat-style team communication audit** | `autonomy/TEAM_CHAT.md` — who said what, commit, AI name, position, lines added/deleted, code comments |
| **Hierarchical reports to leads** | `autonomy/hierarchy/REPORT_TO_<lead>.md` and `autonomy/hierarchy/<task-id>.md` |
| **QC findings / rework** | `autonomy/qc/latest.md`, `autonomy/qc/<task-id>.md` |
| **Published results** | `autonomy/results/<task-id>.md` |
| **Git history of all agent work** | `git log development` — per-agent commits `autonomy: <slot> <task-id> completed` |

Fast commands:

```bash
S=/home/tak_0/.local/state/sunshine-orchestrator
R=/home/tak_0/sunshineos-audit/SunshineOS_Development-Testing

tail -50 "$R/autonomy/SUPERVISION_LOG.md"                 # latest supervisor audit
tail -40 "$S/logs/orchestrator.out"                        # live decisions
python3 -c "import json,collections; d=json.load(open('$S/backlog2.json')); \
print(collections.Counter(t['status'] for t in d['tasks']))"   # queue state
tail -30 "$R/autonomy/pull/GLOBAL_PULL.md"                 # newest pull entries
tail -60 "$R/autonomy/TEAM_CHAT.md"                        # communication audit
git -C "$R" log -20 --format='%h %s'                       # recent published work
```

---

## 2. Two roots

- **Repository (published, shared with other workers):**
  `/home/tak_0/sunshineos-audit/SunshineOS_Development-Testing`, branch `development`,
  remote `tak0dan`. Everything a collaborator must see lives here.
- **Orchestrator state (live, NOT in git):**
  `/home/tak_0/.local/state/sunshine-orchestrator/`. Holds the queue, keys, raw
  logs, download corpus and per-agent task stores. Nothing here is published
  as-is — selected content is mirrored into the repo (see section 5).

---

## 3. Repository map (published content)

| Path | What it is |
|---|---|
| `evolution-engine/` | **Actual migration code.** `src/`, `src/evolution/tools/` (services, snapshots, sealed state, transaction log, channels), `tests/` |
| `openclaw/` | Agent framework: `backends.py` (OpenRouter, Ollama, Codex, shell), `cli.py`, `core.py`, `tests/` |
| `reports/` | Mandate, architecture decisions (AD-01..AD-30), audits, orders, test plans, VM validation |
| `reports/USER_MIGRATION_MANDATE_2026-11-21.md` | The user's full standing instructions — read first |
| `reports/ARCHITECTURE_DECISIONS.md` | Canonical decisions |
| `FINDINGS.md`, `TODO` | Cross-cutting findings and open work |
| `evidence/screenshots/` | Boot/install/repair visual evidence |
| `autonomy/results/` | One Markdown result per completed task |
| `autonomy/pull/` | Global pull: per-task result/log/findings/solutions/code + `GLOBAL_PULL.md` index |
| `autonomy/hierarchy/` | Lead/subordinate communication and reports |
| `autonomy/qc/` | Quality-control findings and rework priority |
| `autonomy/codex/` | Senior developer (Codex) own work: audits, scripts, logs |
| `autonomy/SUPERVISION_LOG.md` | 5-minute supervision cycle log |
| `autonomy/TEAM_CHAT.md` | Chat-style communication + contribution audit |
| `INFRASTRUCTURE_INDEX.md` | This file |
| `autonomy/CODEX_BRIEF.md` | Senior developer onboarding brief and standing rules |

---

## 4. Orchestrator state map (live)

| Path | What it is |
|---|---|
| `orchestrator.py` | Main durable loop: 5-min supervision, 15-min publish, model pinning, rate-limit handling |
| `backlog2.json` | Live task store (authoritative for current state) |
| `backlog.json` | Earlier/backfill backlog |
| `keys/*.env` | 50 OpenRouter keys — **credentials, never publish** |
| `stores/*.json` | One task store per agent (one-writer constraint) |
| `logs/orchestrator.out`, `logs/orchestrator.log` | Orchestrator event log |
| `logs/<task-id>.log` | Raw console output for one task |
| `logs/team_chat_watcher.log` | Watcher health |
| `logs/audit_ticker.log` | 5-minute chat audit ticker |
| `results/`, `hierarchy/`, `qc/` | Pre-mirror copies of agent artifacts |
| `codex/` | Codex final messages |
| `iso/manifest.json` | ISO/source download status for the 10 research systems |
| `iso/isos/`, `iso/repos/` | Downloaded ISOs and cloned source trees (s6, omarchy, cachyos-tools, garuda-toolbox, …) |
| `fetch_research_sources.py` | ISO/source fetcher |
| `audit_ticker.py` | Posts the 5-minute audit prompt into chat |
| `team_chat_watcher.py` | Builds `TEAM_CHAT.md` from commits |
| `controller.py`, `make_backlog.py` | Earlier controller/backlog tooling |
| `deadline-400h`, `STOP`, `STOP-AUDIT` | Deadline and shutdown controls |

---

## 5. Publishing rules (maximum content)

Everything a collaborator needs must be reachable from the repo:

1. **Code and tests** go in `evolution-engine/` (or `openclaw/`), never only in a report.
2. **Every task** writes `autonomy/pull/<task-id>/` with result, log, findings,
   solutions and any fenced code blocks extracted as `code/block-NN.txt`.
3. **Every completed task is committed immediately** by the orchestrator:
   `autonomy: <slot> <task-id> completed`.
4. **Every commit is annotated** in `autonomy/TEAM_CHAT.md` with AI name, position,
   message, code comments and lines added/deleted/total.
5. **Referenced files must be published.** If a report, finding or solution names
   a file that was used or tested, that file must exist in the repo. Currently
   unpublished files found from report references:
   `evolution-engine/src/evolution/tools/artix_services.py`,
   `evolution-engine/tests/test_artix_services.py` (present on disk, untracked —
   commit these). Report references to files that do not yet exist are listed in
   section 7 as build gaps, not as evidence.
6. No credentials, keys, tokens or passwords in any published file.
7. Commit messages must be neutral — no rebranding/forking/other-system names.

---

## 6. Communication channels

| Channel | Purpose |
|---|---|
| `autonomy/TEAM_CHAT.md` | Full chat-style audit of every agent message with attribution |
| `autonomy/hierarchy/REPORT_TO_<lead>.md` | Subordinate → lead reports |
| `autonomy/hierarchy/<task-id>.md` | Lead output routed down to subordinates |
| `autonomy/SUPERVISION_LOG.md` | Supervisor → whole team, every 5 min |
| `autonomy/qc/latest.md` | QC → owning lead rework directives |
| `autonomy/pull/GLOBAL_PULL.md` | Every agent → global work pull, indexed |
| Chat audit ticker | 5-minute audit prompt in the operator chat |

---

## 7. Known build gaps (referenced in reports, not yet on disk)

These are named in reports but have no file yet. Treat as work items, not proof:

`evolution-engine/target_resolver.py`, `state_resolver.py`, `migration_engine.py`,
`resolver/{plan,resolve,validate}.py`, `ledger/check-ledger-integrity.py`,
`catalog/validate.py`, `hooks/artix_transition.py`,
`transition_catalog/dependency_graph.py`, and tests
`test_66_s6_transitions.py`, `test_baseline_reconstruction.py`,
`test_ledger_immutability.py`, `test_ledger_schema.py`,
`test_milestone_coverage.py`, `test_recovery.py`,
`test_resolver_idempotence.py`, `test_secret_scan.py`, `test_target_profile.py`.

---

## 8. Operating model

- ~26% of agents: research, design, QC (testers/designers/researchers).
- ~74%: implementation — must change real source + regression tests and paste
  the exact test command and result. Report-only answers are failures.
- High-role models are pinned; subordinate models rotate to spread rate limits.
- Free-tier OpenRouter daily limit caused mass 429s at 50 concurrent agents;
  `MAX_ACTIVE=12` with exponential cooldown is in force.
- GPU: AMD Radeon RX 9060 XT (RADV gfx1200) is present; installed Ollama is a
  CPU-only build, so local model work currently runs on CPU. See
  `autonomy/GPU_NOTE.md` for details and next steps.
