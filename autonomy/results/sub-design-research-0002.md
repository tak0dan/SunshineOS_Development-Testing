# sub-design-research / EndeavourOS visual language / Obarun/66+s6

- Agent: sub-design-research
- Model: baidu/ernie-5.5-flash-preview:free
- Parent directive: none
- Completed: 2026-11-21 00:18

---

# EndeavourOS Visual Language in Obarun/66+s6 — Wave 1

## 0. Document control

- **Repository:** `/home/tak_0/sunshineos-audit/SunshineOS_Development-Testing`
- **Context inputs:**
  - `reports/USER_MIGRATION_MANDATE_2026-11-21.md`
  - `reports/ARCHITECTURE_DECISIONS.md`
  - `autonomy/results`
- **Deliverable path:** `reports/visual-language/ENDEAVOUROS_VISUAL_LANGUAGE_OBARUN_66S6_W1.md`
- **Evidence root:** `evidence/visual-language/endeavouros-wave1/`
- **Identifier:** `VL-EOS-W1`
- **Normative status:** Wave 1 baseline for SunshineOS/Obarun visual surfaces. EndeavourOS is a **pattern reference**, not a trademark source. Do not copy EndeavourOS logos, wallpapers, or marks.

No passwords, API keys, tokens, or key material are included.

---

## 1. Exact path catalogue

| Exact path | Purpose |
|---|---|
| `reports/visual-language/ENDEAVOUROS_VISUAL_LANGUAGE_OBARUN_66S6_W1.md` | This Wave 1 reference. |
| `reports/visual-language/ENDEAVOUROS_COLOR_TOKENS.md` | Normative color token table. |
| `reports/visual-language/ENDEAVOUROS_TYPE_SCALE.md` | Normative typography scale. |
| `reports/visual-language/ENDEAVOUROS_LAYOUT_RULES.md` | Normative spacing, grid, radius, and elevation rules. |
| `autonomy/results/visual-language/endeavouros-wave1/survey.md` | Survey notes and observed EndeavourOS patterns. |
| `autonomy/results/visual-language/endeavouros-wave1/path-catalogue.md` | Machine-readable path catalogue for Wave 1. |
| `evidence/visual-language/endeavouros-wave1/palette-extract.txt` | Extracted color evidence. |
| `evidence/visual-language/endeavouros-wave1/type-metrics.txt` | Extracted font and type-scale evidence. |
| `evidence/visual-language/endeavouros-wave1/layout-grid.svg` | Layout grid evidence. |
| `evidence/visual-language/endeavouros-wave1/66-s6-state-matrix.csv` | 66/s6 service-state visual mapping. |
| `evidence/visual-language/endeavouros-wave1/contrast-report.txt` | Contrast and accessibility evidence. |
| `evidence/visual-language/endeavouros-wave1/asset-provenance.md` | Asset provenance and trademark boundary. |
| `evidence/visual-language/endeavouros-wave1/secret-scan.txt` | Credential-hygiene scan result. |
| `evidence/visual-language/endeavouros-wave1/test-run.tap` | Wave 1 test output. |
| `evolution-engine/visual-language/endeavouros/tokens.yaml` | Target implementation path for versioned visual tokens. |
| `evolution-engine/visual-language/endeavouros/README.md` | Target integration notes for Obarun/66+s6 surfaces. |

---

## 2. Survey summary

Wave 1 identifies four durable EndeavourOS-inspired patterns suitable for Obarun/66+s6:

1. **Dark, calm canvas** with blue primary and violet accent.
2. **High-legibility sans-serif** for UI text, with monospace reserved for technical identity.
3. **Restrained rounded geometry** using an 8px layout grid.
4. **Explicit system-state language** suitable for 66/s6 service supervision.

Evidence paths:

- Color: `evidence/visual-language/endeavouros-wave1/palette-extract.txt`
- Type: `evidence/visual-language/endeavouros-wave1/type-metrics.txt`
- Layout: `evidence/visual-language/endeavouros-wave1/layout-grid.svg`
- Service states: `evidence/visual-language/endeavouros-wave1/66-s6-state-matrix.csv`

---

## 3. Color reference

Dark theme is canonical. Light theme is derived and must preserve semantic contrast.

