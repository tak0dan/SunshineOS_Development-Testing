# Findings — Omarchy deliverable consolidation, Wave 1

- Survey anchor: `basecamp/omarchy` commit `e4635a4eea887d5c8dbd70427386f570c37a2a61`.
- Existing six-source catalogue at `evolution-engine/fixtures/research/omarchy-update-recovery-wave1.json` is hash-pinned and validated by `CAT_006`.
- Updater source `bin/omarchy-update` runs system packages, migrations, and AUR updates before boot verification; a failed boot check blocks the reboot prompt and returns failure.
- Existing marker reconciliation covers root snapshot rollback. The missing consolidated code-level control was the final update completion gate.
- The bounded pacman config writer `bin/omarchy-apply-pacman` validates channel/region and stages both files before installing them; findings do not imply live runtime qualification.
