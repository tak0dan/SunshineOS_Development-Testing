# **Sunshine OS: evolutionary Arch-to-Sunshine transformation architecture**

This changes the architectural goal in an important way.

You are not designing a migration system that upgrades an existing Sunshine OS installation. You are designing a system that can **take a supported Arch Linux installation, discover what is already present, and construct the current Sunshine OS architecture on top of it**.

In other words, Sunshine OS should be a target state, not a prerequisite.

The most important requirement becomes:

> Installing and running `sunshine-update` on a supported, nearly pure Arch Linux installation must be sufficient to transform that installation into the current Sunshine OS, including introducing components, services, configuration structures, management mechanisms and system policies that did not previously exist.

This is a stronger architecture than conventional distribution upgrades.

I would design it around five principles:

1. **Desired-state convergence:** Sunshine describes what the current system should look like, then reconciles the installed machine with that state.
2. **Capability discovery:** the engine inspects the actual machine instead of assuming a particular installation history.
3. **Evolutionary components:** every Sunshine subsystem can be introduced, upgraded, replaced or removed independently.
4. **Declarative transformation plans:** the engine calculates which operations are needed, including operations that have never existed on the machine before.
5. **Upstream preservation:** Arch remains the underlying distribution. Sunshine adds and integrates its own architecture rather than replacing Arch's package-management model.

The resulting system should be able to handle both:

```
Old Sunshine OS ───────────────> Current Sunshine OS
```

and:

```
Pure Arch Linux ────────────────> Current Sunshine OS
```

without maintaining two separate upgrade implementations.

The second path is the more demanding one. It should be treated as a fundamental test of the design.

# **1. The central concept: target-state construction**

I would stop thinking of migration as a sequence of version upgrades and instead model it as a transformation from an observed system state into a desired system state.

Consider a machine with:

- Arch Linux.
- Pacman.
- systemd.
- GRUB.
- mkinitcpio.
- NetworkManager.
- PipeWire.
- KDE Plasma.
- No Sunshine management infrastructure.

It installs one Sunshine package:

```
sudo pacman -S sunshine-update
```

Then:

```
sudo sunshine-update
```

The updater discovers the system and compares it against the current Sunshine target.

**Source state: detected Arch installation**

**Arch Linux**

Detected

- Pacman package manager
- systemd
- Existing kernel and initramfs
- Existing bootloader
- NetworkManager
- PipeWire
- KDE Plasma
- No Sunshine components

**Sunshine transformation engine**

Discover → Plan → Prepare → Transform → Validate

**Current Sunshine OS**

Target state

- Arch foundation retained and updated
- Sunshine Core installed
- Ownership registry initialized
- Current configuration architecture
- Current recovery infrastructure
- Current desktop integration
- Current repository and update policies
- Kernel and boot integration validated

The engine does not need to know whether the source machine was:

- Installed from an old Sunshine ISO.
- Installed from a recent Sunshine ISO.
- Installed manually from Arch.
- Previously converted from Arch into Sunshine.
- Partially configured by the user.

It needs to know what exists, what is supported, and what must change.

This is the fundamental difference between a release-based migration engine and a target-state transformation engine.

## **1.1 The target must be a complete system specification**

Sunshine should publish a versioned description of the current desired system.

For example:

```
format_version = 1

[distribution]
name = "sunshine-os"
release = "5.0"
architecture = "x86_64"

[foundation]
distribution = "arch"
package_manager = "pacman"
init_system = "systemd"

[components]
core = { schema = 3, required = true }
configuration = { schema = 4, required = true }
ownership = { schema = 2, required = true }
kernel_management = { schema = 2, required = true }
boot_integration = { schema = 2, required = true }
recovery = { schema = 3, required = true }
desktop_integration = { schema = 4, required = true }
nix_integration = { schema = 2, required = false }

[policies]
preserve_user_configuration = true
preserve_user_packages = true
require_signed_packages = true
```

This is a simplified example. A real target specification must also describe package requirements, capabilities, service relationships, supported alternatives, configuration ownership, filesystem requirements and security constraints.

The target is not a script saying what to install.

It is a declaration of what the final system must provide.

The transformation engine determines how to achieve it.

# **2. The bootstrap package:&#x20;**`sunshine-update`

This package has a special responsibility: it must be capable of transforming a system that has none of the Sunshine infrastructure installed.

It is therefore not an ordinary updater package.

It is the **bootstrap entry point** for Sunshine OS.

I would make it deliberately small in scope, but self-sufficient enough to establish the complete management architecture.

## **2.1 What the package contains**

```
sunshine-update/
│
├── usr/
│   ├── bin/
│   │   └── sunshine-update
│   │
│   ├── lib/
│   │   └── sunshine/
│   │       └── bootstrap/
│   │           ├── sunshine-bootstrap
│   │           └── bootstrap-policy.toml
│   │
│   └── share/
│       └── sunshine/
│           └── trust/
│               ├── repository-root.pub
│               └── trust-policy.toml
│
└── etc/
    └── sudoers.d/
        └── sunshine-update
```

I would actually avoid a broad sudoers rule. Prefer a small unprivileged CLI that requests narrowly scoped privileged operations through a polkit-authorized service or a dedicated helper. The bootstrap package can install the initial privileged helper and its authorization policy.

The package should contain:

| Component            | Purpose                                                                 |
| -------------------- | ----------------------------------------------------------------------- |
| `sunshine-update`    | User-facing command and update interface                                |
| Bootstrap executable | Initial discovery, trust establishment and transformation orchestration |
| Trust root           | Initial Sunshine repository trust anchor                                |
| Bootstrap policy     | Defines the operations allowed during initial conversion                |

The bootstrap executable should be Rust, preferably with minimal external runtime dependencies.

It should not depend on Python, Nix, Flatpak, a graphical desktop, or any other Sunshine component that it is supposed to install.

It can use the existing Arch system facilities, but its bootstrap-critical logic should not depend on a particular desktop environment.

## **2.2 The bootstrap trust problem**

There is an important security issue here.

If `sunshine-update` can download and execute arbitrary code as root, it effectively becomes a remote root-execution mechanism.

Therefore, the initial package must establish a trust chain.

The recommended process is:

1. The user installs a genuine Sunshine-signed `sunshine-update` package.
2. The package contains a pinned Sunshine repository trust root.
3. The bootstrap executable verifies signed repository metadata.
4. The metadata identifies the current target definition and required packages.
5. Every downloaded artifact is verified before installation or execution.
6. Signing-key rotation follows a verifiable chain from the original trust root.

Do not download a public key from the same unauthenticated server that supplies the migration code and then trust it automatically.

Arch's package-signing model already relies on trusted signing keys and explicit trust relationships. Sunshine should preserve that principle rather than weaken it for convenience.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://wiki.archlinux.org\&sz=32)

ArchWiki+1



There is a further distinction: the trust root inside the package authenticates future Sunshine releases, but it does not establish that the original package itself was genuine. That authenticity must come from the way the user obtained and installed the initial package.

## **2.3 Bootstrap must be upgradeable**

The bootstrap implementation cannot be permanent.

Five years from now, it may be too old to understand the current target specification or migration protocol.

Therefore, the first transformation should replace or upgrade the bootstrap infrastructure itself.

For example:

