---
name: project_joystick_plan
description: "FINISHED 2026-10-04. Controller support for Sixth Sense Reborn through SDL's game controller layer (pygame._sdl2.controller), cross platform, never XInput: the menus, the stage (stick aims, D-pad, buttons), connect and disconnect sounds and a pause on losing the pad, per-zombie vibration, and a vibration menu row. The dev uses an Xbox One pad."
metadata:
  type: project
---

**Status: FINISHED 2026-10-04, confirmed by the dev** ("I think we have controller support finished"). Built in nine commits' worth of steps: the menus, the stage (stick, D-pad, buttons), the found and lost sounds with the pause on losing the pad, the vibrations, and the menu row. Phase 1 is `sixthsense/ui/controller.py` (`Controllers.feed`, used by the frame loop in `SixthSenseReborn.py`) and `tests/case/controller.py`. It translates only while no stage and no bindings screen is up. The todo list's joystick lines stay in Unfinished until the dev confirms it works ([[feedback_todo_list_format]]).

## Decisions
- **SDL's game controller layer, never XInput** (the dev, 2026-10-04: there is a Linux build, and a macOS one, so XInput is a bad idea). pygame 2.6.1 wraps it as `pygame._sdl2.controller`: `CONTROLLERBUTTONDOWN/UP`, `CONTROLLERAXISMOTION`, `CONTROLLERDEVICEADDED/REMOVED`, the standard `CONTROLLER_BUTTON_*` and `CONTROLLER_AXIS_*` names, and `Controller.rumble`. Checked present on 2026-10-04.
- **No raw `pygame.joystick` button numbers.** The same pad numbers its buttons and D-pad differently on Windows and Linux. SDL's standard layout hides that.
- **The module name starts with an underscore.** It has been stable across pygame 2.x, but it is semi-private; check it again when the pygame pin moves.
- **The dev's pad:** an Xbox One controller. Only the dev can judge how it feels; tests feed fake events.
- **Fixed mappings first.** Rebinding on the F1 screen is a separate, larger job, left out.

## Phase 1: the menus
- A translation layer in the frame loop turns controller events into the keyboard events the screens already take, so no screen changes.
- D-pad and left stick: Up, Down, and Left and Right where the screen reader mode uses them. A is Enter, B is Escape.
- Hot plug in and out, and a dead zone on the stick.
- Its own commit.

## The tester
- `tests/interact/controller_tester.py` (2026-10-04), played by ear like the two choosers: it speaks each button, stick direction and trigger, says what the menus take a button as, buzzes the motors on keys 1 to 5, and keeps a checklist of the 25 controls (15 buttons, 8 stick directions, 2 triggers) on C. It uses the same `Controllers` as the menus and touches no save. Smoke-tested with made-up events only; not yet tried with the Xbox One pad.

## Phase 2: the stage (chosen 2026-10-04, building)
- **The left stick aims, like the swipe.** Its angle goes through the stage's own `_lane_for_angle`, so up is 12, left 9, right 3, the diagonals 10:30 and 1:30, and down is the reload sector. One lean is one shot, locked to the lane it settled on; going back toward the middle and leaning again is the next shot.
- **The diagonal problem:** the two axes arrive as separate events, so a push toward 10:30 first looks like 9 o'clock. A lean waits `AIM_SETTLE` (60 ms) before it fires, from the `pump` the frame loop already calls, and a flick that is released first fires at its peak. This is the stick's version of the keyboard's chord window.
- **Held fire:** the MG80 keeps firing down the locked lane while the stick stays leaned, and stops when it returns to the middle. Every other weapon is one shot per lean.
- **Buttons:** X reload, right bumper next weapon, left bumper previous weapon, A shake (a zombie has grabbed you), B and Start pause and resume, as Escape does.
- **The pause and result panels** take the menu keys: D-pad or stick, A selects, B resumes.
- **The D-pad in play is the arrow keys' clock face** (the dev's idea, 2026-10-04): left 9, left and up 10:30, up 12, right and up 1:30, right 3, down reload. Left, up and right wait out the keyboard's `CHORD_WINDOW` in case a second direction joins them; down and the diagonals fire at once; a tap let go early still fires; left with right, or up with down, do nothing. The MG80 keeps firing while it is held. It is `DPAD_LANES` in `input.py`.
- **Left out for now:** the right stick and the triggers are unused, and there is no vibration in play yet. The tester's checklist still lists them.

## Sounds for finding and losing a pad (2026-10-04, the dev)
- `ctrl_detected.wav` and `ctrl_not_detected.wav` are in `game/sounds/used/sfx/misc/`, entries 372 and 373 of `SoundList.plist` (the original's 371, the bosses' 371, then these two).
- Found: 372 plays and the pad buzzes `CONNECT_BUZZ` (a short 200 ms). Lost: 373 plays. Nothing plays when no pad is found, when a device is not a controller, or for a removal of a pad that was never open.
- The pads attached at start are announced once the sounds can play (`announce_attached`); SDL's own start-up add events for them are ignored by instance id, so none is announced twice.
- `Controllers` takes the controller module as `sdl`, so the tests pass a stand-in and never open or buzz a real pad. The dev's Xbox pad is attached to the dev machine, and an early test run did open it.
- Not trimmed: the new files have no entry in `sound_trims.py`; `tools/sound_trims.py` writes MEASURED, and the dev runs it.

