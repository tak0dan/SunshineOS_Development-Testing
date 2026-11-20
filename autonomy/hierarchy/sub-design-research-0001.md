# sub-design-research-0001 -> hierarchy

# Garuda Visual Language in Obarun/66+s6 — Wave 1 Survey and Catalogue

**Repository:** `/home/tak_0/sunshineos-audit/SunshineOS_Development-Testing`  
**Subject:** Garuda visual language as observed in Obarun/66+s6 service-management contexts, adapted for SunshineOS  
**Wave:** 1 of deepening  
**Scope:** visual-language reference, style variables, layout rules, component catalogue, service-state semantics, test identifiers, evidence paths  
**Constraint:** no passwords, API keys, credentials, or secret material included

---

## 1. Purpose

This deliverable establishes the first durable visual-language baseline for SunshineOS components that are inspired by Garuda’s toolbox and service-management presentation, while removing Garuda branding and replacing it with SunshineOS identity.

The visual language must support:

- long-term maintainability;
- clear system-state communication;
- safe repair and migration workflows;
- Obarun/66+s6 service supervision semantics;
- a Garuda Toolbox-like experience without Garuda marks;
- accessibility, contrast, and predictable layout behavior.

This is a design and verification reference, not a release-specific script.

---

## 2. Governing Context Files

| Path | Role |
|---|---|
| `reports/USER_MIGRATION_MANDATE_2026-11-21.md` | User mandate for autonomous migration, repair, sustainability, and distro research |
| `reports/ARCHITECTURE_DECISIONS.md` | Architectural constraints for migration, evolution, and system reconstruction |
| `autonomy/results/` | Wave-based research and implementation handoff area |

---

## 3. Wave 1 Repository Paths

All paths below are repository-relative.

### 3.1 Primary visual-language report paths

| Path | Purpose |
|---|---|
| `reports/visual-language/README.md` | Entry point for the visual-language catalogue |
| `reports/visual-language/01-color-language.md` | Color semantics, contrast rules, state colors |
| `reports/visual-language/02-type-scale.md` | Typography scale, hierarchy, fallback rules |
| `reports/visual-language/03-layout-rules.md` | Grid, spacing, breakpoints, panel geometry |
| `reports/visual-language/04-component-catalog.md` | Reusable UI components and state variants |
| `reports/visual-language/05-obarun-66-s6-service-semantics.md` | Service-state visual mapping for Obarun/66+s6 |
| `reports/visual-language/06-garuda-toolbox-layout.md` | Garuda Toolbox-inspired layout, debranded for SunshineOS |
| `reports/visual-language/07-repair-and-migration-visual-states.md` | Visual states for repair, staging, validation, rollback |
| `reports/visual-language/08-test-matrix.md` | Test identifiers, acceptance criteria, evidence links |
| `reports/visual-language/09-evidence-index.md` | Evidence catalogue for Wave 1 observations |
| `reports/visual-language/10-handoff-wave2.md` | Next-wave deepening tasks |

### 3.2 Style-variable paths

| Path | Purpose |
|---|---|
| `reports/visual-language/style-variables/colors.md` | Canonical color variables |
| `reports/visual-language/style-variables/typography.md` | Canonical typography variables |
| `reports/visual-language/style-variables/spacing.md` | Spacing, radius, elevation, layout variables |
| `reports/visual-language/style-variables/state-colors.md` | Semantic state color mapping |

### 3.3 Evidence paths

| Path | Purpose |
|---|---|
| `evidence/visual-language/README.md` | Evidence index and usage rules |
| `evidence/visual-language/garuda-toolbox/observation-001.md` | Garuda Toolbox layout and interaction observations |
| `evidence/visual-language/garuda-toolbox/observation-002.md` | Garuda Toolbox information hierarchy observations |
| `evidence/visual-language/obarun-66-s6/service-state-observation-001.md` | Obarun/66+s6 service-state presentation observations |
| `evidence/visual-language/obarun-66-s6/service-tree-observation-001.md` | Service dependency and supervision-tree observations |
| `evidence/visual-language/color-contrast/contrast-audit-001.md` | Contrast and accessibility audit |
| `evidence/visual-language/typography/type-scale-audit-001.md` | Type-scale consistency audit |
| `evidence/visual-language/layout/grid-audit-001.md` | Grid and spacing audit |
| `evidence/visual-language/debranding/no-garuda-marking-audit-001.md` | Confirmation that Garuda marks are excluded |

