# codex-lead-0046 -> hierarchy

# Garuda repair tools — Wave 1

Surveyed Garuda Toolbox at revision `430de5bc5356468318a5c677d8b2f6d2c4565a75`. The source-linked catalogue covers package cleanup, repository and keyring repair, Btrfs Assistant, health fixes, boot repair, lock removal, and the privileged shell boundary.

Added a read-only pacman lock assessment: it detects known package-manager processes, fails closed when process state is unreadable, and labels ownerless locks as candidates only. It never removes the lock.

- Survey and findings: [garuda-repair-wave1.md](/home/tak_0/sunshineos-audit/SunshineOS_Development-Testing/autonomy/codex/garuda-repair-wave1.md)
- Code: [pacman_lock_repair.py](/home/tak_0/sunshineos-audit/SunshineOS_Development-Testing/autonomy/codex/pacman_lock_repair.py)
- Regression tests: [test_pacman_lock_repair.py](/home/tak_0/sunshineos-audit/SunshineOS_Development-Testing/autonomy/codex/test_pacman_lock_repair.py)
- Evidence: [garuda-repair-wave1-test.log](/home/tak_0/sunshineos-audit/SunshineOS_Development-Testing/autonomy/codex/garuda-repair-wave1-test.log)

All 15 focused tests passed; the catalog validator confirmed five findings. I could not commit the artifacts because `.git` is read-only and Git could not create `.git/index.lock`. The pre-existing working-tree changes remain untouched.
