# Cross-distro visual language research

- Agent: sub-design-research
- Model: baidu/ernie-5.5-flash-preview:free
- Completed: 2026-11-21 00:15

---

# SunshineOS Visual Language Research  
**Scope:** Garuda, EndeavourOS, CachyOS, Omarchy, SteamOS, Windows 11  
**Goal:** Define a coherent, enterprise-grade visual language for SunshineOS that supports sustainability, stability, reliability, and long-term migration.

**Context references:**  
- `reports/USER_MIGRATION_MANDATE_2026-11-21.md`  
- `reports/OPENCLAW_ORDER_3_CONVERGENCE_ARCHITECTURE.md`

---

## 1. Executive design direction

SunshineOS should not look like a gaming distro, a terminal-only distro, or a consumer desktop clone. Its visual language should communicate:

- **Trust** — stable, predictable, repairable.
- **Clarity** — system state is visible and understandable.
- **Control** — migration, rollback, validation, and repair are first-class UI concepts.
- **Calm density** — technical information is rich but not noisy.
- **Long-term coherence** — design tokens and semantic rules survive decades of evolution.

Recommended visual thesis:

> **“Calm infrastructure with sunlight clarity.”**  
> Dark, precise, high-contrast surfaces; restrained color; strong state signaling; visible recovery paths.

---

## 2. Comparative visual analysis

| System | Visual thesis | What is visually coherent | Poor decisions / risks | What SunshineOS should adopt |
|---|---|---|---|---|
| **Garuda** | Performance/gaming-oriented Arch with energetic dark visuals | Strong dark base, vivid accents, dense system information, toolbox-style utility apps, clear performance identity | Theme sprawl, mascot/branding can feel consumer-gaming rather than enterprise, inconsistent iconography, excessive visual effects | Adopt the **toolbox/repair-hub pattern**, dense status awareness, and keyboard-friendly utility design, but with restrained SunshineOS branding and semantic color |
| **EndeavourOS** | Friendly, terminal-aware Arch experience | Clean blue/white identity, low visual noise, welcoming installer, developer-friendly clarity | Visual identity can feel generic; terminal-centric patterns may intimidate non-experts; limited enterprise-grade system-state visualization | Adopt **plain-language onboarding**, progressive disclosure, and a calm welcome/repair center |
| **CachyOS** | Performance-optimized Arch with modern dark UI | Crisp dark panels, technical tone, performance/gaming alignment, clean blue/cyan accents | Can resemble generic Arch gaming setups; marketing language may outpace actual UI coherence | Adopt **performance telemetry presentation**, clean optimization status, and explicit system-health indicators |
| **Omarchy** | Opinionated, minimal, keyboard-driven desktop | Calm focus, low distraction, fast interaction model, strong keyboard-first philosophy | Discoverability can suffer; sparse affordances may confuse users who need visible recovery or support paths | Adopt **focus mode**, keyboard shortcuts, and minimal chrome, but keep critical system actions visible |
| **SteamOS** | Console-like, gamepad-first, dark high-contrast UI | Excellent readability at distance, large targets, simple navigation, strong focus states | Too simplified for productivity; limited desktop metaphor; not suitable as full enterprise OS UI | Adopt **large hit targets**, clear focus states, modal task flows, and controller/touch accessibility |
| **Windows 11** | Consumer Fluent design with rounded, material surfaces | Approachable typography, centered shell, depth, acrylic/mica materials, strong consumer polish | Legacy UI inconsistency, visual noise, ads/irrelevant content, rounded chrome can reduce technical density | Adopt **material surfaces, type scale, motion discipline, and accessibility**, but avoid consumer clutter and inconsistent legacy patterns |

---

## 3. What makes each system visually coherent

### Garuda
Garuda is coherent because it commits to a **performance/gaming identity**. Dark backgrounds, bright accents, dense widgets, and utility apps create a recognizable “power user” environment.

**Strength:** It makes system activity feel visible and immediate.  
**Weakness:** The visual language can become too playful or overloaded for an OS intended to be stable for 20 years.

