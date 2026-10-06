---
name: weapon_upgrades_plan
description: "FINISHED 2026-10-05, confirmed by the dev: one upgrade button per weapon raises its level, adding damage, ammo and range on top of its stats; prices start at 100 and grow 1.2x; cap 10 per weapon; every number editable in save.json. Answers the todo item about upgradeable weapons. RETUNED 2026-10-06 (built, not yet confirmed): a level adds a share of the weapon's own stat, 15% a level, so level 10 is two and a half times the weapon, in place of the flat steps that made every weapon gain +260; the range moves a whole metre at a time."
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

## Retuned 2026-10-06: a share of the weapon's own stat

**Status: built, not yet confirmed.** The dev found their level 10 colt holding 267 rounds: "I'm a bit concerned about weapon upgrades. my colt is at level 10, with an ammo capacity of 267. like wow." Agreed the same day, recorded before the code.

**What went wrong.** The three steps were flat counts shared by all eight weapons, and the 1.2 growth compounded them 26x by level 10, so every weapon gained the same `+260` whatever its size. A maxed colt held 267 rounds against the MG80's 310, 86% of a machine gun's magazine, and did 290 damage against zombies of 30 to 200 HP (`game/type*.plist`, index 3), one-shotting every one of them and killing a 2000 HP boss in 7 shots instead of 67. Its range went from 10 m to 36 m. The flat step was the root cause: 10 rounds a level means nothing in particular when it is applied to both a 7-round revolver and a 50-round machine gun.

**Decided with the dev, one question at a time:**
- **A share of the weapon's own stat, not a flat count.** `UPGRADE_AMMO`, `UPGRADE_DAMAGE` and `UPGRADE_RANGE` become percentages, all 10, so each weapon keeps its character and a maxed MG80 still out-ammos a maxed colt. The dev chose this over smaller flat steps and over a per-weapon step for each stat (24 more keys).
- **All three stats retuned, not ammo alone.** The dev's choice: the damage was the same problem less visibly, and 36 m of range let you shoot what you cannot yet hear.
- **15% a level, so level 10 is two and a half times the weapon.** The dev first chose 10% (double at max), then said doubling "seems too small. maybe 2.5?" A maxed colt holds 18 and does 75 damage, so it still takes 2 shots on a 100 HP zombie and 27 on a boss; a maxed MG80 holds 125.
- **The range moves a whole metre at a time.** It is kept in centimetres but read out in metres, and at 15% the M4, the AK47 and the sword landed on two decimals: "Effective range, 14.95 metres". The dev: "I would actually round them. it might read a little odd to someone like 14.95. just say 15." Rounding the gain to the nearest 10 cm instead, which gives one decimal at most, was offered and declined. The cost, which the dev accepted: the knife (2 m) and the sword (3 m) are too short for 15% to make a whole metre, so their range stands still on several levels, the knife reading 2, 2, 3, 3, 3, 4, 4, 4, 4, 5, 5. Only the range is rounded this way; ammo and damage are whole numbers already.
- **`UPGRADE_GROWTH` is dropped; `UPGRADE_PRICE_GROWTH` stays 1.2.** The prices do not change (100, 120, 144 ... 516, 2,596 to max): accelerating cost is the point of a price, while a growing share is a trap on a small weapon. To still only double at max with the growth kept, the share would have to be 3.85% a level, which on a colt is 0.27 rounds at level 1 and rounds away to nothing, so the first upgrades would visibly do nothing.

**The totals, a share of the base, rounded half up:**

```
weapon   ammo 0/5/10    damage 0/5/10   range m 0/5/10
GRENADE  no magazine    150/263/375     16/28/40
KNIFE    no magazine     30/ 53/ 75      2/ 4/ 5
COLT       7/12/18       30/ 53/ 75     10/18/25
SHOTGUN   10/18/25       35/ 61/ 88     10/18/25
M4        25/44/63       40/ 70/100     13/23/33
AK47      30/53/75       40/ 70/100     13/23/33
MG80      50/88/125      45/ 79/113     16/28/40
JAPAN    no magazine     100/175/250     3/ 5/ 8
```

The colt gains a round at every level but the last, where 10.5 rounds up to 11: 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 18. Its range, in whole metres, is 10, 12, 13, 15, 16, 18, 19, 21, 22, 24, 25.

**Build:**
- `weapon_upgrades.py`: `SHARES` in place of `STEPS`, the share read as a percentage, all three 15; `total(step, growth, n)` becomes `total(base, share, n, unit=1)` returning `half_up(base * share / 100 * n / unit) * unit`, capped at `CEILING`; `ROUNDING` gives the range its unit of 100 cm; `GROWTH` and its default gone; `added` takes the base from `weapon_stats.value(name, stat, defaults)`, so a base edited in save.json scales with it.
- **The keys are renamed**, since an old value means something else under the new reading and `UPGRADE_RANGE` of 100 would be 100% a level, eleven times the range at max. `UPGRADE_AMMO_SHARE`, `UPGRADE_DAMAGE_SHARE` and `UPGRADE_RANGE_SHARE` replace them, each 10; `fill` removes the three old keys and `UPGRADE_GROWTH` from an existing save, as `weapon_stats._rename_old_keys` does for its own, but without carrying the value over. The name says percentage, so no marker key is needed.
- **No save migration for levels.** The level is what is stored, never the total, so the dev's level 10 colt reads 14 rounds on the next start by itself.
- `weapon_stats.upgraded` and `store.py` call `added()` and need no change.
- `tests/case/weapon_upgrades.py`: the defaults, the new formula against the table above, the old keys removed, each key edited, the cap, the gold check, the pages' wording, the stage using the upgraded numbers.
- Changelog; `readme.txt` and `README.md` where they give the numbers; `platform/defaults.py`'s key note.
