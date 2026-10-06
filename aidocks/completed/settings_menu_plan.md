---
name: settings_menu_plan
description: "FINISHED 2026-10-06, confirmed by tunmi13productions: a Settings row in the main menu opens a screen holding every setting, the vibration and two headshot rows moved into it, plus a shake row and a controller picker. A row for something the attached pad cannot do stays visible and reads \"not supported\", and will not toggle. The chosen pad is saved by name, not by id, and is the only pad the game reads."
metadata:
  type: project
---

**Status: FINISHED 2026-10-06, confirmed by tunmi13productions** ("makr it finished"), and moved to `completed/` the same day. Built the same day it was agreed, recorded before any code ([[feedback_record_plans_first]]). `sixthsense/game/settings_screen.py`, the menu's one `settings` row in place of three, `AppDelegate`'s `shake_on`, `set_shake`, `controller_choice`, `set_controller_choice`, `can_shake_now`, `skip_intro_on` and `set_skip_intro`, the active pad in `ui/controller.py`, and `ui/vibration.py` and `ui/shake.py` reading it. New `tests/case/settings_menu.py` (13). Covering files passed: menu 18, window 11, shake 15, controller 31, vibration 36, tutorial 31, intro 9, save 13, focus 4, gameplay 59, input 48, paths 22, release 50.

Two commits: the screen itself, and the skip-the-opening-screens row added to it afterwards.

The ask, in tunmi13productions' words: "let's move all the rows involving settings (vibration and headshots so far) under a new row called Settings. because now I want to add a shake option for supported controllers. it'd be off by default if a controller does not have an ability. it wouldn't appear as a changeable option, it'd be hidden. not removed from the row, just invisible. that can apply with anything the controller doesn't support. you can also change the controller in this menu if you have multiple connected (be careful of sdl detecting the same controller twice). save the controler by name, as ID's are unreliable. this is because someone could disconnect the controller in ID 0, which means the next time they plug it in it'd be ID 1, not 0, because they swapped positions."

## Where things stand

The main menu is `MainController`, which is not a `BlindScreen`: it carries its own `ROWS` table of `(selectMenu, flag, sound, action)` and pushes a screen by setting `next_screen`, as `StoreAction_` does. Three of its rows are settings, all PORT ADDITIONS with no recording of their own: vibration (row 9) and the two headshot rows (10 and 11). `SETTINGS_KEYS` in `platform/defaults.py` says which keys live in settings.json; `VIBRATION`, `HEADSHOTSPEECH` and `HEADSHOTBEEP` are already there.

Shaking a pad to break free already works wherever the pad can sense it, with no setting at all ([[controller_shake_plan]]). `ui/shake.py` asks `platform/motion.py` whether each pad has an accelerometer. `ui/vibration.py` and `ui/shake.py` both reach their pads through `controllers.pads` and `controllers.pad_ids`, so what counts as "the pad" is one place.

**tunmi13productions' warning about double detection is already recorded as a real fault**: on Windows SDL lists a DualSense twice at start, the first listing being dropped once its own driver takes the pad, which crashed the game until `read_events` caught it; and pygame's `Controller.id` is the device index, not SDL's instance id, which is why `ui/controller.instance_id` exists ([[controller_shake_plan]]).

## Decided with tunmi13productions, one question at a time

- **The shake row starts on, on a pad that can sense a shake.** It already works that way, so a setting defaulting to off would quietly take it away from DualSense owners. The row is there to turn it off when a stray flick keeps triggering it. A is still the shake button whatever the setting says.
- **The chosen pad is the only pad the game reads.** Its buttons, sticks, vibration and shake are the game's, and any other attached pad is ignored. That is what makes the setting worth having when SDL double-lists a pad, or when a forgotten second pad on the desk feeds stick drift into a game. The alternative, every pad still playing and the choice only deciding who buzzes, was offered and declined.
- **One entry per name.** A pad SDL has listed twice collapses to one row, which is the fault tunmi13productions flagged. The cost, accepted: two genuinely identical pads also show as one, and the game takes whichever SDL found first. Saving by name cannot tell those two apart anyway, so this is what the save can honestly express. Numbering repeats ("Xbox Wireless Controller 2") was offered and declined.
- **A row for something the attached pad cannot do stays visible and says so.** tunmi13productions first asked for it to be hidden ("not removed from the row, just invisible"), then changed it the same day: "actually what I'd do is show the rows, but say something like vibration. not supported. so it won't let you toggle it on." So the row reads "Vibration, not supported." and pressing Enter will not turn it on; it says why instead. **This is the better call for a screen reader**: a row that disappears leaves the player counting rows and wondering what they have lost, where "not supported" answers the question on the spot. The setting keeps its saved value underneath either way, so a pad that can do it later finds the player's old choice intact.
- **What is unsupported, and why:** no pad attached at all makes vibration, shake and the picker unsupported; a pad with no motion sensor makes shake unsupported. The two headshot rows need no pad and are never unsupported.

## The Settings screen