```
sunshine-update package
        |
        v
bootstrap v1
        |
        v
verify repository
        |
        v
install Sunshine Core v5
        |
        v
hand over orchestration
        |
        v
current Sunshine migration engine
```

The bootstrap executable should implement a stable, minimal protocol for handing over control to a newer Core.

It should not attempt to implement every future migration feature.

This gives you a small, relatively stable entry point while allowing the actual migration engine to evolve significantly.

# **3. The transformation architecture**

I would divide the system into six functional stages.

\#chatgpt-mermaid-\_r_228\_{font-family:-apple-system-body,ui-sans-serif,-apple-system,system-ui,Segoe UI,Helvetica,Apple Color Emoji,Arial,sans-serif,Segoe UI Emoji,Segoe UI Symbol;font-size:16px;fill:rgb(237, 237, 237);}@keyframes edge-animation-frame{from{stroke-dashoffset:0;}}@keyframes dash{to{stroke-dashoffset:0;}}#chatgpt-mermaid-\_r_228\_ .edge-animation-slow{stroke-dasharray:9,5!important;stroke-dashoffset:900;animation:dash 50s linear infinite;stroke-linecap:round;}#chatgpt-mermaid-\_r_228\_ .edge-animation-fast{stroke-dasharray:9,5!important;stroke-dashoffset:900;animation:dash 20s linear infinite;stroke-linecap:round;}#chatgpt-mermaid-\_r_228\_ .error-icon{fill:rgb(48, 48, 48);}#chatgpt-mermaid-\_r_228\_ .error-text{fill:rgb(237, 237, 237);stroke:rgb(237, 237, 237);}#chatgpt-mermaid-\_r_228\_ .edge-thickness-normal{stroke-width:1px;}#chatgpt-mermaid-\_r_228\_ .edge-thickness-thick{stroke-width:3.5px;}#chatgpt-mermaid-\_r_228\_ .edge-pattern-solid{stroke-dasharray:0;}#chatgpt-mermaid-\_r_228\_ .edge-thickness-invisible{stroke-width:0;fill:none;}#chatgpt-mermaid-\_r_228\_ .edge-pattern-dashed{stroke-dasharray:3;}#chatgpt-mermaid-\_r_228\_ .edge-pattern-dotted{stroke-dasharray:2;}#chatgpt-mermaid-\_r_228\_ .marker{fill:rgb(175, 175, 175);stroke:rgb(175, 175, 175);}#chatgpt-mermaid-\_r_228\_ .marker.cross{stroke:rgb(175, 175, 175);}#chatgpt-mermaid-\_r_228\_ svg{font-family:-apple-system-body,ui-sans-serif,-apple-system,system-ui,Segoe UI,Helvetica,Apple Color Emoji,Arial,sans-serif,Segoe UI Emoji,Segoe UI Symbol;font-size:16px;}#chatgpt-mermaid-\_r_228\_ p{margin:0;}#chatgpt-mermaid-\_r_228\_ .label{font-family:-apple-system-body,ui-sans-serif,-apple-system,system-ui,Segoe UI,Helvetica,Apple Color Emoji,Arial,sans-serif,Segoe UI Emoji,Segoe UI Symbol;color:rgb(237, 237, 237);}#chatgpt-mermaid-\_r_228\_ .cluster-label text{fill:rgb(237, 237, 237);}#chatgpt-mermaid-\_r_228\_ .cluster-label span{color:rgb(237, 237, 237);}#chatgpt-mermaid-\_r_228\_ .cluster-label span p{background-color:transparent;}#chatgpt-mermaid-\_r_228\_ .label text,#chatgpt-mermaid-\_r_228\_ span{fill:rgb(237, 237, 237);color:rgb(237, 237, 237);}#chatgpt-mermaid-\_r_228\_ .node rect,#chatgpt-mermaid-\_r_228\_ .node circle,#chatgpt-mermaid-\_r_228\_ .node ellipse,#chatgpt-mermaid-\_r_228\_ .node polygon,#chatgpt-mermaid-\_r_228\_ .node path{fill:rgb(52, 24, 11);stroke:rgb(172, 79, 35);stroke-width:1px;}#chatgpt-mermaid-\_r_228\_ .rough-node .label text,#chatgpt-mermaid-\_r_228\_ .node .label text,#chatgpt-mermaid-\_r_228\_ .image-shape .label,#chatgpt-mermaid-\_r_228\_ .icon-shape .label{text-anchor:middle;}#chatgpt-mermaid-\_r_228\_ .node .katex path{fill:#000;stroke:#000;stroke-width:1px;}#chatgpt-mermaid-\_r_228\_ .rough-node .label,#chatgpt-mermaid-\_r_228\_ .node .label,#chatgpt-mermaid-\_r_228\_ .image-shape .label,#chatgpt-mermaid-\_r_228\_ .icon-shape .label{text-align:center;}#chatgpt-mermaid-\_r_228\_ .node.clickable{cursor:pointer;}#chatgpt-mermaid-\_r_228\_ .root .anchor path{fill:rgb(175, 175, 175)!important;stroke-width:0;stroke:rgb(175, 175, 175);}#chatgpt-mermaid-\_r_228\_ .arrowheadPath{fill:rgb(175, 175, 175);}#chatgpt-mermaid-\_r_228\_ .edgePath .path{stroke:rgb(175, 175, 175);stroke-width:1px;}#chatgpt-mermaid-\_r_228\_ .flowchart-link{stroke:rgb(175, 175, 175);fill:none;}#chatgpt-mermaid-\_r_228\_ .edgeLabel{background-color:rgb(0, 0, 0);text-align:center;}#chatgpt-mermaid-\_r_228\_ .edgeLabel p{background-color:rgb(0, 0, 0);}#chatgpt-mermaid-\_r_228\_ .edgeLabel rect{opacity:0.5;background-color:rgb(0, 0, 0);fill:rgb(0, 0, 0);}#chatgpt-mermaid-\_r_228\_ .labelBkg{background-color:rgba(0, 0, 0, 0.5);}#chatgpt-mermaid-\_r_228\_ .cluster rect{fill:rgb(48, 48, 48);stroke:rgba(255, 255, 255, 0.15);stroke-width:1px;}#chatgpt-mermaid-\_r_228\_ .cluster text{fill:rgb(237, 237, 237);}#chatgpt-mermaid-\_r_228\_ .cluster span{color:rgb(237, 237, 237);}#chatgpt-mermaid-\_r_228\_ div.mermaidTooltip{position:absolute;text-align:center;max-width:200px;padding:2px;font-family:-apple-system-body,ui-sans-serif,-apple-system,system-ui,Segoe UI,Helvetica,Apple Color Emoji,Arial,sans-serif,Segoe UI Emoji,Segoe UI Symbol;font-size:12px;background:rgb(48, 48, 48);border:1px solid rgba(255, 255, 255, 0.15);border-radius:2px;pointer-events:none;z-index:100;}#chatgpt-mermaid-\_r_228\_ .flowchartTitleText{text-anchor:middle;font-size:18px;fill:rgb(237, 237, 237);}#chatgpt-mermaid-\_r_228\_ rect.text{fill:none;stroke-width:0;}#chatgpt-mermaid-\_r_228\_ .icon-shape,#chatgpt-mermaid-\_r_228\_ .image-shape{background-color:rgb(0, 0, 0);text-align:center;}#chatgpt-mermaid-\_r_228\_ .icon-shape p,#chatgpt-mermaid-\_r_228\_ .image-shape p{background-color:rgb(0, 0, 0);padding:2px;}#chatgpt-mermaid-\_r_228\_ .icon-shape .label rect,#chatgpt-mermaid-\_r_228\_ .image-shape .label rect{opacity:0.5;background-color:rgb(0, 0, 0);fill:rgb(0, 0, 0);}#chatgpt-mermaid-\_r_228\_ .label-icon{display:inline-block;height:1em;overflow:visible;vertical-align:-0.125em;}#chatgpt-mermaid-\_r_228\_ .node .label-icon path{fill:currentColor;stroke:revert;stroke-width:revert;}#chatgpt-mermaid-\_r_228\_ .node .neo-node{stroke:rgb(172, 79, 35);}#chatgpt-mermaid-\_r_228\_ [data-look="neo"].node rect,#chatgpt-mermaid-\_r_228\_ [data-look="neo"].cluster rect,#chatgpt-mermaid-\_r_228\_ [data-look="neo"].node polygon{stroke:url(#chatgpt-mermaid-\_r_228\_-gradient);filter:drop-shadow( 1px 2px 2px rgba(185,185,185,1));}#chatgpt-mermaid-\_r_228\_ [data-look="neo"].swimlane.cluster rect{filter:none;}#chatgpt-mermaid-\_r_228\_ [data-look="neo"].node path{stroke:url(#chatgpt-mermaid-\_r_228\_-gradient);stroke-width:1px;}#chatgpt-mermaid-\_r_228\_ [data-look="neo"].node .outer-path{filter:drop-shadow( 1px 2px 2px rgba(185,185,185,1));}#chatgpt-mermaid-\_r_228\_ [data-look="neo"].node .neo-line path{stroke:rgb(172, 79, 35);filter:none;}#chatgpt-mermaid-\_r_228\_ [data-look="neo"].node circle{stroke:url(#chatgpt-mermaid-\_r_228\_-gradient);filter:drop-shadow( 1px 2px 2px rgba(185,185,185,1));}#chatgpt-mermaid-\_r_228\_ [data-look="neo"].node circle .state-start{fill:#000000;}#chatgpt-mermaid-\_r_228\_ [data-look="neo"].icon-shape .icon{fill:url(#chatgpt-mermaid-\_r_228\_-gradient);filter:drop-shadow( 1px 2px 2px rgba(185,185,185,1));}#chatgpt-mermaid-\_r_228\_ [data-look="neo"].icon-shape .icon-neo path{stroke:url(#chatgpt-mermaid-\_r_228\_-gradient);filter:drop-shadow( 1px 2px 2px rgba(185,185,185,1));}#chatgpt-mermaid-\_r_228\_ .node text{font-size:14px;font-weight:600;letter-spacing:normal;fill:rgb(255, 183, 144);}#chatgpt-mermaid-\_r_228\_ .edgeLabels text{font-size:13px;font-weight:600;letter-spacing:-0.08px;fill:rgb(255, 183, 144);}#chatgpt-mermaid-\_r_228\_ .node tspan[font-weight="normal"],#chatgpt-mermaid-\_r_228\_ .edgeLabels tspan[font-weight="normal"]{font-weight:600;}#chatgpt-mermaid-\_r_228\_ .edgeLabel .label rect{opacity:1;rx:13px;ry:13px;fill:rgb(40, 17, 5);stroke:rgb(92, 56, 31);stroke-width:1px;}#chatgpt-mermaid-\_r_228\_ .node rect,#chatgpt-mermaid-\_r_228\_ .node circle,#chatgpt-mermaid-\_r_228\_ .node ellipse,#chatgpt-mermaid-\_r_228\_ .node polygon,#chatgpt-mermaid-\_r_228\_ .node path{fill:rgb(74, 34, 6);stroke:rgba(255, 255, 255, 0.1);stroke-width:1px;}#chatgpt-mermaid-\_r_228\_ .node rect{rx:16px;ry:16px;}#chatgpt-mermaid-\_r_228\_ .mermaid-decision .label-container{fill:rgb(40, 17, 5);stroke:rgb(92, 56, 31);stroke-dasharray:2px,2px;}#chatgpt-mermaid-\_r_228\_ .edgePaths .flowchart-link{stroke:rgb(175, 175, 175);stroke-width:1px;stroke-linecap:round;stroke-linejoin:round;}#chatgpt-mermaid-\_r_228\_ .marker{fill:rgb(175, 175, 175);stroke:rgb(175, 175, 175);}#chatgpt-mermaid-\_r_228\_ :root{--mermaid-font-family:-apple-system-body,ui-sans-serif,-apple-system,system-ui,Segoe UI,Helvetica,Apple Color Emoji,Arial,sans-serif,Segoe UI Emoji,Segoe UI Symbol;}sunshine-updateBootstrap and trustverificationSystem discovery andinventoryTarget-state resolutionTransformation planningPreflight and preparationTransformation executorSystem validationTarget state satisfied?Repair or resumeCommit Sunshine systemidentityNormal Sunshine updatemodeNoYes

