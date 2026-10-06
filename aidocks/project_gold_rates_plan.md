---
name: project_gold_rates_plan
description: "PLANNED 2026-10-05: the gold a game pays becomes kills x GOLD_PER_KILL + headshots x GOLD_PER_HEADSHOT, two save.json keys defaulting to 15 and 5 (the original's 12 and 2), so weapons are easier to get and the rates can be edited."
metadata:
  type: project
---

**Status: PLANNED, agreed with the dev on 2026-10-05, not built.** Recorded before any code ([[feedback_record_plans_first]]). It answers the todo item "Raise the gold you earn after a death a little, so weapons are a bit easier to get." Mark it finished only once the dev says it works, then move it to `completed/` ([[feedback_completed_projects]]).

**Why:** a game pays `12 * killMonsterCount + 2 * HeadShotCount` (`Stage_1_E.ObtainedGold`, 0x3c616), paid when you die (`missionFailTell_`) or on the mission success ending (`MissionSuccessTell`). The sword at 50,000 took about 4,000 kills. The dev chose two editable rates over lowering prices, since a raise helps every save at once, while prices already in a save are never overwritten ([[real_weapon_stats_plan]]).

## Decided (the dev, 2026-10-05)
- Two keys in `save.json`: **`GOLD_PER_KILL`** (default **15**) and **`GOLD_PER_HEADSHOT`** (default **5**), named in the style of the weapon stats (capitals, underscores). "I love that!", and "Yes" to 15 and 5.
- `GOLD` stays what it is: the gold you have.
- A game pays `kills * GOLD_PER_KILL + headshots * GOLD_PER_HEADSHOT`. Headshots are every headshot hit, as the original counts them (`HeadShotCount`, 0x3a1dc), not only headshot kills; the dev was told.
- Written on every start where missing; a value that is not a whole number of 0 or more is put back to the default, as the weapon stats do. Existing saves get 15 and 5 on their next start.

## Left as they are
- The weapon test range keeps its own pay, 12% of its score ([[project_test_range]]).
- `--debug` counts no kills or headshots, so it still pays nothing.
- No change to how the result panel reads "Obtained gold"; it reads `ObtainedGold()`, which uses the rates.

## Build
- A small `game/gold_rates.py`: the two keys and defaults, `fill(defaults)` (sharing `weapon_stats._usable`), and `per_kill()` / `per_headshot()`.
- `AppDelegate.didFinishLaunching` calls `fill` beside `volume.load`.
- `Stage_1_E.ObtainedGold` uses the rates.
- Tests: defaults written on a new save, bad values put back, an edited rate changes what a game pays, the original's formula shape kept.
- Changelog line; `readme.txt` and `README.md` on the two keys; `platform/defaults.py`'s key note; the todo item to finished once confirmed.
