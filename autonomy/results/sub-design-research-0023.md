# sub-design-research / desktop shell patterns / Arch 2015 sysvinit

- Agent: sub-design-research
- Model: baidu/ernie-5.5-flash-preview:free
- Parent directive: none
- Completed: 2026-11-21 01:01

---

# Wave 1 Deepening — Desktop Shell Patterns: Arch 2015 (sysvinit baseline)

| Field | Value |
|---|---|
| Deliverable ID | `DEL-W1-DS-ARCH2015-SYSVINIT` |
| Wave | 1 (deepening) |
| Baseline | `B-1-2015` (recovery anchor) |
| Engine / schema | `ME12` / `INV7` / `EVS4` / `TC18` |
| Governing mandate | `reports/USER_MIGRATION_MANDATE_2026-11-21.md` (invariants M-01…M-10) |
| Decision record | `reports/ARCHITECTURE_DECISIONS.md` — **not readable in this context window; all `AD-*` cross-refs below are pending** |
| Status | Catalogue complete; asset-level verification pending (see §0.3) |

---

## 0. Scope, method, confidence

### 0.1 Scope
Desktop-shell surface only: session bootstrap, display manager, autostart, desktop entries, theme/visual propagation, input, i18n, a11y, notifications, tray, power policy, MIME, HiDPI. Kernel, initramfs, bootloader and package-manager internals are **out of scope** for this wave (tracked separately).

### 0.2 Confidence legend

| Tag | Meaning |
|---|---|
| `[V]` | Verified against a file in this repository |
| `[P]` | Proposed canonical path — must be confirmed against the VM image before it is cited as fact |
| `[S]` | Spec-derived (freedesktop / GNOME / XKB published specification) |
| `[R]` | Reconstructed — inferred from the baseline manifest, not observed |

### 0.3 Baseline caveat (durable, do not re-litigate)

Arch Linux completed its init migration to systemd in **October 2012**. A 2015 Arch install is systemd by default. Therefore `B-1-2015` described as "Arch 2015 sysvinit" is a **reconstructed baseline**, not an upstream release:

- It must be built by pinning `initscripts` + `sysvinit` and freezing the package set.
- `initscripts` was removed from the Arch repositories after the systemd transition, so the reconstruction depends on the **Arch Linux Archive** (`https://archive.archlinux.org/`) — this is a direct instance of invariant **M-07** (historical artifacts archived; old paths must not depend on repositories that may disappear).
- **Invariant to encode:** *the init system is a property of the baseline manifest, not of the release year.* Any migration logic that infers init system from a date will be wrong.

### 0.4 Verification status
No file in this repository was read during this wave. Every path below is `[P]` or `[S]` until a Wave 1b pass confirms it against the VM image and records a hash. **Do not promote any `[P]` path into `evolution-engine/` until it carries an evidence hash.**

---

## 1. Baseline identity

| Property | Value | Confidence |
|---|---|---|
| Baseline ID | `B-1-2015` | `[R]` |
| Init | sysvinit + `initscripts` | `[R]` |
| Runlevel model | `2` / `3` multi-user, `5` graphical | `[S]` |
| Session bus | `elogind` or `consolekit` (sysvinit-era) | `[R]` |
| Toolkit generation | GTK+ 2 / GTK+ 3, Qt 4 / Qt 5 | `[S]` |
| Icon theme | Adwaita, inheriting `hicolor` | `[S]` |
| GTK theme | Adwaita (`gtk-3.0/gtk.css`) | `[S]` |
| Font | Cantarell, 11 pt default | `[S]` |
| Display manager | GDM / SDDM / LightDM (one per image variant) | `[R]` |

---

## 2. Catalogue

### 2.1 Session bootstrap and init

