# Solutions

Fixed a fail-closed gap: `bad` unit-file states now block inventory assessment, so checked service planning cannot emit commands for a broken unit. Regression **T-ARCH2026-SYSTEMD-017** covers the block. The full inventory suite passed: **17 tests**.
