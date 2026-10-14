---
name: project_dev_tasks
description: "The developer-side task list: work on the repository, the tools, the tests, the build and the docs that a player never sees. Moved out of todo list.txt on 2026-09-23, when that file became players only. Open tasks first, then finished ones, newest first."
metadata:
  type: project
---

Since 2026-09-23, `todo list.txt` holds only what a player notices ([[feedback_todo_list_format]]). Everything else that needs doing, or has been done, lives here, in the same style: one plain sentence per line, newest first. The technical detail behind each line is in SixthSenseOriginal's `project_evaluation_2026_09` note.

**How to apply:** a new developer task goes at the top of Open. When it lands and the dev confirms, it moves to the top of Finished. A task that changes what a player hears or sees belongs in `todo list.txt` instead, and in `changelog.txt` once it is done ([[feedback_changelog]]). **Debug mode is developer-facing** (the dev, 2026-09-23: players will not know it exists), so its lines live here and never go in `todo list.txt` or `changelog.txt`. The four oldest debug lines below came from the changelog, which had them in more detail than the todo list.

## Open

The seven lines below are from the 2026-10-14 rescan, after release V26.10.08-1 and the dev's move of every aidocks note into `aidocks/general/` and `aidocks/plans/` (uncommitted then; all 72 files byte for byte the same as before). The full suite passed, 675 of 675 in 96.8 s.
- Correct the Settings labels the game window shows (`SCREEN_ROWS['settings']` in `SixthSenseReborn.py`, line 418), which are in an old row order: the screen's rows are 2 Debug mode, 3 Skip the opening screens, 4 Spoken headshot, 5 Headshot beep, 6 Controller support, 7 Vibration, 8 Shake to break free and 9 Controller (`settings_screen.py`), so the window calls row 2 "skip the opening screens" and every row up to 7 is one or two places off. Speech is right. Better still, build the labels from `settings_screen` so they cannot drift again.
- Repoint `aidocks/general/MEMORY.md` to the new layout: 40 of its 73 links are `completed/<name>.md`, which should now be `../plans/<name>.md`, and its "Completed projects" heading and lines 3 and 84 still name `aidocks/completed/`.
- Rewrite the memory rules for the new layout in `CLAUDE.md` (lines 5, 43 and 85: links resolve to `aidocks/<name>.md`, finished projects go to `aidocks/completed/`, `GAME_STRUCTURE.md` sits in `aidocks/`), `feedback_completed_projects.md`, `feedback_memory_in_aidocks.md` and `feedback_record_plans_first.md`. The dev's rule (2026-10-14): `aidocks/plans/` holds every plan, planned or complete, so a finished plan is marked finished in its own note and stays where it is, instead of moving; `aidocks/general/` holds the rest of the notes.
- Repoint the roughly 100 comments and docstrings that cite `aidocks/completed/...` or `aidocks/<name>.md`: in `sixthsense/` (most in `stage_1_e.py`, `app_delegate.py`, `defaults.py`, `main_controller.py`, `controller.py` and `settings_screen.py`), `tests/case/`, `tests/suite.py`, `tests/interact/_own_save.py`, `tools/`, `compiler.py`, `releaser.py`, `SixthSenseReborn.py`, `README.md`, `.github/workflows/release.yml` and a few plans. None affects how the game runs.
- Remove or correct the ten links to `aidocks/DIVERGENCES.md`, eight in plans and one each in `project_binary_analysis_notes.md` and `project_sound_organization.md`: that file stayed in SixthSenseOriginal, so they were broken before the move.
- Remove the unused constants `SOUND_NOW_LOADING` (`stage_1_e.py`), `SOUND_PAUSED` and `SOUND_CONTINUE` (`stage_1_test.py`) and `OLD_KEPT` (`defaults.py`), and decide whether `SWIPE_BANDS` (`stage_1_e.py`), `paths.BINARY`, `paths.set_resources` and `runloop.main_loop` stay for documentation or older callers.
- Correct the comment at line 404 of `SixthSenseReborn.py`, which says the player hears the original's WAV for the shop and inventory rows, which are now spoken. (Line 466's "ten bands" is right: it describes the original's `selectTapPointSoundStart`.)

