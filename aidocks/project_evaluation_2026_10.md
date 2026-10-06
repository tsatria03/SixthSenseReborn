---
name: project_evaluation_2026_10
description: "The first whole-repository evaluation of SixthSenseReborn, 2026-10-06, first at d1eb337 and rechecked at dc5b7c2 after pulling tunmi13productions' 20 commits: what is stale or risky, and the five recommendations."
metadata:
  type: project
---

Evaluated at the dev's asking on 2026-10-06, read-only, at `d1eb337`. The same day the dev pulled tunmi13productions' 20 commits (`8d7420d`..`dc5b7c2`: the upgrade retune to 15% a level, the weapon order, the Settings screen with shake, pad picker and skip intro, the tutorial hints, the one-or-two shake), and every finding was rechecked at `dc5b7c2`. Tests: [[project_safe_test_run]].

**Why:** a baseline for Reborn after SixthSenseOriginal was frozen ([[project_two_repos]]), listing what the removed voice over mode ([[screen_reader_only_plan]]) and coins ([[free_games_plan]]) left behind.

**How to apply:** none of these has been acted on except the one marked fixed; each needs the dev's go-ahead. Check an item still stands before working on it, and mark it here when done.

Fixed:
- `tests/case/volume.py`'s `test_settings_json_lists_them_in_the_devs_order` failed after `46efca7` added `SHAKE`, `CONTROLLER` and `SKIPINTRO` to `defaults.SETTINGS_KEYS` without updating it. Fixed on 2026-10-06 (uncommitted at the time of writing). Lesson: a contributor runs only their own tests, so a test elsewhere that pins the same thing only fails on a full run.

Risky (checked by hand, still standing at `dc5b7c2`):
- `tests/interact/level_chooser.py`, `tutorial_chooser.py` and `headshot_tester.py` keep off the real save only by changing `APPDATA`, which `paths.save_base()` reads on Windows alone. On Linux and macOS they would play on the real save. `controller_tester.py` already uses `SIXTHSENSE_USER_DIR`, the safe way. The three copy the same `_own_save` code.
- `compiler.py` ships all of `game/sounds/unused/`, now including the old speech and `unused/bloopers/`, though CLAUDE.md says builds leave the blooper out.

Leftovers (still standing at `dc5b7c2`):
- Coins: `SixthSenseReborn.py:436` panel label "restart (costs a coin)"; `main_controller.py` keeps `SOUND_COIN_COUNT`, `SOUND_NO_COIN`, `READ_COIN_COUNT_DELAY`, a `readNumberOfCoin` cancel and the "A game costs a coin" docstring; `defaults.RETIRED_KEYS` is only `ENTITYVOLUME` and `EYEMODE`, so `COIN`, `COIN_TIMER`, `COIN_TIMER_START` and `FIREST` linger in old saves.
- Voice over: `row_sound` / `ROW_SOUND` in `blind_screen.py`, `main_controller.py`, `store.py`, `inventory.py`, `intro.py` and the new `settings_screen.py`; "self-voiced" and voice over rows in `main_controller.py`'s docstring.
- `SOUND_HEADSHOT_BEEP = 374` is still defined twice, now in `settings_screen.py` and `stage_1_e.py` (the Settings screen moved it out of `main_controller.py`).
- The macOS bundle id in `compiler.py:317` is still `org.sixthsense.port`.
- Unlike the volumes, the toggles (`VIBRATION`, `SHAKE`, `SKIPINTRO`, `CONTROLLER`, `HEADSHOTSPEECH`, `HEADSHOTBEEP`) are only written to settings.json once changed; reading a missing key gives the default, so this is a style difference, not a bug.

Stale docs (still standing at `dc5b7c2`):
- README.md, though tunmi13productions updated parts of it for the Settings screen, still describes voice over, coins, 12 and 2 gold, "six rows", "24 plain scripts" and a `tests/case/digits.py` that does not exist. `docks/readme.txt` is current.
- CLAUDE.md (14,541 characters): the SoundList count (375 entries now, 372 to 374 added) and the sound folder counts are stale.
- MEMORY.md: older SixthSense names, paths and counts in finished-project lines; [[project_tests_layout]] lists two by-ear tools of four.
- `release.yml` runs no tests before building and does not pin PyInstaller.

The five recommendations, in order: fix the three by-ear tools' saves; rewrite README.md's stale parts; clear the coin and voice over leftovers; decide whether builds ship `unused/` and the blooper; add a test job and pinned PyInstaller to the workflow, plus tests for the upgrade cap and the settings file routing.
