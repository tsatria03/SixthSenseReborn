---
name: project_dev_tasks
description: "The developer-side task list: work on the repository, the tools, the tests, the build and the docs that a player never sees. Moved out of todo list.txt on 2026-09-23, when that file became players only. Open tasks first, then finished ones, newest first."
metadata:
  type: project
---

Since 2026-09-23, `todo list.txt` holds only what a player notices ([[feedback_todo_list_format]]). Everything else that needs doing, or has been done, lives here, in the same style: one plain sentence per line, newest first. The technical detail behind each line is in SixthSenseOriginal's `project_evaluation_2026_09` note.

**How to apply:** a new developer task goes at the top of Open. When it lands and the dev confirms, it moves to the top of Finished. A task that changes what a player hears or sees belongs in `todo list.txt` instead, and in `changelog.txt` once it is done ([[feedback_changelog]]). **Debug mode is developer-facing** (the dev, 2026-09-23: players will not know it exists), so its lines live here and never go in `todo list.txt` or `changelog.txt`. The four oldest debug lines below came from the changelog, which had them in more detail than the todo list.

## Open

One of the lines below is built in [[rescan_fixes_plan]] (group 7) and waits for a workflow test run; the rest of that plan's twenty are finished.
- Have someone with a Mac open a build made since 2026-10-07 once, to check that the app the compiler signs again after changing its Info.plist still opens ([[mac_plist_plan]]).
- Decide whether `release.yml` should run `tests/suite.py` instead of its own one-at-a-time test loop, add a `concurrency` group so two runs cannot overlap, and use the same Python on the Macs (3.13) as on Windows and Linux (3.12). (Built 2026-10-14, group 7: the suite with `--rerun-decides`, a concurrency group that waits, and 3.13 kept on the Macs with a comment; waiting for a workflow test run.)
The line below is from the 2026-10-06 evaluation ([[evaluation_fixes_plan]]); its other five are finished.
- Split the longest functions into smaller ones, main in the entry script (about 243 lines) and the biggest stage methods, carefully, since timing-sensitive code is only partly covered by tests (the dev, 2026-10-06: leave it as a developer task).

## Finished

- A wrong `--game` folder stops the game and says which folder, a sound past the last slot is logged once, the three ALCboolean calls read one byte, a failed context closes its device, and OpenAL is closed however the game ends; tested silently on 2026-10-14 at the dev's request, which the dev accepted ([[rescan_fixes_plan]], group 9).
- The game keeps a log of each run in `logs/log.txt` in the save folder, the run before as `log.old.txt`, and `crash.txt` when an error stops it; confirmed by the dev on 2026-10-14, whose real logs folder held both logs, each naming the game data ([[rescan_fixes_plan]], group 10).
The six lines below are groups 1, 2, 4, 6, 8 and 12 of [[rescan_fixes_plan]], confirmed by the dev on 2026-10-14 ("I'm happy with these"), newest group first.
- GAME_STRUCTURE.md says the original never sets the listener, so its pan table and basis are the port's, and that `Stage_1_E` carries its own copy of the tutorial; the boss check it once described as reproduced was fixed long before (`f2a1e96`).
- The walk holds the next step back for 0.6 s as the original does (0x31f7a), and a pause cancels the step's pending let-go.
- The releaser's Prepare and tag pushes the branch before the tag, every time, and makes no tag when that push fails.
- The unused names are gone (`SOUND_NOW_LOADING`, `SOUND_PAUSED`, `SOUND_CONTINUE`, `OLD_KEPT`, the `RunLoop` import in `app_delegate.py`, `paths.BINARY`, `paths.set_resources`, `runloop.main_loop`), `SWIPE_BANDS` stays as the record of the original's bands, and the comments on the shop's WAVs, the save.json docstrings and the zig-zag walks are right.
- The notes left from the 2026-09-23 rescan are up to date: the tests layout's 36 files, the safe test run note's past tense and the latest full run; the rest of that rescan's docs task was already done.
- Every aidocks path in the repository names the dev's 2026-10-14 layout, `aidocks/general/` or `aidocks/plans/`: 160 paths in 55 files, `MEMORY.md`'s 40 plan links, the memory rules in `CLAUDE.md` and three feedback notes, and the nine mentions of `DIVERGENCES.md` in finished plans, which now name SixthSenseOriginal.
- The Settings screen's Debug mode row shows the live mode and says when `--debug` is the reason: "Debug mode, currently on, from --debug." while settings.json says off; confirmed by the dev on 2026-10-14 ([[rescan_fixes_plan]], group 5).
- The game window shows the Settings rows in the screen reader's own words, state included, instead of an old list of names in the wrong order; confirmed by the dev on 2026-10-14 ([[rescan_fixes_plan]], group 3).
- The compiler's test build is back: the game takes `--exit-after SECONDS` and logs its game data, and `compiler.py --test`, menu choice 2, starts a finished build for six seconds, silently on a throwaway save, and reads its log; confirmed by the dev on 2026-10-14 with a real Windows folder build, which started, found its game data and quit by itself ([[rescan_fixes_plan]], group 11).
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