| ID | Pattern | Canonical path(s) | Mechanism | Invariant | Confidence |
|---|---|---|---|---|---|
| `DS-01` | sysvinit session bootstrap | `/etc/inittab`, `/etc/rc.conf`, `/etc/rc.d/rc.sysinit`, `/etc/rc.d/rc.multi`, `/etc/rc.local` | Declarative runlevel table; `DAEMONS=()` array; display manager respawned at runlevel 5 | Session start is an **ordered, declared, idempotent** sequence; the display manager is a respawned service, not a shell child | `[S]` |
| `DS-02` | Display manager greeter | `/etc/gdm/custom.conf`, `/etc/gdm/Xsession`, `/etc/sddm.conf`, `/usr/share/sddm/themes/`, `/etc/lightdm/lightdm.conf` | Separate greeter process, unprivileged, themeable, no access to user session state | Greeter and session are **separate trust domains**; greeter theming must never read user config | `[S]` |
| `DS-03` | X session composition | `/etc/X11/xinit/xinitrc`, `/etc/X11/xinit/xserverrc`, `/etc/X11/xinit/xinitrc.d/*.sh`, `~/.xinitrc`, `~/.Xresources` | Ordered drop-ins gated by executable bit; user file overrides system file | Composition is **declarative and ordered**; drop-ins are opt-in by mode bit, not by name | `[S]` |
| `DS-04` | XDG autostart | `/etc/xdg/autostart/*.desktop`, `~/.config/autostart/*.desktop` | `.desktop` entries with `OnlyShowIn`, `NotShowIn`, `Hidden`, `X-GNOME-Autostart-enabled` | Autostart is **declarative, DE-scoped, user-overridable**; system entries are shadowed by user entries of the same filename | `[S]` |
| `DS-05` | Desktop entry | `/usr/share/applications/*.desktop`, `~/.local/share/applications/` | `[Desktop Entry]` with `Type`, `Exec`, `TryExec`, `MimeType`, `Categories`, `StartupWMClass` | `Exec` is a **field-code-substituted** command line; `TryExec` gates on binary presence; `StartupWMClass` binds window to launcher | `[S]` |

### 2.2 Visual propagation

| ID | Pattern | Canonical path(s) | Mechanism | Invariant | Confidence |
|---|---|---|---|---|---|
| `DS-06` | XSettings bus | `/usr/bin/xsettingsd`, `/etc/xdg/xsettingsd/xsettingsd.conf`, `~/.config/xsettingsd/xsettingsd.conf` | Typed, namespaced settings broadcast to all X clients | Theme is **toolkit-agnostic**; settings are typed and namespaced, never stringly-typed | `[S]` |
| `DS-07` | GSettings / dconf layering | `/usr/share/glib-2.0/schemas/*.gschema.xml`, `/etc/dconf/db/local.d/`, `/etc/dconf/db/local.d/locks/`, `/etc/dconf/profile/user` | Precedence: defaults → mandatory → user; locks are declarative | **Defaults, mandatory and user layers are distinct**; a lock is a declaration, not a runtime patch | `[S]` |
| `DS-08` | GTK theme cascade | `/usr/share/themes/Adwaita/gtk-3.0/gtk.css`, `gtk-dark.css`, `settings.ini`, `/usr/share/themes/Adwaita/index.theme`, `~/.config/gtk-3.0/gtk.css`, `~/.gtkrc-2.0` | CSS cascade with a documented dark variant selected by `gtk-application-prefer-dark-theme` | Theme is a **cascade with an explicit dark variant**; user override is a file, not a fork | `[S]` |
| `DS-09` | Icon theme inheritance | `/usr/share/icons/Adwaita/index.theme` (`Inherits=hicolor`), `/usr/share/icons/hicolor/index.theme` | Inheritance chain resolved at lookup time | Inheritance chain **terminates at `hicolor`**; no dangling `Inherits` | `[S]` |
| `DS-10` | Cursor theme | `/usr/share/icons/Adwaita/cursors/`, `/usr/share/icons/Adwaita/index.theme`, `~/.icons/default/index.theme`, `Xcursor.theme` | Single ordered resolution chain | Cursor resolution is **one ordered chain**, not per-toolkit | `[S]` |
| `DS-11` | Fontconfig | `/etc/fonts/fonts.conf`, `/etc/fonts/conf.d/*.conf` (`10-*`, `30-*`, `45-*`, `60-*`, `90-*`), `~/.config/fontconfig/fonts.conf` | Numeric-prefix ordering; later files override earlier | Config is **ordered by numeric prefix**; ordering is the contract | `[S]` |
| `DS-12` | Qt theming bridge | `/etc/qt5ct/qt5ct.conf`, `~/.config/qt5ct/qt5ct.conf`, `QT_QPA_PLATFORMTHEME`, `qt.conf` | Environment-selected platform theme | Qt and GTK+ must resolve to the **same visual tokens** via a bridge, not by duplication | `[S]` |
| `DS-13` | Sound theme | `/usr/share/sounds/freedesktop/index.theme` | Same inheritance model as icon themes | Sound themes follow **icon-theme inheritance semantics** | `[S]` |

