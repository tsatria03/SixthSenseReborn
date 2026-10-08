---
name: project_unused_save_keys_plan
description: "PLANNED 2026-10-07: remove the five save.json keys nothing uses, REVIEWCOUNT, TOPSCOREWEEK, WEEKTIME, NOWRANK and STAGE, with the code that writes or reads them (the ranking server's leftovers among it), and retire them so an old save drops them. TUTORIAL, TOPSCORE and WEAPON_STATS_REAL stay."
metadata:
  type: project
---

**Status: planned, 2026-10-07.** Nothing built yet. The todo line is "Remove the keys the game no longer uses from save.json, such as REVIEWCOUNT, which counts game overs only because the original used it to ask for an App Store review." It also finishes the developer task "Remove the code left from the publisher's ranking server" ([[project_dev_tasks]]).

## What each key in saves/save.json does today
Traced through the code on 2026-10-07:
- **`REVIEWCOUNT`**: one more at every game over (`Stage_1_E.missionFailTell_`, 0x32be6); nothing reads it. The original asked for an App Store review from it.
- **`TOPSCOREWEEK`**: the week's best score, written when a run beats it (`SuccessOrFailMission`, 0x34cc0..0x34e7c); nothing shows it. It was kept for uploading to the publisher's ranking server, which is gone.
- **`WEEKTIME`**: when that week ends. Nothing sets it; only `intro._expire_week` (0x1763c) reads it and clears it with `TOPSCOREWEEK`.
- **`NOWRANK`**: the place the server gave you. Nothing writes it; `Stage_1_E.updateTopscoreRank` reads it into `RankLabel`, which nothing shows, and `pause_row_text`'s row 9, which the panel never offers.
- **`STAGE`**: the highest stage unlocked, set to 11 by a mission success (`MissionSuccessTell`, 0x32efe..0x32f58) and read into `AppDelegate.stage` (and again in `intro.py`, 0x17918), which feeds only that same check. The original's stage select is not in the port, so it changes nothing in play.
- Staying, because they are used: **`TUTORIAL`** (whether Start Game plays the tutorial first), **`TOPSCORE`** (the panel's "Top score") and **`WEAPON_STATS_REAL`** (an old save already converted to the real weapon stats, `weapon_stats.REAL_MARKER`).

**The dev's decision (tsatria03, 2026-10-07):** all five go, `STAGE` too ("Yes. That should go too.").

## The plan
1. Remove the code that writes or reads them:
   - `stage_1_e.py`: the `REVIEWCOUNT` count in `missionFailTell_`; the `TOPSCOREWEEK` comparison and write in `SuccessOrFailMission`; `RankLabel`, `updateTopscoreRank` and its callers, and row 9's text in `pause_row_text` (the panel already leaves row 9 out); the `STAGE` write in `MissionSuccessTell`. Each removal leaves a one-line note of what the original did there and its address, as the coin removal did.
   - `intro.py`: `_expire_week` and its call, and the `STAGE` read.
   - `app_delegate.py`: `stage` and its `STAGE` read.
   - `defaults.py`'s docstring: the five keys' lines.
2. `defaults.RETIRED_KEYS` gains the five, so an existing save drops them the next time it is opened, as the coin keys were on 2026-10-06.
3. Tests: `save.py` checks the five are dropped from an old save; `pause.py`'s top score test keeps `TOPSCORE` and loses `TOPSCOREWEEK` and the `STAGE` check; the `save.py` tests that use `STAGE` only as an example key move to one that stays, such as `TOPSCORE`, since a retired key is dropped on load.
4. README.md and `docks/readme.txt` where they name these keys; a changelog line.

## How it is checked
- The covering tests in the background, then the full suite when the dev asks.
- By the dev: an existing save.json loses the five keys on the next start, and the panel still reads the top score.