### EndeavourOS
EndeavourOS is coherent through **restraint**. Its blue/white palette and terminal-friendly presentation communicate simplicity and Arch transparency.

**Strength:** Low visual noise.  
**Weakness:** It does not strongly communicate advanced recovery, migration, or enterprise reliability.

### CachyOS
CachyOS is coherent through **technical performance signaling**. Dark surfaces and cool accents suggest speed, optimization, and modern hardware awareness.

**Strength:** Clean technical mood.  
**Weakness:** It risks looking like another Arch gaming variant unless the UI clearly exposes optimization, reliability, and system state.

### Omarchy
Omarchy is coherent through **minimalism and keyboard-first flow**. It feels calm and fast.

**Strength:** Excellent focus.  
**Weakness:** Minimalism can hide important system affordances. SunshineOS needs visible recovery and migration controls.

### SteamOS
SteamOS is coherent because it is designed for **controller-first, low-friction interaction**. Large targets, strong focus, and dark contrast make it readable.

**Strength:** Excellent accessibility for non-desktop input.  
**Weakness:** It is not designed for complex system administration or long-term desktop workflows.

### Windows 11
Windows 11 is coherent through **Fluent material design**: rounded corners, layered surfaces, typography, and motion.

**Strength:** Approachable and polished.  
**Weakness:** Consumer priorities can conflict with technical density, transparency, and enterprise trust.

---

## 4. Poor decisions SunshineOS should avoid

1. **Mascot-first branding**  
   Avoid making the OS feel like a gaming community product. SunshineOS should feel durable and trustworthy.

2. **Too many accent colors**  
   Use one primary accent and semantic colors only.

3. **Heavy blur, glow, or neon effects**  
   These reduce readability and can make the system feel unstable.

4. **Hidden recovery tools**  
   Repair, rollback, migration validation, and recovery must be visible.

5. **Terminal-only user experience**  
   Terminal is powerful, but SunshineOS should provide guided UI for migration and repair.

6. **Inconsistent icon sizes and stroke weights**  
   Use one icon grid and one stroke system.

7. **Consumer clutter**  
   No ads, no promotional widgets, no irrelevant notifications.

8. **Over-rounded consumer chrome**  
   Use subtle rounding, not excessive pill-shaped UI.

9. **Theme sprawl**  
   Themes should be token-driven and semantically constrained.

10. **Visual discontinuity between releases**  
   The visual language must remain stable across evolutionary milestones.

---

# 5. SunshineOS mood-board reference list

| Reference | Mood | Borrow | Avoid | SunshineOS translation |
|---|---|---|---|---|
| **Arch terminal clarity** | Precise, direct, transparent | Monospace accents, explicit state, no hidden magic | Hostile minimalism | Use monospace for logs, package states, and migration journals |
| **Garuda Toolbox** | Utility-rich, action-oriented | Category navigation, repair actions, status chips, one-click tools | Gaming branding, visual overload | Build a SunshineOS Repair & Migration Center with calm enterprise styling |
| **EndeavourOS Welcome** | Friendly onboarding | Clear first-run guidance, simple language | Generic flatness | Create a “System Readiness” dashboard with migration status and next actions |
| **CachyOS performance panels** | Technical, optimized | Performance telemetry, optimization badges | Marketing-heavy tone | Show kernel, scheduler, power, and storage health as verifiable system state |
| **Omarchy focus mode** | Calm, distraction-free | Keyboard-first flows, minimal chrome | Hidden critical controls | Add Focus Mode while keeping recovery and migration always accessible |
| **SteamOS Deck UI** | Console-like clarity | Large targets, strong focus, simple navigation | Oversimplified desktop | Use large actionable cards for major system operations |
| **Windows 11 Fluent** | Material, approachable | Layered surfaces, typography, motion | Consumer noise, inconsistent legacy UI | Use subtle elevation, accessible contrast, and disciplined motion |
| **SunshineOS synthesis** | Solar, reliable, infrastructural | Warm accent, dark technical base, semantic state colors | Neon overload | “Sunlight on slate”: dark surfaces with warm signal color |

