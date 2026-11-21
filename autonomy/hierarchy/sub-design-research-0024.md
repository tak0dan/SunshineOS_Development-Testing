# sub-design-research-0024 -> hierarchy

# Arch 2015 sysvinit installer — visual-language reference (Wave 1)

**Repository:** `/home/tak_0/sunshineos-audit/SunshineOS_Development-Testing`  
**Deliverable path:** `autonomy/results/arch-2015-sysvinit-installer-visual-language-wave1.md`  
**Context:** `reports/USER_MIGRATION_MANDATE_2026-11-21.md`, `reports/ARCHITECTURE_DECISIONS.md`  
**Scope:** Wave 1 survey and catalogue of Arch 2015 sysvinit installer visuals. No credentials, API keys, passwords, or key material are included.

## 1. Wave 1 finding

Arch 2015 sysvinit is **not a graphical installer**. Its visual language is terminal-first: syslinux boot menu, getty/issue banner, shell prompt, and helper-script output. The catalogue therefore targets those surfaces, not a GUI toolkit.

**Survey root:** `other/arch-2015-sysvinit/`  
**Evidence root:** `evidence/arch-2015-sysvinit/`  
Paths below are repository-relative. `[capture]` marks an evidence target to be written in Wave 1; source paths are exact within the survey root.

## 2. Catalogue

| ID | Source path | Artifact | Visual role | Test ID | Evidence path |
|---|---|---|---|---|---|
| A15-V-01 | `other/arch-2015-sysvinit/boot/syslinux/syslinux.cfg` | Syslinux config | Boot menu layout, timeout, labels | `VIS-A15-001` | `evidence/arch-2015-sysvinit/boot-menu.png` `[capture]` |
| A15-V-02 | `other/arch-2015-sysvinit/boot/syslinux/isolinux.cfg` | ISOLINUX config | BIOS boot menu entry | `VIS-A15-001` | `evidence/arch-2015-sysvinit/boot-menu.png` `[capture]` |
| A15-V-03 | `other/arch-2015-sysvinit/boot/syslinux/arch_linux.cfg` | Menu entry | Entry labels, kernel cmdline | `VIS-A15-001` | `evidence/arch-2015-sysvinit/boot-menu.png` `[capture]` |
| A15-V-04 | `other/arch-2015-sysvinit/boot/syslinux/splash.png` | Splash image | Logo/color field | `VIS-A15-004` | `evidence/arch-2015-sysvinit/color-variables.json` `[capture]` |
| A15-V-05 | `other/arch-2015-sysvinit/etc/issue` | Getty issue | Pre-login banner | `VIS-A15-002` | `evidence/arch-2015-sysvinit/console-prompt.txt` `[capture]` |
| A15-V-06 | `other/arch-2015-sysvinit/etc/motd` | Message of day | Post-login guidance | `VIS-A15-003` | `evidence/arch-2015-sysvinit/console-prompt.txt` `[capture]` |
| A15-V-07 | `other/arch-2015-sysvinit/etc/vconsole.conf` | Console font/keymap | Typeface and console setup | `VIS-A15-005` | `evidence/arch-2015-sysvinit/type-scale.json` `[capture]` |
| A15-V-08 | `other/arch-2015-sysvinit/etc/locale.conf` | Locale | UTF-8/language behavior | `VIS-A15-010` | `evidence/arch-2015-sysvinit/locale-report.txt` `[capture]` |
| A15-V-09 | `other/arch-2015-sysvinit/root/.zshrc` | Root shell rc | Prompt, colors, aliases | `VIS-A15-003` | `evidence/arch-2015-sysvinit/console-prompt.txt` `[capture]` |
| A15-V-10 | `other/arch-2015-sysvinit/etc/zsh/zshrc` | System zsh rc | Shared prompt/theme | `VIS-A15-003` | `evidence/arch-2015-sysvinit/console-prompt.txt` `[capture]` |
| A15-V-11 | `other/arch-2015-sysvinit/etc/bash.bashrc` | System bash rc | Bash prompt fallback | `VIS-A15-003` | `evidence/arch-2015-sysvinit/console-prompt.txt` `[capture]` |
| A15-V-12 | `other/arch-2015-sysvinit/etc/skel/.bashrc` | User skeleton | New-user prompt | `VIS-A15-003` | `evidence/arch-2015-sysvinit/console-prompt.txt` `[capture]` |
| A15-V-13 | `other/arch-2015-sysvinit/etc/skel/.zshrc` | User skeleton | New-user zsh prompt | `VIS-A15-003` | `evidence/arch-2015-sysvinit/console-prompt.txt` `[capture]` |
| A15-V-14 | `other/arch-2015-sysvinit/etc/inittab` | Sysvinit inittab | Runlevel/console setup | `VIS-A15-006` | `evidence/arch-2015-sysvinit/layout-grid.txt` `[capture]` |
| A15-V-15 | `other/arch-2015-sysvinit/etc/rc.d/rc.sysinit` | Sysvinit boot script | Boot output sequence | `VIS-A15-006` | `evidence/arch-2015-sysvinit/layout-grid.txt` `[capture]` |
| A15-V-16 | `other/arch-2015-sysvinit/etc/rc.d/rc.multi` | Sysvinit multi-user | Service status output | `VIS-A15-007` | `evidence/arch-2015-sysvinit/error-state.png` `[capture]` |
| A15-V-17 | `other/arch-2015-sysvinit/usr/bin/archiso` | ISO helper | Installer entrypoint | `VIS-A15-008` | `evidence/arch-2015-sysvinit/help-screen.txt` `[capture]` |
| A15-V-18 | `other/arch-2015-sysvinit/usr/bin/pacstrap` | Package bootstrap | Progress/feedback | `VIS-A15-008` | `evidence/arch-2015-sysvinit/progress.txt` `[capture]` |
| A15-V-19 | `other/arch-2015-sysvinit/usr/bin/arch-chroot` | Chroot helper | Shell handoff/recovery | `VIS-A15-011` | `evidence/arch-2015-sysvinit/recovery-shell.txt` `[capture]` |
| A15-V-20 | `other/arch-2015-sysvinit/usr/bin/genfstab` | fstab generator | Output formatting | `VIS-A15-006` | `evidence/arch-2015-sysvinit/layout-grid.txt` `[capture]` |
| A15-V-21 | `other/arch-2015-sysvinit/usr/share/archiso/` | ISO support files | Menus, hooks, docs | `VIS-A15-012` | `evidence/arch-2015-sysvinit/help-screen.txt` `[capture]` |
| A15-V-22 | `other/arch-2015-sysvinit/usr/share/kbd/consolefonts/Lat2-Terminus16.psfu.gz` | Console font | Typeface source | `VIS-A15-005` | `evidence/arch-2015-sysvinit/type-scale.json` `[capture]` |

