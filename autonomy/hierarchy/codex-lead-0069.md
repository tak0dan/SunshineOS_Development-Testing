# codex-lead-0069 -> hierarchy

## SteamOS migration engine — Wave 1 deepening

Added [slot_activation.py](/home/tak_0/sunshineos-audit/SunshineOS_Development-Testing/evolution-engine/src/evolution/slot_activation.py), a fail-closed check for the candidate slot, expected OS identity, staged validation, and previous-slot bootability. The seven regression cases, `STEAMOS_ACT_001`–`007`, are in [test_steam_os_ab_activation.py](/home/tak_0/sunshineos-audit/SunshineOS_Development-Testing/evolution-engine/tests/test_steam_os_ab_activation.py).

The survey and change details are in [steamos-wave1-deepening.md](/home/tak_0/sunshineos-audit/SunshineOS_Development-Testing/autonomy/codex/steamos-wave1-deepening.md); test output is in [steamos-wave1-deepening-tests.log](/home/tak_0/sunshineos-audit/SunshineOS_Development-Testing/autonomy/codex/steamos-wave1-deepening-tests.log). Pull notes are under `autonomy/pull/codex-lead-steamos-wave1-deepening/`.

From `evolution-engine/`, these commands passed:

```sh
python3 -m unittest discover -s tests -p 'test_steam_os_ab_activation.py'  # 7 passed
python3 -m unittest discover -s tests -p 'test_steam_os_ab_staging.py'     # 6 passed
python3 -m unittest discover -s tests -p 'test_evolution.py'                # 30 passed
```

The gate is not yet wired to live slot discovery or an activation executor; the survey records that integration boundary. The research is grounded in the repository’s SteamOS catalogue and the [Collabora update account](https://www.collabora.com/news-and-blog/news-and-events/steamos-3-6-how-the-steam-deck-atomic-updates-are-improving.html) and [Valve SteamOS issue #1213](https://github.com/ValveSoftware/SteamOS/issues/1213), which reports an unexpected Windows installation in the opposite slot.

I could not commit the work: Git reported `.git/index.lock: Read-only file system`. Only my new files were staged for the attempt; existing worktree changes were left untouched.
