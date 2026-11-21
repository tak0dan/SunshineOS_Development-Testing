# codex-lead-0037 -> hierarchy

## EndeavourOS Wave 1

Added a fail-closed package ownership check. When any of `pacman -Q`, `pacman -Qqdt`, or `pacman -Qqm` fails, discovery withholds official-package claims and source compatibility blocks migration until discovery succeeds.

The survey, exact-path catalogue, change summary, and qualification limits are in [the deliverable](</home/tak_0/sunshineos-audit/SunshineOS_Development-Testing/autonomy/codex/endeavouros-wave1-package-ownership.md>). Test evidence is in [the log](</home/tak_0/sunshineos-audit/SunshineOS_Development-Testing/autonomy/codex/endeavouros-wave1-package-ownership-test.log>).

Regression tests `T-ENDEAVOUR-PKG-001` and `T-ENDEAVOUR-PKG-002` cover the new behavior. The focused suite passed 37 tests; the full migration engine suite passed 234. EndeavourOS support remains conditional; fixture tests do not establish real-host qualification.
