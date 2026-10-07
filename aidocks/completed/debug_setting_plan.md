---
name: debug_setting_plan
description: "FINISHED 2026-10-07, confirmed by the dev: a Debug mode row, first on the Settings screen, source runs only (hidden in builds), remembered as DEBUG in config/settings.json; turns on what --debug does, at once."
metadata:
  type: project
---

**Status: FINISHED 2026-10-07, confirmed by the dev: "It works."** Built the same day: `app_delegate.debug_setting_on` and `set_debug` (with `on_debug_change`, which the frame loop sets to retitle the window), `DEBUG_ROW` first in `settings_screen.py` with `rows()` leaving it out when `paths.FROZEN`, `DEBUG` first in `SETTINGS_KEYS` and in `SETTING_DEFAULTS`, skipped by `fill_settings` in a build. Two new tests in `settings_menu.py`, and the walk test there now passes Debug mode on its way down. settings_menu, volume, save, window, menu, input, controller and paths pass 208 of 208.

**The dev's idea:** "I wish there was a keyboard key to enable/disable debug mode, without typing python SixthSenseReborn.py --debug ... this will only work in source form."  Offered a key (Ctrl+F12 was Claude's suggestion, F3, F4, F9, F10 and F12 being free), the dev had a better one: "What about in the settings screen, it says debug mode, on or off?"  Then: "I want it to be remembered. Also it should be the first setting in the screen."

## The plan
- **A "Debug mode" toggle**, the first row after Back on the Settings screen, reading "currently on" or "currently off" like the others; the rows below move down one.
- **Source runs only.** In a built game (`paths.FROZEN`) the row is not there at all, rather than reading "not supported", since debug mode is a developer tool players never see, and the setting is ignored and never written.
- **Remembered:** `DEBUG`, '1' or '0', in `config/settings.json`, first in `SETTINGS_KEYS` as it is first on the screen, written '0' on a first start from source.
- **What it switches** is what `--debug` sets: `app.debug` and `KeyMap.shared().debug`, at once, so the debug keys work and the F1 screen lists them straight away; the window title follows ("Sixth Sense Reborn (debug)").  The Settings screen is reached only from the main menu, so no game is ever half in debug mode.
- **`--debug` still works** for one run without saving; the row reads whatever is on.
- Tests in `settings_menu.py`; the settings order test in `volume.py`; a changelog line is not needed, since players never see it; the README's debug paragraph and CLAUDE.md's `--debug` line mention the row.
