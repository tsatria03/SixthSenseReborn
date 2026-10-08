---
name: save_folders_plan
description: "PLANNED 2026-10-06: split the save into folders inside the save folder: saves/save.json (progress), config/settings.json and keys.json, store/shop.json and inventory.json (lowercase names, lists of weapon names), weapons/<name>.json (short names). defaults.py routes and translates; old layouts move over once."
metadata:
  type: project
---

**Status: FINISHED 2026-10-06, confirmed by the dev: "Everything works!", after starting the game on their real save, which sorted itself out as the copy had.** Built the same day, At the dev's word ("please build the save split first"), ahead of the evaluation's groups 9 to 11.

**What was built:** `defaults.py` routes every key by name to its file and translates it (`_home`, `objectForKey_`, `setObject_forKey_`); `flat()` gives every key back under the game's names, which the tests use to check what reached the disk. `keymap.py` uses `config/keys.json` and moves a flat one once (`_move_flat_keys`). `_own_save.py` copies from `config/`, or from the flat layout where a player's save has not moved yet. A byte order mark (Notepad) is read. **One bug found by the new tests and fixed before commit:** moving a flat save in, the first equipped weapon created the `equipped` list, so the others read "0" and counted as already set, and only the grenade stayed equipped; "already there" now means what inventory.json held before the move began (`_place`). Checked on a copy of the dev's real save in the session scratchpad (never the real one): every key in its file, save.json left with `WEAPON_STATS_REAL`, nothing set aside as damaged, the game reading gold 0, the colt equipped and the same order. Full suite **619 of 619 across 34 files** in 336 s; save.py has 24.

**Before the dev starts the game on the real save:** nothing to do. The first start sorts the hand-made layout out the same way; the old keys.json beside the folders does not exist there, so the keys stay in `config/`. Built inside the held batch of [[evaluation_fixes_plan]], which is paused at its group 5 for this; nothing of either is pushed until both are done, tested and confirmed.

**The dev's idea (2026-10-06):** "This folder will store keys, settings, shop stuff, your inventory, and each individual weapon setting in there ... I wanted to dee-cludder the save.json file." They first made it as `data/` in the repository; Claude pointed out a save beside the game is shared between players, cannot be written in a read-only install, is replaced by an update and would ship in builds, and the dev agreed ("You are absolutly right") and moved the layout into the save folder by hand, `%APPDATA%\SixthSenseReborn`. Short names in the weapon files ("I like short names a lot better") and lowercase in both store files ("I like lowercase yes") were the dev's choices, each Claude's recommendation.

**Why:** save.json held 58 keys, 48 of them weapon numbers; each file now holds one thing and is short enough to read and edit by ear.

## The layout, under `paths.user_dir()`
Every system's save folder (`%APPDATA%\SixthSenseReborn` on Windows), so the tests' `SIXTHSENSE_USER_DIR` and the by-ear tools' saves ([[evaluation_fixes_plan]] group 3) keep working unchanged.

- `saves/save.json`: progress, and the catch-all for any key not routed elsewhere, as today: `TUTORIAL`, `STAGE`, `TOPSCORE`, `TOPSCOREWEEK`, `WEEKTIME`, `NOWRANK`, `REVIEWCOUNT`, `WEAPON_STATS_REAL`. Names unchanged.
- `config/settings.json`: `defaults.SETTINGS_KEYS`, in that order. Names unchanged.
- `config/keys.json`: the key bindings (`keymap.py`). Unchanged inside.
- `store/shop.json`, lowercase, in this order: `gold_per_kill`, `gold_per_headshot`, `upgrade_start_price`, `upgrade_price_growth`, `upgrade_ammo_share`, `upgrade_damage_share`, `upgrade_range_share` (from `GOLD_PER_KILL` ... `UPGRADE_RANGE_SHARE`).
- `store/inventory.json`, lowercase:
  - `gold` and `grenades`: plain numbers (from `GOLD` and `GRENADECOUNT`, which the game kept as text).
  - `owned`: a list of weapon names (from the `SHOTGUN`, `M4`, `AK47`, `MG80`, `JAPAN` keys at "1").
  - `equipped`: a list of weapon names (from the eight `...USE` keys at "1").
  - `order`: a list of weapon names (from `WEAPON_ORDER`'s slot numbers).
- `weapons/<name>.json`, one per weapon, short names in this order: `ammo_capacity`, `range`, `damage`, `price`, `level`, `max_level` (from `<W>_AMMO_CAPACITY` ... `<W>_MAX_LEVEL`). A weapon has only the keys it has today: no ammo capacity for the knife, the sword and the grenade, no price for the knife and the colt.

Weapon names, by slot: 0 `grenade` (GRENADE), 1 `knife` (KNIFE), 2 `colt` (COLT), 3 `shotgun` (SHOTGUN), 4 `m4a1` (M4), 5 `ak47` (AK47), 6 `mg80` (MG80), 7 `sword` (JAPAN).

## How the game reads it
- **Nothing outside `defaults.py` changes.** The game keeps asking for `'SHOTGUN_DAMAGE'`, `'GOLD'` or `'M4USE'`; `defaults.py` routes each key to its file and translates the name, as it already routes by name between save.json and settings.json (aidocks/completed/save_split_plan.md). Values read back in the form the code expects today (e.g. `GOLD` as text for `stringForKey_`, `M4USE` as "1" or "0").
- **Each file keeps its own `.bak`, and one that cannot be read is set aside as `.damaged`**, as now. **An empty file counts as new**, not damaged (the dev made the store and weapon files empty by hand).
- `keymap.py` reads and writes `config/keys.json`.
- `tests/interact/_own_save.py` copies `config/keys.json` and `config/settings.json`.

## Moving an old save over, once
- **A key found in the wrong file goes to its own file**, unless that file already has it, and the file it came from is rewritten without it. This one rule covers the dev's current save (a full flat `saves/save.json` beside empty files) and anything hand-moved later.
- **The old flat layout** (`save.json`, `settings.json`, `keys.json` directly in the save folder, every player's until this ships, and every by-ear tool's save) is moved into the new files on the first start, and each old file kept beside them as `<file>.old`, as `defaults.json` was. A `defaults.json` from before the split keeps working through the same path.
- SixthSenseOriginal's save, copied once on a first start (`paths.adopt_old_save`), lands in the flat layout and is moved over the same way.

## Tests, docs and the rest
- `tests/case/save.py`: every file's contents, the translations, the move-over from the flat layout and from the dev's hand-made one, `.old` kept, an empty file as new, a damaged one set aside. Tests that read `save.json` or `settings.json` by path follow the new paths.
- A changelog line (players see the new folders), `docks/readme.txt` where it names the save files, README.md, CLAUDE.md's save paragraph, `defaults.py`'s docstring.
- The todo list carries one line until the dev confirms.

## Left out
- `settings.json`, `keys.json` and `save.json` keep their names inside; only the store and weapon files are lowercase.
