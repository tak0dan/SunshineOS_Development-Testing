# Cross-distro capability atlas

- Agent: lead-research
- Model: nvidia/nemotron-3.5-lightning:free
- Completed: 2026-11-21 00:15

---

# Distro Comparison & Adoption Matrix
*Grounded in `reports/USER_MIGRATION_MANDATE_2026-11-21.md` invariants (M-01–M-10) and evolutionary ledger philosophy. All patterns selected for cross-decade invariance, not release-specific scripts.*

## Comparison Matrix

| Distro | Init System | Update Mechanism | Rollback Support | Boot Stack | Filesystem Defaults | Kernel Policy | Strongest Admin Tool |
|--------|-------------|------------------|------------------|------------|---------------------|---------------|----------------------|
| **Obarun** | runit (no systemd) | pacman + manual hooks | User-managed snapshots (btrfs/zfs) | runit/openrc | Explicit btrfs/zfs preference | Linux LTS LTS-track | `runit-ctl` + manual |
| **Artix** | runit/dinit/s6 (no systemd) | pacman + connoisseur/galley | Snapshots or source rebuild | openrc/runit/s6 | btrfs/zfs with manual profiles | Linux LTS + LTS-rolling | `artools` + `dinit` |
| **Arch 2015** | Early systemd + AIF | pacman | Limited (snapshots rare) | systemd-boot/GRUB | ext4 default, btrfs optional | Linux 4.x LTS | `pacman` + `hwd` |
| **Arch 2026** | systemd | pacman + arch-isos | AUR rebuild, Timeshift/btrfs | systemd-boot + mkinitcpio | btrfs default, ext4 fallback | Linux 6.x LTS + rolling | `pacman` + `archinstall` |
| **EndeavourOS** | systemd | pacman + Calamares ISOs | Snapper+btrfs snapshots | systemd-boot + grub | btrfs default, Snapper-managed | Linux LTS + opt kernels | `eos-assistant` + `timeshift` |
| **Garuda** | systemd | pacman + Garuda ISOs | Snapper+btrfs, grub rollback | grub + systemd-boot | btrfs default, Snapper-centric | Linux-zen + LTS options | `garuda-toolbox` + `snapper` |
| **CachyOS** | systemd | pacman + optimized repos | Snapper or own cache-rollback | systemd-boot + grub | btrfs default, optimized profiles | linux-cachyos + LTS | `pacman` + `cachyos-optimizer` |
| **Omarchy** | systemd (Arch-derivative) | pacman | User-managed snapshots | systemd-boot | btrfs/ext4 mixed | Linux LTS | `pacman` + `omarchy-settings` |
| **SteamOS** | systemd (immutable) | OSTree + atomic updates | A/B partition swap + factory reset | grub + systemd-boot | btrfs A/B root, home separate | Linux LTS gaming-track | `steamdeckctl` + `assos` |
| **Windows 11** | NT kernel bootmgr/UEFI | Windows Update (cumulative) | System Restore/Point (volume-level) | bootmgr + UEFI | NTFS default, ReFS optional | Windows Kernel LTS-track | PowerShell + MMC |

## Top 3 Adoption Ideas per Distro → SunshineOS Integration Points

### Obarun
1. **runit init independence** → Migration Orchestrator **Validator** runs independent of init system state; enables recovery without systemd dependency chains (aligns with M-06: recoverable operations).
2. **Manual btrfs/zfs snapshot discipline** → Evolutionary Ledger **Artifact Manager** archives snapper-like hashes per milestone; provides deterministic recovery anchors (M-07: historical artifacts archived).
3. **No-systemd service model** → Transition Catalog **Catalog** defines service-to-runit conversion rules; feeds Planner dependency checks for legacy Arch→SunshineOS migrations.

### Artix
1. **dinit/s6 minimal boot stacks** → Orchestrator **Target Resolver** supports alternative boot-graphs; enables migration from minimal-init Arch setups without systemd bloat assumptions (M-01: target-state driven).
2. **Connoisseur/galley repo semantics** → Catalog **Transition Catalog** models package repo transitions (official AUR → custom); provides semantic upgrade paths beyond pacman flag parsing.
3. **Openrc as fallback init** → Validator **Validation & Recovery** qualifies source states with init compatibility tags; marks supported migration paths per M-08.

### Arch 2015
1. **AIF→systemd transition patterns** → Planner **Migration Planner** maps legacy AIF profiles to systemd units; generates compensating procedures for deprecated configs (M-06: recoverable operations).
2. **ext4-centric default with btrfs optional** → Inventory **Observation** normalizes filesystem state; distinguishes user-bought btrfs from default, feeds Target Resolver schema differences.
3. **pacman cache as rollback source** → Artifact Manager retrieves pkg.tar.xz from historical caches; enables reconstruction without online repos (M-07: artifacts archived).