### 3.4 Autonomy result paths

| Path | Purpose |
|---|---|
| `autonomy/results/wave1/garuda-visual-language-survey.md` | Wave 1 survey summary |
| `autonomy/results/wave1/garuda-visual-language-handoff.md` | Handoff to implementation agents |
| `autonomy/results/wave1/garuda-visual-language-test-results.md` | Wave 1 test result summary |

---

## 4. Design Principles

### 4.1 Invariants

| ID | Invariant |
|---|---|
| VL-INV-01 | SunshineOS visual language must not include Garuda branding, logos, mascots, or proprietary marks. |
| VL-INV-02 | Color must communicate state, not decoration alone. |
| VL-INV-03 | Destructive actions must be visually distinct from routine actions. |
| VL-INV-04 | Service state must be readable without relying on color alone. |
| VL-INV-05 | Layout must remain usable at compact, standard, and wide widths. |
| VL-INV-06 | Repair and migration views must always expose plan, validation, and recovery state. |
| VL-INV-07 | Typography must degrade predictably when preferred fonts are unavailable. |
| VL-INV-08 | Visual changes must be verifiable through repository evidence and test identifiers. |

### 4.2 Capability checks

| ID | Capability check |
|---|---|
| VL-CAP-01 | Display server can render dark-mode surfaces with sufficient contrast. |
| VL-CAP-02 | Terminal renderer supports ANSI-like state colors or fallback text labels. |
| VL-CAP-03 | Font fallback chain resolves to a readable sans-serif and monospace face. |
| VL-CAP-04 | Service manager exposes queryable state through Obarun/66+s6 interfaces. |
| VL-CAP-05 | UI can render staged migration plans without executing mutations. |
| VL-CAP-06 | UI can display rollback or compensating-action state after failure. |

---

## 5. Color Language

Canonical path: `reports/visual-language/style-variables/colors.md`  
Evidence path: `evidence/visual-language/color-contrast/contrast-audit-001.md`

### 5.1 Base surfaces

| Variable | Value | Usage |
|---|---:|---|
| `color.bg.void` | `#05070A` | Application background, deepest layer |
| `color.bg.base` | `#0A0F16` | Main workspace background |
| `color.bg.surface` | `#111823` | Panels, cards, tool surfaces |
| `color.bg.raised` | `#182231` | Hover, selected, elevated controls |
| `color.bg.overlay` | `#0B111CCC` | Modal and drawer overlay |
| `color.border.subtle` | `#263449` | Dividers, card borders |
| `color.border.strong` | `#3B4C66` | Focus boundaries, active frames |

### 5.2 Text colors

| Variable | Value | Usage |
|---|---:|---|
| `color.text.primary` | `#E6F1FF` | Primary labels and content |
| `color.text.secondary` | `#9FB3C8` | Supporting text, metadata |
| `color.text.muted` | `#6F8199` | Disabled or low-priority text |
| `color.text.inverse` | `#05070A` | Text on bright accent surfaces |

### 5.3 Accent colors

| Variable | Value | Usage |
|---|---:|---|
| `color.accent.primary` | `#38BDF8` | Primary actions, active navigation, selection |
| `color.accent.hover` | `#7DD3FC` | Hover state for primary accent |
| `color.accent.pressed` | `#0EA5E9` | Pressed state for primary accent |
| `color.accent.soft` | `#0B2A3A` | Accent-tinted background |
| `color.accent.focus` | `#7DD3FC` | Focus ring |

### 5.4 Semantic state colors