---

# 6. Concrete SunshineOS visual system

## 6.1 Core palette: “Sunlight on Slate”

### Dark theme — default

| Token | Hex | Use |
|---|---:|---|
| `bg.base` | `#0B0F14` | Application background |
| `bg.surface` | `#111827` | Panels, cards, sidebars |
| `bg.elevated` | `#1F2937` | Modals, menus, elevated controls |
| `border.subtle` | `#263241` | Dividers, card borders |
| `border.strong` | `#3B4A5A` | Focused or active borders |
| `text.primary` | `#F8FAFC` | Primary text |
| `text.secondary` | `#CBD5E1` | Secondary text |
| `text.muted` | `#94A3B8` | Metadata, hints |
| `accent.sunlight` | `#FFB020` | Primary SunshineOS accent |
| `accent.sky` | `#4CC2FF` | Informational highlights |
| `state.success` | `#34D399` | Healthy, validated, complete |
| `state.warning` | `#FBBF24` | Caution, pending review |
| `state.danger` | `#F87171` | Failure, destructive action |
| `state.migration` | `#A78BFA` | Migration-specific states |
| `state.neutral` | `#64748B` | Disabled or unknown |

### Light theme — optional but recommended

| Token | Hex | Use |
|---|---:|---|
| `bg.base` | `#F8FAFC` | Light background |
| `bg.surface` | `#FFFFFF` | Cards and panels |
| `border.subtle` | `#E2E8F0` | Borders |
| `text.primary` | `#0F172A` | Primary text |
| `text.secondary` | `#334155` | Secondary text |
| `accent.sunlight.fill` | `#FFB020` | Accent fills with dark text |
| `accent.sunlight.text` | `#92400E` | Accent text on light backgrounds |
| `state.success` | `#047857` | Success text/fills |
| `state.danger` | `#B91C1C` | Danger text/fills |

**Rule:** Use `accent.sunlight` sparingly. It should signal SunshineOS identity, primary actions, and important system signals — not every button.

---

## 6.2 Typography

### Recommended fonts

| Role | Font | Reason |
|---|---|---|
| UI | **Inter** | Open, highly legible, excellent for enterprise UI |
| Display / headings | **Inter Tight** or Inter SemiBold | Clean hierarchy without decorative excess |
| Code / logs | **JetBrains Mono** | Clear terminal and migration journal readability |
| Optional numeric | Inter tabular numerals | Useful for versions, hashes, package counts |

### Type scale

| Token | Size / Line | Weight | Use |
|---|---:|---|---|
| `display` | 32 / 40 | 600 | Major dashboard title |
| `h1` | 24 / 32 | 600 | Page title |
| `h2` | 20 / 28 | 600 | Section title |
| `h3` | 16 / 24 | 600 | Card title, subsection |
| `body` | 14 / 20 | 400 | Default UI text |
| `label` | 12 / 16 | 500 | Buttons, metadata, table headers |
| `micro` | 11 / 14 | 500 | Status chips, timestamps |
| `code` | 13 / 20 | 400 | Logs, package names, hashes |

**Rule:** Avoid body text below 12px except for nonessential metadata. Critical system state should never rely on tiny text.

---

## 6.3 Spacing and layout

### Spacing scale

Use an 8px base grid with 4px half-steps where needed.

| Token | Value |
|---|---:|
| `space.1` | 4px |
| `space.2` | 8px |
| `space.3` | 12px |
| `space.4` | 16px |
| `space.5` | 24px |
| `space.6` | 32px |
| `space.7` | 48px |
| `space.8` | 64px |

### Application shell

| Region | Recommended size |
|---|---:|
| Left navigation | 240px expanded, 64px collapsed |
| Top bar | 48px |
| Status bar | 32px |
| Content max width | 1200px |
| Main gutter | 16px |
| Page margin | 24px |

### Grid

- 12-column responsive grid.
- Desktop content max width: `1200px`.
- Tablet: 8-column.
- Mobile: 4-column.
- Critical actions must remain reachable at `800x600` and above.

