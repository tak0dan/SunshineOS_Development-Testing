# codex-lead-0036 -> hierarchy

# EndeavourOS architecture enforcement — Wave 1

Added an EndeavourOS fixture to the source matrix. It verifies that observed `ID_LIKE=arch` qualifies the source as **conditional**, then exercises the shared matrix’s discovery, planning, apply, and repeat-apply checks. This improves fixture-based enforcement; it does not establish real-host migration qualification.

The findings and exact-path catalogue are in [the change summary](</home/tak_0/sunshineos-audit/SunshineOS_Development-Testing/autonomy/codex/endeavouros-wave1-architecture-enforcement.md>). The regression output is in [the test log](</home/tak_0/sunshineos-audit/SunshineOS_Development-Testing/autonomy/codex/endeavouros-wave1-architecture-enforcement-test.log>).

Changed the fixture and matrix in [fixtures.py](/home/tak_0/sunshineos-audit/SunshineOS_Development-Testing/evolution-engine/src/fixtures.py), [source-matrix.toml](/home/tak_0/sunshineos-audit/SunshineOS_Development-Testing/evolution-engine/tests/source-matrix.toml), [test_source_matrix.py](/home/tak_0/sunshineos-audit/SunshineOS_Development-Testing/evolution-engine/tests/test_source_matrix.py), and `evolution-engine/fixtures/endeavouros/etc/os-release`.

**Regression:** `python3 -m unittest tests.test_source_matrix tests.test_compatibility tests.test_discovery` — 35 tests passed. Relevant IDs: `T-ENDEAVOUR-MATRIX-001`, `T-ENDEAVOUR-COMP-001`–`004`, and `T-ENDEAVOUR-DISC-001`.

**Commit:** Not created. `git add` could not create `.git/index.lock` because the Git index is read-only.