### 2.3 Input, locale, accessibility

| ID | Pattern | Canonical path(s) | Mechanism | Invariant | Confidence |
|---|---|---|---|---|---|
| `DS-14` | Input method selection | `/etc/environment` (`GTK_IM_MODULE`, `QT_IM_MODULE`, `XMODIFIERS`), `/etc/X11/xinit/xinitrc.d/50-ibus.sh`, `70-fcitx.sh` | Env-var contract consumed by toolkits | IM is selected by **env-var contract**, never by toolkit-specific config | `[S]` |
| `DS-15` | Keyboard layout / XKB | `/etc/X11/xorg.conf.d/00-keyboard.conf`, `localectl` | Declarative XKB options shared by console and X | Layout is **declarative and identical** across console and X | `[S]` |
| `DS-16` | Locale | `/etc/locale.conf`, `/etc/locale.gen`, `/etc/environment` | Generated locales + single resolved environment | Locale is **one resolved set**, not per-process drift | `[S]` |
| `DS-17` | Accessibility | `/usr/share/glib-2.0/schemas/org.gnome.desktop.a11y*.gschema.xml`, `GTK_MODULES=gail:atk-bridge`, `/usr/libexec/at-spi2-core` | AT-SPI bus + toolkit bridge modules | A11y is a **first-class, testable surface**, not an afterthought | `[S]` |

### 2.4 Session services and policy

| ID | Pattern | Canonical path(s) | Mechanism | Invariant | Confidence |
|---|---|---|---|---|---|
| `DS-18` | Notification daemon | `/usr/share/dbus-1/services/org.freedesktop.Notifications.service`, `/usr/share/applications/*notify*.desktop` | D-Bus activation | **Exactly one** notification daemon per session; activation is declarative | `[S]` |
| `DS-19` | Tray / StatusNotifierItem | `/usr/share/dbus-1/interfaces/org.kde.StatusNotifierItem.xml` | SNI over D-Bus; legacy XEmbed deprecated | SNI is the **supported** tray protocol; legacy embedding is a compatibility shim only | `[S]` |
| `DS-20` | Power and session policy | `polkit`: `/usr/share/polkit-1/actions/*.policy`, `/etc/polkit-1/`; sysvinit-era ACPI hooks under `/etc/acpi/` | Declarative policy actions with allow/deny/ask | Privileged actions are **declared**, never scripted inline | `[S]` |
| `DS-21` | MIME association | `/usr/share/applications/mimeapps.list`, `~/.config/mimeapps.list`, `/usr/share/applications/defaults.list` | Declarative default-handler table | Association is **declarative and user-overridable** | `[S]` |
| `DS-22` | User directories | `/etc/xdg/user-dirs.defaults`, `~/.config/user-dirs.dirs`, `~/.config/user-dirs.locale` | Resolved once, recorded | XDG dirs are **resolved once and recorded**, not re-guessed per launch | `[S]` |
| `DS-23` | Compositor / vsync | `/etc/X11/xorg.conf.d/`, `org.gnome.desktop.interface` gsettings, `compton.conf` | Session-scoped compositor | Compositing is a **session property**, not a global one | `[S]` |
| `DS-24` | HiDPI scaling | `/etc/X11/xorg.conf.d/`, `GDK_SCALE`, `GDK_DPI_SCALE`, `Xft.dpi`, `text-scaling-factor` | Per-monitor scale resolution, recorded | Scale is **resolved per-monitor and recorded**, never guessed from resolution alone | `[S]` |