## Losing the pad pauses (2026-10-04, the dev)
- A pad that was open going away pauses the stage (`StopPlayAction_`), through `Controllers.just_lost`, so you can plug it back in. A removal of something never opened does not pause, a stage already paused stays so, and the tutorial, which has no pause (`ESCAPE_LEAVES`), is left running.

## Vibration (the dev's layout, 2026-10-04, built, not yet felt by the dev)
Built in `ui/vibration.py` (the effects and the player), with hooks in `MonsterControl.hitPlayer`, `_monster_killed`, `_pause` and `teardown`, `AppDelegate.vibrate_effect`/`vibrate_zombie`/`vibrate_stop` (not `vibrate`, the original's phone buzz when zombie 8 grabs you, left as it was), and tests in `tests/case/vibration.py` (22).

How it works: every blow on you goes through `MonsterControl.hitPlayer` (a zombie reaching you, or zombie 8 when you fail to shake it off), so one hook there gives every zombie its own effect, started with its hit sound; the girl's is in `_monster_killed`. An effect is a timeline of (start ms, low motor, high motor, ms), played by `ui/vibration.py` from the frame loop; pygame's `rumble` holds one setting at a time, so pulses and ramps are separate calls and a new effect replaces the one playing. Pausing, leaving the stage and losing the pad stop it. The tests never vibrate: `app.vibration` is None unless the game's frame loop sets it, and the player takes a fake clock and fake pads.

The dev's layout, times from the start of the zombie's hit sound (its file length in brackets):
- **Zombie 1** (1.536 s): wait 803 ms, then one light simple thump, a punch, nothing huge.
- **Zombie 2** (3.593 s): scratching, so firm but not too hard pulses, spread out a bit, along the file.
- **Zombie 3** (2.941 s): wait 454 ms, then a heavy but not too heavy, firm rumble to the end of the file (mauling).
- **Zombie 4** is zombie 2's. **Zombies 5 and 7** are zombie 3's (they share those hit sounds in the original too, `MONSTER_SOUNDS`).
- **Zombie 6** (1.466 s): wait 234 ms, then a quick firm pounce.
- **Zombie 8**, the animal that grabs you: only when you fail to shake it off, a firm vibration of about 750 ms.
- **Zombie 9** (0.937 s): from 227 ms, a hard, big, short smash, "whoa, that hurt".
- **Zombie 10** (3.198 s), the chainsaw: soft at first, rising over about 405 ms, a solid rumble through the sawing, then at 2.219 s dropping away, revving down to the end.
- **The girl:** if you shoot her by mistake, a long rumble: that was a bad move.
- **Dying** (added 2026-10-04): two hard seconds (`death`), started with the game over music, 1.3 s after the lethal hit (`playerDie_`). It replaces whatever the killing zombie's effect is still doing, since only one effect plays at a time.
- **Not in the layout, so no vibration:** the woman zombie, the bosses, zombies 11 and 12 (never spawned), the girl reaching you (her thank you), and gun fire. Ask the dev before adding any.
- The numbers (motor strengths, pulse spacing, the ramp) are in `EFFECTS` in `vibration.py` for tuning by feel; the tester's V key plays each one in turn (Shift+V back), and Z (the dev's idea) turns the zombie's own hit sound with it on and off, to judge a vibration's timing against its sound; the girl has no sound there.
- No menu switch for vibration yet.

## The vibration row (the dev's request, 2026-10-04, built, not yet confirmed)
Built in `main_controller.py` (the row, `VibrationAction_`), `app_delegate.py` (`vibration_on`, `set_vibration`), `vibration.py` (`enabled`, `confirm`), `controller.py` (the connect buzz), with tests in `menu.py` (3 new) and the readme's new controller section.
- A new main menu row between Store and the voice over row: it says "Vibration, currently on." or "Vibration, currently off.", and activating it flips the setting, clicks, and says the new state. Turning it on gives a short confirming buzz; turning it off silences the motors.
- Saved as `VIBRATION` ('1' or '0'; absent means on) in settings.json, in `SETTINGS_KEYS` before `EYEMODE`. `AppDelegate.vibration_on` reads it and `set_vibration` writes it.
- Off stops every effect in play, the connect buzz and the confirming buzz; the connect and disconnect sounds stay, since they are sounds, not vibration.
- There is no recording for the row, so it is spoken through the screen reader in both modes, as the other lines the bundle has no recording for are. It is row number 9 in `ROWS` (5 and 8 are the original's left-out ranking and Game Center rows); the order, not the number, is what moves.

## Afterwards
- Vibration through `Controller.rumble`, if it is worth having.
- Controller rebinding, if wanted.