The six lines below are deferred findings from the 2026-10-07 rescan, after release V26.10.07-2. The long `main()` it also found is already listed further down, and the ranking server leftovers it found are finished; the Mac app identity line in `todo list.txt` was confirmed by the dev and moved to Finished the same day, and so were the five evaluation lines the batch had built and the Mac app's version and minimum macOS ([[mac_plist_plan]]).
- Have someone with a Mac open a build made since 2026-10-07 once, to check that the app the compiler signs again after changing its Info.plist still opens ([[mac_plist_plan]]).
- Correct the docstrings of `gold_rates.py`, `weapon_stats.py`, `weapon_upgrades.py` and the top of `defaults.py`, which still say the values are kept in save.json, where they now live in `store/` and `weapons/`.
- Decide whether the Settings screen's Debug mode row shows the saved `DEBUG` setting or the live mode: it reads `app.debug`, so a game started with `--debug` says on while `DEBUG` in settings.json is 0.
- Remove the unused `RunLoop` import in `app_delegate.py`.
- Decide whether `release.yml` should run `tests/suite.py` instead of its own one-at-a-time test loop, add a `concurrency` group so two runs cannot overlap, and use the same Python on the Macs (3.13) as on Windows and Linux (3.12).
- Make the releaser's Prepare and tag push main before it pushes the tag, every time. `step_commit` pushes only after it commits; when VERSION and the changelog are already committed, as on a re-tag, it says there is nothing to commit and returns without pushing, while `step_tag` still pushes a tag at HEAD. On 2026-10-07 that left main a commit behind the tag of V26.10.07-1 until the test fix was pushed by hand (tunmi13productions' note in [[evaluation_fixes_plan]], item 7).
The line below is from the 2026-10-06 evaluation ([[evaluation_fixes_plan]]); its other five are finished.
- Split the longest functions into smaller ones, main in the entry script (about 243 lines) and the biggest stage methods, carefully, since timing-sensitive code is only partly covered by tests (the dev, 2026-10-06: leave it as a developer task).
- From the 2026-09-24 binary recheck: the walk never sets walkXFlag for its 0.6 seconds; (the docs lines behind the nine todo items were corrected with their fixes on 2026-09-24).
- Bring the docs and notes up to date with the code, from the 2026-09-23 rescan. game/sounds/unused holds 27 files (26 WAV and one bloopers OGG), not the 25 in CLAUDE.md and these notes or the 26 in the README. CLAUDE.md still says the game opens on the splash, where it now opens on the logo, and that only the key bindings screen is synthesised, leaving out the screen reader mode. The README layout leaves out debug.py, stage_1_test.py and ui/focus.py, and CLAUDE.md says Python 3.12 where the README says 3.12 or newer. tests/case/paths.py line 6 and a few notes still use old test_*.py names. project_tests_layout.md opens with 17 files and 270 tests, feedback_changelog.md says unrelease starts at 0, and a finished line below says findings are listed in the todo list's unfinished section.
- Update the outdated code comment about the zig-zag walks. (The README half was done on 2026-09-23, and the run loop's header about the timers on 2026-09-24.)
- Add a log file and a crash.txt beside the save, so a failed start can be diagnosed.
- Add an exit after option and a game data line to the log, so the compiler's test build can come back.
- A wrong game folder silently falls back to the default one, sounds past slot 122 are dropped without a log line, a few OpenAL calls have the wrong return type, and OpenAL is never closed on exit.
- Update GAME_STRUCTURE.md and the tests where they describe misreadings of the original as reproduced, such as the boss check.

## Finished

- README.md's Tests section gives the right number of test scripts, 36 since `d580fe2`, and `release.py`'s `test_the_readme_counts_and_lists_every_test` checks that number and the list of files against `tests/case/`, so a new test cannot be left out again (the dev's idea); confirmed by the dev on 2026-10-14.
- The code left from the publisher's ranking server is gone: the rank (`NOWRANK`, `RankLabel` and the panel's unreachable row 9) and the week's best score (`TOPSCOREWEEK`, and `WEEKTIME` with `intro._expire_week`), along with `STAGE` and `REVIEWCOUNT`, all five retired from save.json; confirmed by the dev on 2026-10-07, whose save.json held three keys after a start ([[unused_save_keys_plan]]).
- The Mac app's Info.plist carries the release's version and `LSMinimumSystemVersion` 11.0, written by `compiler.finish_app_plist` after the build and signed again by `sign_app`; read from both Mac archives of test run 37711352768 and confirmed by the dev on 2026-10-07 ([[mac_plist_plan]]).
The five lines below are the 2026-10-06 evaluation's groups 2, 3, 8, 9 and 10, confirmed by the dev on 2026-10-07 after checking their commits in the git log ([[evaluation_fixes_plan]]).
- The level chooser, tutorial chooser and headshot tester keep off the real save on Linux and macOS too, through one shared helper, `tests/interact/_own_save.py`, and spell the game's name right (`e7eaf2c`).
- The code and comments left from voice over are gone, the headshot beep sound is defined once, and the docstrings no longer describe the recordings or Windows only (`2d8c484`).
- Tests cover the weapon upgrade cap, a level above the cap in the save, the test range playing with upgraded stats, and the settings going to settings.json; a level above the cap now counts only up to it (`735bf10`, `d2a7c21`).
- README.md no longer describes voice over, coins, the old gold rates, the old menu rows or the old tests as current (`893508b`).
- CLAUDE.md, MEMORY.md and the tests layout note have the right sound and SoundList counts, names, paths and tools (`b8f17dc`).
- The release workflow runs every test before it builds and has a pinned PyInstaller, proved by V26.10.07-1 on 2026-10-07: all four systems built, the tests ran on GitHub's Linux and macOS runners for the first time, and the release published with its four archives. The first tagged run did find a test that assumed Windows, as the plan expected, and failed three builds rather than publishing a bad release ([[evaluation_fixes_plan]], item 7).
- The release workflow's test step passes on Linux and macOS: `music_memory.py` reads the process's private memory through `psapi`, so it now says it is skipped and passes off Windows instead of failing three of the four builds, and the new `music_buffer.py` checks the same music buffer freeing on every system through OpenAL's `alIsBuffer`.
- `tests/suite.py` runs the whole suite at once, each file its own process, eight at a time and the slowest first, rerunning a failing file on its own to tell a timing-sensitive test from a broken one, and writing every result to a gitignored `tests/results/results-<date>-<n>.txt`. 637 of 637 in 85.8 s, against 286.9 s one after another ([[test_suite_plan]]).
- The run loop runs each timed event once, runs everything due in time order, timers and delayed calls alike, and keeps time to well under a millisecond.
- The tests are silent wherever they are run from: nothing reaches the screen reader or a Windows voice, no sound plays and no window opens, and a test fails if one file is left out.
- The debug keys shown in the game window include F7, and a test checks that every debug key is listed.
- The tests never touch the real save. Each test file sends the save to a throwaway folder first, and a test fails if one does not.
- The full test suite passes after the second sound sort, 309 of 309, and no test logs a missing sound.
- In debug mode, starting a game from the menu or restarting from the panel needs no coin and spends none.
- A tutorial tester in tests/interact/tutorial_chooser.py starts the tutorial at any lesson, with the Start ending or the Tutorial button's, and voice over on or off. It asks when opened on its own, and plays on its own save so yours is never touched.
- The tutorial can be finished in debug mode. Killing its zombies still counts for nothing, but each kill now finishes its lesson as it should.
- In debug mode F2 now goes to the next section of the corridor, and Shift+F2 to the next level, instead of the other way round.
- In debug mode Shift+F2 waits two seconds between sections, as F2 does between levels, and says "Not while the section is changing" until it is ready.
- In debug mode Tab goes through every weapon, bought or not, and no gun or grenade ever runs out.
- In debug mode F7 lets zombies that reach you hit you as in a normal game, still without taking a heart, and F7 again has them die on you.
- In debug mode F2 goes back to level 1 after level 8, and Shift+F2 says "Not while the section is changing" while a level is changing.
- Starting the game with --debug gives a debug mode, and each stage says "Debug mode" as it starts. A zombie that reaches you dies on the spot, heard only by its death, so you cannot die.
- In debug mode your kills and headshots do not count, so a run earns no score and no gold. The girl still thanks you when she reaches you, but gives you no heart.
- In debug mode F2 goes to the next section of the corridor, Shift+F2 goes to the next level, F5 spawns a zombie in the lane you last attacked, and Shift+F5 chooses what F5 spawns.
- In debug mode F6 holds the zombies in place, and F11 says where they are. The key bindings screen lists the debug keys and can rebind them, but only in debug mode.
- tools/README.md says the addresses are memory addresses, and how to find them in the file, instead of calling them file offsets.
- A level tester in tests/interact/level_chooser.py starts the game at any level, in the cave, the forest or the rain, and near the boss if you like. It asks when opened on its own, and plays on its own save so yours is never touched.
- A test checks that zombie sounds really move, by reading each zombie's sound back from OpenAL itself.
- The compiler builds a working game. A console build starts and plays, and its release zip opens and holds all 643 files: the game, its data, and the licenses beside it. While it packs the zip, the compiler says so and says how far it has got, so the window is not closed too early.
- A requirements.txt lists the two packages the game needs, pygame and prismatoid, so pip install -r requirements.txt installs both.
- Every sound the game uses sits together in game/sounds/used, 329 files covering all 269 of the original's sounds, apart from the 25 in game/sounds/unused.
- The 25 sounds that are not the original's own, 11 extra copies and 14 the original never had, are kept apart in game/sounds/unused, in the same folders they came from, so the rest of game/sounds holds only the original's sounds.
- Every one of the original game's 269 sounds now has a copy in game/sounds, including the six the organized folder was missing: Game Start Button, Welcome to, game center button10, restore button, weapon_m4_fire and weapon_saw_start.
- The organized sounds are 16-bit WAV again, the format the game's sound loaders read, instead of the 24-bit the OGG conversion had left them in.
- The sounds are organized into folders in game/sounds, and every one that came from the original carries its original file name again, 323 files in all, each checked by comparing its audio with the original's.
- The compiler has been changed to build Sixth Sense. It only needs pygame, copies just the files the game reads, and leaves the original iOS executable out of the release.
- The whole port has been evaluated, and every bug and missing feature that turned up was listed in the todo list's unfinished section, most important first.
- The initial commit is credited to lbk2907 on GitHub, and every commit uses GitHub usernames instead of real names.
- The license credits tsatria03 and lbk2907.
- The private user folder and the scratchpad are kept out of the repository by the git ignore file.
- Project notes for AI-assisted work are set up in CLAUDE.md and the aidocks folder.
