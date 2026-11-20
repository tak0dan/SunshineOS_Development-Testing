# sub-design-research-0003 -> hierarchy

# CachyOS Visual Language — Wave 1 Survey (SunshineOS)

## Verification status — read first

I need to be direct about what this deliverable can and cannot assert.

- I was given the body of `reports/USER_MIGRATION_MANDATE_2026-11-21.md`. `reports/ARCHITECTURE_DECISIONS.md` was **omitted (context budget exhausted)**, and no repository tree, file bodies, test manifests, or `evidence/` contents were provided.
- The task instructs "no tool calls," so I cannot read the repo to confirm paths, hashes, or test IDs.
- Therefore I will **not** fabricate exact repo paths, test IDs, or evidence paths. Inventing them would be fabricated evidence and would violate the migration ledger's own integrity requirements (signed, hashed, verifiable artifacts — M-02, M-07).

What follows separates three things cleanly: (A) durable upstream knowledge that stays valid across releases, (B) canonical asset locations that are stable conventions, and (C) a catalogue template with explicit `TBD-repo` fields for the agent that actually has repository access to complete.

## Scope clarification (important)

"CachyOS visual language in Obarun/66+s6" conflates two unrelated layers:

- **CachyOS** is an Arch-based desktop distro with a rich visual identity (KDE Plasma-first theming, brand color, boot/login splash). It has a genuine visual language.
- **Obarun** is an Arch-based distro whose distinguishing trait is **66**, a service manager built on **s6** (skarnet supervision stack). 66/s6 are **CLI/supervision tools** — they have essentially no graphical visual language. Their "visual" surface is terminal output, man pages, and help text.

So there are two distinct survey targets, not one. Treating 66/s6 as a source of color/type/layout rules would be a category error. I have split them below.

---

## Part A — CachyOS visual language reference (durable)

### A.1 Color model

CachyOS's identity is a **blue/teal primary on dark neutral surfaces**, delivered through KDE Plasma's color-scheme mechanism (Breeze-derived conventions). Structure to catalogue:

- **Primary / accent**: brand blue (hue family: blue→teal). *Exact hex must be extracted from source — see A.4; I will not assert a hex I cannot verify.*
- **Neutrals**: dark window/background, view, and base surfaces with lighter text-on-dark.
- **Semantic**: standard KDE roles — `Highlight`, `HighlightedText`, `Button`, `ButtonText`, `Window`, `WindowText`, `View`, `ViewText`, `Tooltip*`, plus error/warning/success accents.

Do not hardcode hex into SunshineOS. Reference the **semantic color roles** and resolve them from the active scheme, so the palette survives theme changes and decade-scale drift (aligns with M-04: installation is authoritative, not a fixed number).

### A.2 Type scale

CachyOS ships Plasma defaults rather than a bespoke type system. Catalogue the **role→size→weight** mapping actually in effect:

- UI base font (Plasma `general/font`), then derived roles: window title, tooltip, small, and monospace (Konsole/terminal).
- Record the resolved family, point size, and weight per role from the live config, not from documentation.

### A.3 Layout rules

- Panel geometry, icon sizes, and spacing come from the Plasma look-and-feel package.
- Treat these as **parameters resolved from the active theme**, not constants.

### A.4 Canonical asset locations (stable upstream conventions)

These paths are durable across KDE Plasma releases and are where visual-language data actually lives. Use them to locate assets to hash and catalogue:

| Asset | Canonical location |
|---|---|
| Color schemes | `/usr/share/color-schemes/*.colors`, `~/.config/kdeglobals` (`[ColorScheme]`) |
| Global look-and-feel | `/usr/share/plasma/look-and-feel/`, `~/.local/share/plasma/look-and-feel/` |
| Plasma desktop theme | `/usr/share/plasma/desktoptheme/` |
| Icons | `/usr/share/icons/` |
| SDDM login theme | `/usr/share/sddm/themes/`, `/etc/sddm.conf.d/` |
| Plymouth boot splash | `/usr/share/plymouth/themes/` |
| GRUB theme | `/boot/grub/themes/`, `/etc/default/grub` |
| Terminal (Konsole) schemes | `/usr/share/konsole/`, `~/.local/share/konsole/` |
| Distro skel/branding | `/etc/skel/`, `/usr/share/cachyos-*` (verify actual package names) |

