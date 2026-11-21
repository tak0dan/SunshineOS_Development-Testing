# Findings — SteamOS repair tool, Wave 1

- `reports/CROSS_DISTRO_RESEARCH_2026-11-21.md:283-310` and `reports/cross-distro-stability.md:19,106-110,147` catalogue SteamOS read-only root, developer mode, RAUC/Casync A/B recovery and evidence caveats.
- ValveSoftware/SteamOS issue #1654 reports readonly status disabled while devmode marker creation fails and pacman remains unable to write; `/usr/lib/steamos/steamos-devmode` is the reported failing marker path.
- `/usr/lib/rauc/bootloader-custom-backend.sh` appears in local research as the custom RAUC bootloader backend path; no SteamOS source tree or ISO files were available here to inspect these paths directly.
- Fresh status observations need consistency checks; status output alone cannot prove root mount state or devmode completion.
