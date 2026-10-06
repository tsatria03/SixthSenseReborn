---
name: project_evaluation_fixes_plan
description: "PLANNED 2026-10-06: fix all 19 findings of the 2026-10-06 evaluation in about ten local commits, none pushed until every item is done, tested and confirmed by the dev. Groups, order, open questions and what each commit carries."
metadata:
  type: project
---

**Status: planned, 2026-10-06.** Nothing built yet. The findings and their evidence are in [[project_evaluation_2026_10]]; this note is how they get fixed.

**The dev's words (2026-10-06):** "I believe we'll need a bunche of non pushed commits to fix these. I say non pushed because I do not people seeing them untill we resolved all of them." And: "we might as well add some of these things to the todo list, asooming some of them are player facing." tunmi13productions said they would stop pushing for a few hours that day, so the shared files (`main_controller.py`, `stage_1_e.py`, `SixthSenseReborn.py`) go first, while no rebase is needed.

## How the batch works
- This note is committed first, on its own, with the todo list and developer task lines ([[feedback_record_plans_first]]).
- One commit per group below, each with its own changelog line when a player notices it ([[feedback_changelog]]), and the todo or [[project_dev_tasks]] line moved to finished only when the dev confirms ([[feedback_todo_list_format]]).
- **Nothing is pushed** until every group is done, the full suite passes ([[project_safe_test_run]]), and the dev has checked by ear. Then everything goes out in one push, including the two commits made before this plan (the `volume.py` test fix and the evaluation notes).
- After each group, only the test files covering the changed code are run ([[feedback_dont_run_or_build]]); the full suite runs once at the end.
- `git fetch` after every few commits (the dev's rule, 2026-10-06). If tunmi13productions pushes in the meantime, report the incoming commits and wait; with local commits held, bringing theirs in needs a rebase of ours (unpushed, so no published history changes), and that needs the dev's go-ahead ([[feedback_git_commits]]).
- Open questions are asked one at a time, each with a recommendation, as its group comes up ([[feedback_one_question_at_a_time]]).

## The groups, in the order they will be done
Item numbers are the 19 of the evaluation's list, ranked high to low.

1. **Coin leftovers** (items 5, 7, 10, and the coin docstrings of 13). Player-facing. **Built 2026-10-06; confirmed by the dev the same day ("These 3 are fixed", with group 4)**: save, menu, menu_music, pause, window, settings_menu and intro pass 107 of 107, with the new `save.test_the_old_coins_are_dropped`; `save.py`'s old defaults.json test no longer expects `COIN` to be carried over, and `menu_music.py` no longer sets `FIREST` and `COIN`.
   - `SixthSenseReborn.py`: the panel row label "restart (costs a coin)" becomes "restart"; the comment above `PANEL_ROWS` saying the player hears a WAV is corrected.
   - `main_controller.py`: remove `SOUND_COIN_COUNT`, `SOUND_NO_COIN`, `READ_COIN_COUNT_DELAY` and the `readNumberOfCoin` cancel; the module docstring describes the free games, keeping the binary's coin logic only as a short note of what the original did.
   - `defaults.RETIRED_KEYS` gains `COIN`, `COIN_TIMER`, `COIN_TIMER_START` and `FIREST`, so an old save drops them; a test in `save.py` checks it, beside the one for `EYEMODE`.
2. **Voice over leftovers** (items 11, 12, 13). Not player-facing. **Built 2026-10-06, not yet confirmed**: nothing played from `row_sound`, so it went everywhere, with more than the evaluation saw: `PAUSE_ROW_SOUND` in `stage_1_e.py` and `stage_1_test.py`, the sound column of `main_controller.ROWS` (now `(number, flag, action)`) and the stops of sounds the menu never plays, and the `image` and `label` fields of `store.SHOP` and `inventory.SLOTS`.  The intro keeps its sound constants, which still stop and play sounds.  The tests that checked WAV numbers now check the spoken words, and the three that only checked the recordings exist went.  16 test files pass 352 of 352.
   - Remove `row_sound` / `ROW_SOUND` and the `type_*_sound` helpers from `blind_screen.py`, `main_controller.py`, `store.py`, `inventory.py`, `intro.py` and `settings_screen.py`, after checking each caller: if anything still plays from them (the evaluation saw `intro.select` reading them), that part stays and is renamed for what it does now.
   - The tests that read them are updated in the same commit.
   - `SOUND_HEADSHOT_BEEP` is defined once, in `stage_1_e.py`, and imported by `settings_screen.py`.
   - Docstrings: `main_controller.py` ("self-voiced", the voice over rows), `speech.py` (the 269 WAVs), `stage_1_e.py` ("with voice over off"), `blind_screen.py` ("blind-mode"), `SixthSenseReborn.py` ("on Windows" only).
3. **The by-ear tools' saves** (items 1, 14, 15). Not player-facing; the most severe item. **Built 2026-10-06, not yet confirmed**: `tests/interact/_own_save.py`'s `own_save(name)` sets `SIXTHSENSE_USER_DIR` to `<save_base>/SixthSenseReborn/<name>/SixthSenseReborn`, exactly the Windows folder each tool used before, so existing tester saves carry on; it copies keys.json and settings.json, never the save. `paths.py`'s two new tests (no tool sets `APPDATA`, and the helper's folder and copies) pass, 24 of 24. To check by ear: each of the three tools still starts on its own save with your keys and settings.
   - One shared helper in `tests/interact/` that sets `SIXTHSENSE_USER_DIR` to the tool's own folder under `paths.save_base()` + `SixthSenseReborn`, and copies the key bindings, as `controller_tester.py` already does for its save. The Windows folders stay where they are (`%APPDATA%\SixthSenseReborn\level_chooser` and so on), so the dev's existing tester saves carry on.
   - `level_chooser.py`, `tutorial_chooser.py` and `headshot_tester.py` use it instead of changing `APPDATA`.
   - Their "SixthSense Reborn" text becomes "Sixth Sense Reborn".
   - A test in `tests/case/paths.py` checks that no file in `tests/interact/` sets `APPDATA`.
