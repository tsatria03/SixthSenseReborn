---
name: debug_level_toggles_plan
description: "FINISHED 2026-10-07, confirmed by the dev: in debug mode F3 holds zombie health at level 1's and F4 their speed, each a toggle, live on zombies already walking; the spawner keeps F5 and Shift+F5."
metadata:
  type: project
---

**Status: FINISHED 2026-10-07, confirmed by the dev: "It works!"** Built the same day: `Stage_1_E.level_gains`, the two toggles in `debug.py`, the two keymap actions and the window's debug line; zombies keep `baseHP`, `baseComingRange`, `hpGain` and `speedGain`.  The first try scaled a walking zombie's health by the ratio of the gains, which drifted with rounding (67 to 30 and back to 68); it is now rebuilt from `baseHP` and the share of health left, rounded as a new zombie is, so full health comes back exact.  gameplay 61, window, input, monster_sound, weapon_range, tutorial and data all pass.

**The dev's idea:** first "Replace the f5 key in the debug mode with a toggle to enable/disable zombies speeding up past level 1, as in they will all stay at level 1's movement speed."  Told that F5 is the spawner, they chose: "Keep the zombie spawner keys, but make f3 and f4 toggle the zombie health and speed changes per level."

**How a level scales zombies, from the binary:** `ChangeLevel:` multiplies `monsterHPGain` by 1.5 (0x32314), and `initWithMonsterPatern` multiplies both `HP` (0x10704) and the step, `comingRange` (0x10832), by it.  The girl and the woman zombie are built at 1.0 whatever the level (0x38d8c, 0x39034).

## The plan
- **F3, `debug_level_health`:** zombies keep level 1's health; again, health grows with the level.  **F4, `debug_level_speed`:** the same for speed.  Each says what it now does.  Both are keymap actions, so the F1 screen lists and rebinds them, in debug mode only.
- `MonsterInit:` passes a health gain and a speed gain, each 1.0 while its toggle is on, the level's otherwise; `initWithMonsterPatern` takes the speed gain apart from HPGain, and every zombie remembers its unscaled step and the gains it was built with.
- **Live:** a toggle also changes zombies already walking: the step rebuilt from the unscaled one, and the health scaled by the ratio of the new gain to the old, so damage already done stays done.
- The girl, the woman zombie and level 1 are unchanged (their gain is 1.0 anyway).  The toggles last for the stage, like F6 and F7.
- Tests in `gameplay.py`; `debug.py`'s docstring, the window's debug line, README.md and CLAUDE.md list F3 and F4.  No changelog line: debug mode is developer-facing.