Each stage should have a separate contract.

## **Stage A — Bootstrap and trust verification**

Responsibilities:

- Verify the local bootstrap version.
- Verify repository signatures.
- Retrieve the current target index.
- Retrieve the migration engine package.
- Validate artifact hashes.
- Verify compatibility between the bootstrap and the new engine.
- Establish the privileged execution channel.

No system transformation should begin before the repository trust and artifact verification succeed.

## **Stage B — System discovery**

This stage is particularly important because the source system is not necessarily a known Sunshine release.

The engine must inspect the machine itself.

It should discover:

| Category        | Information                                                         |
| --------------- | ------------------------------------------------------------------- |
| Distribution    | Arch identity, release metadata and architecture                    |
| Packages        | Installed packages, repositories, foreign packages, package reasons |
| Package manager | Pacman version, configuration, keyring and database state           |
| Kernel          | Running kernel, installed kernels, modules, DKMS packages           |
| Boot            | UEFI/BIOS, ESP, bootloader, entries, initramfs configuration        |
| Storage         | Filesystems, mounts, encryption, LVM, subvolumes                    |
| Services        | systemd units, enabled services and dependencies                    |
| Network         | NetworkManager, alternative networking services                     |
| Audio           | PipeWire, PulseAudio, other audio configurations                    |
| Desktop         | Installed sessions, display manager and desktop packages            |
| Users           | Existing users, groups, home directories and permissions            |
| Sunshine        | Existing component schemas, if already installed                    |
| Nix             | Whether Nix exists, its daemon and existing user configuration      |

The inventory must distinguish between:

- Installed.
- Configured.
- Enabled.
- Running.
- Actually functional.

For example, discovering an installed GRUB package does not prove that the machine boots through GRUB.

Likewise, discovering PipeWire packages does not prove that the audio configuration is operational.

The engine should use confidence levels for its findings.

```
[[observations]]
component = "bootloader"
detected = "grub"
confidence = "high"
evidence = [
    "installed-package",
    "efi-boot-entry",
    "grub-configuration"
]

[[observations]]
component = "audio"
detected = "pipewire"
confidence = "medium"
evidence = [
    "installed-package",
    "systemd-user-unit"
]
```

A low-confidence observation must not authorize destructive operations.