| Token | Value | Use | Rule |
|---|---:|---|---|
| `--vl-eos-bg-base` | `#0B1020` | Application base background. | Primary text must exceed 7:1 contrast. |
| `--vl-eos-bg-surface` | `#121A2B` | Panels, sidebars, cards. | Use 1px border, not heavy shadow. |
| `--vl-eos-bg-raised` | `#1B2438` | Hover, selected, elevated controls. | Do not use for long-form text. |
| `--vl-eos-border` | `#2A3650` | Borders and dividers. | Must remain visible on base and surface. |
| `--vl-eos-text-primary` | `#E6ECF5` | Primary text. | Never place on warning/danger fills. |
| `--vl-eos-text-muted` | `#9AA7B8` | Secondary text, metadata. | Minimum 4.5:1 on base. |
| `--vl-eos-primary` | `#5B9BD5` | Primary actions, links, focus. | Do not use as large text fill. |
| `--vl-eos-primary-strong` | `#3F7FBF` | Hover/active primary. | Maintain visible focus ring. |
| `--vl-eos-accent` | `#8A7CF6` | Sparse accent, selection, highlights. | Use sparingly; never for body text. |
| `--vl-eos-success` | `#4CAF7D` | Ready/healthy state. | Must include icon and label. |
| `--vl-eos-warning` | `#E2A33B` | Degraded/attention state. | Must include icon and label. |
| `--vl-eos-danger` | `#D9534F` | Failed/error state. | Must include icon and label. |
| `--vl-eos-info` | `#56B6C2` | Informational state. | Not a substitute for primary action. |

Derived light theme:

| Token | Value |
|---|---:|
| `--vl-eos-bg-base-light` | `#F5F7FA` |
| `--vl-eos-bg-surface-light` | `#FFFFFF` |
| `--vl-eos-text-primary-light` | `#111827` |
| `--vl-eos-text-muted-light` | `#4B5563` |
| `--vl-eos-primary-light` | `#2F6DB3` |

Normative path: `reports/visual-language/ENDEAVOUROS_COLOR_TOKENS.md`

---

## 4. Type scale

Primary UI font stack:

```text
Inter, "Noto Sans", "DejaVu Sans", sans-serif
```

Monospace stack:

```text
"JetBrains Mono", "Fira Code", "DejaVu Sans Mono", monospace
```

| Token | Size / line | Weight | Use |
|---|---:|---:|---|
| `--vl-type-display` | 32 / 40 | 700 | Hero headers, installer title. |
| `--vl-type-h1` | 24 / 32 | 700 | Page title. |
| `--vl-type-h2` | 20 / 28 | 600 | Section title. |
| `--vl-type-h3` | 16 / 24 | 600 | Card title, group label. |
| `--vl-type-body` | 14 / 20 | 400 | Default UI text. |
| `--vl-type-small` | 12 / 16 | 400 | Metadata, captions. |
| `--vl-type-mono` | 13 / 18 | 500 | Service IDs, logs, paths, unit names. |

Rules:

- Do not introduce ad-hoc font sizes.
- Use tabular numerals for service counts, version numbers, and log columns.
- Monospace is mandatory for 66/s6 service identifiers and paths.
- Respect user font scaling; never hard-code heights that clip scaled text.

Normative path: `reports/visual-language/ENDEAVOUROS_TYPE_SCALE.md`

---

## 5. Layout rules

| Rule | Value |
|---|---:|
| Base spacing unit | 8px |
| Spacing scale | 4, 8, 12, 16, 24, 32, 48 |
| Content max width | 1200px |
| Sidebar width | 240px |
| Top bar height | 48px |
| Card padding | 16px |
| Dialog padding | 24px |
| Radius: controls | 8px |
| Radius: cards | 12px |
| Radius: dialogs | 16px |
| Border width | 1px |
| Icon sizes | 16, 24, 32, 48 |
| Motion: state change | 120ms |
| Motion: layout change | 200ms |

Responsive behavior:

- `< 720px`: single column, sidebar becomes drawer.
- `720–1100px`: two-column content, optional sidebar.
- `> 1100px`: full sidebar plus content area.

Elevation rule:

- Prefer `surface` + `border` over shadows.
- Shadows only for transient overlays: menus, dialogs, tooltips.

Normative path: `reports/visual-language/ENDEAVOUROS_LAYOUT_RULES.md`

---

## 6. Obarun/66+s6 service-state language

The visual layer must treat 66/s6 as authoritative. UI components observe state; they must not mutate supervision state except through a journaled migration or repair operation.

