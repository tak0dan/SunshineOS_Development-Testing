# lead-design / typography / Obarun/66+s6

- Agent: lead-design
- Model: baidu/ernie-5.5-flash-preview:free
- Parent directive: none
- Completed: 2026-11-21 00:18

---

I don't have access to the actual repository contents — the context provided includes only the mandate file and a truncated architecture decisions file, with no filesystem access to `/home/tak_0/sunshineos-audit/SunshineOS_Development-Testing`. I cannot survey Obarun/66+s6 typography assets, cite exact file paths, or produce evidence-backed findings without reading the actual files.

Here is what I can deliver: a **structured survey protocol and deliverable template** that a subagent with filesystem access should execute and populate. This is the Wave 1 deepening framework.

---

# Wave 1 Deliverable: Obarun/66+s6 Typography Survey & Inconsistency Catalogue

## 1. Survey Scope

### 1.1 Target Systems
- **Obarun** (Artix-based, uses s6/66 init system)
- **66** (s6-based service manager, standalone or embedded)
- **s6** (skarnet.org supervision suite)

### 1.2 Typography Surfaces to Catalogue

| Surface ID | Description | Expected Asset Types |
|---|---|---|
| TTY-01 | Console font (kernel/bootsplash) | PSF/PSFU, consolefont configs |
| TTY-02 | Bootloader typography | GRUB/Syslinux theme fonts |
| DM-01 | Display manager greeter | SDDM/LightDM/GDM theme fonts |
| GUI-01 | Desktop environment fonts | GTK/Qt fontconfig, DE-specific |
| GUI-02 | Terminal emulator fonts | URXVT/kitty/alacritty/foot configs |
| CLI-01 | TUI application fonts | Dialog/whiptail, ncurses apps |
| CLI-02 | Man page rendering | groff/nroff device fonts |
| DOC-01 | Documentation rendering | MkDocs/Sphinx/LaTeX output |
| INIT-01 | Init system output | s6/66 status messages, boot text |
| PKG-01 | Package manager output | pacman/xbps-install output formatting |

---

## 2. Survey Methodology (for executing subagent)

### 2.1 Discovery Commands

```bash
# Font files system-wide
find / -type f \( -name "*.psf" -o -name "*.psfu" -o -name "*.psf.gz" \
  -o -name "*.bdf" -o -name "*.pcf" -o -name "*.otf" -o -name "*.ttf" \
  -o -name "*.woff" -o -name "*.woff2" \) 2>/dev/null

# Fontconfig configuration
find /etc/fonts /usr/share/fontconfig -type f 2>/dev/null

# Console font configuration
cat /etc/vconsole.conf 2>/dev/null
cat /etc/default/console-setup 2>/dev/null

# Bootloader theme assets
find /boot /usr/share/grub /usr/share/syslinux -type f 2>/dev/null

# Display manager themes
find /usr/share/sddm/themes /usr/share/lightdm /usr/share/gdm -type f 2>/dev/null

# Terminal emulator configs
find /etc /home -name "*.Xresources" -o -name "*.Xdefaults" \
  -o -name "alacritty.yml" -o -name "foot.ini" -o -name "kitty.conf" 2>/dev/null

# s6/66 specific output
find /etc/s6* /etc/66 /usr/share/66 -type f 2>/dev/null
```

### 2.2 Evidence Capture Protocol

For each discovered asset, record:
1. **Exact path** (absolute)
2. **File type** (`file` command output)
3. **Size and hash** (`stat` + `sha256sum`)
4. **Ownership and permissions** (`ls -la`)
5. **Package ownership** (`pacman -Qo` or equivalent)
6. **Configuration references** (grep for filename in config files)
7. **Rendered output sample** (where applicable — screenshot or text capture)

### 2.3 Test ID Scheme

```
OB-TYP-[SURFACE]-[NNN]
```

Example: `OB-TYP-TTY-001` = first TTY font asset test

---

## 3. Inconsistency Severity Ranking Framework

### 3.1 Severity Levels

| Level | Label | Criteria |
|---|---|---|
| S1 | **Critical** | Missing font causes unreadable output; blocks boot or login |
| S2 | **High** | Visible rendering defect in primary user path (boot, DM, default terminal) |
| S3 | **Medium** | Inconsistent typography across related surfaces; user-visible but not blocking |
| S4 | **Low** | Cosmetic inconsistency in secondary paths (man pages, docs, package output) |
| S5 | **Informational** | Deviation from upstream default; no functional impact |

### 3.2 Inconsistency Categories

| Category ID | Description |
|---|---|
| CAT-FAM | Font family mismatch across surfaces that should share identity |
| CAT-SIZE | Size/scale inconsistency (e.g., TTY vs DM vs terminal) |
| CAT-FALL | Missing fallback chain; glyph coverage gaps |
| CAT-RENDER | Hinting/antialiasing/subpixel configuration inconsistency |
| CAT-LOCALE | Missing or incorrect locale-specific glyph support |
| CAT-CONFIG | Configuration drift between similar components |
| CAT-DEAD | Referenced font/asset does not exist on system |
| CAT-DUP | Redundant or conflicting font definitions |

---

## 4. Deliverable Template (to be populated by executing subagent)

### 4.1 Asset Inventory Table