## **Stage C — Target-state resolution**

The engine downloads the current Sunshine target definition and resolves the appropriate installation profile.

Some decisions can be automatic:

- Preserve the existing desktop if it is supported.
- Preserve the existing bootloader where Sunshine supports it.
- Preserve existing user accounts.
- Preserve existing networking and audio implementations when compatible.

Other decisions may require user input:

- Which primary desktop should be used if multiple are installed?
- Should Nix be enabled?
- Should Sunshine install its recommended recovery integration?
- Should an unsupported boot arrangement be replaced?
- Which filesystem integration is appropriate?

The user should not have to answer dozens of questions merely because they started with Arch.

The engine should automatically preserve compatible existing choices and ask only when it cannot safely determine intent.

## **Stage D — Transformation planning**

This is where the migration engine calculates the operations needed to achieve the target.

For example:

```
Detected:
    Arch Linux
    Pacman
    systemd
    GRUB
    mkinitcpio
    KDE Plasma
    NetworkManager
    PipeWire

Target:
    Sunshine Core
    Current ownership registry
    Current configuration architecture
    Current recovery integration
    Current kernel management
    Current GRUB integration
    Current Plasma profile
    Current update policy

Required transformations:
    Install Sunshine Core
    Initialize system identity
    Initialize component registry
    Install configuration manager
    Initialize ownership registry
    Initialize recovery infrastructure
    Configure Sunshine repository
    Migrate kernel management
    Integrate GRUB
    Initialize Plasma profile
    Configure Sunshine Update
```

Notice that the planner does not say:

> Upgrade from Sunshine 1.0 to Sunshine 2.0, then 3.0, then 4.0.

It says:

> These are the missing or outdated capabilities. These are the operations needed to achieve the target.

This is the heart of the architecture.

# **4. The transformation planner: capabilities, dependencies and operations**

I would make this the most important subsystem of Sunshine Core.

It needs to answer three questions:

1. What does the system currently have?
2. What must the system have?
3. What is the safest sequence of operations to make them match?

The planner should not be hardcoded around a list of Sunshine releases.

## **4.1 Three layers of system knowledge**

Use three distinct data models.

**1. Observed state**

What the machine actually has, including components that Sunshine does not manage.

```
GRUB installed
Plasma installed
PipeWire installed
Sunshine Core absent
```

**2. Desired state**

What the selected Sunshine target requires.

```
GRUB integration configured
Plasma profile registered
PipeWire integration validated
Sunshine Core installed
```

**3. Transformation state**

What must happen to move between those states.

```
Install Core
Register Plasma
Configure GRUB
Validate PipeWire
```

The observed state is a factual inventory. The desired state is a versioned specification. The transformation state is a generated execution plan.

Do not combine these into one configuration file. They have different lifecycles and trust requirements.

## **4.2 Capabilities instead of package-name assumptions**

A target should declare capabilities.

For example:

```
[requirements.kernel]
capabilities = [
    "kernel-installation",
    "initramfs-generation",
    "kernel-fallback"
]

[requirements.boot]
capabilities = [
    "boot-entry-management",
    "boot-validation"
]

[requirements.desktop]
capabilities = [
    "desktop-session-discovery",
    "sunshine-profile-management"
]
```

A component can provide those capabilities:

```
id = "grub-adapter"

[provides]
capabilities = [
    "boot-entry-management",
    "boot-validation"
]

[requires]
capabilities = [
    "systemd",
    "efi-detection"
]
```

This makes the architecture extensible.

Imagine Sunshine replaces its GRUB integration with a new boot management component five years later.

The target changes its required provider. The planner detects that the current provider is obsolete and constructs a transition to the new one.

It does not need to know which Sunshine ISO originally installed GRUB integration.

## **4.3 Typed transformation operations**

Do not let migration manifests consist of arbitrary shell scripts.

Define a set of typed operations that the executor understands.

For example:

| Operation              | Function                                                |
| ---------------------- | ------------------------------------------------------- |
| `InstallPackages`      | Install packages through the designated package backend |
| `RemovePackages`       | Remove explicitly identified packages                   |
| `TransferOwnership`    | Transfer component ownership between backends           |
| `CreateConfiguration`  | Create a Sunshine-managed configuration                 |
| `MigrateConfiguration` | Transform an existing configuration                     |
| `RegisterComponent`    | Register a new Sunshine component                       |
| `EnableService`        | Enable an approved systemd service                      |
| `DisableService`       | Disable an obsolete or conflicting service              |
| `InstallKernel`        | Install a kernel provider                               |
| `GenerateInitramfs`    | Generate and validate an initramfs                      |
| `InstallBootEntry`     | Create a boot entry                                     |
| `CreateCheckpoint`     | Create a supported recovery checkpoint                  |
| `ValidateCapability`   | Verify that a capability is operational                 |

A migration may also use a versioned Rust adapter for operations that cannot be expressed through standard primitives.

For example, a new storage migration mechanism might require specialized filesystem logic. The engine should be able to load an approved, signed adapter implementing a stable interface.

The important restriction is that the adapter runs under the executor's security model. It must not be able to bypass authorization, signature verification, journaling or validation.

## **4.4 Operation manifests**

An example of a transformation introducing a new ownership registry:

```
format_version = 1

id = "ownership.initialize"
component = "ownership"

[transition]
from = 0
to = 1

[requirements]
capabilities = [
    "pacman-database-access"
]

[[operations]]
id = "install-registry"
type = "InstallPackages"

packages = ["sunshine-ownership"]

[[operations]]
id = "initialize-registry"
type = "RegisterComponent"

component_id = "ownership"
schema = 1

[[operations]]
id = "validate-registry"
type = "ValidateCapability"

capability = "package-ownership-registry"
```

The package is installed, the registry is initialized, and the resulting capability is validated.

A system that already has ownership schema 1 does not execute this transformation again.

## **4.5 Dependency graph**

Every operation should declare its prerequisites.

For example:

```
Install Sunshine Core
       |
       v
Initialize system identity
       |
       v
Initialize component registry
       |
       +--------------------+
       |                    |
       v                    v
Install configuration   Install ownership
manager                 registry
       |                    |
       v                    v
Migrate defaults        Register package owners
       |                    |
       +----------+---------+
                  |
                  v
          Configure desktop
                  |
                  v
          Validate final system
```

The planner constructs a directed acyclic graph of operations.

It should:

- Reject dependency cycles.
- Reject missing providers.
- Check conflicting operations.
- Resolve mutually exclusive implementations.
- Identify operations that can safely run in parallel.
- Enforce operations that must run sequentially.
- Recalculate the graph when a prerequisite changes the observed state.

That last point matters.

Suppose a kernel package transition reveals that the system uses a previously unknown DKMS module. The engine should be able to stop, update its inventory, and replan rather than blindly continue with an outdated plan.

# **5. Component lifecycle: introducing, evolving and replacing mechanisms**

The architecture must support components that did not exist in the original Arch installation.

I would define five component lifecycle operations.

**Introduce**

A component does not exist. Install and initialize it.

Example: introduce Sunshine Core, recovery manager or ownership registry.

**Evolve**

A component exists but its schema or capabilities are outdated.

Example: configuration schema 1 → 4.

**Replace**

Replace one implementation with another while preserving the component's contract.

Example: replace an old boot integration with a new boot management adapter.

**Reconfigure**

