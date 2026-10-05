---
name: project_tutorial_controller_callouts_plan
description: "Planned 2026-10-05. While a game controller is attached, the tutorial says the controller's way of doing each lesson (left stick direction or D-pad, X, bumper, A, B or Start) after each recording, in both voice over modes, with PlayStation button names on a PlayStation pad. No pad: the keyboard hints stay as they are."
metadata:
  type: project
---

**Status: built 2026-10-05, not yet confirmed.** `platform/controller_names.py`, `AppDelegate.controllers` and `controller_name()`, `CONTROLLER_HINTS`, `controller_hint` and `callout` in `stage_tutorial.py`, and the frame loop setting `app.controllers`. Tests: controller_names 5, tutorial 22. Not yet heard by ear with a real pad. Asked for by tunmi13productions: "use controller callouts when a controller is connected in the tutorial", e.g. push left on the left stick to shoot toward 9 o'clock, or the D-pad's left and up together; the wording left to Claude and approved ("yes I like those"). Builds on [[project_joystick_plan]], and on the tutorial's key hints (`Stage_Tutorial.key_hint`, [[project_tutorial_tester_plan]], [[project_screen_reader_mode]]).

## Decisions (tunmi13productions, 2026-10-05)
- **When:** whenever a pad is attached, in **both** voice over modes (the dev took the recommendation: the recordings describe touch swipes, so a controller player has no other way to learn the stick directions). The speech goes through the screen reader either way.
- **No pad:** the keyboard hints stay exactly as they are (spoken with voice over off only).
- **Wording**, stick first, D-pad as the alternative:
  - One: "Push the left stick left to shoot toward 9 o'clock, or press D-pad left."
  - Two: "Push the left stick diagonally up and left to shoot toward 10:30, or press D-pad left and up together."
  - Three: "Push the left stick up to shoot toward 12 o'clock, or press D-pad up."
  - Four: "Push the left stick diagonally up and right to shoot toward 1:30, or press D-pad right and up together."
  - Five: "Push the left stick right to shoot toward 3 o'clock, or press D-pad right."
  - Six: "Pull the left stick down, or press X, to reload."
  - Seven: "Press the right bumper to change to the next weapon."
  - Eight: "Press A a few times to shake the zombie off."
  - Nine: "Press B or Start to end the tutorial."
  - FiveHalf teaches nothing new and says nothing.
- **Button names follow the pad:** a pad whose name says PlayStation (PS3, PS4, PS5, DualShock, DualSense, Sony) hears Square for X, Cross for A, Circle for B, Options for Start and R1 for the right bumper; any other pad hears the Xbox names. Nintendo pads are not told apart (not checked how SDL labels them).

## The build
- `sixthsense/platform/controller_names.py`: `is_playstation(name)` and `button_names(name)`; pure, no pygame.
- `AppDelegate.controllers` (set by the frame loop, none in the tests) and `controller_name()`: the name of the first attached pad, or None.
- `Stage_Tutorial.controller_hint(name)` and `callout(name)`: the controller wording when a pad is attached, else `key_hint`; `tutorial_sound_stop` speaks `callout`.
- Tests in `tests/case/tutorial.py` and a new `tests/case/controller_names.py`; a changelog line; README and the player readme if they describe the tutorial's hints.

## Not in it
- The recordings are unchanged. Nothing changes in the stage's own controls.
- No hint repeats; like the key hints, each is said once, after its recording.
