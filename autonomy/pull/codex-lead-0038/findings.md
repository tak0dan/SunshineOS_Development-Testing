# Findings

- `eos-pacdiff`, which wraps `pacdiff` to review configuration candidates. Its [source](https://github.com/endeavouros-team/eos-bash-shared/blob/main/eos-pacdiff#L629) includes a warning about sensitive account files; it also supports backups and invokes `pacdiff -s` ([source](https://github.com/endeavouros-team/eos-bash-shared/blob/main/eos-pacdiff#L699)).
- `eos-update`, a pacman updater with optional yay support.
- `paccache-service-manager`, which manages the package-cache service.
- `T-EOS-REPAIR-001`: classifies candidates without modifying configuration.
- `T-EOS-REPAIR-002`: treats an absent configuration root as incomplete.
- `T-EOS-REPAIR-003`: does not follow symlinks.