The component is current, but the installed configuration does not satisfy the selected target.

Example: register an already-installed Plasma session in Sunshine's desktop registry.

**Retire**

A component is no longer part of the target. Disable it, migrate its data, and remove it only when safe.

Example: retire a deprecated Sunshine service.

These operations should be generic. The migration engine should not need a new global architecture every time Sunshine introduces another subsystem.

## **5.1 Component contracts**

Every component should publish a contract:

```
format_version = 1

id = "sunshine-recovery"
name = "Sunshine Recovery Manager"

[version]
software = "2.1.0"
schema = 3

[provides]
capabilities = [
    "recovery-checkpoints",
    "migration-journal-recovery",
    "system-diagnostics"
]

[requires]
capabilities = [
    "systemd",
    "transaction-journal"
]

[ownership]
managed_paths = [
    "/etc/sunshine/recovery.toml",
    "/var/lib/sunshine/recovery"
]

[ lifecycle ]
installable = true
upgradeable = true
replaceable = true
removable = true
```

The contract tells the rest of Sunshine what the component does, what it needs and which paths it owns.

This enables a new component to be introduced without embedding its internal implementation throughout Sunshine Core.

## **5.2 Replacing a component without losing its state**

Imagine a future Sunshine release replaces its recovery mechanism entirely.

The old system has:

```
recovery schema 1
```

The new target expects:

```
recovery schema 3
```

The new component should provide a state adapter:

```
Old recovery data
       |
       v
Export to neutral recovery model
       |
       v
Validate exported data
       |
       v
Import into new recovery mechanism
       |
       v
Validate new mechanism
       |
       v
Retire old implementation
```

This is more robust than trying to translate every historical recovery implementation directly into every future implementation.

It also introduces an important architectural pattern:

**Stable interchange formats between replaceable components.**

Use them where the complexity of direct migrations would otherwise grow rapidly.

# **6. The Arch foundation transformation**

This is where Sunshine must be especially careful not to become a second package manager.

The transformation engine should preserve the existing Arch foundation and bring it to a coherent current package state.

It should not independently reconstruct all of Arch.

## **6.1 Pacman remains the foundation authority**

For the initial transformation, the sequence should be:

1. Inspect pacman and its configuration.
2. Check the installed package database.
3. Identify foreign and locally built packages.
4. Verify repository configuration and signing trust.
5. Configure the Sunshine repository.
6. Resolve package conflicts.
7. Prepare a full system upgrade.
8. Install required Sunshine packages.
9. Validate the resulting package state.

A critical rule: do not synchronize repository databases and then install only selected packages from the new databases. Arch does not support partial upgrades because package dependencies and shared libraries are expected to move together. Use a coherent full-upgrade transaction.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://wiki.archlinux.org\&sz=32)

ArchWiki+1



The actual pacman operation should be coordinated carefully with Sunshine's own package installation. Depending on repository and package-manager constraints, Sunshine may need an initial full Arch upgrade followed by a Sunshine package installation, or a coordinated full transaction using both repository sets.

The planner must ensure that no incompatible intermediate package state is exposed.

## **6.2 Package ownership must be established, not assumed**

Pure Arch does not have Sunshine's ownership registry.

Therefore, the first ownership migration must inspect the existing pacman database and classify packages.

For example:

```
[[packages]]
name = "linux"
detected_owner = "pacman"
classification = "arch-foundation"

[[packages]]
name = "plasma-desktop"
detected_owner = "pacman"
classification = "desktop"

[[packages]]
name = "sunshine-update"
detected_owner = "pacman"
classification = "sunshine-bootstrap"
```

Foreign packages should be classified separately:

```
Official Arch packages
Foreign packages
AUR-built packages
Manually installed packages
Unknown packages
```

Do not automatically remove every foreign package.

AUR packages are build recipes rather than official binary repository packages, and may require rebuilding or intervention after dependency changes.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://wiki.archlinux.org\&sz=32)

ArchWiki+1



The initial registry should record uncertainty rather than pretending every installed file and package has a known owner.

## **6.3 Repository transition**

The transformation should configure the official Sunshine repository without destroying the user's existing pacman configuration.

Prefer managed configuration fragments or clearly delimited Sunshine-owned sections.

For example:

```
/etc/pacman.conf
/etc/pacman.d/
/etc/pacman.d/sunshine-mirrorlist
```

The exact arrangement should respect pacman's supported configuration format.

Sunshine must preserve:

- User repositories.
- User mirror choices where possible.
- Package signature requirements.
- Existing package ignore settings, while warning about conflicts with full upgrades.
- Custom pacman options.

If a setting prevents safe transformation, report the blocker and explain what needs to change.

Do not silently delete it.

# **7. Kernel and boot transformation from pure Arch**

A pure Arch installation may already have a working kernel and bootloader, but Sunshine must not assume that their configuration satisfies its target.

This is a separate transformation domain.

For example, if Sunshine's target uses its own kernel fallback management, the engine must introduce that mechanism.

The process:

1. Discover installed kernel packages.
2. Discover the currently running kernel.
3. Discover kernel module and DKMS dependencies.
4. Identify the actual bootloader and boot mode.
5. Identify the EFI System Partition or other boot storage.
6. Inspect initramfs generation.
7. Install the Sunshine kernel management component.
8. Register existing kernel providers.
9. Introduce fallback handling.
10. Validate boot entries and recovery availability.

The key is that introducing Sunshine kernel management does not necessarily mean replacing the kernel package.

The existing Arch kernel may remain perfectly suitable.

Only the management mechanism changes.

If the target does require a different kernel provider, install it alongside the existing kernel, generate and validate its initramfs, add a separate boot entry, and preserve the previous working entry until the new kernel has successfully booted.

This distinction is essential:

- Kernel package migration: change the actual kernel.
- Kernel management migration: change how Sunshine manages kernels.
- Boot integration migration: change how the machine boots them.

They are separate components and must have separate schemas.

# **8. Configuration and user ownership**

A pure Arch system has no Sunshine configuration ownership model.

The initial transformation must introduce one without taking ownership of the entire machine.

I would classify configuration into four categories:

| Category          | Migration behaviour                            |
| ----------------- | ---------------------------------------------- |
| Sunshine-owned    | May be migrated automatically                  |
| System-owned      | Modified through explicit, documented adapters |
| User-owned        | Preserved                                      |
| Unknown ownership | Inspected and handled conservatively           |

For example, Sunshine can introduce:

```
/etc/sunshine/
├── system.toml
├── repositories.toml
├── desktops.toml
└── policies/

/var/lib/sunshine/
├── system-state.toml
├── ownership/
├── migration/
├── transactions/
└── recovery/
```

But it must not simply overwrite:

```
/etc/pacman.conf
/etc/mkinitcpio.conf
/etc/default/grub
/etc/systemd/system/
~/.config/
```

Instead, use targeted transformations.

A particularly useful technique is **three-way configuration migration**:

```
Old known default
        |
        +----------+
        |          |
        v          v
User's current   New default
configuration
        |          |
        +----+-----+
             |
             v
      Merge and validate
             |
             v
      Preserve user changes
```

If a value was never changed by the user, it can be updated automatically. If the user changed it, preserve that change unless it conflicts with a mandatory new constraint.

When a conflict cannot be resolved safely, ask the user.