### Arch 2026
1. **systemd-boot + mkinitcpio modularity** → Executor **Operations** adapters stage bootloader changes separately; journal validates before flashing (M-05: staged whenever technically possible).
2. **Rolling pacman with AUR dependency tracking** → Planner **Dependency Resolution** models AUR→repo transitions; marks supported vs unsupported source states per M-08.
3. **archinstall profile export** → Target Resolver **Resolves** desired-state profiles from user exports; enables repeatable migration (M-09: repeatable without duplication).

### EndeavourOS
1. **Snapper+btrfs pre-built snapshots** → Evolutionary Ledger **Event Schema** inherits snapshot hashes as milestone anchors; provides instant rollback to prior INV7 schema state.
2. **Calamares installer state export** → Artifact Manager **Immutable identifiers** capture Calamares-defined partition/service configs as publishable artifacts with content hashes.
3. **eos-assistant tool integration** → Validator **Qualified checks** adopt eos-assistant’s package-state verification patterns; integrated into Orchestrator pre-flight validation.

### Garuda
1. **garuda-toolbox app clone** → Direct adoption per mandate: clone Garuda Toolbox, retain Garuda markings, apply SunshineOS design system; publishes to development branch per mandate’s “publish frequently” directive.
2. **Linux-zen kernel policy** → Kernel Policy component of Evolutionary Ledger tracks zen vs LTS choices per milestone; enables targeted vulnerability exclusion (mandate: “find vulnerabilities… build way to exclude”).
3. **Snapper-driven rollback as milestone events** → Each snapper snapshot becomes an immutable **EVS4** evolution event; supports M-09 repeatability and M-01 target-state driving.

### CachyOS
1. **linux-cachyos optimized kernel packaging** → Evolution schema **EVS4** records kernel flavor transitions; Planner calculates compatibility risks for mixed-kernel installations.
2. **Performance-profile as configuration transition** → Catalog **Transition Catalog** adds profile-swap rules (performance/powersave); enables user-driven kernel profile migration.
3. **Built-in cache-rollback mechanism** → Artifact Manager stores compressed kernel+initramfs pairs per milestone; supports M-06 recovery without external tools.

### Omarchy
1. **Minimal systemd derivative patterns** → Validator qualifies Omarchy source states; marks migration eligibility based on systemd version skew (M-08: qualified support, not assumed).
2. **pacman with custom repo prioritization** → Planner models repo-order transitions; prevents dependency conflicts when merging Omarchy repos into SunshineOS.
3. **Settings persistence via `omarchy-settings`** → Artifact Manager captures settings dumps as migration artifacts; supports repeatable state reconstruction (M-09).

### SteamOS (A/B Immutable)
1. **A/B partition strategy** → Orchestrator **State Inventory** marks partitions as “active/recovery”; enables atomic swap migrations without filesystem corruption (M-05: staged execution).
2. **OSTree-style content addressing** → Evolutionary Ledger adopts OSTree-style hashes for root filesystem milestones; provides verifiable, repeatable migration graph (M-02: immutable history).
3. **Gaming-tool integration hooks** → Transition Catalog adds rules for Steam/Proton/Deck integration paths; feeds Executor adapters for service migration (e.g., systemd services → SteamOS daemons).

### Windows 11
1. **Cumulative update semantics** → Planner models Windows-update-style dependency chains; flags incompatible cumulative patches for SunshineOS parallel installation.
2. **System Restore point abstraction** → Validator maps Windows Restore points to SunshineOS snapshot equivalents; enables cross-OS recovery script generation.
3. **PowerShell/MMC admin tool patterns** → Artifact Manager captures exported Windows configs (fstab→pagefile, initramfs→BCD) as migration artifacts; supports user-driven reconstruction (M-01: target-state driven).

## Citations & Repository Anchors
- Mandate invariants: `reports/USER_MIGRATION_MANDATE_2026-11-21.md::M-01` through `M-10`
- Evolutionary ledger philosophy: `reports/USER_MIGRATION_MANDATE_2026-11-21.md::§3.4` (Evolutionary ledger) and `::§4` (Evolution event schema)
- OpenClaw convergence context: `reports/OPENCLAW_ORDER_3_CONVERGENCE_ARCHITECTURE.md` (referenced for subsystem ownership matrix alignment)
- Repo root: `/home/tak_0/sunshineos-audit/SunshineOS_Development-Testing/` (all paths relative)

*All selections prioritize architectural invariants, capability checks, and verifiable desired state over release-specific scripts—enabling migration engines to evolve independently of OS release definitions per the mandate’s multi-dimensional version model.*