| Variable | Value | Meaning |
|---|---:|---|
| `color.state.success` | `#34D399` | Healthy, ready, committed, validated |
| `color.state.info` | `#60A5FA` | Informational, discovered, planned |
| `color.state.warning` | `#FBBF24` | Degraded, staged, pending validation, restart |
| `color.state.danger` | `#F87171` | Failed, blocked, destructive, rollback required |
| `color.state.neutral` | `#9FB3C8` | Unknown, disabled, inactive |

### 5.5 Color usage rules

1. Use `color.accent.primary` only for primary interaction or active state.
2. Use `color.state.danger` only for failure, destructive confirmation, or blocked migration.
3. Use `color.state.warning` for staged, pending, degraded, or attention-required states.
4. Use `color.state.success` only after validation or confirmed healthy state.
5. Do not encode service state by color alone; pair with icon or text label.
6. Maintain minimum readable contrast for body text and controls.
7. Avoid saturated accent fills for large surfaces.

---

## 6. Typography

Canonical path: `reports/visual-language/style-variables/typography.md`  
Evidence path: `evidence/visual-language/typography/type-scale-audit-001.md`

### 6.1 Font families

| Variable | Preferred stack | Fallback |
|---|---|---|
| `font.ui` | `Inter`, `Noto Sans`, `DejaVu Sans` | system sans-serif |
| `font.display` | `Inter`, `Noto Sans`, `DejaVu Sans` | system sans-serif |
| `font.mono` | `JetBrains Mono`, `Noto Sans Mono`, `DejaVu Sans Mono` | system monospace |

### 6.2 Type scale

| Variable | Size / line height | Usage |
|---|---:|---|
| `type.display` | 48px / 56px | Splash, major empty-state headline |
| `type.h1` | 32px / 40px | Page title |
| `type.h2` | 24px / 32px | Section title |
| `type.h3` | 20px / 28px | Card title, panel heading |
| `type.h4` | 18px / 26px | Subsection heading |
| `type.body` | 16px / 24px | Default content |
| `type.body.small` | 14px / 20px | Secondary content |
| `type.caption` | 12px / 16px | Metadata, timestamps, hints |
| `type.button` | 14px / 20px | Buttons and controls |
| `type.mono` | 14px / 20px | Logs, commands, service identifiers |

### 6.3 Typography rules

1. Use `type.h1` once per main view.
2. Use `type.h3` for tool cards and service groups.
3. Use `type.mono` for service names, unit names, package names, and command output.
4. Do not use uppercase for long labels.
5. Use sentence case for actions and descriptions.
6. Keep line length readable; avoid full-width paragraphs in dense tool views.
7. If preferred fonts are unavailable, preserve hierarchy through size and weight.

---

## 7. Layout Rules

Canonical path: `reports/visual-language/style-variables/spacing.md`  
Evidence path: `evidence/visual-language/layout/grid-audit-001.md`

### 7.1 Spacing scale

| Variable | Value | Usage |
|---|---:|---|
| `space.0` | 0px | Reset |
| `space.1` | 4px | Tight icon-label pairs |
| `space.2` | 8px | Base control spacing |
| `space.3` | 12px | Compact groups |
| `space.4` | 16px | Default gap |
| `space.5` | 24px | Card padding, section spacing |
| `space.6` | 32px | Panel separation |
| `space.7` | 48px | Major layout separation |

### 7.2 Radius and elevation

| Variable | Value | Usage |
|---|---:|---|
| `radius.control` | 8px | Buttons, inputs, small controls |
| `radius.card` | 12px | Tool cards, service cards |
| `radius.panel` | 16px | Large panels, drawers |
| `elevation.low` | subtle border + surface | Default cards |
| `elevation.medium` | raised surface + border | Hover or selected cards |
| `elevation.high` | overlay + shadow | Modals, command palette |

### 7.3 Layout geometry

| Variable | Value | Usage |
|---|---:|---|
| `layout.sidebar.width` | 280px | Primary navigation |
| `layout.sidebar.collapsed` | 72px | Compact navigation |
| `layout.content.max` | 1200px | Maximum content width |
| `layout.card.min` | 240px | Minimum tool-card width |
| `layout.card.gap` | 16px | Grid gap |
| `layout.detail.width` | 360px | Detail drawer or inspector |
| `layout.topbar.height` | 56px | Global top bar |

