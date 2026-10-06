---
name: weapon_upgrades_plan
description: "FINISHED 2026-10-05, confirmed by the dev: one upgrade button per weapon raises its level, adding damage, ammo and range on top of its stats, growing 1.2x a level; prices start at 100 and grow 1.2x; cap 10 per weapon; every number editable in save.json. Answers the todo item about upgradeable weapons."
metadata:
  type: project
---

**Status: FINISHED 2026-10-05, confirmed by the dev** ("Everything works!"), and moved to `completed/` the same day. Built alongside it at the dev's request: `GOLD` written as '0' on start when missing (`AppDelegate.didFinishLaunching`), as `GRENADECOUNT` already was. `game/weapon_upgrades.py` (settings, `fill`, `level`, `max_level`, `total`, `added`, `price`, `upgrade`), filled in `AppDelegate.didFinishLaunching`; `weapon_stats.upgraded` adds the level for play (`apply`) and the pages (`store.load_stats`); `store.py` has `LEVEL_ROW` 9, `UPGRADE_ROW` 10, `owns`, the row texts and `upgrade_action`, used by both pages' `rows()` and `activate`; buying moves the cursor to the upgrade button. New `tests/case/weapon_upgrades.py` (9). Covering files passed: store 20, inventory 2, weapon_stats 11, gold_rates 4, save 13, paths 22, window 10, menu 20, data 19, weapon_range 15, input 48, pause 30, gameplay 59, controller 26.

Agreed with the dev on 2026-10-05 and recorded before any code ([[feedback_record_plans_first]]). The todo item (reworded by the dev, uncommitted at planning time): "Make weapons upgradeable, so that they can have more ammo, and do more damage." Mark it finished only once the dev says it works, then move it to `completed/` ([[feedback_completed_projects]]). Builds on [[real_weapon_stats_plan]] (the stats in the save) and [[gold_rates_plan]].

## Decided with the dev, one question at a time
- **One level per weapon, one button.** Each press raises the weapon one level, and its damage, ammo and range all go up together (the dev: "One button to upgrade all stats for that weapon"). Weapons with no magazine (the grenade, the knife, the sword) gain only damage and range. Their first idea had three buttons; the dev chose one level for the whole weapon.
- **Additive.** What play uses is the weapon's own save stat (`<W>_DAMAGE` and the rest, still editable) plus what its level adds.
- **What a level adds grows by `UPGRADE_GROWTH`, 1.2.** Level 1 adds the base step, each level after adds 1.2 times the one before; the total added at level n is `step * (g^n - 1) / (g - 1)` (or `step * n` when g is 1), rounded half up. Base steps: `UPGRADE_DAMAGE` 10, `UPGRADE_AMMO` 10, `UPGRADE_RANGE` 100 cm. At 1.2 the totals added are 10, 22, 36, 54, 74, 99, 129, 165, 208, 260 (range: 1 m to 25.96 m). The dev looked at 1.5, 1.1 and 1.05 first, then chose 1.2.
- **Price grows by `UPGRADE_PRICE_GROWTH`, 1.2, from `UPGRADE_START_PRICE`, 100.** Level n costs `start * pg^(n-1)`, rounded half up: 100, 120, 144, 173, 207, 249, 299, 358, 430, 516; maxing costs 2,596 (about 170 kills at 15 gold). The same for every weapon, the free ones included; the dev looked at doubling from 50 and from 10 first.
- **A cap per weapon, `<W>_MAX_LEVEL`, 10.** One cap for the weapon, not one per stat (the dev: "one level per weapon, not 3 level caps").
- **Every number editable, all six upgrade settings for all weapons at once** (the dev: "Fully editable"); the cap and the level per weapon.
- **Where the button is:**
  - Every owned weapon's **inventory page**, a row after Equip. The knife and colt, never sold, are upgraded only there.
  - A bought weapon's **shop page**: the upgrade button takes Buy's place once owned (Try stays).
  - The **grenade's shop page** keeps Buy, since grenades are bought again and again, and gets the upgrade button beside it.

## What the pages say
- A row after the four numbers: "Level, 3 of 10".
- The button: "Upgrade stats to level 4 for 173 gold, Button" (the dev's wording).
- At the cap: "Fully upgraded" and it does nothing.
- Without the gold: "Gold is lacking.", as buying says.
- After an upgrade: "Upgraded to level 4.", and the page's numbers read the new values: ammo capacity, range and damage are the totals with the level.

## Save keys
- Per weapon: `<W>_LEVEL` (0) and `<W>_MAX_LEVEL` (10), for all eight.
- For all weapons: `UPGRADE_START_PRICE` (100), `UPGRADE_PRICE_GROWTH` (1.2), `UPGRADE_DAMAGE` (10), `UPGRADE_AMMO` (10), `UPGRADE_RANGE` (100), `UPGRADE_GROWTH` (1.2).
- Filled on every start where missing, bad values put back (whole numbers of 0 or more; the two growths any number above 0). A level above its cap is left as edited; the button just says fully upgraded.

## Build
- A `game/weapon_upgrades.py`: the keys and defaults, `fill`, `level`, `added(name, stat)`, `price(level)`, `upgrade(name)`.
- `weapon_stats.apply` and `store.load_stats` add the level's amounts, so play, the test range and both pages use them.
- The shop page's row 7 is Upgrade once a weapon is owned (Buy for the grenade, with Upgrade after it); the inventory page gains the upgrade row; both gain the level row.
- Tests: the defaults, the formulas against the tables above, editing each key, the cap, the gold check, the pages' wording, the stage using the upgraded numbers.
- Changelog; `readme.txt` and `README.md`; `platform/defaults.py`'s key note; the todo item to finished once confirmed.
