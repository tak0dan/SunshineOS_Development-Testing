# Findings — CachyOS repair Wave 1

- Exact upstream paths and observed behaviors are catalogued in `autonomy/codex/cachyos-repair-wave1.md`.
- `sdboot-manage` suppresses initramfs generator failures in the UKI and regular-entry flows; the regular-entry path has explicit artifact validation afterward, while nonempty output alone remains weaker than structural or boot validation.
- SunshineOS now has a read-only, root-confined expected boot artifact assessment in `evolution-engine/src/evolution/tools/boot_artifact_repair.py`.