This should be a core mechanism of Sunshine configuration management, not a special-case migration feature.

# **9. The transformation executor and transaction model**

A target-state planner can produce a perfect plan and still destroy a system if execution is poorly designed.

I would separate planning from execution completely.

The planner produces a signed, reviewable execution plan. The executor applies it.

## **9.1 Execution plan**

For example:

```
format_version = 1

plan_id = "arch-to-sunshine-2026-001"

[source]
distribution = "arch"
sunshine_installed = false

[target]
distribution = "sunshine-os"
release = "5.0"

[[steps]]
id = "bootstrap-core"
operation = "install_packages"
packages = ["sunshine-core"]

[[steps]]
id = "initialize-state"
operation = "initialize_component"
component = "system-state"
schema = 1
requires = ["bootstrap-core"]

[[steps]]
id = "ownership-registry"
operation = "initialize_component"
component = "ownership"
schema = 2
requires = ["initialize-state"]

[[steps]]
id = "configuration-manager"
operation = "initialize_component"
component = "configuration"
schema = 4
requires = ["initialize-state"]

[[steps]]
id = "desktop-integration"
operation = "configure_desktop"
profile = "plasma"
requires = ["configuration-manager"]

[[steps]]
id = "final-validation"
operation = "validate_target"
requires = [
    "ownership-registry",
    "configuration-manager",
    "desktop-integration"
]
```

This is illustrative. A real plan should include artifact digests, package transaction IDs, capability requirements, recovery contracts and exact operation parameters.

The user can inspect the plan before applying it.

The plan should also identify:

- Packages to install.
- Packages to remove.
- Services to enable or disable.
- Configuration files to modify.
- Boot artifacts to generate.
- Components to introduce.
- User decisions required.
- Operations that require reboot.
- Operations that cannot be automatically reversed.

## **9.2 Transaction boundaries**

I would divide execution into several transaction groups.

```
Transaction 1: Bootstrap
    Install Sunshine Core
    Initialize state registry
    Initialize migration engine

Transaction 2: Foundation
    Configure Sunshine repository
    Perform full package upgrade
    Install foundation integrations

Transaction 3: Core architecture
    Initialize configuration management
    Initialize ownership registry
    Initialize recovery infrastructure

Transaction 4: Kernel and boot
    Install kernel management
    Integrate bootloader
    Validate boot artifacts

Transaction 5: Desktop
    Register installed desktop
    Apply Sunshine desktop profile
    Validate session integration

Transaction 6: Finalization
    Validate all components
    Commit target state
    Enable Sunshine Update
```

The groups are examples, not a universal fixed order. The planner may move operations when dependencies require it.

A transaction group should have:

- Preflight.
- Required artifacts.
- Recovery checkpoint.
- Execution journal.
- Validation.
- Commit condition.

Do not pretend that all six groups can be rolled back atomically.

Pacman package transactions, filesystem snapshots, service changes and bootloader updates have different recovery properties.

## **9.3 Persistent execution journal**

Use:

```
/var/lib/sunshine/
├── state/
│   ├── system.toml
│   ├── components.toml
│   └── capabilities.toml
│
├── migration/
│   ├── active/
│   ├── completed/
│   ├── failed/
│   └── journal/
│
├── transactions/
│   ├── active/
│   ├── completed/
│   └── failed/
│
└── recovery/
    ├── checkpoints/
    └── reports/
```

A journal entry should record:

```
id = "transaction-2026-001"
operation = "initialize-ownership"
status = "completed"

started_at = "2026-11-20T18:00:00Z"
completed_at = "2026-11-20T18:00:03Z"

component = "ownership"
source_schema = 0
target_schema = 1

[validation]
passed = true

[recovery]
strategy = "not-required"
```

For long-running operations, record each individual step and its output.

If power fails after installing packages but before configuring services, the next execution must discover that packages are already installed and continue from the correct state.

Do not simply rerun the entire plan.

## **9.4 Reconciliation after interruption**

The engine should never blindly trust its last journal entry as proof of the current system state.

After interruption:

1. Read the journal.
2. Inspect the actual system.
3. Compare the actual state against the last committed state.
4. Identify partially applied operations.
5. Determine whether they are safe to resume.
6. Resume, repair or initiate recovery.

This is particularly important for package transactions and boot migrations.

The journal records what the engine intended and observed. The machine itself remains the source of truth for what actually exists.

# **10. System state and component registry**

The system needs a persistent record of what Sunshine has established.

I would use three related files.

### `system.toml`

Identifies the system and its current Sunshine target.

```
[identity]
distribution = "sunshine-os"
installation_id = "generated-uuid"
architecture = "x86_64"

[release]
installed = "5.0"
target = "5.0"

[foundation]
distribution = "arch"
package_manager = "pacman"
```

### `components.toml`

Tracks independently versioned components.

```
[components.core]
schema = 3
software_version = "5.2.0"
status = "active"

[components.configuration]
schema = 4
software_version = "3.8.1"
status = "active"

[components.kernel_management]
schema = 2
software_version = "2.1.0"
status = "active"

[components.boot_integration]
schema = 2
software_version = "2.0.0"
status = "active"

[components.ownership]
schema = 2
software_version = "2.4.0"
status = "active"

[components.nix_integration]
schema = 0
status = "not-installed"
```

### `capabilities.toml`

Tracks capabilities actually provided by installed components.

```
[capabilities]
package_ownership_registry = true
kernel_fallback_management = true
boot_entry_validation = true
configuration_ownership = true
migration_recovery = true
nix_integration = false
```

The distinction is important:

- `components.toml` describes component identity and schema.
- `capabilities.toml` describes functionality available on the machine.
- `system.toml` identifies the distribution and target.

These should be generated or updated by Sunshine Core, not manually edited by users.

# **11. The repository architecture**

I would make the Sunshine repository publish a continuously evolving target and its required transformation components.

The repository should not be structured around historical Sunshine releases as the primary migration mechanism.

Suggested layout:

```
sunshine-repository/
│
├── bootstrap/
│   ├── compatibility.toml
│   └── protocol.toml
│
├── targets/
│   ├── current.toml
│   └── profiles/
│       ├── plasma.toml
│       ├── hyprland.toml
│       ├── xfce.toml
│       ├── gnome.toml
│       └── sway.toml
│
├── components/
│   ├── core/
│   ├── configuration/
│   ├── ownership/
│   ├── kernel/
│   ├── boot/
│   ├── recovery/
│   ├── desktop/
│   └── nix/
│
├── transformations/
│   ├── introduce/
│   ├── evolve/
│   ├── replace/
│   ├── reconfigure/
│   └── retire/
│
├── compatibility/
│   ├── arch/
│   ├── pacman/
│   ├── kernel/
│   ├── boot/
│   └── hardware/
│
├── packages/
│   ├── x86_64/
│   └── aarch64/
│
└── signatures/
```

This is a logical repository structure. The actual binary package repository can remain a conventional pacman repository.

## **11.1 Target manifest**

The target manifest references components and their requirements.

```
format_version = 1

[target]
id = "sunshine-current"
release = "5.0"

[components.core]
schema = 3
required = true

[components.configuration]
schema = 4
required = true

[components.ownership]
schema = 2
required = true

[components.kernel]
schema = 2
required = true

[components.boot]
schema = 2
required = true

[components.recovery]
schema = 3
required = true

[components.desktop]
schema = 4
required = true

[components.nix]
schema = 2
required = false
```