### 7.4 Breakpoints

| ID | Range | Behavior |
|---|---|---|
| VL-BP-01 | compact: `< 900px` | Sidebar collapses, cards become single-column |
| VL-BP-02 | standard: `900px–1280px` | Sidebar visible, two-column card grid |
| VL-BP-03 | wide: `> 1280px` | Sidebar visible, multi-column grid, detail pane allowed |

### 7.5 Layout rules

1. Use an 8px base grid; 4px is allowed only for icon-text alignment.
2. Tool cards must remain readable at `layout.card.min`.
3. Destructive actions must not be placed adjacent to routine primary actions without separation.
4. Service lists must align status, name, and action columns.
5. Repair and migration views must show state progression in a stable vertical or horizontal flow.
6. Drawers must not obscure the primary decision unless they are modal and explicitly labeled.

---

## 8. Component Catalogue

Canonical path: `reports/visual-language/04-component-catalog.md`

### 8.1 Application shell

| Component | Purpose | Required states |
|---|---|---|
| `AppShell` | Root layout | default, compact, wide |
| `TopBar` | Global context, search, status | default, busy, error |
| `SidebarNav` | Category navigation | expanded, collapsed, active, disabled |
| `StatusBar` | Persistent system health summary | healthy, warning, danger, unknown |

### 8.2 Toolbox components

| Component | Purpose | Required states |
|---|---|---|
| `ToolGrid` | Grid of available tools | default, filtered, empty, loading |
| `ToolCard` | Single tool entry | default, hover, selected, disabled, destructive |
| `ToolCategoryHeader` | Category grouping | default, collapsed |
| `ToolDetailPane` | Detailed tool information | default, running, success, failure |
| `CommandPalette` | Search and command entry | closed, open, no-results |
| `TerminalDrawer` | Command output and logs | closed, running, success, failure |

### 8.3 Service and supervision components

| Component | Purpose | Required states |
|---|---|---|
| `ServiceRow` | One service entry | down, up, ready, failed, restarting, disabled |
| `ServiceTree` | Dependency or supervision tree | collapsed, expanded, failed-child |
| `StatusPill` | Compact state label | success, info, warning, danger, neutral |
| `ServiceActionGroup` | Start, stop, restart, enable, disable | default, destructive, disabled |
| `LogViewer` | Service or journal output | idle, streaming, paused, error |

### 8.4 Repair and migration components

| Component | Purpose | Required states |
|---|---|---|
| `RepairPlanView` | Shows planned repair actions | draft, validated, staged, executing |
| `MigrationTimeline` | Shows migration or repair progression | pending, active, complete, failed, rolled-back |
| `ValidationPanel` | Shows checks and results | pending, passing, failing, skipped |
| `RollbackBanner` | Shows recovery or compensating action | available, required, completed |
| `JournalEntry` | One auditable operation record | recorded, verified, failed |

---

## 9. Obarun/66+s6 Service-State Visual Semantics

Canonical path: `reports/visual-language/05-obarun-66-s6-service-semantics.md`  
Evidence paths:

- `evidence/visual-language/obarun-66-s6/service-state-observation-001.md`
- `evidence/visual-language/obarun-66-s6/service-tree-observation-001.md`

### 9.1 State mapping

| Service state | Visual variable | Label | Icon/text requirement |
|---|---|---|---|
| `down` | `color.state.neutral` | Down | Must include text label |
| `up` | `color.state.info` | Up | May include activity indicator |
| `ready` | `color.state.success` | Ready | Must include text label |
| `failed` | `color.state.danger` | Failed | Must include text label and recovery hint |
| `restarting` | `color.state.warning` | Restarting | Must include animated or textual progress |
| `disabled` | `color.text.muted` | Disabled | Must include disabled action state |
| `unknown` | `color.state.neutral` | Unknown | Must not imply healthy state |

### 9.2 Semantic transitions