A pushed screen, as the shop and the inventory are, so Escape goes back and the rows read themselves. Every row is always there, in this order, with the ones that need a pad last:

1. Back
2. Skip the opening screens, currently off.
3. Spoken headshot, currently on.
4. Headshot beep, currently off.
5. Vibration, currently on.
6. Shake to break free, currently on.
7. Controller, Xbox Wireless Controller.

The rows are named in the module (`BACK_ROW`, `SKIP_INTRO_ROW` and so on), so inserting one is a matter of those numbers and nowhere else. Row 2 was added on 2026-10-06, after the rest was built, at tunmi13productions' asking: "add a setting to optionally disable the splash screen and take you to the main menu". It is `SKIPINTRO`, '1' or '0', default '0', and does for good what `--no-intro` does for one run; it needs no pad, so it joins the rows that are never unsupported.

Enter on a setting flips it and says the new state, as the menu rows do now. Enter on the Controller row moves to the next attached pad and says its name.

**With nothing attached, or a pad that cannot do it**, the row says so instead of its state, and Enter says why rather than changing anything:

- **Vibration**, no pad: reads "Vibration, not supported."; Enter says "No controller is attached."
- **Shake to break free**, no pad: reads "Shake to break free, not supported."; Enter says "No controller is attached."
- **Shake to break free**, a pad with no sensor: the same row text; Enter says "This controller cannot sense a shake."
- **Controller**, no pad: reads "Controller, none attached."; Enter says "No controller is attached."
- **Controller**, one pad: reads "Controller, Xbox Wireless Controller."; Enter says "This is the only controller attached."

Turning a setting **off** is always allowed where it is supported, and an unsupported row never turns anything on, so a save can never end up claiming a pad does something it cannot.

The main menu keeps `title`, `start`, `tutorial` and `store`, and its three settings rows become one **Settings** row in their place, at row 9, which sets `next_screen = 'settings'`.

## Save keys

- `SHAKE`, '1' or '0', default '1' (on), in `SETTINGS_KEYS` beside the other toggles.
- `SKIPINTRO`, '1' or '0', default '0' (the opening screens play), also in `SETTINGS_KEYS`.
- `CONTROLLER`, the chosen pad's name as SDL reports it, or '' for "whichever is found first", also in `SETTINGS_KEYS`. **Never an id.**
- A saved name that is not attached is **left alone, not cleared**, and the game falls back to the first pad it finds, so plugging the preferred pad back in restores it without the player doing anything.

## The build

- **`sixthsense/game/settings_screen.py`**: `SettingsController(BlindScreen)` with the rows above, always all of them; `supported(row)` saying whether the attached pad can do it, `row_text` reading the state or "not supported", and `activate` saying why instead of toggling when it cannot.
- **`main_controller.py`**: the three settings rows become one `settings` row; `SettingsAction_` sets `next_screen`. Its `VibrationAction_`, `HeadshotSpeechAction_` and `HeadshotBeepAction_` move to the new screen.
- **`SixthSenseReborn.py`**: `'settings'` in the screen table, in `PUSHED`, and in `SCREEN_ROWS`/`SCREEN_TITLE`; the menu's branch pushes it as it pushes the store.
- **`AppDelegate`**: `shake_on` and `set_shake`, beside `vibration_on`; `controller_choice` and `set_controller_choice`.
- **`ui/controller.py`**: `names` (the distinct names attached, in the order found), `active_pad` and `active_pads`/`active_pad_ids` (the chosen pad, else the first found), and `feed` ignoring buttons and axes from any other pad. `pads` and `pad_ids` keep meaning every pad, so nothing else shifts under them.
- **`ui/vibration.py` and `ui/shake.py`**: read `active_pads` and `active_pad_ids`, so both follow the choice without knowing about it.
- **`ui/shake.py`**: `Shake.tick` does nothing while `SHAKE` is off, and the tutorial's shake callout ([[tutorial_controller_callouts_plan]]) only offers a shake when it is on and the pad can.
- **Tests**: a new `tests/case/settings_menu.py` (the rows, what reads "not supported" and when, that an unsupported row will not toggle on, each toggle, the picker cycling, a saved name that is absent, a pad listed twice showing once), and changes to `menu.py` (the Settings row in place of three), `shake.py` (off does nothing), `controller.py` (the active pad and the ignored others) and `tutorial.py`. **Drive the real keyboard, not just the screen's methods** — that is what let the reorder screen ship broken ([[weapon_order_plan]]).
- **Docs**: a changelog line; `docks/readme.txt` and `README.md` for the new screen, the shake setting, the picker and the two new keys.

## Not in it

- The volume knobs stay where they are, in settings.json and on Page Up and Page Down; tunmi13productions named only the vibration and headshot rows. Moving them into this screen is a separate question.
- Rumble capability is not asked of the pad: the vibration row is hidden only when no pad is attached at all. SDL can be asked whether a pad rumbles, and pygame does not expose it, so that would need another ctypes call like `platform/motion.py`.
- Nothing about the key bindings screen (F1), which is the stage's keys.