---

## 3. Visual-language reference

> All values are `[S]` spec-derived from the Adwaita / GNOME 3.16 generation. They must be re-derived from the shipped assets at `/usr/share/themes/Adwaita/gtk-3.0/gtk.css` and `/usr/share/icons/Adwaita/index.theme` before being frozen into `evolution-engine/`. Token *names* below are the later libadwaita formalization applied retroactively to 2015 raw values — the mapping is a reconstruction, not an observation.

### 3.1 Color tokens

| Token | Hex | Source path | Usage |
|---|---|---|---|
| `--blue-3` | `#3584E4` | `/usr/share/themes/Adwaita/gtk-3.0/gtk.css` | Primary accent, links, selection |
| `--blue-4` | `#1C71D8` | same | Hover accent |
| `--blue-5` | `#1A5FB4` | same | Active accent |
| `--green-3` | `#33D17A` | same | Success |
| `--green-5` | `#26A269` | same | Success, text-safe |
| `--yellow-3` | `#F6D32D` | same | Warning |
| `--yellow-5` | `#E5A50A` | same | Warning, text-safe |
| `--orange-3` | `#FFBE6F` | same | Caution |
| `--orange-5` | `#FF7800` | same | Caution, text-safe |
| `--red-3` | `#F66151` | same | Destructive |
| `--red-5` | `#E01B24` | same | Destructive, text-safe |
| `--purple-3` | `#DC8ADD` | same | Accent, alternate |
| `--purple-5` | `#9141AC` | same | Accent, text-safe |
| `--light-1` | `#FFFFFF` | same | Base surface (light) |
| `--light-2` | `#F6F5F4` | same | Window background (light) |
| `--light-3` | `#DEDDDA` | same | Border / divider (light) |
| `--light-4` | `#C0BFBC` | same | Disabled foreground (light) |
| `--dark-1` | `#77767B` | same | Secondary text (light) |
| `--dark-2` | `#5E5C64` | same | Tertiary text (light) |
| `--dark-3` | `#3D3846` | same | Border / surface (dark) |
| `--dark-4` | `#241F31` | same | Window background (dark) |
| `--dark-5` | `#000000` | same | Base surface (dark) |

**Rules**
- Accent tokens are used at `-3` for fills and `-5` for text/icons on light surfaces; never `-3` as text on `--light-2`.
- Semantic colors (`green`/`yellow`/`orange`/`red`) are **reserved**; they must not be used as decorative accents.
- Dark variant is a **token remap**, not a separate stylesheet fork (`gtk-dark.css` exists but must resolve to the same token set).

### 3.2 Type scale

Family: **Cantarell**. Default body size **11 pt**.

| Token | Size | px @96 dpi | Line height | Usage |
|---|---|---|---|---|
| `--type-caption` | 10 pt | 13.33 | 1.33 | Captions, metadata, footnotes |
| `--type-body` | 11 pt | 14.67 | 1.43 | Default body, labels, list rows |
| `--type-body-emphasis` | 11 pt / bold | 14.67 | 1.43 | Emphasized body |
| `--type-heading` | 14 pt | 18.67 | 1.33 | Section headings, dialog titles |
| `--type-display` | 18 pt | 24.00 | 1.25 | Page titles, greeter headings |
| `--type-large` | 24 pt | 32.00 | 1.20 | Splash, lock screen clock |
| `--type-jumbo` | 32 pt | 42.67 | 1.15 | Greeter clock, hero numerals |

**Rules**
- Scale is **modular on the 11 pt body**; no intermediate sizes.
- Weight is the only emphasis mechanism within a size; do not introduce size steps to signal emphasis.
- Never set body text below 10 pt; never set captions above 11 pt.

