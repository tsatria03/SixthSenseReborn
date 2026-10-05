---
name: project_reborn_identity_plan
description: "PLANNED 2026-10-04, not started: give SixthSenseReborn its own identity apart from SixthSenseOriginal: the name Sixth Sense Reborn, its own save folder (copying the old save once), SixthSenseReborn builds and releases, a kept changelog history, and the docs saying Reborn instead of the custom branch."
metadata:
  type: project
---

**Status: built, waiting on the dev's check.** Planned 2026-10-04, agreed with the dev one question at a time, and every step built the same day. Step 2, the save folder and the one-time copy (`8f81032`), was confirmed by the dev ("the save thing worked for both repos"); the entry script became `SixthSenseReborn.py` (`ad701c4`). Step 3, the builds, releases and in-game name (`a4a548b`), and step 4, the changelog's `SixthSense:` heading (a heading of its own, with one line under it, so the releaser never counts it and files new versions above it; tested in `release.py`), CLAUDE.md, the README, the player readme, `project_custom_branch` renamed `project_reborn`, and the links to SixthSenseOriginal's first evaluation made plain mentions, wait on the dev. Mark it finished, then push, once the dev says it works. Mark it finished only once the dev says it works ([[feedback_record_plans_first]]).

**Background.** SixthSenseReborn is the old `custom` branch of SixthSenseOriginal, moved here with its full history on 2026-10-04 (237 commits, no tags) and deleted there. Everything in it still carries SixthSenseOriginal's identity, so the two games would overwrite each other's save and publish look-alike downloads.

## The dev's decisions (2026-10-04)
1. **The name players see is "Sixth Sense Reborn".**
2. **Its own save folder, `SixthSenseReborn`, which copies an existing Sixth Sense save once on the first start.**
3. **The executable and builds use the new name:** `SixthSenseReborn.exe` (`SixthSenseReborn` on Linux and macOS).
4. **The changelog keeps the 8 released Sixth Sense sections,** under a heading that says they are from Sixth Sense before Reborn. Reborn's own releases go above them, and its version numbering restarts.

## What changes
- **Save folder** (`sixthsense/paths.py` `user_dir`): `%APPDATA%\SixthSenseReborn`, `~/.local/share/SixthSenseReborn`, `~/Library/Application Support/SixthSenseReborn`. Comments and docstrings that name the folder (`paths.py`, `platform/defaults.py`, `platform/keymap.py`, `tests/case/_scratch_save.py`) follow.
- **Copying the old save once:** when the Reborn folder does not exist yet, take the first of `SixthSenseOriginal` and `SixthSense` that exists (SixthSenseOriginal renames its save folder to its own name on its first start from 2026-10-04, its `project_save_folder_rename_plan.md`; a player who has not run that update still has `SixthSense`), and copy its `save.json`, `settings.json` and `keys.json` (and an unsplit `defaults.json`, which the save split then moves over) into the new folder, before anything reads the save. Never write to, move or delete the old folder; never copy the choosers' subfolders. Once the Reborn folder exists, never copy again. A failed copy logs and starts fresh rather than stopping the game.
- **The level and tutorial choosers** (`tests/interact/`) take their copies from, and keep their own saves under, the Reborn folder.
- **Builds** (`compiler.py` `NAME`): `SixthSenseReborn.exe`, `dist\SixthSenseReborn-Windows`, `-Linux`, `-macOS` (`SixthSenseReborn.app`); docstrings follow.
- **Releases** (`releaser.py`): titles "SixthSenseReborn V<version>", archives `SixthSenseReborn-Win-<version>.zip` and `SixthSenseReborn-Linux-<version>.tar.gz`. Tags stay `V<version>`; this repository has none yet, so the first release is that day's `-1`. `VERSION` is rewritten by the releaser, so it needs no hand reset.
- **The changelog** (`docks/changelog.txt`): a heading line above `26.09.28-2:` saying the sections below are Sixth Sense's, before Reborn. Check that the releaser's entry counting and filing still work with it (it files only the `unrelease:` block).
- **In the game:** the window title "Sixth Sense Reborn" (and "(debug)"); the menu title the screen reader speaks, "Sixth Sense: The Zombies", becomes "Sixth Sense Reborn: The Zombies". The recordings that say "Sixth Sense" stay; they go with the recordings later.
- **The entry script is `SixthSenseReborn.py`** (renamed from `SixthSense.py` at the dev's word on 2026-10-04; `compiler.ENTRY`, `tests/case/window.py` and the choosers follow). SixthSenseOriginal keeps `SixthSense.py`: it was renamed there too the same day, then put back at the dev's word, so the plain name marks the original port. **Other code names stay:** the `sixthsense` package and the `SIXTHSENSE_*` variables keep their names (the branch's Seventh Sense rename of them was undone on purpose).
- **Tests** that pin the old names change in the same change: `paths.py`, `save.py`, `weapon_stats.py`, `release.py` and `menu.py`, plus new tests for the one-time copy (copies when only the old folder exists, never touches the old folder, does nothing the second time or when there is no old save).
- **Docs:** CLAUDE.md's "This branch: custom" section becomes "This repository: SixthSenseReborn", the save and build names in CLAUDE.md, README.md and `docks/readme.txt` follow, `project_custom_branch.md` becomes a Reborn note, and the links to the four notes that were never carried over (`DIVERGENCES.md`, `PORTING_STATUS.md`, `project_evaluation_2026_09`, `feedback_side_by_side`) are fixed. The changelog gets one line for players: the new name, and the save copied over from Sixth Sense.

## Order
1. This note, committed on its own, not pushed until the whole plan is built and tested.
2. The save folder and the one-time copy, with tests.
3. Builds, releases and the in-game name, with their tests.
4. The changelog heading and line, and the docs.
5. Run only the test files covering the changed Python files ([[project_safe_test_run]]); the dev builds and checks by ear.