```markdown
| Test ID | Surface | Path | Type | Package | Hash (first 12) | Status |
|---------|---------|------|------|---------|-----------------|--------|
| OB-TYP-TTY-001 | TTY-01 | /usr/share/kbd/consolefonts/... | PSF.gz | kbd | a1b2c3d4e5f6 | Present |
```

### 4.2 Inconsistency Register

```markdown
| Finding ID | Severity | Category | Test IDs | Description | Asset Paths | Evidence Path |
|------------|----------|----------|----------|-------------|-------------|---------------|
| OB-FND-001 | S2 | CAT-FAM | OB-TYP-TTY-001, OB-TYP-DM-001 | TTY uses Terminus while DM uses DejaVu Sans; no shared identity | /usr/share/kbd/consolefonts/ter-... , /usr/share/sddm/themes/.../... | evidence/typography/OB-FND-001/ |
```

### 4.3 Evidence Directory Structure

```
evidence/
└── typography/
    └── wave1/
        ├── OB-FND-001/
        │   ├── discovery.txt          # find/grep output
        │   ├── file-info.txt          # file, stat, sha256sum
        │   ├── config-dump.txt        # relevant config file contents
        │   └── render-sample.txt      # captured output or screenshot ref
        ├── OB-FND-002/
        └── ...
```

---

## 5. Specific Areas of Concern for Obarun/66+s6

Based on the architecture of these systems, the executing subagent should pay particular attention to:

### 5.1 s6/66 Init Output Typography
- **Path patterns**: `/etc/s6-overlay/s6-rc.d/`, `/etc/66/`, `/usr/lib/66/`
- **Concern**: s6 uses `s6-echo` or direct `echo` for boot messages. Font rendering depends on kernel console font at that stage. Check if 66 has its own output formatting that assumes specific character widths.
- **Test IDs**: `OB-TYP-INIT-001` through `OB-TYP-INIT-020`

### 5.2 Console Font Lifecycle
- **Concern**: When does the console font load relative to s6/66 execution? If s6 starts before `setfont` runs, early boot messages use the kernel default font.
- **Check**: `/etc/vconsole.conf`, hooks in `/etc/init.d/` or s6 service definitions, kernel cmdline (`vconsole.keymap`, `font` parameters)
- **Test IDs**: `OB-TYP-TTY-001` through `OB-TYP-TTY-010`

### 5.3 Artix/Obarun Package Font Dependencies
- **Concern**: Which packages pull in fonts as dependencies vs. optional dependencies? Are there conflicts?
- **Check**: `pacman -Ssq font` or equivalent, `/var/lib/pacman/local/*/desc`
- **Test IDs**: `OB-TYP-PKG-001` through `OB-TYP-PKG-015`

### 5.4 Display Manager Integration
- **Concern**: Obarun may use sddm or lightdm. Theme font references may point to fonts not installed by default.
- **Check**: Theme configuration files, `QT_QPA_PLATFORMTHEME` environment, fontconfig XML
- **Test IDs**: `OB-TYP-DM-001` through `OB-TYP-DM-010`

---

## 6. Execution Checklist for Subagent

- [ ] Run discovery commands from §2.1 on target Obarun/66+s6 installation or VM
- [ ] Populate Asset Inventory Table (§4.1) with all discovered assets
- [ ] Cross-reference each asset against configuration files that reference it
- [ ] Identify missing assets (CAT-DEAD) — referenced but not present
- [ ] Identify family mismatches (CAT-FAM) across surfaces
- [ ] Identify size/scale inconsistencies (CAT-SIZE)
- [ ] Check fallback chains (CAT-FALL) — what happens when primary font is unavailable
- [ ] Capture evidence for each finding into `evidence/typography/wave1/`
- [ ] Populate Inconsistency Register (§4.2) with severity-ranked findings
- [ ] Assign test IDs per §2.3 scheme
- [ ] Cross-reference findings against `reports/ARCHITECTURE_DECISIONS.md` for any typography-related decisions
- [ ] Publish results to development branch per mandate requirement

---

## 7. Integration with Migration Architecture

Per the mandate's architectural invariants (M-01 through M-10), typography findings should be classified as:

| Finding Type | Migration Relevance | Applicable Invariant |
|---|---|---|
| Missing font asset | Package transition needed | M-01, M-07 |
| Config drift | Configuration migration rule needed | M-04, M-10 |
| Dead reference | Cleanup/retirement rule needed | M-02, M-06 |
| Family mismatch | Target profile definition needed | M-01, M-03 |
| Fallback gap | Transition catalog entry needed | M-03, M-08 |

Each finding in the Inconsistency Register should include a **Migration Action** column mapping to the transition catalog structure defined in the architecture decisions.

---

## 8. Next Steps

1. **Assign this task** to a subordinate agent with filesystem access to the Obarun/66+s6 installation or VM
2. **Provide the agent** with: this template, the discovery commands (§2.1), and the evidence directory structure (§4.3)
3. **Set completion criteria**: All surfaces in §1.2 surveyed, minimum 1 test ID per surface, all findings severity-ranked, evidence captured
4. **Review output** against §6 checklist before accepting
5. **Feed findings** into the Transition Catalog (TC) and Target Profile (TP) definitions per the migration architecture

---

**Note**: This deliverable is a protocol and template because I lack filesystem access to the target repository. An agent with access to `/home/tak_0/sunshineos-audit/SunshineOS_Development-Testing` and the Obarun/66+s6 installation should execute §2 and populate §4 to produce the final catalogue.
