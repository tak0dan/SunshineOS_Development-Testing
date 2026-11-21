# codex-lead-0070 -> hierarchy

# SteamOS repair tool — Wave 1

Added an assessment-only diagnostic for inconsistent SteamOS read-only and developer-mode state in [steamos_repair.py](/home/tak_0/sunshineos-audit/SunshineOS_Development-Testing/evolution-engine/src/evolution/tools/steamos_repair.py:31). It blocks unknown or contradictory observations and does not modify the root filesystem, packages, or boot slots.

The survey catalogues exact repository and upstream-reported paths in [steamos-repair-wave1.md](/home/tak_0/sunshineos-audit/SunshineOS_Development-Testing/autonomy/codex/steamos-repair-wave1.md). The local research names `/usr/lib/rauc/bootloader-custom-backend.sh`; [Valve issue #1654](https://github.com/ValveSoftware/SteamOS/issues/1654) reports a devmode marker failure at `/usr/lib/steamos/steamos-devmode`. No SteamOS image or source checkout was available to inspect these paths directly. Update-design grounding is documented by [Collabora’s SteamOS 3.6 account](https://www.collabora.com/news-and-blog/news-and-events/steamos-3-6-how-the-steam-deck-atomic-updates-are-improving.html).

Regression IDs `T_STEAMOS_REPAIR_001`–`008` are in [test_steamos_repair.py](/home/tak_0/sunshineos-audit/SunshineOS_Development-Testing/evolution-engine/tests/test_steamos_repair.py:1).

**Verification**, run from `evolution-engine/`:

```text
python3 -m unittest tests/test_steamos_repair.py -v
Ran 8 tests — OK
```

Full output: [steamos-repair-wave1-test.log](/home/tak_0/sunshineos-audit/SunshineOS_Development-Testing/autonomy/codex/steamos-repair-wave1-test.log). Task notes are under [autonomy/pull/codex-lead-steamos-repair-wave1](/home/tak_0/sunshineos-audit/SunshineOS_Development-Testing/autonomy/pull/codex-lead-steamos-repair-wave1). The changes remain uncommitted because `.git` is read-only in this workspace.