### 3.3 Layout rules

| Rule | Value | Rationale |
|---|---|---|
| Base spacing unit | 8 px | All gaps are integer multiples |
| Layout grid | 12 px | Alignment lattice for panels and content |
| Window margin | 24 px | Content inset from window edge |
| Panel / header bar height | 48 px | Consistent across shell surfaces |
| List row height | 40 px (single-line), 56 px (two-line) | Density contract |
| Icon size (menu) | 16 px | Menu and inline |
| Icon size (toolbar) | 24 px | Toolbar |
| Icon size (content) | 32 / 48 px | Content and file views |
| Icon size (symbolic) | 16 px | Monochrome, recolored by token |
| Minimum hit target | 32 px (pointer), 48 px (touch) | Accessibility floor |
| Maximum content measure | 720 px | Readable line length |
| Corner radius | 4 px (controls), 8 px (surfaces) | Consistent silhouette |

**Rules**
- Spacing is **never** a non-multiple of 8 except for optical alignment of icon glyphs.
- Density is a **session-level** setting, not per-window; all windows in a session share one density.
- Layout must be expressible as a **token set**, so a migration can re-target it without rewriting component code.

### 3.4 Component rules

| Component | Rule |
|---|---|
| Header bar | 48 px, title centered, `--type-heading`, no border on flat surfaces |
| Buttons | 4 px radius, 8 px horizontal padding, 24 px icon + label gap 8 px |
| Entries | 4 px radius, 1 px `--light-3` border, focus ring 2 px `--blue-3` |
| Menus | 4 px radius, 8 px padding, 40 px rows, 16 px icons, separators `--light-3` |
| Notifications | Top-center, 8 px from edge, 320 px max width, `--type-body`, auto-expire with progress |
| Dialogs | 8 px radius, 24 px padding, header 48 px, action row right-aligned |
| Switches | 40×20 px track, 16 px handle, on = `--blue-3` |
| Progress | 4 px height, `--blue-3` fill on `--light-3` track |

---

## 4. Test IDs and evidence paths

Evidence root convention: `evidence/wave1/arch2015-sysvinit/`