4. **Settings written on the first start** (item 18). Player-facing. **Built 2026-10-06; confirmed by the dev the same day**: `app_delegate.SETTING_DEFAULTS` and `fill_settings`, called in `didFinishLaunching` beside `volume.load`, write each missing toggle at the value its reader already assumed (VIBRATION 1, HEADSHOTSPEECH 1, HEADSHOTBEEP 0, SHAKE 1, CONTROLLER empty, SKIPINTRO 0). The new `settings_menu.test_a_new_settings_json_shows_every_setting` checks the order, that play does not change and that a player's value is kept; 13 files pass 277 of 277. To check: a fresh save's settings.json lists all thirteen settings.
   - `VIBRATION`, `SHAKE`, `SKIPINTRO`, `CONTROLLER`, `HEADSHOTSPEECH` and `HEADSHOTBEEP` are written with their defaults on the first start, like the volumes, so settings.json shows every setting.
   - A test checks a fresh settings.json holds every key of `SETTINGS_KEYS`, in order.
5. **What builds ship** (item 3). Player-facing: a smaller download. **Paused 2026-10-06** for [[save_folders_plan]], built inside this same held batch. Found so far: of `unused/`'s 191 files, `speech/` is 145 (58.5 MB) and `sfx/` 46 (12.7 MB, with `weapon_saw_wait`, which `stage_1_test.SOUND_SAW_WAIT` still names); `used/` is 103 (42.4 MB). The dev moved the blooper out of `game/sounds/unused/bloopers/` to the repo's `bloopers/` folder the same day, so builds no longer carry it. Sounds load only when played (`oal_playback.initBuffers`), and no path plays an `unused/` sound: the test range's saw is slot 8, which is never loaded, and zombie kinds 11 and 12 never spawn. **The dev's decision (2026-10-06): "When I compile the game, it should only build with sounds/used."** **Built 2026-10-06, not yet confirmed**: `compiler.shipped_sound_folders()` is `used/` alone, for folder and `--embed` builds; `.ogg` is no longer counted as a sound; a build carries 248 files, 103 of them sounds. `release.py`'s new test checks a build carries no `unused/` or blooper file; release, data and paths pass 94 of 94. To check: a build's `game\sounds` folder holds only `used`.
   - Open question: ship only `game/sounds/used/`, or `unused/` minus the old speech and the blooper? Recommendation: only `used/`, since `paths.path_for_resource` reaching into `unused/` would mean a sound in the wrong folder. Before deciding, a check (no game run) lists any `SoundList.plist` name the game plays that exists only in `unused/`.
   - The `compiler.py` docstring counts are corrected in the same commit; `tests/case/release.py` checks the blooper is never shipped.