| Transition | Visual behavior |
|---|---|
| `down → up` | Status changes from neutral to info; optional activity indicator |
| `up → ready` | Status changes from info to success; readiness confirmed |
| `ready → failed` | Status changes to danger; failure details become available |
| `failed → restarting` | Status changes to warning; restart progress shown |
| `restarting → ready` | Status returns to success after validation |
| `ready → down` | Status changes to neutral; reason should be available if known |
| `enabled ↔ disabled` | Action availability changes; state label remains explicit |

### 9.3 Service-tree rules

1. Parent service state must not hide failed child state.
2. A failed child must propagate a visible warning or danger marker to the parent.
3. Collapsed tree nodes must show aggregate health.
4. Service identifiers must use `type.mono`.
5. Actions must be disabled when the current user lacks capability, with an explanatory label.

---

## 10. Garuda Toolbox-Inspired Layout for SunshineOS

Canonical path: `reports/visual-language/06-garuda-toolbox-layout.md`  
Evidence paths:

- `evidence/visual-language/garuda-toolbox/observation-001.md`
- `evidence/visual-language/garuda-toolbox/observation-002.md`
- `evidence/visual-language/debranding/no-garuda-marking-audit-001.md`

### 10.1 Adopted interaction patterns

The SunshineOS toolbox should preserve the useful interaction model of Garuda Toolbox while replacing branding and visual identity:

| Pattern | SunshineOS adoption |
|---|---|
| Category navigation | Left sidebar with system, services, packages, recovery, logs, network, storage, security |
| Tool grid | Searchable card grid with concise descriptions |
| One-click task entry | Cards expose primary action and secondary details |
| Output visibility | Terminal or log drawer shows command output |
| Status awareness | Cards and rows show success, warning, failure, or disabled state |
| Recovery orientation | Repair and rollback tools are first-class categories |

### 10.2 Required exclusions

| Exclusion | Rule |
|---|---|
| Garuda name | Must not appear as product branding |
| Garuda logo or mascot | Must not appear in SunshineOS UI |
| Garuda-specific marketing copy | Must be rewritten in SunshineOS voice |
| Garuda color branding | Must be replaced by SunshineOS color variables |
| Garuda repository or support links | Must not be presented as SunshineOS support |

### 10.3 Toolbox layout structure

| Region | Content |
|---|---|
| Top bar | Application title, global search, system health summary |
| Sidebar | Tool categories and pinned tools |
| Main content | Tool grid or selected tool detail |
| Detail pane | Selected tool description, actions, prerequisites, output |
| Bottom drawer | Terminal output, logs, validation results |

### 10.4 Tool-card anatomy

Each `ToolCard` should contain:

1. Tool name.
2. One-line purpose.
3. Category label.
4. State indicator.
5. Primary action.
6. Optional secondary action.
7. Safety note if the action is destructive or requires staging.

---

## 11. Repair and Migration Visual States

Canonical path: `reports/visual-language/07-repair-and-migration-visual-states.md`

### 11.1 State mapping

| State | Color | Label | Required behavior |
|---|---|---|---|
| `unknown` | neutral | Unknown | Do not imply safety |
| `discovered` | info | Discovered | Show observed system facts |
| `planned` | accent | Planned | Show proposed operations |
| `staged` | warning | Staged | Show that changes are prepared but not committed |
| `validating` | info | Validating | Show checks in progress |
| `committed` | success | Committed | Show completed desired state |
| `failed` | danger | Failed | Show failure and recovery options |
| `rolled-back` | warning | Rolled back | Show compensating action completed |
| `blocked` | danger | Blocked | Show unmet precondition |

### 11.2 Repair workflow display

A repair workflow should be visible as a sequence:

1. Inspect.
2. Diagnose.
3. Plan.
4. Stage.
5. Validate.
6. Commit or roll back.
7. Record evidence.

Each step must have a visible state and must not silently skip validation.

### 11.3 Safety rules

1. Destructive repair actions require explicit confirmation.
2. Staged changes must be distinguishable from committed changes.
3. Rollback availability must be visible before commit when possible.
4. Failed validation must not be presented as success.
5. Logs must remain accessible after failure.

---

## 12. Test Matrix

Canonical path: `repo…
