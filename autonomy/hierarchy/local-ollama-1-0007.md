# local-ollama-1-0007 -> hierarchy

Based on the `ARCHITECTURE_DECISIONS.md` file inspection, here's the consolidated Markdown deliverable:

```markdown
## Wave 1 Offline Verification Findings - Artix Runit/OpenRC

This document details the offline verification of key architectural decisions identified in the `ARCHITECTURE_DECISIONS.md` file.

**1. Decision AD-01: Arch 2026 Baseline**

*   **File Path:** `evolution-engine/src/evolution/baseline.py::ARCH_2026_BASELINE`, `evolution/docs/BASELINE_ARCH_2026.md`
*   **Test ID:**  (No specific test ID identified in the document, but this decision is asserted by the `EvolutionUpdater.upgrade` function in `evolution-engine/src/evolution/updater.py`)
*   **Evidence Path:** `evolution-engine/src/evolution/updater.py::EvolutionUpdater.upgrade`

**2. Decision AD-02: Milestones as Logical Gates**

*   **File Path:** `evolution-engine/src/evolution/milestones.py::MilestoneRegistry.chain`, `evolution-engine/src/evolution/scheme.toml`
*   **Test ID:** (No specific test ID identified, but related to the `MilestoneRegistry` implementation)
*   **Evidence Path:** `evolution-engine/src/evolution/scheme.toml`

**3. Decision AD-03: Target Resolution**

*   **File Path:** `evolution-engine/src/evolution/target_resolver.py::TargetResolver`, `src/planner.py`
*   **Test ID:** (No specific test ID identified, but related to the `TargetResolver` implementation)
*   **Evidence Path:** `src/planner.py`

**4. Decision AD-04: Single Migration Engine**

*   **File Path:** `evolution-engine/src/evolution/compatibility.py::CompatibilityEngine`, `evolution-engine/src/evolution/inventory.py::from_observed`
*   **Test ID:** (No specific test ID identified, but related to the `CompatibilityEngine` implementation)
*   **Evidence Path:** `evolution-engine/src/evolution/inventory.py::from_observed`

**5. Decision AD-05: Authority of Observed Installation**

*   **File Path:** `evolution-engine/src/evolution/invariants.py::_m04`, `src/context.py::ExecutionContext`
*   **Test ID:** (No specific test ID identified, but related to the `ExecutionContext` implementation)
*   **Evidence Path:** `src/context.py::ExecutionContext`

**6. Decision AD-06: Trust Failure Closed**

*   **File Path:** `evolution-engine/src/trust/model.py`, `evolution-engine/src/evolution/repository.py`, `evolution-engine/src/evolution/tools/channels.py`
*   **Test ID:** (No specific test ID identified, but related to the `Repository` and `Channels` implementations)
*   **Evidence Path:** `evolution-engine/src/evolution/repository.py`

**7. Decision AD-07: Declarative Scheme Data**

*   **File Path:** `evolution-engine/src/evolution/scheme.toml`, `evolution-engine/src/evolution/scheme.py`
*   **Test ID:** (No specific test ID identified, but related to the `Scheme` implementation)
*   **Evidence Path:** `evolution-engine/src/evolution/scheme.py`

**8. Decision AD-08: Adaptor Sandboxing**

*   **File Path:** `src/adapters/runtime.py`, `evolution-engine/src/evolution/hooks.py::HookRunner.validate_command`
*   **Test ID:** (No specific test ID identified, but related to the `HookRunner` implementation)
*   **Evidence Path:** `src/adapters/runtime.py`

**9. Decision AD-09: Engine Code Constraints**

*   **File Path:** `src/engine.py`, `evolution-engine/src/evolution/hooks.py::HookRunner.validate_command`
*   **Test ID:** (No specific test ID identified, but related to the `Engine` implementation)
*   **Evidence Path:** `src/engine.py`

**10. Decision AD-10: Root-Run Separation**

*   **File Path:** `src/context.py::ExecutionContext`, `evolution-engine/src/evolution/journal_state.py`
*   **Test ID:** (No specific test ID identified, but related to the `ExecutionContext` implementation)
*   **Evidence Path:** `src/context.py::ExecutionContext`
```
