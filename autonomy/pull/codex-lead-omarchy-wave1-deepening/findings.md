# Findings

- Omarchy's pinned per-user migration marker lives under `$HOME/.local/state/omarchy/migrations` (`bin/omarchy-migrate`).
- Its snapshot manual explicitly says root restore leaves `/home` untouched, so markers can outlive their root filesystem effects (`manual/47-system-snapshots.md`).
- All six surveyed source files match the pinned catalogue hashes at commit `e4635a4eea887d5c8dbd70427386f570c37a2a61`.
- This is an evidence-driven hazard model, not a claim that the docs prove runtime update correctness.