6. **The macOS bundle identity** (item 8). Player-facing on a Mac.
   - Open question: the new identifier. Recommendation: `org.sixthsense.reborn`.
   - **The dev's decision (2026-10-06): "Fix the macoss build bugs. I like what you said."** **Built 2026-10-06, not yet confirmed**: `compiler.BUNDLE_ID` is `org.sixthsense.reborn`; `release.py`'s macOS test checks it; 51 of 51. The save folder is found by name, not by this id, so a Mac player's save is unaffected. SixthSenseOriginal was not checked out beside this repository, so its id was not read; the change stands either way. To check: the next macOS build's app reports the new id.
7. **The release workflow** (items 2, 4). Not player-facing. **Built 2026-10-06, not yet confirmed.** The dev had not known the workflow existed (tunmi13productions built it on 2026-10-05, leaving tests out on purpose); told so, they kept the go-ahead. A "Run the tests" step before "Build and pack" runs every `tests/case` file but `_*.py`, failing the job if any fails; PyInstaller is pinned to 6.22.3 and pyinstaller-hooks-contrib to 2026.7 (read from the dev's machine with `pip show`); the Mac runner comment says the names were proved. `release.py`'s new test checks all three; 52 of 52. **Unproven until a workflow run:** the suite has only ever run on Windows (and Linux in WSL), never on GitHub's Linux or macOS runners, so the first "Test the workflow" after the push may find a test that assumes Windows; it would fail the build, not publish anything.
   - `release.yml` runs the whole test suite on each system before building, the same safe way (`_scratch_save` makes it silent), and stops the release on a failure.
   - PyInstaller is pinned to the version the dev builds with now (read from their environment with `pip show`, not guessed).
   - `tests/case/release.py` checks both.
8. **Missing tests** (item 9). Not player-facing. **Built 2026-10-06, not yet confirmed**: `weapon_upgrades.py` gains an absurd hand edit capped at `CEILING` without a crash, a level above the cap refused at no cost, and the test range (`Stage_1_TEST`) playing with upgraded stats; `save.py` gains every setting in settings.json and nothing else there. 15 of 15 each, first run, so no code needed changing. **Found:** a level edited past the cap was played as written (COLT_LEVEL 15 of 10 added 15 levels' worth) and the page read "Level, 15 of 10". **The dev's decision (2026-10-06): "Count only up to the cap."** Built the same day, its own commit: `weapon_upgrades.level()` is the saved level limited by the cap, so play, the page ("Level, 10 of 10") and the button agree; the saved number stays as written, so a raised cap lets it count again. A changelog line; weapon_upgrades, weapon_stats, weapon_range, store and gameplay pass 119 of 119.
   - The weapon upgrade cap, a level above the cap in save.json, the test range playing with upgraded stats, and the settings landing in settings.json rather than save.json.
9. **README.md** (item 6). Not player-facing (players read `docks/readme.txt`, which is current).
   - Remove voice over and coins, give the gold as 15 and 5, the main menu's real rows, the 34 test scripts with their real names, no `digits.py`, and the sound counts from the folders.
10. **CLAUDE.md and the notes** (items 16, 17).
    - CLAUDE.md: SoundList's 375 entries (372 to 374 added), the sound folder counts from the folders, the blooper under `unused/bloopers/`.
    - MEMORY.md's finished-project lines: the Reborn names and paths, no `defaults.json`, `EYEMODE` or coins as current facts. [[project_tests_layout]] lists all four by-ear tools.
    - Done last, so the counts and file names match the code after every other group.
11. **Long functions** (item 19).
    - Open question: refactor `main()` in `SixthSenseReborn.py` and the longest `stage_1_e.py` methods now, or leave them noted? Recommendation: leave them as a developer task; splitting them changes no behaviour and risks breaking timing the tests cover only partly.

## Todo list and developer tasks
- `docks/todo list.txt` ##Unfinished. gets the player-facing groups 1, 4, 5 and 6 (five lines; group 1 is two), replacing the "Nothing is waiting here" line.
- [[project_dev_tasks]] Open gets one line for each of groups 2, 3, 7, 8, 9, 10 and 11.

## Left out
- Nothing from the evaluation is left out; item 19 may be, if the dev agrees.