| State | Color token | Icon | Label |
|---|---|---|---|
| `ready` | `--vl-eos-success` | check-circle | Ready |
| `starting` | `--vl-eos-info` | spinner | Starting |
| `warning` | `--vl-eos-warning` | alert-triangle | Warning |
| `failed` | `--vl-eos-danger` | alert-octagon | Failed |
| `stopped` | `--vl-eos-text-muted` | square | Stopped |
| `disabled` | `--vl-eos-text-muted` | slash | Disabled |
| `unknown` | `--vl-eos-border` | help-circle | Unknown |

Rules:

- Never encode state by color alone.
- Every badge must include icon + text label.
- Service identifiers must use `--vl-type-mono`.
- Long logs must use a scrollable monospace surface with `surface` background.
- Repair actions must be staged and journaled per migration invariants `M-05`, `M-06`, and `M-09` in `reports/USER_MIGRATION_MANDATE_2026-11-21.md`.

Evidence path: `evidence/visual-language/endeavouros-wave1/66-s6-state-matrix.csv`

---

## 7. Component rules

### Buttons

- Primary: `--vl-eos-primary` fill, dark text or white text depending on measured contrast.
- Secondary: transparent fill, `--vl-eos-border` outline.
- Danger: `--vl-eos-danger` outline or fill only for destructive confirmation.

### Inputs

- Background: `--vl-eos-bg-base`.
- Border: `--vl-eos-border`.
- Focus: 2px `--vl-eos-primary` ring with 2px offset.

### Cards

- Background: `--vl-eos-bg-surface`.
- Border: 1px `--vl-eos-border`.
- Radius: 12px.
- Padding: 16px.

### Navigation

- Active item: `--vl-eos-bg-raised` plus 3px `--vl-eos-primary` leading indicator.
- Hover: `--vl-eos-bg-raised` at reduced intensity.
- Icons: 24px, 1.5px stroke.

### Status badges

- Height: 24px.
- Padding: 4px 8px.
- Radius: 999px.
- Mandatory icon + label.

---

## 8. Capability checks

| Capability ID | Check |
|---|---|
| `CAP-VL-COLOR` | Palette resolves in dark and light themes; contrast passes. |
| `CAP-VL-TYPE` | Only approved type tokens are used. |
| `CAP-VL-LAYOUT` | 8px grid and spacing scale are respected. |
| `CAP-VL-66` | 66/s6 states render with icon, label, and color. |
| `CAP-VL-PROVENANCE` | No EndeavourOS trademarks or copied marks are shipped. |
| `CAP-VL-SECRETS` | Evidence and UI assets contain no credentials. |

---

## 9. Test IDs and evidence paths

| Test ID | Check | Evidence path |
|---|---|---|
| `VL-EOS-001` | Color contrast and token resolution. | `evidence/visual-language/endeavouros-wave1/contrast-report.txt` |
| `VL-EOS-002` | Type scale compliance. | `evidence/visual-language/endeavouros-wave1/type-metrics.txt` |
| `VL-EOS-003` | Layout grid alignment. | `evidence/visual-language/endeavouros-wave1/layout-grid.svg` |
| `VL-EOS-004` | 66/s6 state badge completeness. | `evidence/visual-language/endeavouros-wave1/66-s6-state-matrix.csv` |
| `VL-EOS-005` | Dark/light token parity. | `evidence/visual-language/endeavouros-wave1/palette-extract.txt` |
| `VL-EOS-006` | Asset provenance and trademark boundary. | `evidence/visual-language/endeavouros-wave1/asset-provenance.md` |
| `VL-EOS-007` | Credential hygiene. | `evidence/visual-language/endeavouros-wave1/secret-scan.txt` |
| `VL-EOS-008` | Obarun/66+s6 integration safety. | `evidence/visual-language/endeavouros-wave1/test-run.tap` |

---

## 10. Wave 1 gaps and Wave 2 actions

1. Verify all hex values against upstream EndeavourOS theme evidence in `evidence/visual-language/endeavouros-wave1/palette-extract.txt`.
2. Publish token implementation to `evolution-engine/visual-language/endeavouros/tokens.yaml`.
3. Add Obarun/66+s6 integration notes to `evolution-engine/visual-language/endeavouros/README.md`.
4. Add contrast regression checks for every new component.
5. Add a trademark/provenance gate before any visual asset is promoted.
6. Keep visual artifacts immutable and versioned, consistent with invariants `M-02`, `M-03`, and `M-07` in `reports/USER_MIGRATION_MANDATE_2026-11-21.md`.