---

## 6.4 Shape, elevation, and borders

| Element | Recommendation |
|---|---|
| Corner radius | 6px for controls, 8px for cards, 12px for modals |
| Border | 1px solid `border.subtle` |
| Focus ring | 2px `accent.sky` with 2px offset |
| Shadow | Subtle only; avoid heavy glow |
| Elevation | Use background lightness, not aggressive shadows |

**Rule:** SunshineOS should feel precise, not glossy.

---

## 6.5 Iconography

- Grid: **24px**
- Stroke: **2px**
- Caps: rounded
- Style: monochrome line icons with semantic color accents
- Avoid: mascots, 3D icons, inconsistent filled/outline mixtures

Icon categories:

| Category | Examples |
|---|---|
| System | CPU, memory, disk, network, power |
| Migration | source state, target state, diff, journal, rollback |
| Recovery | repair, snapshot, restore, validate |
| Packages | installed, available, broken, orphaned |
| Services | running, stopped, failed, masked |
| Security | policy, signature, permission, audit |

---

# 7. Key SunshineOS screens

## 7.1 System Overview

Purpose: show whether the system is healthy, migratable, and recoverable.

Layout:

```text
┌──────────────────────────────────────────────┐
│ Top bar: system name, version, status        │
├────────────┬─────────────────────────────────┤
│ Sidebar    │ Main content                    │
│            │                                 │
│ Overview   │ ┌─────────────┐ ┌─────────────┐ │
│ Migration  │ │ Health      │ │ Recovery    │ │
│ Packages   │ │ score/state │ │ readiness   │ │
│ Services   │ └─────────────┘ └─────────────┘ │
│ Storage    │                                 │
│ Security   │ ┌─────────────────────────────┐ │
│ Logs       │ │ Recent events / alerts      │ │
│ Settings   │ └─────────────────────────────┘ │
├────────────┴─────────────────────────────────┤
│ Status bar: kernel, initramfs, last check    │
└──────────────────────────────────────────────┘
```

Visual rules:

- Health state uses `state.success`, `state.warning`, `state.danger`.
- Migration readiness uses `state.migration`.
- Never hide failed services behind generic “OK” indicators.

---

## 7.2 Migration Center

Purpose: make target-state migration understandable and recoverable.

Recommended pipeline visualization:

```text
Discover → Plan → Stage → Validate → Commit → Recover
```

Each stage should show:

- Current state
- Target state
- Required artifacts
- Validation result
- Journal entry
- Rollback availability

Color usage:

| Stage | Color |
|---|---|
| Discover | `accent.sky` |
| Plan | `accent.sunlight` |
| Stage | `state.migration` |
| Validate | `state.warning` or `state.success` |
| Commit | `state.success` |
| Recover | `state.danger` or `state.warning` |

**Rule:** The UI must make it obvious whether an operation is staged, validated, committed, or recoverable.

---

## 7.3 SunshineOS Toolbox

Inspired by Garuda Toolbox, but visually distinct.

Recommended layout:

```text
┌──────────────────────────────────────────────┐
│ Search tools, packages, services, logs       │
├────────────┬─────────────────┬───────────────┤
│ Categories │ Tool list       │ Detail/actions│
│            │                 │               │
│ Repair     │ Package repair  │ Status        │
│ Migration  │ Initramfs check │ Actions       │
│ Services   │ fstab validator │ Logs          │
│ Storage    │ Service doctor  │ Journal       │
│ Network    │ Boot checker    │ Rollback      │
│ Security   │ Snapshot verify │               │
└────────────┴─────────────────┴───────────────┘
```

Toolbox principles:

- Every tool has a visible state: `healthy`, `warning`, `failed`, `unknown`.
- Every mutating action requires confirmation and produces a journal entry.
- Every repair action should show what will be changed before execution.
- No Garuda branding, mascots, or copied visual identity.

---

## 7.4 Repair and Recovery Screen

This is a core SunshineOS differentiator.

Required modules:

