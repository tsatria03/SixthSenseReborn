---
name: project_save_game_plan
description: "PLANNED 2026-10-07: save a game in progress and continue it later. Save and Save and quit on the pause panel, a Continue row before Game start, the run kept in saves/continue.json and resumed at the start of the section it was saved in (8 per level), deleted by that game's game over; an L key says the level and section. Not in the tutorial or the weapon test range."
metadata:
  type: project
---

**Status: being built, 2026-10-07.** Step 1 of 4 built, not yet confirmed: `sixthsense/game/saved_game.py` (the file, the section rows, `snapshot` and `resume`), the main menu's Continue row (10), the frame loop's `'continue'` screen, a continued game past level 1 getting the other area's ambience note (`Stage_1_E._other_area_note`, shared with `ChangeLevel:`), its game over deleting its save, Restart giving the save up, and debug F2 using the same section rows; `tests/case/saved_game.py`. Still to build: step 2, the pause panel's rows; step 3, the L key; step 4, the docs. The todo line is "Add the ability to save the game from where you are in a level, and continue it from where you last left off." Every decision below is tsatria03's, made one question at a time on 2026-10-07.

**What the original does.** It has no saving: a run lives in memory only. The pause panel's Main menu (`-[Stage_1_E GameEndAction:]`, 0x32fe1) drops the run and pays no gold; gold is paid only by a game over (`missionFailTell:`, 0x32760) or a mission success (`MissionSuccessTell`, 0x32c10).

## Where it is kept
- **`saves/continue.json`**, beside `save.json` (the dev chose the name over `run.json` and `game.json`). It exists only while there is a game to continue, so whether it can be read is the whole test for the Continue row.
- It is written and read as one JSON object of its own, not as loose `UserDefaults` keys, which `defaults.py` would send to `save.json`. Written the safe way the other save files are, through `defaults._File` (a temporary file, then replaced, with a `.bak`); a file that cannot be read is kept as `.damaged` and the game carries on from the `.bak`, as every other save file does; with neither, or with one that makes no sense, the Continue row is not offered, never a crash.
- What it holds: the level (`LVUP`), the area (`gameMode`), the zombies' toughness (`monsterHPGain`, which sets both their health and their speed; F3 and F4 only split it in debug mode), the start row of the section saved in, the hearts (`HP`), the weapon in hand (`useWepon`), each gun's rounds (`BulletCount`), the run's tally (`killMonsterCount`, every `killMonsterNcount`, `killMonster5000count`, `HeadShotCount`, `gunEggCountShot`) and `GirlMonsterNumber`. The score and the gold are worked out from the tally, so they come back with it. Grenades and gold are not in it: both already live in `store/inventory.json`.
- Not kept: the zombies on the field, their timers and a grab. A section starts with a quiet stretch, so an empty corridor there is natural.

## Where a game resumes
- **At the start of the section it was saved in** (the dev: "I like starting at each level's section"). Every level is the same corridor of **8 sections**, read from `game/a_CH1_E.txt`'s action layer, column 20, the rows whose cell is 9: 680, 601, 500, 400, 300, 200, 99 and 34 (the dev's count from debug mode, checked against the map). Section 8 is the boss's; it starts at row 34, before the alarm at 29 and the boss at 23, so continuing in it always brings the boss back. Resuming at the exact spot was not chosen: with no boss in the buffer, `checkBoosDie` would let a level past the boss's trigger end at once.
- Saved during a level change, a game is saved as the start of the next level.

## The pause panel
While paused (`gameState` 1), in this order:
1. Paused, then the kills, headshots, score, obtained gold and top score, as now.
2. **Resume, Button**: the old "Continue", renamed so it is not confused with the main menu's Continue (row 6; after a mission success it still says "Next stage").
3. Restart, Button.
4. **Save, Button**: writes `continue.json`, says "Game saved.", and carries on playing, as Resume does (`continueAction_`).
5. **Save and quit, Button**: writes `continue.json`, says "Game saved.", and goes to the main menu (`GameEndAction_`).
6. Main menu, Button: goes to the main menu without saving, as now; an older save is left as it was.

The two save rows are port rows with numbers of their own beside the original's (11 and 12; the original's numbers come from its ten touch bands, and 9, the rank, is already left out). They are not offered on game over or mission success, nor in the tutorial or the weapon test range (`Stage_Tutorial`, `Stage_1_TEST`; they check the stage is a real game, as `real_game` does). Saving works in debug mode too, so F2 and Shift+F2 can reach any section to test it (the dev agreed, 2026-10-07).

## The main menu
- **Continue, Button**, before Game start, only while `continue.json` can be read; it says "Continue" alone (the dev: "Just make it say continue only"). Pressing it says "Now loading", as Game start does, and starts the saved game at its section's start.
- **Game start** always starts a fresh game, and leaves a save alone. Pressing Save in that fresh game replaces the old save.

## When the save goes
- **A game over deletes it** (the dev: "I want the save to be deleted if the game is over"), so the run's gold is paid once. Only when the save belongs to that game: one it continued from, or one it saved (`Stage_1_E.ownsSave`). A fresh game that never saved does not touch an older save, and Restart makes a fresh game, so it gives up a continued game's claim on the save. Gold is still paid at the game over, for the whole run, before and after the save; Save and quit and Main menu pay none, as Main menu never did.

## The L key
- A new keymap action (`location`, "Say the level and section", default L), so the F1 screen lists it and it can be rebound. In a game it says, for example, "Level 1, section 1 of 8", saved or not. In the tutorial and the weapon test range it says "No level to report." Keyboard only (see below).

## Tests and docs
- Tests, the safe way: the file written and read back; resuming at each section's start; a game over deleting only its own save; the save rows absent from the tutorial, the test range, game over and mission success; Main menu leaving a save alone; Game start leaving it alone; a damaged file hiding Continue; the L key's words in each place; Resume's new name.
- `docks/readme.txt`, the changelog and README.md; the todo line moves to Finished once the dev confirms by ear.

## Left for later
- A controller button for L. tsatria03 owns no controller and has no idea what to map it to (2026-10-07), so L stays keyboard only; tunmi13productions, who built the controller support on real pads, is the one to pick a button if one is wanted. Claude's suggestion for them, not a decision: **Y**, free during play and already the "tell me" button (in the tutorial it says the lesson again); second choice Back (View or Share). Not the triggers, which players expect to fire, nor a stick click, easy to press by accident while aiming. During play the free buttons are Y, Back, the right stick, both triggers and both stick clicks; the left stick and D-pad aim, X reloads, the bumpers change weapon, A shakes free, and B and Start pause.
