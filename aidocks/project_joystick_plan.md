---
name: project_joystick_plan
description: "PLANNED 2026-10-04, not started. Controller support for Sixth Sense Reborn through SDL's game controller layer (pygame._sdl2.controller), cross platform, never XInput. Phase 1 is the menus, phase 2 the stage, vibration after. The dev has an Xbox One pad."
metadata:
  type: project
---

**Status: planned, not started (2026-10-04).** Nothing is built. The todo list's joystick lines stay in Unfinished until the dev confirms it works ([[feedback_todo_list_format]]).

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

## Phase 2: the stage
- The stick's angle snapped to the five lanes directly, like the original's swipe angle, instead of the keyboard's chords.
- Buttons for reload, next and previous weapon, shake and pause. Held fire for the MG80 carries over from held keys.
- The mapping is decided after the dev has tried phase 1.

## Afterwards
- Vibration through `Controller.rumble`, if it is worth having.
- Controller rebinding, if wanted.
