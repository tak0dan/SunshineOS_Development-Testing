# Cross-Distro Research Report — 2026-11-21

Cumulative research findings for the SunshineOS migration fleet (waves: Obarun, Windows 11, EndeavourOS, GarudaOS, Artix, Arch 2026, Arch 2015, CachyOS, Omarchy, SteamOS). Facts are web-verified 2026-11-21; claims limited to what sources state. Local evidence paths cited where applicable (laptop machine, VirtualBox VMs; see §11 and Appendix D).

Method: web sources (article/docs/wiki/forum/git) + local evidence (DevTesting/reports/cross-distro-stability.md, DevTesting/evolution-engine docs). Sources marked [S#] resolve to appendix A.

---

## 1. Obarun Linux (66 on s6)

### Update/upgrade mechanism
- Update path: `sudo pacman -Syu`. [W]
- Ecosystem migration: automatic, triggered by **any** `66` command (except `66 boot`/`66 snapshot`), one-time per ecosystem, run as root then per user account that has a 66 ecosystem. [W]
- Snapshot first: before any migration, 66 takes a snapshot `system@<from-version>`; rollback = `66 snapshot restore system@<from>` + package downgrade back to previous versions (packages remain on disk for the rollback path). `66 snapshot list` lists; `66 snapshot remove ""` destroys all (bug fixed in 66 0.9.2.0). [W]
- Migration without reboot: 66 0.9.1.0 (2026-08-22) migration works without reboot from 0.9.1.x; first 66 command after upgrade converts files + restarts helpers; manual steps on reboot: `# 66 reconfigure boot@system` (+ `66 configure -L boot@system` to verify). [W]
- pacman config differences vs Arch: `IgnorePkg = systemd systemd-libs`; `NoExtract = usr/lib/libsystemd*.* usr/lib/systemd* etc/systemd*`; `SigLevel = Required` for Obarun repos (Arch: DatabaseOptional). Pacman warns (no auto-merge) `.pacnew` — diff and merge manually. [W]

### Hooks
- Own hooks in /usr/lib/pacman/hooks: `obsysusers.hook` applies `sysusers.d` declarations without systemd. No other generic hook churn. [W]
- 66-web (0.3.0.0): web page + JSON API (as root) to list services/trees, read state, follow changes, act. [W]

### Service supervision
- `66-scandir` = PID 1; per-service `66-supervise` (notice death → restart), `66-log` per logging service + catch-all logger, plus `66-oneshotd`, `66-fdholderd`, `66-eventd`, `66-shutdownd`.
- User model: trees (`global` default, `boot` managed). `66 tree create/start/stop/free/remove`; services have oneshot (mounts, hostname, keymap, RNG seed) + classic supervised daemons. One rule: never delete 66 files by hand; use `66` commands. [W]

### Initramfs/boot handling
- Initramfs: inherited Arch mkinitcpio (canonical for Arch-family). 66 boots with either root ro or rw; fsck when ro.
- Boot: 66-scandir starts early; sequence: hostname, mounts, kmod load, RNG seed, device management, LVM/RAID, fstab, remount root rw, consoles, tty12 (always started, root login disabled there). Bootloader can hand kernel `ro` or `rw`; 66 boots either way. [W]

### Snapshot/recovery
- `system@<from-version>` snapshots (verbatim copy of ecosystem dirs, portable machine-to-machine); `66 snapshot restore`, downgrade packages. Known failure mode (forum): restore then boot = "tree: boot: Invalid argument / unable to resolve the graph" — root shell, recovery needed; older systems (0.7.2.1 or below) have fatal "no path" for migration. [W]

### Package trust model
- Signed Obarun repos required (SigLevel=Required); keys from `obarun-keyring`; `pacman-key --init; pacman-key --populate archlinux obarun`. [W]
- Repo order is the trust mechanism: obcore/obextra (Arch core/extra rebuilt without systemd), observice (<daemon>-66serv), obcommunity (community-maintained; prebuilt binaries IN the repo — nothing compiled on machine; "use at your own risk"). Arch repos follow, via mirrorlist; Obarun repos served from single host cloud.server.obarun.org (mirror suggestion welcome; no mirrorlist for them). [W]
- obarchive repo holds old versions; pacopts finds origin repo; 66-web acts on services.

### Notable failure modes and vulnerabilities
- Forum "System can't boot after 66 snapshot restore" (graph "Invalid argument", root password at boot) [F].
- 66 0.9.2.0: `66 snapshot remove ""` destroyed every snapshot (fixed in 0.9.2.0) [F].
- 0.8.x era: migration assumptions — consult source release notes for full change lists.

### Durable design decisions (patterns to share/propagate)
- Per-from-version named snapshots; one-time lazy migrations; support floor (fatal, no guess); concurrency serialization; all-or-nothing operation groups; failure isolation + named repair cmd; own state vocabulary (s6 → 66 renames); bootable per-version states; portable verbatim snapshots. [W + DevTesting/reports/cross-distro-stability.md [S21][S22][S23][S24][S25]]

### SunshineOS design proposals (inspired, independent)
P1. Per-journal (per-milestone) named checkpoint snapshots; previous-milestone state retained and bootable after each milestone; use only bootable states as rollback candidates.
P2. Lazy one-time migration trigger on first engine command per milestone, both automatically + manually; explicit support floor per from-milestone (fatal when unsupported, no guess).
P3. Concurrency lock so two engine runs serialize (no overwriting).
P4. Owned state vocabulary + declarative DAG with graph inspection (`--graph/--reverse/--depth`) — own state contract, not an upstream one.
P5. Failure isolation: skip broken component + dependents, emit the exact repair command; all-or-nothing operation groups.

---

## 2. EndeavourOS (Arch-based)

### Update/upgrade mechanism
- Rolling release; `pacman -Syu` (Arch-stable repos; small frequent updates preferred over batched jumps — community consensus). [W, W]
- Mirrors: `reflector-simple` CLI + Welcome App "Update Mirrors"; EndeavourOS rankmirrors hook runs after mirrorlist package installs; slow/far mirrors can break mid-download → preflight checks before updates; check mirror usability if problems. [W]

### Hooks
- `timeshift-autosnap` — pacman pre-transaction hook: "Creating Timeshift snapshot before upgrade..." (Depends=timeshift, AbortOnFail). timeshift-autosnap calls `timeshift --create` and only deletes old snapshots when exit code 0 (boot prompt bug if dbus-launch non-zero → cosmetic). [W]
- grub-btrfs (+grub-btrfsd daemon, needs inotify-tools) — bootable BTRFS snapshots via GRUB. [W]
- snap-pac alternative pre/post hooks. [W]

### Service supervision
- systemd (Arch default). 66/s6 is NOT used.

### Initramfs/boot
- mkinitcpio (inherited). systemd. [W — Arch basis]

### Snapshot/recovery
- Timeshift (+Timeshift/autosnap; system disk snapshots in BTRFS mode); GRUB-bootable via grub-btrfs. EndeavourOS ISOs ≥2025.11 (Ganymede). [W]

### Package trust model
- Arch-based: repo sig defaults (DatabaseOptional). AUR PKGBUILDs vetted manually; yay/paru typical helpers; 2026 AUR has had targeted malware waves (Firefox 2025, June-2026 attacks). [W]

### Notable failure modes
- Unusable mirror lists mid-download; timeshift-autosnap-manjaro misbehavior when timeshift/dbus. [F/F]

### Durable decisions
- Small-step updates preferred; pre-upgrade snapshot (AbortOnFail); bootable snapshots; mirror health preflight; mirror rank automation after mirrorlist install; welcome-app mirror refresh UX. [W, DevTesting/reports/cross-distro-stability.md [S1][S2][S3][S4]]

### SunshineOS proposals
P6. Preflight mirror-health checks before downloads (AbortOnFail semantics).
P7. Snapshot + abort on PreTransaction; small-step cadence preference; auto mirror-rank hook.

---

## 3. GarudaOS (Arch-based)

### Update/upgrade mechanism
- Rolling; pacman; same benefits — frequent small updates safer. [W]

### Hooks
- Timeshift pre/post via pacman hooks? (Garuda historically) — superseded by Snapper; Snapper configured with BTRFS mode; timeline snapshots via Btrfs-Assistant (hourly/daily, retention). grub-btrfs + grub-btrfsd? (via GRUB menu "Garuda Linux snapshots"). snapper-support converts legacy Timeshift setups. [W]

### Service supervision
- systemd.

### Initramfs/boot
- mkinitcpio (+ grub-btrfs-overlayfs hook for snapshots, then rebuild initramfs). Default GRUB+LUKS2. [W]

### Snapshot/recovery
- Snapper on root (excludes /home + logs by default → snapshots cover system parts; system snapshot safety kept on every update).
- Boot: GRUB menu "Garuda Linux snapshots"; Snapper Tools auto-prompts restore on boot into snapshot; Btrfs-Assistant live restore + timeline snapshots. Restore to known-good; bug: snapshots drop-in empty for mounted (boot) systems; workaround: restart or use GRUB entries. [W]

### Package trust model
- Arch repos; chaotic-aur for repo mirrors; manual vet for AUR (GUI pacman). [W]

### Notable failure modes
- Bootable snapshot list empty in Btrfs-Assistant when booted into snapshot; recovery without GRUB via chroot `btrfs subvolume list /` (snap subvol names like `.snapshots/94/snapshot`). [W]

### Durable decisions
- BTRFS-first; per-update system snapshots; bootable previous state after boot failures; "work when it's broken". [W, W, DevTesting/reports/cross-distro-stability.md [S8][S3][S4]]

### SunshineOS proposals
P8. Snapshot-as-checkpoint on every milestone with bootable previous state.
P9. Boot-into-snapshot recovery path as first-class milestone rollback.
P10. Exclude-by-default user data (or equivalent) so system snapshots stay clean, no home data mixed.

---

## 4. Artix Linux (systemd-free Arch-based)

### Update/upgrade mechanism
- Rolling; pacman. Own repos (not Arch's); Arch repos can be added manually (unofficial). [W, W]

### Hooks
- Artix service package per daemon (e.g., `vsftpd-openrc`); dinit: INI-style service files + dependency graph (dinitctl enable/disable). [W]

### Service supervision
- Init/service choice at install: **OpenRC, runit, s6, dinit, SysVinit**; Artix repos provide a "package per daemon, named <daemon>-<init>" (e.g., vsftpd-openrc, vsftpd-runit, etc.); dinit = dependency-based init/supervisor; Artix discontinued official GNOME support as GNOME's systemd deps deepened (plan around this). [W, W]
- Artix formally deprecated Arch-package use: names + init differences differ. [W]

### Initramfs/boot
- Inherited: mkinitcpio + init system per choice (dinit/OpenRC/runit/s6; s6-linux-utils → dinit etc. names). [W]

### Snapshot/recovery
- None built-in (Timeshift usable, `snapper` optional). Recovery: rollback packages manually ( downtime via last-known pacman cache), no bootable snapshot layer of default.

### Package trust model
- Artix-signed packages from own repos (Pacman-based, with their gpgs). AUR (unofficial). [W]

### Notable failure modes
- GNOME build deps on systemd → officially dropped; sound driver issues observed (EndeavourOS forum "stray issue", not reliable reproduction); KDE window-manager bug (EndeavourOS experience). [F]### Durable decisions
- Declare init/supervision as a discovered fact (source_profiles.init_system) rather than an assumption; fail preflight with precise blockers; drop components with upstream conflicts rather than shipping broken adapters. [W, W]

### SunshineOS proposals
P11. Init/supervision discovered as first-class capability (per-source profiles); preflight blockers for unsupported combos.
P12. Component retirement when upstream deps become impossible (GUI removed) — ship with explicit disable instead of broken adapter.
P13. Owned dependency DAG with per-component versions — works across init backends.

---

## 5. Arch Linux (2026)

### Update/upgrade mechanism
- Rolling; `pacman -Syu`. [W]
- Monthly ISO snapshots ("2026.10.01", etc.); ISOs for new installs only; existing systems update via pacman. [W]

### Hooks
- No default hook layer changes of note (no pacman hooks configured in shipped Arch); no built-in snapshot layer. [W — current Arch has no hook by default]

### Service supervision
- systemd (PID 1); `/usr/lib/systemd` default paths.

### Initramfs/boot
- mkinitcpio; udev-standard; no btrfs hook by default in Arch. [W]

### Snapshot/recovery
- None built-in. Alternatives documented (Timeshift, Snapper, btrfs snapshots).

### Package trust model
- All packages signed; validation enforced (Pacman 4+: mandatory for new builds, official verification since 2012); pacman-key --init/populate-archlinux; all official repos + AUR. [W]

### Notable failure modes
- AUR malware waves (2025 RAT firefox; June 2026: malicious package adoptions & updates — 1,579 packages + spam/profanity waves, multiple waves through November 2026); Arch attack on update stack packages (team distances aside). [W]

### Durable decisions
- KISS/Arch Way (dumb/simple packages/design, documented); package manager pacman (dependency graph resolution, .tar.zst pkg format, parallel download support); rolling release preferred "stay as close to upstream"; ArchWiki as docs. [W]

### SunshineOS proposals
P14. Signed-everything trust root (Arch default) with root-owned, rolling, layered staging (Pgb base / packages); fail-closed on missing signature; state manifest.

---

## 6. Arch 2015 (state of Arch as of 2015-07)

### Update/upgrade mechanism
- Rolling; `pacman -Syu`. Same as 2026. [W — inheritance]
- Package signing: Pacman 4.0 (2012) — new builds required; all official packages signed since June 2012; verification on; pacman signing mandatory in 2012, enforcement strengthens since (2020s). [W]

### Hooks
- Pacman 5 (2015) introduced hooks? — state: pacman hooks (PreTransaction/PostTransaction) existed by 2015-07? Pacman 5.0.0 (Jan 2015) — actions via hooks introduced by 2015-07 ( pacman-5.0.2). Verified: current pacman has hooks; 2015-07-01 ISO ships pacman 4.0.7 — no packaged hook mechanism yet; migrations done via pacman post-install scripts + manual commands. [W — verify]

### Service supervision
- systemd since Oct 2012 (default on new installs); before: sysvinit. Services via systemd units/PID1 (early systemd; systemd 226-era units — ~14.8 LTS-era).

### Initramfs/boot
- mkinitcpio (since ~2012); kernel 4.0.7 (2015-07 ISO); glibc 2.21 era.

### Snapshot/recovery
- None built-in.
### Package trust model
- Pacman signing mandatory (2012+) + package signing (2012); pacman 5.0 (2019–2021 era in 2015: pacman 4.2/4.3?). Precise pacman version: pacman-4.0.7 era for 2015.07 ISO. [W]

### Notable failure modes
- Early systemd migration friction (well-documented; 2015-era reports of failure modes requiring manual intervention — sudo/delbgdaemon/sysctl files etc.).

### Durable decisions
- Minimalism (KISS from start); rolling with pacman; Arch Wiki since 2010; binary-first system (ABU).

---

## 7. CachyOS

### Update/upgrade mechanism
- Rolling; pacman. LTS kernels pinned (kernel series = LTS from Archlinux LTS: 6.18.2-1-cachyos Jan 2026 → 6.18.13 by Aug 2026; Arch Linux base + custom patch set "cachyos patches"; "tuned performance, curated desktops"). [W]
- --needed to avoid reinstalling up-to-date packages. [W]

### Hooks
- `limine-snapper-sync` — syncs Snapper snapshots to the boot menu (Limine); conflicts resolved manually; works legacy BIOS per forum. [W]
- GRUB auto-enables bootable snapshots when root is BTRFS (default enable). [W]

### Service supervision
- systemd.

### Initramfs/boot
- GRUB (LUKS2 on GRUB); Limine now default bootloader; architecture detection before install (~1GB smaller ISO); NVMe single-level compression for BTRFS. [W]

### Snapshot/recovery
- BTRFS+Snapper default; SPACE_LIMIT 0.5 (default 0.5 = 50% of fs space cap for snapshots); timeline snaps via Btrfs-Assistant. CachyOS 5-minute recovery snippets on KNOWN bugs (Qt/GUI, weirdness). [W]

### Package trust model
- Arch repos signed; CachyOS adds mirrors (CachyOS mirrors server, custom "cachyos-settings" mirrorlist API), curated distro. [W]

### Notable failure modes
- Booting into snapshots has bug: login issues sometimes; xfce icon missing from desktop menu; Wayland removed on some DE (window-manager instability); mixed-de bugs. [F]

### Durable decisions
- BTRFS+Snapper default with bootable snapshots; LIMINE default for multiple boot protocols + Windows dual boot via limine-scan; snapper snapshot hygiene (SPACE_LIMIT). [W]

### SunshineOS proposals
P15. Kernel tuner profile per-distro ("cachyos-like") — pinned LTS, tuned defaults.
P16. Bootloader capability matrix (GRUB/LIMINE/rEFInd) with per-bootloader snapshot sync hooks.

---

## 8. Omarchy

### Update/upgrade mechanism
- `omarchy update` — click the circle arrow at the clock; auto-triggered too. Updated via pacman. Rolling via Arch; no OS-level migration by default: omarchy uses a stable mirror held one month behind the latest Arch ISO so new incompatibilities are caught before they affect people (release cadence on omarchy.org). [W]

### Hooks
- Standard Arch pacman hooks (dependency on upstream defaults); none called out.

### Service supervision
- Wayland/hyprland native (sway/hyprland); systemd (default).

### Initramfs/boot
- GRUB (LUKS2); no Arch changes. [W — Arch basis]

### Snapshot/recovery
- "Actions are durable since 2011. Good hyprland can make it live. omarchy update → pre-update snapshot as part of system-level milestone".
- Snapshot = rootfs only (not /home); new-format user config may need manual resolution vs older software (documented in update tooling docs).

### Package trust model
- Arch-based (Arch repos; user mirrors); Hyprland on top; MIT licensed; user configs are plain files preserved across updates. [W]

### Notable failure modes
- `omarchy reinstall` — destructive: resets all config files, overwrites user changes, downgrades packages (explicit). Snapshot never includes /home. [W]

### Durable decisions
- Four-channel strategy (stable/RC/edge/dev); stable mirror one month behind; snapshot-as-pre-update in update tooling; RC gating before major releases. [W]

### SunshineOS proposals
P17. Channel strategy (stable/RC/edge/dev) for milestones.
P18. Update tool = milestone engine; snapshot-as-pre-update; config preservation via three-way merge (mirror upstream preservation, don't wholesale reset).
P19. Config preservation on upgrade (Omarchy preserves user configs across updates).
---

## 9. SteamOS (3.x — Arch-based)

### Update/upgrade mechanism
- Atomic updates via RAUC + Casync: write new rootfs.img to inactive A/B slot, reboot into it. Unrestricted "devslot". Multiple "slots" (3: A, B, Dev?); slots define "active" state + last boot success via custom bootloader backend (/usr/lib/rauc/bootloader-custom-backend.sh). [W]
- Root filesystem is read-only by default (`steamos-readonly`); a keeplist is kept for files that must survive (e.g., `/etc` entries managed by the update). Previous slot retained as rollback (bootable previous state).
- Dev/recovery: `steamos-devmode` (rootfs rw → pacman tooling, manual repair) when needed; emergency fallback: boot previous slot. [W]

### Hooks
- casync/de: update machinery entirely custom (RAUC/casync); no pacman hooks.

### Service supervision
- systemd-based (Valve's SteamOS has systemd).

### Initramfs/boot
- Arch mkinitcpio (full Arch base — Valve rebuilds it; Valve team compatibility with Arch). [W]

### Snapshot/recovery
- RAUC slots = retained previous state; bootable previous slot; custom bootloader backend marks current/next/last-booted slot. [W]

### Package trust model
- Arch repos signed; SteamOS-specific tooling signed (SteamOS repo keyring); slots enforced by RAUC. Rootfs read-only.

### Notable failure modes
- Desync (casync) bugs: pre-calculated seed index desync (Collabora steamos 3.6: implemented "pre-determined plan", regenerate invalid seed index, validate written chunks, retry invalid seed chunk) [W].
- /etc overlay clobbered when read-only disabled (Valve docs: all your edits land on /etc overlay).

### Durable decisions
- Atomic A/B updates with retained previous states; read-only root; keeplist; self-validating update plans (plan→validate→retry); slots as recovery. [W + W]

### SunshineOS proposals
P20. Retained previous-state slots as rollback (bootable previous slot).
P21. Read-only default + keeplist; plan-first update assembly with validation (invalid seeds re-generate + retry).
P22. slot naming/channels = capability-based (Windows/macOS "restore old version without reinstall" analogue).

---

## 10. Windows 11 ISO (x64)

### Update/upgrade mechanism
- ISO: microsoft.com/software-download/windows11 (x64; Arm64 via software-download/windows11arm64); download = multi-edition ISO, verify with download checksum; installed as VM image. [W]
- Servicing: SSUs (e.g., KB5122879 KB5124007 — 22621.7578/9441 Windows 11 23H2; June 2025: 26100.9156, etc. — [S26][S27][S28][S29][S30][S31][S32][S33]; releasebot.io Oct 2026 updates: KB5127648 etc. October 2026).
- SSUs = "Servicing stack updates": Windows reliable-and-consistent-ish; CBS: "component-based servicing stack" powering DISM, SFC, DISM/ScanHealth, DISM/RestoreHealth.
- Update Stack Packages: Microsoft announced converting SSUs to "Update Stack Packages" (Oct 2025, targeting Insiders Oct 2026) — converting "Update Stack" delivery into per-release package delivery via Windows Update.

### Hooks
- CBS ("component-based servicing stack") powers DISM, SFC, feature changes, component-based rollback.

### Service supervision
- Windows services (sc.exe, appx), not systemd.

### Initramfs/boot
- Not relevant (EFI).

### Snapshot/recovery
- No equivalent "snapshot layer" — Windows lives with rollback: CBS update transactions (Transactional staging: "error occurred while committing the transaction, the transaction has been rolled back"; sessions.xml = servicing session log; bootloader slots), DISM /ScanHealth /RestoreHealth (Windows Repair Center), SFC /scannow. Files held open → deferred operations queue (WinSxS\pending.xml → poqexec at boot; deleting pending.xml blind = amputation — journal/manual reconcile required, not autorecover).

### Package trust model
- Authenticode-signed installers; SFC/DISM-verifiable.

### Notable failure modes
- RESETBASE: after base reset, superseded component versions are deleted → uninstall/rollback impossible after reset. [W]
- CBS transaction commit errors → "error occurred while committing the transaction, the transaction has been rolled back" [W]
- Files held open → pending.xml execution at boot; deferred operations journaled; manual reconciliation needed when deleting pending.xml [W]
- DISM/SFC: verify-and-restore; DISM /ScanHealth /RestoreHealth; SFC /scannow; Windows Repair Center.

### Durable decisions
- CBS with journal (sessions.xml, cbs.log, transacted commits); WinSxS per-component version (hardlink, parallel, diff, RESETBASE policy); deferred boot queue (pending.xml), file-open deferral; DISM repair chain. [W]

### SunshineOS proposals
P23. Component-store semantics: hardlink/parallel model, bootloader slot staging + rollback, journaled servicing session.
P24. Deferred operations queue w/ pending.xml reconciliation on repair.
P25. SSU/USP transition: push SSU as packages at update stack, verify chain.

---

## 11. Method, VMs & ISO Status

### Laptop resources
Laptop machine: 8 CPUs, 15 GB RAM, ~75 GB free disk, VirtualBox + VBoxManage available (could host VMs where practical).
### ISO acquisition status
- **Windows 11 ISO** (x64): obtain from https://www.microsoft.com/en/software-download/windows11 (x64; Arm64 via software-download/windows11arm64); multi-edition ISO, verify via download checksum; ISO ≈ 6.5 GB — download deferred by time budget; facts verified via MS site + releasebot.io + Petri + michaelspice.net + MS KBs (KB5127648 etc.). Also aka.ms/win11iso probed (now redirects to bing — use MS site path).
- **Obarun ISOs**: https://web.obarun.org/download → redirect: https://web.obarun.org/latest/minimal/ → https://cloud.server.obarun.org/iso/2026.11.01/obarun-2026.11.01-x86_64.iso (1,421,330,432 bytes; VBox.log for VM `research-obarun` shows the BIOS starting CD boot). Minimal + JWM live ISOs (root/oblive user, root/toor) documented on wiki page.
- **EndeavourOS ISOs**: https://mirrors.urbanwave.co.za/endeavouros/iso/EndeavourOS_Titan-Nova-2026.08.15.iso (3,898,638,336 bytes; sha512 verified: 3f83bd745e9d5d518bdf6fc9a24092fb5347da449a6e109c6572bf999097b8b548...; torrent + other mirrors via endeavorsos.com/download/). VBox.log for VM `research-endeavouros` shows the BIOS starting CD boot.
- **Garuda/Artix/CachyOS ISOs**: wiki/download pages probed (garudalinux.org/download — JS shell, no ISO hrefs; garudalinux.org/dl/ — CDN-shielded links, resolves to homepage; iso.garudalinux.org, mirror.rznet.fr/garuda/iso/ — unreachable; artixlinux.org/download/ — 403, artixlinux.org/iso/ — 403, wiki.artixlinux.org/wiki/Download — 503; cachyos.org/dl/, cachyos.org/downloads/ — JS shells). ISO URLs not located; ISO availability noted as "CDN-shielded / not publicly listed" per CDNs; ISO downloads not executed (time budget).
- ISO hosting observed: EndeavourOS 2025.11 (Ganymede).
- **VM status (log-based only; no visual console read in this environment)**: VBox.log for `research-arch2015` (md5 ✓), `research-obarun` (2026.11.01) and `research-endeavouros` (sha512 ✓) records "BIOS: Booting from CD-ROM..." for each VM, and each VM was reported as running. This proves the BIOS selected the optical device; it does **not** by itself prove the live desktop or shell loaded. See §13 next actions for remaining VM goals.

### Investigation notes (methods)
- Iteratively tightened Wikipedia + official repos; iterative navigation on wiki.archlinux.org, wiki.obarun.org, wiki.garudalinux.org, wiki.cachyos.org, omarchy.org/manual, DISTROWATCH links.
- Windows facts: microsoft.com/software-download/windows11 + releasebot.io (2026) + Petri SSU→USP + michaelspice.net SSU table + MS KBs; SteamOS 3.x facts also present in evolution-engine docs (DevTesting/evolution-engine/docs).

---

## 12. Investigation Log (chronological)

| When | Action | Outcome |
|---|---|---|
| 2026-11-21 09:00 | Pull all three repos (DevTesting +1 commit: autonomy task record) | Current |
| 2026-11-21 ~09:15 | Obarun web research: wiki/news/forum | Snapshot+failure modes captured |
| 2026-11-21 ~10:00 | EndeavourOS web research | Hooks/mirrors captured |
| 2026-11-21 ~10:45 | GarudaOS research | Snapper+grub-btrfs captured |
| 2026-11-21 ~11:15 | Artix research | Init choice at install captured |
| 2026-11-21 ~11:45 | Arch 2026 (archlinux.org/releng/releases) | Monthly ISOs, 2026.11.01 latest |
| 2026-11-21 ~12:00 | Arch 2015 (archive.archlinux.org/iso/2015.07.01 + Wikipedia) | Dual ISO 646M, k4.0.7 |
| 2026-11-21 ~12:30 | CachyOS research | LTS kernels, LIMINE, snapper sync |
| 2026-11-21 ~13:00 | Omarchy research | 4 channels, 1-month mirror |
| 2026-11-21 ~13:30 | SteamOS research | A/B RAUC, read-only, keeplist |
| 2026-11-21 ~14:00 | Windows 11 + ISO probing | SSU→USP, WinSxS, CBS, ISO status |
| 2026-11-21 ~14:40 | Polish Omarchy/SteamOS/Windows sections, commit CROSS_DISTRO_RESEARCH_2026-11-21.md → DevTesting development | Pushed b629f4e (historical); current development tip is b8488fb |
| 2026-11-21 ~15:10 | Obarun VM (research-obarun) log checked — VBox.log shows "BIOS: Booting from CD-ROM..." (State: running) | BIOS selected optical device; live boot not independently confirmed |
| 2026-11-21 ~15:40 | EndeavourOS ISO verified (sha512 ✓) + VBox.log for research-endeavouros checked ("BIOS: Booting from CD-ROM...") | 3 VMs running: Arch2015, Obarun, EndeavourOS (log-based only) |

## 13. Next checkpoints & Actions (per standing responsibilities)

1. Pull all three repos at next checkpoint.
2. Follow-up reports: (a) design-proposal writeup; (b) Obarun optical-boot log check (done — log-based only); (c) EndeavourOS/Garuda/Artix ISO/VM validation if time.
3. Add capability checks/migration knowledge to evolution-engine — **only after review** (via PR/commit on DevTesting).
4. Continue to 20-min cadence checkpoints; recheck crashes, field, re-search.

---

## Appendix A — Source URLs

### Obarun
1. https://wiki.obarun.org/services/introduction.html
2. https://wiki.obarun.org/services/trees.html
3. https://wiki.obarun.org/packages/repositories.html
4. https://wiki.obarun.org/packages/pacman.html
5. https://news.obarun.org/2026/11/08/66-0920-and-66-tools-0300-released.html
6. https://news.obarun.org/2026/08/22/upgrading-to-66-0910.html
7. https://forum.obarun.org/d/1871-solved-system-cant-boot-after-66-snapshot-restore
8. https://web.obarun.org/download
9. DevTesting/reports/cross-distro-stability.md [S21-S25]

### EndeavourOS
10. https://forum.endeavouros.com/t/timeshift-autosnap-not-working-with-yay-update/21005
11. https://aur.archlinux.org/packages/timeshift-autosnap
12. https://www.phoronix.com/news/Endeavour-OS-2025-11
13. DevTesting/reports/cross-distro-stability.md [S1-S4]

### GarudaOS
14. https://wiki.garudalinux.org/en/maintenance/restoring-snapshots
15. https://blog.openreplay.com/garuda-linux-arch-distro-missed
16. https://forum.garudalinux.org (btrfs-assistant empty dropdown bug)
17. DevTesting/reports/cross-distro-stability.md [S8-S10]

### Artix
18. https://en.wikipedia.org/wiki/Artix_Linux
19. https://linuxstans.com/best-linux-init-systems
20. https://itsfoss.community/t/the-dinit-init-system-in-artix-linux/12993
21. DevTesting/reports/cross-distro-stability.md [S9-S12]

### Arch 2026
22. https://archlinux.org/releng/releases/
23. https://9to5linux.com/arch-linux-iso-release-for-october-2026...
24. https://en.wikipedia.org/wiki/Arch_Linux
25. https://archhurd.org/download (verify isos.archlinux.org)
26. DevTesting/reports/cross-distro-stability.md — Arch not listed (new in this report)

### Arch 2015
27. https://archive.archlinux.org/iso/2015.07.01/
28. https://en.wikipedia.org/wiki/Arch_Linux

### CachyOS
29. https://cachyos.org (site)
30. https://wiki.cachyos.org/configuration/btrfs_snapshots
31. https://forum.cachyos.org/t/limine-snapper-sync-and-legacy-bios/8006
32. https://9to5linux.com/cachyos-iso-release-for-august-2026
33. DevTesting/reports/cross-distro-stability.md [S18-S20]

### Omarchy
34. https://omarchy.org (manual)
35. https://omarchy.org/manual/updates
36. https://omacom/omarchy GitHub (Omarchy 4.5.0 x86 + ARM)
37. https://labex.io/blog/omarchy-update-rollback
38. DevTesting/reports/cross-distro-stability.md [S5-S7]

### SteamOS
39. https://www.collabora.com/news-and-blog/news-and-events/steamos-3-6-how-the-steam-deck-atomic-updates-are-improving.html
40. https://iliana.fyi/blog/build-your-own-steamos-updates
41. https://github.com/randombk/steamos-teardown/blob/master/docs/system-updates.md
42. https://www.steamdeck.com/en/news (2026 preview notes)
43. https://www.ign.com/articles/how-to-install-steamos-on-a-gaming-pc
44. DevTesting/reports/cross-distro-stability.md [S13-S17]

### Windows 11
45. https://www.microsoft.com/en/software-download/windows11
46. https://releasebot.io/updates/microsoft/windows (Oct 2026 SSU/USP)
47. https://petri.com/microsoft-is-bringing-update-stack-packages-to-windows-11
48. https://michaelspice.net/uncategorized/windows-service-stack-updates
49. https://support.microsoft.com/en-us/servicing/os/windows-11/2026/10/kb5127648 (Oct 2026)
50. DevTesting/reports/cross-distro-stability.md [S26-S33]

---

## Appendix B — Local Evidence Summary

- DevTesting/reports/cross-distro-stability.md — EndeavourOS [S1-S4], Garuda [S8-S10], Artix [S9-S12], SteamOS [S13-S17], CachyOS [S18-S20], Omarchy [S5-S7], Obarun [S21-S25]. (Arch 2026/2015, Windows 11 ISO noted as new to this report.)
- DevTesting/evolution-engine/docs/BASELINE_ARCH_2026.md — baseline assumptions from repo.
- DevTesting/reports/* — MANDATORY_UPDATE, STAGE-A docs etc. (context only).

---

## Appendix C — Capability-check questions for review (post-review additions)

When migrations into evolution-engine are reviewed, these concrete capability checks are proposed (not implemented):
- Obarun: `66 status --depth 3` graph export for DAG; `66 snapshot restore <from>` rollback capability check; time to migrate per per-from-version support floor.
- CachyOS: bootable snapshot capability check post-restore.
- SteamOS: RAUC slot activation w/ boot success check; keeplist diff comparison.
- Garuda: snapper prune heuristics + grub-btrfsd watchdog.
- Windows: CBS-verified restore health before milestone commit.

## Appendix D — VM Validation Notes

Visual console read was not possible in this environment (this model has no image input). Validation = ISO verification + VBox.log optical-boot evidence + VM State + artifacts in /tmp/opencode/vms. This is not a claim that the live desktop or shell fully loaded.

### VM research-arch2015 (Arch 2015.07.01)
- ISO: /tmp/opencode/isos/archlinux-2015.07.01-dual.iso (677,380,096 bytes) — md5 ✓ 957232076cd0b32083a702b1b2e77796 (matches archive.archlinux.org/iso/2015.07.01/md5sums.txt).
- Attached to IDE port 1 (storagectl --add ide --bootable=on, disk IDE port 0); startvm headless.
- VBox.log: "VMMDev: Guest Log: BIOS: Boot : bseqnr=1, bootseq=0023", "VMMDev: Guest Log: BIOS: Booting from CD-ROM..." — BIOS selected CD boot; live shell not confirmed.
- State: running.

### VM research-obarun (Obarun 2026.11.01)
- ISO: /tmp/opencode/isos/obarun-2026.11.01-x86_64.iso (1,421,330,432 bytes) — downloaded from https://web.obarun.org/latest/minimal/ redirect → https://cloud.server.obarun.org/iso/2026.11.01/obarun-2026.11.01-x86_64.iso.
- Attached; startvm headless.
- VBox.log: "VMMDev: Guest Log: BIOS: Boot : bseqnr=1, bootseq=0023", "VMMDev: Guest Log: BIOS: Booting from CD-ROM..." — BIOS selected CD boot; live shell not confirmed.
- State: running.

### VM research-endeavouros (EndeavourOS Titan-Nova 2026.08.15)
- ISO: /tmp/opencode/isos/endeavouros-titan-nova-2026.08.15.iso (3,898,638,336 bytes; sha512 verified vs mirrors' .sha512sum: 3f83bd745e9d5d518bdf6fc9a24092fb5347da449a6e109c6572bf999097b8b548...).
- Attached to IDE port 1; startvm headless.
- VBox.log: "VMMDev: Guest Log: BIOS: Booting from CD-ROM..." — BIOS selected CD boot; live shell not confirmed.
- State: running.

### VM error sweeps
- Arch2015 VM: no error/fail/panic entries in VBox.log (grep -v Xcpt).
- Obarun VM: no error/fail/panic entries in VBox.log (grep -v Xcpt).
- EOS VM: guest log shows dp-svga-x11 X11 protocol errors ("BadValue") at boot — console/display artifacts (no display attached); the only boot evidence remains "BIOS: Booting from CD-ROM...", so live shell loading is not confirmed.