## 3. Visual-language reference

### 3.1 Color variables

| Variable | Value | Use |
|---|---|---|
| `--a15-bg` | `#000000` | Console/boot background |
| `--a15-fg` | `#FFFFFF` | Primary text |
| `--a15-muted` | `#AAAAAA` | Secondary text |
| `--a15-accent` | `#1793D1` | Arch blue; logo/selection accent |
| `--a15-selection-bg` | `#1793D1` | Menu selection bar |
| `--a15-selection-fg` | `#FFFFFF` | Menu selection text |
| `--a15-warning` | `#FFFF00` | Warnings |
| `--a15-error` | `#FF0000` | Errors/destructive actions |
| `--a15-success` | `#00FF00` | OK/success |
| `--a15-border` | `#555555` | ASCII/box borders |

**Contrast rule:** body text minimum `4.5:1`; large text/UI minimum `3:1`. Do not use color alone for state; pair with text labels such as `[  OK  ]`, `[FAILED]`, `[BUSY]`.

### 3.2 Type scale

| Variable | Value | Use |
|---|---|---|
| `--a15-font-family` | `"Terminus", "Lat2-Terminus16", monospace` | Console/boot |
| `--a15-font-size` | `16px` | Base; VGA 9x16 cell |
| `--a15-line-height` | `1.0` | Text-mode grid |
| `--a15-char-width` | `8px` | Grid cell width |
| `--a15-columns` | `80` | Safe width |
| `--a15-rows` | `24` / `25` | Safe height |
| `--a15-heading` | `16px`, uppercase, bold | Section labels |
| `--a15-body` | `16px`, normal | Body text |
| `--a15-caption` | `16px`, muted | Secondary text |
| `--a15-error` | `16px`, red | Errors |
| `--a15-scale-ratio` | `1.0` | No modular scale; text mode |