The SunshineOS repo's *adopted copies* of these would live under paths I cannot see; they must be located via the repo tree and recorded as `TBD-repo`.

---

## Part B — Obarun / 66 + s6 "visual language" (CLI/TUI)

There is no color/type/layout language here in the desktop sense. The surveyable surface is:

- **66 / s6 help & man output**: `man 66`, `66 --help`, `man s6-supervise`, etc. Catalogue formatting conventions (sectioning, colorized output if any, exit-message style).
- **Any TUI**: confirm whether 66 ships an interactive/ ncurses front end; if not, record "none" as a verified negative.
- **Service-state presentation**: how `66 status`/`66 tree` render state — this is the closest thing to a "visual language" and is worth cataloguing for SunshineOS's own service tooling.

Recommendation: for SunshineOS's user-facing visual language, source from **CachyOS (Part A)**; for **service/CLI UX**, source from **66/s6 (Part B)**. Do not merge them.

---

## Part C — Survey catalogue template (complete with repo access)

Each row must be filled from the actual repository. Fields marked `TBD-repo` require reading the tree; do not guess.

| Field | Meaning |
|---|---|
| `asset_id` | Stable id (e.g., `CVL-COLOR-001`) |
| `logical_asset` | What it is (color role, type role, layout param, CLI format) |
| `canonical_path` | Upstream location (from A.4 / B) |
| `repo_path` | `TBD-repo` — path inside SunshineOS repo |
| `content_hash` | `TBD-repo` — sha256 of the file |
| `schema_version` | e.g., `INV7` / `EVS4` per mandate |
| `source_baseline` | `B0-2026` (CachyOS anchor) or Obarun anchor |
| `test_id` | `TBD-repo` — from the repo test suite |
| `evidence_path` | `TBD-repo` — under `evidence/` or `reports/` |
| `signature` | `TBD-repo` — required by M-02/M-07 |

Integrity rule: a row is not "catalogued" until `content_hash`, `test_id`, and `evidence_path` are real and verified. Until then it is a *candidate*, not an *anchor* (M-08: support is qualified, not assumed).

---

## Part D — How to complete Wave 1 correctly

1. Enumerate the repo tree; locate adopted CachyOS/66 assets. Record `repo_path`.
2. For each, compute `content_hash`; extract exact hex/type/layout values from the file bodies (not from memory or docs).
3. Map each asset to a semantic role (A.1–A.3) so SunshineOS references roles, not literals.
4. Add or reference a test that asserts the resolved values; record its `test_id`.
5. Write a short evidence note under `evidence/`; record `evidence_path`.
6. Sign the catalogue entry (M-02, M-07).

Capability checks (decade-durable, per mandate preference): verify asset presence by path existence + hash match rather than by release name; verify color/type resolution by rendering/serializing the *active* scheme rather than comparing to a pinned literal.

---

## Migration-engine relevance

- This is a **target-profile** input (`TP040`-style), not an evolution step. Visual language belongs in the resolved desired state, kept separate from user data (M-10).
- Catalogue entries are **immutable, signed artifacts** (M-02, M-07); the engine (`ME12`-style) reads them without owning target-state decisions (component-ownership rule: Artifact Manager must not decide the target).
- Reference **semantic roles + hashes**, never hardcoded hex, so the visual layer survives theme and decade drift (M-04).

No credentials, tokens, or key material are included, per policy and the mandate's key-handling note.

Bottom line: I can give you the durable *what* and *where*, and a rigorous catalogue schema — but the exact repo paths, hashes, test IDs, and evidence paths must be filled by an agent with repository access. I won't invent them.