| Test ID | Asserts | Evidence path | Status |
|---|---|---|---|
| `T-DS-001` | `DS-01` runlevel table resolves to a single graphical target; no duplicate DM respawn | `evidence/wave1/arch2015-sysvinit/DS-01/observation.md` | pending |
| `T-DS-002` | `DS-02` greeter runs unprivileged and cannot read `~/.config` | `evidence/wave1/arch2015-sysvinit/DS-02/observation.md` | pending |
| `T-DS-003` | `DS-03` drop-in ordering is deterministic and executable-bit gated | `evidence/wave1/arch2015-sysvinit/DS-03/observation.md` | pending |
| `T-DS-004` | `DS-04` user autostart shadows system entry of same filename; `OnlyShowIn` honored | `evidence/wave1/arch2015-sysvinit/DS-04/observation.md` | pending |
| `T-DS-005` | `DS-05` `TryExec` false ⇒ entry not shown; `StartupWMClass` binds window | `evidence/wave1/arch2015-sysvinit/DS-05/observation.md` | pending |
| `T-DS-006` | `DS-06` XSettings broadcast reaches GTK+2, GTK+3 and Qt clients | `evidence/wave1/arch2015-sysvinit/DS-06/observation.md` | pending |
| `T-DS-007` | `DS-07` mandatory > user; locked key cannot be changed by user | `evidence/wave1/arch2015-sysvinit/DS-07/observation.md` | pending |
| `T-DS-008` | `DS-08` dark variant resolves to same token set; user `gtk.css` overrides | `evidence/wave1/arch2015-sysvinit/DS-08/observation.md` | pending |
| `T-DS-009` | `DS-09` inheritance chain terminates at `hicolor`; no dangling `Inherits` | `evidence/wave1/arch2015-sysvinit/DS-09/observation.md` | pending |
| `T-DS-010` | `DS-10` cursor resolution is a single ordered chain | `evidence/wave1/arch2015-sysvinit/DS-10/observation.md` | pending |
| `T-DS-011` | `DS-11` `conf.d` numeric ordering is the effective precedence | `evidence/wave1/arch2015-sysvinit/DS-11/observation.md` | pending |
| `T-DS-012` | `DS-12` Qt and GTK+ resolve to identical accent token | `evidence/wave1/arch2015-sysvinit/DS-12/observation.md` | pending |
| `T-DS-013` | `DS-13` sound theme inheritance matches icon-theme semantics | `evidence/wave1/arch2015-sysvinit/DS-13/observation.md` | pending |
| `T-DS-014` | `DS-14` IM env-var contract honored by all toolkits | `evidence/wave1/arch2015-sysvinit/DS-14/observation.md` | pending |
| `T-DS-015` | `DS-15` console and X report identical layout | `evidence/wave1/arch2015-sysvinit/DS-15/observation.md` | pending |
| `T-DS-016` | `DS-16` one resolved locale set across session | `evidence/wave1/arch2015-sysvinit/DS-16/observation.md` | pending |
| `T-DS-017` | `DS-17` AT-SPI tree exposes all toolkit widgets | `evidence/wave1/arch2015-sysvinit/DS-17/observation.md` | pending |
| `T-DS-018` | `DS-18` exactly one notification daemon owns the D-Bus name | `evidence/wave1/arch2015-sysvinit/DS-18/observation.md` | pending |
| `T-DS-019` | `DS-19` SNI items render; legacy XEmbed is shim-only | `evidence/wave1/arch2015-sysvinit/DS-19/observation.md` | pending |
| `T-DS-020` | `DS-20` privileged actions are declared in polkit, none inline-scripted | `evidence/wave1/arch2015-sysvinit/DS-20/observation.md` | pending |
| `T-DS-021` | `DS-21` user `mimeapps.list` overrides system defaults | `evidence/wave1/arch2015-sysvinit/DS-21/observation.md` | pending |
| `T-DS-022` | `DS-22` XDG dirs resolved once and recorded | `evidence/wave1/arch2015-sysvinit/DS-22/observation.md` | pending |
| `T-DS-023` | `DS-23` compositor state is session-scoped | `evidence/wave1/arch2015-sysvinit/DS-23/observation.md` | pending |
| `T-DS-024` | `DS-24` per-monitor scale recorded, not inferred from resolution | `evidence/wave1/arch2015-sysvinit/DS-24/observation.md` | pending |
| `T-VL-001` | All §3.1 tokens present in shipped `gtk.css` with matching hex | `evidence/wave1/arch2015-sysvinit/VL/colors.md` | pending |
| `T-VL-002` | Type scale matches shipped `settings.ini` / `gtk.css` font sizes | `evidence/wave1/arch2015-sysvinit/VL/type.md` | pending |
| `T-VL-003` | Layout metrics match shipped CSS padding/margin values | `evidence/wave1/arch2015-sysvinit/VL/layout.md` | pending |
| `T-VL-004` | Dark variant resolves to identical token set | `evidence/wave1/arch2015-sysvinit/VL/dark-variant.md` | pending |
| `T-VL-005` | Icon theme ships all sizes declared in `index.theme` | `evidence/wave1/arch2015-sysvinit/VL/icons.md` | pending |
| `T-MIG-001` | Baseline manifest pins `initscripts` + `sysvinit`; init system is manifest-derived, not date-derived | `evidence/wave1/arch2015-sysvinit/MIG/baseline-manifest.md` | pending |
| `T-MIG-002` | All 2015 packages resolvable from Arch Linux Archive (M-07) | `evidence/wave1/arch2015-sysvinit/MIG/ala-resolvability.md` | pending |
| `T-MIG-003` | Every `DS-*` path is either present or explicitly declared absent in the baseline | `evidence/wave1/arch2…