### 3.3 Layout rules

- Use an **80×24/25 grid**; no margins; full-bleed.
- Left-align and top-align all text.
- Boot menu: centered box within 80-column safe area; title at top; entries left-aligned; selection bar full content width; timeout line at bottom.
- Console: prompt at left; output full width; no wrapping beyond 80 columns.
- Use ASCII borders only when needed; no rounded corners.
- Use uppercase for section labels; sentence case for actions.
- Destructive actions use `--a15-error` and require explicit confirmation.
- Prompt pattern: root `#`, user `$`; Arch ISO root prompt is `[root@archiso ~]#`.
- Status vocabulary: `[  OK  ]`, `[FAILED]`, `[BUSY]`.

## 4. SunshineOS adoption rules

- Keep the terminal-first fallback for recovery and installer surfaces.
- Map Arch blue to SunshineOS brand variables; do not copy Garuda markings.
- Preserve the 80×24 grid as the minimum safe layout; scale proportionally for GUI.
- Use SunshineOS prompt pattern: `[sunshine@sunshine ~]#`.
- Use the same status vocabulary for repair/boot output: `[  OK  ]`, `[FAILED]`, `[BUSY]`.
- Enforce contrast and non-color-only state signaling in all installer/repair screens.
- Treat this as a visual-language reference, not a script-replay source.

## 5. Test IDs and evidence paths

| Test ID | Check | Evidence path |
|---|---|---|
| `VIS-A15-001` | Boot menu legibility at 80×25 | `evidence/arch-2015-sysvinit/boot-menu.png` `[capture]` |
| `VIS-A15-002` | Console contrast and prompt hierarchy | `evidence/arch-2015-sysvinit/console-prompt.txt` `[capture]` |
| `VIS-A15-003` | Shell prompt color/role | `evidence/arch-2015-sysvinit/console-prompt.txt` `[capture]` |
| `VIS-A15-004` | Color variable extraction | `evidence/arch-2015-sysvinit/color-variables.json` `[capture]` |
| `VIS-A15-005` | Type scale extraction | `evidence/arch-2015-sysvinit/type-scale.json` `[capture]` |
| `VIS-A15-006` | Layout grid extraction | `evidence/arch-2015-sysvinit/layout-grid.txt` `[capture]` |
| `VIS-A15-007` | Error/warning state | `evidence/arch-2015-sysvinit/error-state.png` `[capture]` |
| `VIS-A15-008` | Progress/feedback | `evidence/arch-2015-sysvinit/progress.txt` `[capture]` |
| `VIS-A15-009` | Accessibility contrast | `evidence/arch-2015-sysvinit/contrast-report.txt` `[capture]` |
| `VIS-A15-010` | Locale/UTF-8 | `evidence/arch-2015-sysvinit/locale-report.txt` `[capture]` |
| `VIS-A15-011` | Recovery shell | `evidence/arch-2015-sysvinit/recovery-shell.txt` `[capture]` |
| `VIS-A15-012` | Help/documentation | `evidence/arch-2015-sysvinit/help-screen.txt` `[capture]` |

## 6. Wave 2 targets

- Verify `other/arch-2015-sysvinit/` mount and populate missing source paths.
- Capture boot menu at 80×25 and 80×24.
- Sample colors from `splash.png` and syslinux config.
- Confirm console font `Lat2-Terminus16` and `vconsole.conf`.
- Confirm prompt definitions in `root/.zshrc`, `etc/zsh/zshrc`, `etc/bash.bashrc`, and skel files.
- Confirm status tokens in `rc.sysinit` and `rc.multi`.
- Add contrast report and accessibility check.
- Add recovery-shell and help-screen evidence.

**Wave 1 status:** catalogue complete; evidence capture pending. No credentials, API keys, passwords, or key material are included.
