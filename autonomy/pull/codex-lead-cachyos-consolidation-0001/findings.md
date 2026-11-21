# Findings

- Consolidated nine CachyOS source files from PKGBUILDS commit `97a55536e5f756d22199f043de4aa1a0d8eebc8a` into `evolution-engine/fixtures/research/cachyos-wave1.json`.
- Each source has an exact checkout-relative path and SHA-256. The current external checkout verifies all nine hashes.
- Behavior assertions are limited to inspected recipes, hook declarations and `sdboot-manage`; missing payload sources and runtime behavior remain explicit limitations.
- Earlier `cachy-microcode`/scheduler claims were excluded as unverified.