The target should also reference package sets and provider alternatives.

For example, the desktop target may accept Plasma, Hyprland, XFCE, GNOME or Sway, but it should not require all five.

Likewise, the boot target should express supported boot capabilities rather than mandate one bootloader if Sunshine intends to support multiple implementations.

## **11.2 Historical migration definitions**

Although this is not a release-by-release migration system, you still need historical transformations.

Suppose configuration schema evolves:

```
0 -> 1 -> 2 -> 3 -> 4
```

Those transformations must remain available for supported source states.

However, if a machine is already at schema 3, it only needs `3 → 4`.

If a machine is at schema 0, the planner needs the complete valid path.

If a machine has no Sunshine configuration component, it starts at schema 0.

This means the repository stores the evolutionary history of individual components, not entire historical OS images as the primary migration mechanism.

## **11.3 Repository generations**

The repository index itself also needs versioning and integrity protection.

For example:

```
format_version = 1
repository_generation = 500

[target]
release = "5.0"

[bootstrap]
minimum_protocol = 1

[compatibility]
minimum_core = "1.0.0"
```

A repository generation identifies a published repository state. It must not be confused with the Sunshine release or any component schema.

The migration engine should reject rollback to an older repository generation unless an explicitly authorized recovery procedure allows it.

# **12. How the five-year migration works in practice**

Let's make the scenario concrete.

## **Initial installation**

A user installs Arch Linux.

They have:

```
Arch Linux
├── pacman
├── systemd
├── linux
├── mkinitcpio
├── GRUB
├── NetworkManager
├── PipeWire
└── KDE Plasma
```

They install:

```
sudo pacman -S sunshine-update
```

No other Sunshine packages are installed.

## **Five years pass**

During that time, Sunshine develops:

- Rust-based Sunshine Core.
- A package ownership registry.
- A declarative configuration manager.
- A new kernel management mechanism.
- A new recovery system.
- New desktop profile infrastructure.
- Nix integration.
- A new update validation mechanism.

The user has never installed any of those components.

## **User runs the updater**

```
sudo sunshine-update
```

The updater:

1. Verifies the bootstrap and repository trust.
2. Downloads the current migration engine.
3. Discovers the actual Arch installation.
4. Determines the existing package, kernel, bootloader and desktop state.
5. Downloads the current target specification.
6. Calculates the missing components and required transformations.
7. Checks Arch compatibility and repository prerequisites.
8. Produces a migration plan.
9. Requests confirmation for consequential changes.
10. Executes the transformations.
11. Validates the resulting system.
12. Commits Sunshine system identity and component schemas.

**Result**

Original source

**Pure Arch**

Transformation

**Target-state construction**

Final result

Current Sunshine OS

The user does not need to install historical Sunshine releases or reconstruct the system manually.

The same engine can also process an old Sunshine installation. It simply finds that some components are already present and skips their introduction operations.

That is the real benefit of the model.

# **13. Handling completely new mechanisms five years later**

This is the requirement that makes the architecture interesting.

Imagine Sunshine's current recovery system is based on Timeshift and Snapper integration.

Five years later, you introduce a completely new mechanism called Sunshine Recovery Engine, which provides:

- Unified recovery checkpoints.
- Bootable recovery environments.
- Transaction-aware recovery.
- Kernel fallback management.
- Configuration restoration.
- Recovery diagnostics.

The original Arch installation has none of these.

The transformation engine must be capable of introducing all of it.

I would solve this through **component bundles**.

## **13.1 Component bundles**

A component bundle contains everything necessary to introduce a new mechanism:

```
sunshine-recovery/
│
├── component.toml
│
├── packages/
│   ├── sunshine-recovery-core
│   └── sunshine-recovery-tools
│
├── migrations/
│   ├── initialize.toml
│   └── migrate-timeshift.toml
│
├── adapters/
│   ├── btrfs.rs
│   └── ext4.rs
│
├── services/
│   └── sunshine-recovery.service
│
├── configuration/
│   └── recovery.toml
│
└── validators/
    └── recovery-validation.rs
```

The component bundle describes:

- Which packages to install.
- Which existing components it can replace.
- Which capabilities it provides.
- Which capabilities it requires.
- Which configurations it owns.
- Which services it introduces.
- Which existing data it can migrate.
- How it validates its own installation.
- How it can be removed or recovered.

The migration engine does not need to understand the internal implementation of Sunshine Recovery Engine.

It needs to understand the component contract and execute its approved transformations.

This is how you can introduce entirely new system mechanisms without repeatedly redesigning Sunshine Core.

## **13.2 Avoid making the migration engine a plugin execution free-for-all**

There is a security boundary here.

A component should not be able to publish arbitrary code and declare:

> Run this as root; trust me.

Instead:

- Component metadata is signed.
- Packages are signature-verified.
- Migration modules have approved interfaces.
- Privileged operations go through Sunshine Core.
- Every operation is journaled.
- Component permissions are declared.
- The executor validates operation parameters.
- Components cannot modify the trust root or bypass migration validation.

For extensibility, I would use a combination of:

1. Built-in typed operations for common transformations.
2. Versioned Rust adapters for complex privileged operations.
3. Python for non-privileged workflows and configuration transformations.
4. Package-manager transactions for package installation and removal.

This preserves the Rust/Python division you established for Sunshine OS without forcing every operation into one implementation language.

# **14. The critical limitation: pure Arch is not one uniform starting state**

There is one thing I would not promise: that every installation calling itself Arch Linux can be transformed automatically.

A clean Arch installation with standard systemd, pacman, a supported bootloader and a supported filesystem is a reasonable source state.

But consider:

- An installation using a custom kernel.
- An installation without systemd.
- A manually constructed bootloader configuration.
- An unsupported filesystem.
- A broken pacman database.
- An unsupported encryption arrangement.
- An installation with conflicting foreign packages.
- A machine with no usable bootloader entry.
- A machine with a modified package-signature trust configuration.

These are not equivalent starting points.

Therefore, define **source compatibility profiles**.

Example:

```
[[source_profiles]]
id = "arch-standard"
distribution = "arch"
architecture = "x86_64"
init_system = "systemd"
package_manager = "pacman"
support_level = "official"

[[source_profiles]]
id = "arch-customized"
distribution = "arch"
architecture = "x86_64"
init_system = "systemd"
package_manager = "pacman"
support_level = "conditional"
```

The standard profile should be the primary conversion target.

The customized profile can be accepted when its detected configuration is compatible.

Unsupported configurations should fail preflight with a precise explanation rather than being forcibly converted.

**Your five-year guarantee should apply to the supported source profiles and supported Sunshine states, not arbitrary Linux installations.**

## **14.1 Another important limitation: the Arch package gap**

Your five-year requirement has a difficult implication.

If a user genuinely does not update Arch for five years, Sunshine's updater cannot assume that a normal current `pacman -Syu` will work without intervention.

Arch expects regular full upgrades, and upstream changes can require manual action.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://wiki.archlinux.org\&sz=32)

ArchWiki+1



The transformation engine therefore needs an Arch compatibility subsystem.

Its responsibility is to:

