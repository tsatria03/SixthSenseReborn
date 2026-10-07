# CLAUDE.md

This file guides Claude Code when it works in this repository. **It is a lean dispatcher.** It says what the project is and how it is laid out, then points to focused memory files (`[[name]]`) for the detail. When you start work in an area, read its linked memory first.

**Memory location:** all memory files (the `[[name]]` links and the `MEMORY.md` index) live in the repo's **`aidocks/`** folder, as `aidocks/<name>.md`; a finished project lives in **`aidocks/completed/`** under its name without the `project_` prefix, as `aidocks/completed/<name>.md` ([[feedback_completed_projects]]). Read memory from there and write new or updated memory there, never to the `~/.claude` memory store. `aidocks/MEMORY.md` is the index, so add a one-line pointer there for every new memory. Keep this file under 40,000 characters and move detail into memory ([[feedback_memory_in_aidocks]]).

## This repository: SixthSenseReborn (read first)

**This is Sixth Sense Reborn, where changes need not be faithful to the original** ([[project_reborn]]). The faithful port is the separate repository SixthSenseOriginal; this one was its `custom` branch until 2026-10-04, when it moved here with its full history. Since 2026-10-05 SixthSenseOriginal is frozen and all work happens here; read it only as a reference ([[project_two_repos]]).

- **Fidelity is not the goal here.** Do what the dev asks, even when the original did otherwise.
- **Compare, then follow the dev.** When a change is proposed, say briefly what the original did (and the binary address when it matters) and the likely better solution or difference, then do what the dev picks. Never refuse or argue for a change because it departs from the original.
- **Where this file says the port matches the original, that is how SixthSenseOriginal works.** Here it describes the starting point. `DIVERGENCES.md`, `PORTING_STATUS.md`, the first evaluation note and the side-by-side rule stayed in SixthSenseOriginal; use the changelog and the plan note for a feature.
- **Its own name:** players see Sixth Sense Reborn; the entry script is `SixthSenseReborn.py`, the executable `SixthSenseReborn.exe`, and the save is in its own `SixthSenseReborn` folder, which copies a Sixth Sense save once on the first start ([[reborn_identity_plan]]). SixthSenseOriginal keeps the plain `SixthSense` names.
- **Direction:** all game speech goes through the screen reader and the recordings are gone from play; the self-voiced mode and its main menu row were removed on 2026-10-05 ([[screen_reader_only_plan]]). See the todo list.
- Everything else still applies: Python only, the dev runs and builds, safe silent tests, NVDA-friendly output and the commit rules.

## What this is

**Sixth Sense Reborn**, grown from a Windows, Linux and macOS port of **Sixth Sense** (`kr.co.bitbee.sixsense` 1.2), a 2013 iPhone audio-only zombie shooter for blind players. You walk down a dark corridor and shoot what you hear coming, in five lanes laid out like a clock face.

There is no source code for the original. The port is **recovered from the ARMv7 binary** and rewritten method by method **entirely in Python**. **lbk2907 created it**, including the binary extraction, and handed it to tsatria03 to publish and develop together; the "Initial commit" is entirely their work ([[project_provenance]]). Each Python module mirrors one Objective-C class and cites the binary address it came from ([[project_python_only]]).

The game plays the original's own recorded WAVs, which `SoundList.plist` names by number in the original's 371 entries (0 to 370), plus the port's four, 371 to 374 (the bosses' being-hurt sound, the two controller sounds and the headshot beep). Since 2026-10-05 the game plays none of its recorded speech: the menus, the shop, the inventory, the opening screen, the tutorial and the result panel are spoken, with the weapon's name when you change weapon ([[screen_reader_only_plan]], which supersedes [[screen_reader_mode]]), and the recordings it no longer plays are in `game/sounds/unused/speech/`. All of it goes through NVDA, another screen reader via Prism, or a system voice ([[prism_speech]]).

## Layout

