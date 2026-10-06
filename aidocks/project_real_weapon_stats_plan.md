---
name: project_real_weapon_stats_plan
description: "PLANNED 2026-10-05: each weapon's stats in save.json become the real ones and the game reads them: damage, range (in cm) and ammo capacity drive play, price is what the shop charges, and the shop and inventory read them out, range in metres. Replaces the never-read keys of [[weapon_stats_in_save_plan]]."
metadata:
  type: project
---

**Status: PLANNED, agreed with the dev on 2026-10-05, not built.** Recorded before any code ([[feedback_record_plans_first]]). The todo list has it as unfinished. Mark it finished only once the dev says it works, then move it to `completed/` ([[feedback_completed_projects]]).

**Why:** [[weapon_stats_in_save_plan]] (2026-09-25) wrote the shop's numbers into the save and never read them back. Those numbers are not the ones the game plays with: the original typed the shop's into its code (`store.SHOP`, `inventory.SLOTS`, which disagree with each other too), while play reads the weapon plists. The shotgun reads 45 damage and range 50, and plays at 35 damage and 1000 cm. Reborn need not be faithful ([[project_two_repos]]). The dev: "I want the shop to read the real numbers, but also, modifying the stat in the save file should effect the game as well."

## The keys, and the starting numbers
The real numbers, from the weapon plists (damage index 3, range 5, bullets 7) and the shop's prices (what `buyAction_` charges). Range is in centimetres.

Each line is ammo capacity, range, damage, price:
- GRENADE: none (its count is GRENADECOUNT), 1600, 150, 1000
- KNIFE: none, 200, 30, none
- COLT: 7, 1000, 30, none
- SHOTGUN: 10, 1000, 35, 7000
- M4: 25, 1300, 40, 13000
- AK47: 30, 1300, 40, 15000
- MG80: 50, 1600, 45, 45000
- JAPAN: none, 300, 100, 50000

- **"none" means no key**, because nothing could ever use it (the dev agreed each): the grenade's count is `GRENADECOUNT`, already real; the knife and sword spend no ammo; the shop never sells the knife or colt.
- Keys keep the existing names, `<W>AMMOCAPACITY`, `<W>RANGE`, `<W>DAMAGE`, `<W>PRICE`, in `save.json`.

## What the game does with them
- **All eight weapons, from the start**, owned or not, so a price can be edited before buying (the dev: "Yes"). Written on every start where a key is missing.
- **A bad value is put back** to the weapon's real number on the start (the dev: "Yes"): anything not a whole number of 0 or more (text, a negative, a fraction). 0 is allowed.
- **Once only, an existing save's old shop numbers are replaced** by the real ones (the dev: "Yes"). A marker key in `save.json` records that it was done, so a later hand edit is never undone.
- **Damage and range** replace the plist's in play (`WeaponControl` after `loadWeaponForGun_fileType_`, in `Stage_1_E.weaponInit`; the test range shares it). A headshot still doubles the damage.
- **Ammo capacity** is the magazine: `ReloadGun` returns it, so starting, reloading and the test range fill to it.
- **The grenade's range becomes real** (the dev: "It should be a real number actually used"): the blast hits only monsters within it (`monsterRange <= Range`). At 1600 it plays as now, since zombies appear at 1000.
- **Price** is what the shop charges and checks gold against.
- Edits are read when the game starts, so the game must be closed while editing (it rewrites the file on save).

## What the pages say
Shop and inventory pages both read the save, so they always agree.
- Ammo capacity as a number; the grenade keeps "Number of grenades"; the knife and sword say **"Ammo capacity, none"**.
- **Range in metres**, cm / 100, at most two decimals, trailing zeros dropped (the dev: "Exactly right"):

  - 1000 says "10 metres"
  - 162 says "1.62 metres"
  - 2505 says "25.05 metres"
  - 150 says "1.5 metres"
  - 100 says "1 metre"
  - 5 says "0.05 metres"

- Damage as a number. Price as a number; the knife and colt say **"Price, free"**.
- `SHOP` and `SLOTS` keep names, sounds and keys; their stat fields go.

## Tests and docs
- `tests/case/weapon_stats.py` rewritten: the table above in a new save, all eight weapons, missing and bad values put back, the one-time replacement and that a later edit survives it, no key where "none".
- Edits take effect: damage, range and ammo in the stage (`gameplay.py` or `weapon_stats.py`), the grenade's range, the price at buying (`store.py`), the pages' words, metres formatting.
- Update tests that pin the shop's old numbers (`store.py`, `inventory.py`, `weapon_range.py` if any).
- Changelog line; `docks/readme.txt` on editing weapons; `README.md`'s test line; `platform/defaults.py`'s key note; a pointer from [[weapon_stats_in_save_plan]] to this note.
