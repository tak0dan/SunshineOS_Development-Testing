# Findings

- Pinned Omarchy CI snapshot: `basecamp/omarchy` commit `e4635a4eea887d5c8dbd70427386f570c37a2a61`.
- `.github/workflows/test.yml` pins checkout actions and checks the downloaded VM disk hash, but runs a mutable Arch `:latest` Docker image and does not independently hash the downloaded kernel/initrd/cmdline.
- `i18n-sync.yml` separates credential-free validation from trusted publication and hash-checks a downloaded executable.
- Full path/hash catalogue: `autonomy/codex/omarchy-ci-hardening-wave1.md`.