- **`SixthSenseReborn.py`**: the entry point and screen loop (stands in for `UINavigationController`).
- **`sixthsense/game/`**: one module per original class. `stage_1_e.py` is the core loop; the others include `monster_control.py`, `weapon_control.py`, `main_controller.py` (the menu), `stage_tutorial.py`, `stage_1_test.py` (the weapon test range behind the shop's Try button, [[project_test_range]]), `debug.py` (the `--debug` keys), `store.py`, `inventory.py`, `intro.py`, `app_delegate.py` and `oal_playback.py`, and the port's own `settings_screen.py`, `weapon_stats.py`, `weapon_upgrades.py`, `weapon_order.py` and `gold_rates.py`.
- **`sixthsense/platform/`**:
  - `openal.py`: a ctypes binding to OpenAL Soft, with HRTF off.
  - `runloop.py`: stands in for `NSTimer` and `performSelector:afterDelay:`.
  - `defaults.py`: stands in for `NSUserDefaults`, as short files in folders ([[save_folders_plan]]).
  - `speech.py`, `keymap.py`, `music.py` and `volume.py` (the decibel knobs, [[project_volume_knobs]]), with `sound_trims.py`, `sound_position.py`, `motion.py` (a pad's motion sensor) and `controller_names.py`.
- **`sixthsense/ui/`**: the keyboard input for the stage, the menus and the screens, plus the F1 key-bindings screen, and the game controller (`controller.py`, `vibration.py`, `shake.py`).
- **`game/`**: the original app bundle's data: the plists, the maps, the images and the iOS binary. Every sound the game uses lives in `game/sounds/used/`, in folders, a deliberate divergence. Since the dev's third sort (2026-09-25), the zombies, bosses, monster and characters have one folder each, `used/` holds only what the game plays (103 files, counted 2026-10-06), `game/sounds/unused/` the 191 it never plays (145 retired speech recordings in `speech/`, and in `sfx/` the original's sounds for left-out features and unspawned zombies, extra copies and the non-original WAVs), and the repo's `bloopers/` folder the blooper clip (moved there on 2026-10-06), which builds leave out. Most keep their original file name; sounds the dev found misnamed are renamed (the "woman" monster is a man, shared zombie sounds are named for one zombie), and `SoundList.plist` follows them, with four entries added, 371 to 374: the only changes to the original's plists ([[sound_rename_plan]]). `paths.path_for_resource` looks in the top folder first, then by file name under `game/sounds/used/`, and last under `game/sounds/unused/`, so a name in `used/` always wins; builds carry only `used/` since 2026-10-06, the dev's rule, while running from source still searches both ([[project_sound_organization]]). Don't move, rename, convert or delete sound files unless the dev asks.
- **`analysis/`**:
  - `bin/sixsense_armv7`: the binary itself.
  - `disasm/dc_*.txt`: per-class decompiled listings.
  - `digest/dg_*.txt`: condensed call summaries.
  - `data/objc_classes.json`.
- **`tools/`**: the Mach-O and disassembly tools that produced `analysis/`. `dz.py` and `dc.py` need `capstone`.
- **`aidocks/`** also holds `GAME_STRUCTURE.md`, the developer reference for how the original works, beside the memory notes.
- **`docks/`**: the documents a player reads, which the build puts in a `docks` folder beside the executable, laid out as here: `readme.txt` (plain text for players, kept in step with what it describes, [[player_readme_plan]]), `changelog.txt` and `todo list.txt`.
- **`tests/`** ([[project_tests_layout]]): `tests/case/` holds the tests, plain scripts, each with its own runner. **They keep off the real save and are silent by themselves**: each imports `_scratch_save`, which sets `SIXTHSENSE_USER_DIR` to a throwaway folder, `SIXTHSENSE_SILENT` so nothing reaches the screen reader, and the null audio and dummy video drivers; `paths.py` fails if one does not. Testing must speak nothing whatsoever; read [[project_safe_test_run]] before running any. **`tests/suite.py` runs the whole suite**, each file its own process, eight at a time and the slowest first, writing every result to a gitignored `tests/results/results-<date>-<n>.txt` and exiting 1 on a failure, in about 85 s against 290 ([[test_suite_plan]]). `tests/interact/` holds four tools played by ear. `tests/interact/level_chooser.py` is not a test: it starts the real game at any level, area and row, on its own save in `%APPDATA%\SixthSenseReborn\level_chooser`, for checking by ear. `tests/interact/tutorial_chooser.py`, likewise not a test, does the same for the tutorial: any lesson, either ending, on its own save in `%APPDATA%\SixthSenseReborn\tutorial_chooser` ([[tutorial_tester_plan]]). `tests/interact/controller_tester.py`, the third, speaks what a game controller does: each button, stick direction and trigger, the menu key a button stands for, vibration on keys 1 to 5 and a checklist of the controls not yet used; it touches no save ([[joystick_plan]]). `tests/interact/headshot_tester.py` plays a real game where every gun hit is a headshot, asking first whether the spoken headshot and the beep are on, on its own save in `%APPDATA%\SixthSenseReborn\headshot_tester`.
- **`vendor/`**: `soft_oal.dll` and `nvdaControllerClient64.dll` (x64), and `libopenal.so.1` for Linux ([[linux_build_plan]]).
- **`compiler.py`**: the PyInstaller build script. Run it with no flags for a menu; it builds `dist\SixthSenseReborn-Windows` (around `SixthSenseReborn.exe`; the release zip extracts to that folder too), a folder build or with `--embed` one exe holding the sounds and data, and never zips or changes the repository ([[project_compiler_py]]). Run on Linux (the dev builds in WSL) it builds `dist/SixthSenseReborn-Linux` around `SixthSenseReborn` instead, from its `SYSTEMS` table ([[linux_build_plan]]).
- **`releaser.py`**: sets the date version, files the changelog, runs the compiler, zips the build, commits, tags `V<version>` and uploads the zip to GitHub through `gh` ([[release_tooling_plan]]). Its "Prepare and tag" option only files, commits and tags; the tag starts `.github/workflows/release.yml`, which builds Windows, Linux and both Macs and publishes the release ([[release_workflow_plan]]). Built and confirmed working by the dev on 2026-09-23. Since 2026-09-28 one release carries the Windows zip and the Linux .tar.gz: the full release on one system, then "Add this system's build to the release" on the other ([[linux_release_plan]]).
- **`bloopers/`**: short clips of funny bugs, kept for fun and preferably under two minutes. Its README sets the naming and format rules. The build leaves it out; only add clips the dev provides.
- **`New File.txt`** at the root is the dev's private scratchpad. It is gitignored; never read, edit, flag or delete it.
- **`user/`** is gitignored private reference material. Read it, but never edit it. Never name the dev's other games that are kept in it, in the todo list, memory, or code and comments ([[feedback_no_other_games]]). The dev's old NVGT remake of this game used to be there; it was deleted on 2026-09-21 ([[project_nvgt_remake_reference]]).

The save lives in `%APPDATA%\SixthSenseReborn\` (on Linux `~/.local/share/SixthSenseReborn/`, on macOS `~/Library/Application Support/SixthSenseReborn/`), copied once from SixthSenseOriginal's on the first start. Since 2026-10-06 it is short files in folders, the dev's layout ([[save_folders_plan]]): `saves/save.json` (progress), `config/settings.json` (`defaults.SETTINGS_KEYS`) and `config/keys.json`, `store/shop.json` and `store/inventory.json` (lowercase, weapons as lists of names) and `weapons/<name>.json` (short names). The game still asks for the original's key names; `defaults.py` routes and translates. An older flat `save.json`, `settings.json` or `defaults.json` is moved in on the first start and kept as `.old` ([[save_split_plan]]).

## Running and building

**The dev runs and builds, not Claude.** Never build unless told to. The tests may be run without asking, always the safe way ([[project_safe_test_run]]), but only the scripts that cover the Python files changed; the full suite runs only when the dev asks ([[feedback_dont_run_or_build]]). Ask before running the game, `compiler.py`, or anything else that executes game code or speaks ([[feedback_dont_run_or_build]]).

`python SixthSenseReborn.py` plays the publisher's logo, then the opening screen, then the menu. Flags:
- `--no-intro` opens straight on the menu.
- `--stage` and `--tutorial` start those directly.
- `--skip-tutorial` writes `TUTORIAL=1`.
- `--no-window` runs headless.
- `--debug`, or the Settings screen's first row, Debug mode (source runs only, remembered as `DEBUG` in settings.json, [[debug_setting_plan]]): a zombie that reaches you just dies, nothing takes a heart, and no kill, headshot, score or gold counts. Tab reaches every weapon and nothing runs out. It adds F2, Shift+F2, F3 and F4 (zombie health and speed held at level 1's, [[debug_level_toggles_plan]]), F5, Shift+F5, F6, F7, F8 (the sound trims off and on, [[sound_trims_plan]]) and F11 (`game/debug.py`), which the F1 screen lists only in debug mode.
- `-v` gives verbose logging.

This needs 64-bit Python 3.12 or newer, pygame and `prismatoid` (Prism). Without Prism the game still runs, but only NVDA speaks ([[prism_speech]]). `pip install -r requirements.txt` installs both.

## Working with the binary

- The binary is a reference, not a rule here. Cite the address when a comment leans on it.
- Before relying on anything that hinges on one branch or constant, check the raw bytes. The decompiled listings mislead in known ways, and addresses are VM addresses, so file offset = address - 0x1000 ([[project_binary_analysis_notes]]).
- Several tests assert current behavior, including some misreadings. Changing that behavior means updating its test in the same change.

## Where the detail lives

- **macOS runtime** (11+, universal OpenAL, Prism speech and Application Support saves): [[project_macos_runtime_plan]]. **Native-architecture app builds** and console debugging builds: [[project_macos_build_plan]].

- **Reading the binary correctly**: [[project_binary_analysis_notes]].
- **The screen reader** (the game's only voice since 2026-10-05; the voice over row is gone): [[screen_reader_only_plan]]; the original design is [[screen_reader_mode]].
- **Running the tests safely**, once the dev says yes: [[project_safe_test_run]].
- **Adapting the build script**: [[project_compiler_py]].
- **The task list** (`docks/todo list.txt`) and how to write in it: [[feedback_todo_list_format]]. It holds only what a player notices, since it ships beside the game; developer tasks, open and finished, are in [[project_dev_tasks]].
- **The changelog** (`docks/changelog.txt`): every player-facing fix or enhancement adds a line at the top of the `unrelease:` block in the same commit, newest first ([[feedback_changelog]]).
- **Plans**: an agreed plan goes into its own aidocks note before any code, and is marked finished there only once the dev says it works; a finished project then moves to `aidocks/completed/` without its `project_` prefix ([[feedback_record_plans_first]], [[feedback_completed_projects]]).
- **Committing and pushing** (commit only when asked; "commit" means commit only and "commit/push" means both; history rewrites need a go-ahead): [[feedback_git_commits]].
- **Who made what, the permission to publish, and how to credit contributors in commits**: [[project_provenance]]. Name people by GitHub username only: [[feedback_use_github_usernames]].
- **Who you're working with**: [[user_screen_reader]]. The dev uses NVDA, so prefer lists and short lines, and never make noise from tools.

`CLAUDE.md` and `aidocks/` are committed, not gitignored.