- Detect outdated package-manager prerequisites.
- Detect keyring and repository problems.
- Detect known upstream manual-intervention requirements.
- Identify obsolete packages and replacements.
- Resolve known package conflicts.
- Install necessary bootstrap packages.
- Coordinate full package transitions.
- Report anything that still requires user intervention.

It should not attempt to reproduce Arch's entire package manager.

If an old pacman cannot install the required bootstrap package, provide a compatible bridge package or a documented recovery-environment path.

The five-year guarantee is only credible if you test this actual scenario.

# **15. How to guarantee that the same architecture works for five years**

I would introduce a permanent test category called **Arch-to-Sunshine Transformation Tests**.

Every Sunshine release should test at least the following:

| Source state                | Expected result                |
| --------------------------- | ------------------------------ |
| Clean Arch, no desktop      | Sunshine base installed        |
| Arch + Plasma               | Sunshine with Plasma profile   |
| Arch + Hyprland             | Sunshine with Hyprland profile |
| Arch + XFCE                 | Sunshine with XFCE profile     |
| Arch + GNOME                | Sunshine with GNOME profile    |
| Arch + Sway                 | Sunshine with Sway profile     |
| Arch + custom packages      | Compatible packages preserved  |
| Arch + custom configuration | User changes preserved         |
| Old Sunshine installation   | Current Sunshine architecture  |
| Five-year-old Arch fixture  | Current Sunshine architecture  |

Additional tests:

- Old pacman and keyring.
- Kernel replacement.
- Bootloader transition.
- mkinitcpio configuration migration.
- Btrfs integration.
- ext4 integration.
- Existing Nix installation.
- Missing Sunshine components.
- Partially installed Sunshine components.
- Interrupted transformations.
- Failed package transaction.
- Insufficient disk space.
- Failed kernel boot.
- Failed recovery checkpoint.
- Invalid repository signature.
- Revoked repository key.
- Repeated execution of `sunshine-update`.

That last test is especially important.

Running the updater twice without changing the target should produce no unnecessary modifications.

This is a fundamental property of a desired-state reconciliation system.

# **16. Recommended implementation structure**

I would now organize Sunshine Core around this architecture:

```
sunshine-core/
│
├── bootstrap/
│   ├── trust.rs
│   ├── repository.rs
│   └── handover.rs
│
├── discovery/
│   ├── system.rs
│   ├── packages.rs
│   ├── kernel.rs
│   ├── boot.rs
│   ├── storage.rs
│   ├── services.rs
│   ├── desktop.rs
│   └── capabilities.rs
│
├── target/
│   ├── manifest.rs
│   ├── components.rs
│   ├── profiles.rs
│   └── resolver.rs
│
├── planner/
│   ├── planner.rs
│   ├── dependency_graph.rs
│   ├── conflicts.rs
│   ├── operations.rs
│   └── plan.rs
│
├── transformation/
│   ├── executor.rs
│   ├── primitives.rs
│   ├── adapters.rs
│   ├── packages.rs
│   ├── configuration.rs
│   └── services.rs
│
├── migration/
│   ├── registry.rs
│   ├── schemas.rs
│   ├── component_state.rs
│   └── compatibility.rs
│
├── transaction/
│   ├── coordinator.rs
│   ├── journal.rs
│   ├── checkpoint.rs
│   └── recovery.rs
│
├── validation/
│   ├── component.rs
│   ├── capability.rs
│   ├── boot.rs
│   └── system.rs
│
└── backends/
    ├── pacman.rs
    ├── nix.rs
    ├── flatpak.rs
    ├── systemd.rs
    ├── initramfs.rs
    ├── bootloader.rs
    └── filesystem.rs
```

And the system's persistent data:

```
/etc/sunshine/
├── system.toml
├── repositories.toml
├── policies.toml
└── profiles/

/var/lib/sunshine/
├── state/
├── components/
├── capabilities/
├── ownership/
├── migration/
├── transactions/
└── recovery/

/var/cache/sunshine/
├── repository/
├── packages/
├── components/
└── transformations/

/usr/lib/sunshine/
├── core/
├── adapters/
├── validators/
└── bootstrap/
```

The updater CLI remains simple:

```
sunshine-update
sunshine-update --check
sunshine-update --plan
sunshine-update --apply
sunshine-update --verify
sunshine-update --repair
sunshine-update --history
```

On a pure Arch installation, `sunshine-update` detects that Sunshine is not initialized and enters transformation mode.

On an existing Sunshine installation, it enters normal update and reconciliation mode.

Same executable. Same planner. Same component registry. Same transaction engine.

# **17. Implementation priorities**

I would build this in the following order:

Priority 1 — Foundation

**Build the transformation engine**

- System discovery.
- Component registry.
- Capability registry.
- Target manifest.
- Dependency graph.
- Typed operations.
- Persistent journal.
- Preflight and validation.

Priority 2 — Arch conversion

**Make pure Arch a supported source**

- Pacman integration.
- Repository and trust configuration.
- Package ownership discovery.
- Full package upgrade coordination.
- systemd integration.
- Kernel and boot discovery.
- Initial Sunshine component installation.

Priority 3 — Sunshine architecture

**Introduce the actual OS mechanisms**

- Configuration manager.
- Ownership registry.
- Kernel management.
- Recovery infrastructure.
- Desktop registry.
- Sunshine services.
- Update validation.

Priority 4 — Evolution

**Make future component replacement possible**

- Component bundles.
- Versioned adapters.
- Replacement contracts.
- Historical schema migrations.
- Capability negotiation.
- Automatic replanning.

Priority 5 — Long-term guarantees

**Prove the five-year requirement**

- Historical Arch fixtures.
- Historical Sunshine fixtures.
- Five-year package-manager compatibility tests.
- Kernel and boot recovery tests.
- Interrupted transformation tests.
- Repeated-run idempotency tests.

Do not start by building every Sunshine component. Start by building the engine capable of discovering, installing, configuring and validating components. Then each new Sunshine mechanism becomes an extension of the same architecture.

# **18. Final architectural decision**

I would formally define the Sunshine migration system as follows:

> **Sunshine Evolution Engine**
>
> A repository-driven, target-state transformation and reconciliation system responsible for evolving supported Arch Linux installations and existing Sunshine OS installations into the currently published Sunshine OS architecture.
>
> The engine discovers the installed system, resolves the current target, calculates the required component transformations, executes them through validated operations and commits the resulting system state.
>
> It supports the introduction, evolution, replacement, reconfiguration and retirement of components independently of Sunshine release history.
>
> It preserves the Arch Linux foundation and delegates standard package management to pacman, while managing Sunshine-specific architecture, integration, configuration, services and system policies.
>
> Every supported source state must have a tested transformation path to the current supported target.

The most important engineering decision is this:

**Do not make Sunshine migrations depend on knowing which Sunshine version a machine came from. Make them depend on knowing what the machine currently is.**

That gives you the ability to introduce completely new mechanisms years after installation, transform a nearly untouched Arch installation into a fully integrated Sunshine OS, and avoid accumulating redundant release-by-release migration scripts.

It also gives Sunshine a particularly useful property: the ISO and the updater become two different ways of reaching the same target.

- The ISO starts with many components already installed.
- The updater starts with whatever compatible components the user already has.
- Both use the same target specification, component contracts, transformation engine and validation rules.

**The ISO is a preconstructed Sunshine state.&#x20;**`sunshine-update`**&#x20;is the mechanism that constructs and maintains that state.**