| Module | Purpose |
|---|---|
| Service repair | Detect and recover failed daemons |
| Package repair | Verify package database and reinstall broken packages |
| Initramfs repair | Rebuild and validate initramfs |
| fstab validation | Check mounts, UUIDs, and filesystem states |
| Boot repair | Validate bootloader entries and kernel links |
| Snapshot recovery | Restore from known-good state |
| Migration rollback | Return to pre-migration state |
| Journal export | Produce evidence bundle for support |

Visual pattern:

- Use a large status header: `System Healthy`, `Degraded`, `Recovery Required`.
- Use cards for each repair domain.
- Use explicit buttons: `Validate`, `Stage Repair`, `Apply Repair`, `Rollback`.
- Avoid vague labels like “Fix Now” without explaining the operation.

---

# 8. Component styling rules

## Buttons

| Type | Use |
|---|---|
| Primary | Main safe action, e.g. `Validate`, `Continue` |
| Secondary | Alternative action, e.g. `View Journal` |
| Danger | Destructive or high-risk action, e.g. `Rollback` |
| Ghost | Low-emphasis utility action |
| Icon | Toolbar actions with tooltips |

Button heights:

- Compact: 32px
- Default: 40px
- Touch/controller: 44px minimum

## Status chips

| State | Color |
|---|---|
| Healthy | `state.success` |
| Pending | `state.warning` |
| Failed | `state.danger` |
| Migration | `state.migration` |
| Unknown | `state.neutral` |

## Tables

- Row height: 40px
- Header height: 36px
- Use tabular numerals for versions, sizes, timestamps.
- Show state as text plus color, not color alone.

## Logs and journals

- Use JetBrains Mono.
- Timestamp, severity, component, message.
- Provide filtering by service, package, migration event, and severity.
- Logs must be exportable as evidence bundles.

---

# 9. Motion guidelines

Motion should communicate state changes, not decorate.

| Duration | Use |
|---|---|
| 120ms | Hover, focus, small state changes |
| 200ms | Dropdowns, tooltips, inline validation |
| 320ms | Panels, modals, major transitions |
| 500ms+ | Avoid except for explicit long-running progress |

Rules:

- Respect `prefers-reduced-motion`.
- Do not animate critical warnings in a way that delays comprehension.
- Progress indicators must show determinate progress when possible.

---

# 10. Accessibility requirements

SunshineOS visual language must meet enterprise accessibility expectations.

- WCAG AA contrast minimum for normal text.
- Do not rely on color alone for state.
- Focus states must be visible.
- Keyboard navigation must reach all critical actions.
- Controller/touch targets should be at least 44px where feasible.
- Provide high-contrast mode.
- Provide reduced-motion mode.
- Ensure logs and migration journals are screen-reader navigable.

---

# 11. Recommended SunshineOS visual identity summary

| Attribute | Recommendation |
|---|---|
| Personality | Calm, precise, reliable, solar |
| Primary accent | Sunlight amber `#FFB020` |
| Secondary accent | Sky blue `#4CC2FF` |
| Base mood | Dark slate infrastructure |
| Typography | Inter + JetBrains Mono |
| Shape | Subtle rounded rectangles |
| Density | Technical but breathable |
| Motion | Functional, fast, restrained |
| Iconography | 24px line icons, 2px stroke |
| Avoid | Mascots, neon overload, ads, hidden recovery |

---

# 12. Final recommendation

SunshineOS should adopt the **best structural ideas** from the researched systems while rejecting their visual weaknesses:

- From **Garuda**: toolbox utility, system awareness, action density.
- From **EndeavourOS**: clarity, friendliness, low noise.
- From **CachyOS**: performance telemetry and technical precision.
- From **Omarchy**: focus, keyboard-first speed, minimal distraction.
- From **SteamOS**: large targets, strong focus states, simple task flows.
- From **Windows 11**: material surfaces, typography discipline, accessible polish.

The resulting SunshineOS visual language should be:

> **A calm, dark, high-trust system interface with warm solar accents, explicit migration states, visible recovery tools, and en…
