---
name: project_controller_shake_plan
description: "Planned 2026-10-05. A game controller with a motion sensor (a DualSense; not an Xbox pad) can shake the animal zombie off by being shaken, beside the A button, and the tutorial offers it only when the attached pad can. SDL's accelerometer is read through ctypes on the SDL2 library pygame ships, only while a zombie holds you."
metadata:
  type: project
---

**Status: planned 2026-10-05, building.** Asked for by tunmi13productions, after asking whether Xbox or DualSense pads can detect shaking: "I'd say support both. but only offer shaking if the controller is capable". Support both means A and a shake both work where the pad can sense one; Xbox pads keep only A. Builds on [[project_joystick_plan]] and [[project_tutorial_controller_callouts_plan]].

## What the original did, and what is chosen
- The original shook the phone: `-[Stage_1_E accelerometer:didAccelerate:]` (0x3c84c) counts shakes, ten of them (`shake_step`). The port counts 1 to 5 presses of the shake key per grab (`shakesNeeded`). A controller shake is one more way to make one press: it calls `shake_step()` once per detected shake, so the count, the timing and the grab itself are untouched.

## Facts checked
- A DualSense (and DualShock 4, Switch Pro, Joy-Cons) has an accelerometer and a gyroscope. Xbox One and Series pads have no motion sensors.
- pygame 2.6.1 (SDL 2.28.4) does not wrap SDL's sensor calls, so the port reads them through `ctypes` on the SDL2 library pygame ships: `SDL_GameControllerFromInstanceID`, `SDL_GameControllerHasSensor`, `SDL_GameControllerSetSensorEnabled` and `SDL_GameControllerGetSensorData`, sensor type 1 (accelerometer, in m/s², gravity included). SDL 2.0.14 or newer is needed.

## The plan
- **`sixthsense/platform/motion.py`:** finds the SDL2 library (next to pygame, in `pygame.libs` or `.dylibs`, or the frozen bundle's folder), and offers `has_accelerometer(id)`, `enable(id, on)` and `acceleration(id)`. Any failure means no motion, never an error. The library is a parameter, so the tests use a fake.
- **`sixthsense/ui/shake.py`:** `Shake` decides what is a shake and when to listen.
  - **Capable** means an attached pad reports an accelerometer. That is the only thing the tutorial's offer and the sensor depend on.
  - **Only while a zombie holds you** (`isShake`): the sensor is switched on when the grab starts and off when it ends, so nothing reads or drains a pad the rest of the time.
  - **A shake** is the acceleration's size leaving gravity (9.81 m/s²) by `SHAKE_THRESHOLD` (12 m/s², about 1.2 g) or more; one spike is one shake, and the next counts only after `SHAKE_GAP` (0.25 s). Both are constants to tune by ear on a real pad.
- **Frame loop:** `app.shake` beside `app.vibration`; each frame, `shake.tick(grabbed, on_shake)` with `on_shake` performing the stage's `shake` action, which is what A does. `AppDelegate.can_shake()` says whether a capable pad is attached.
- **Tutorial:** lesson Eight's controller callout adds the shake only when `can_shake()`: "Press A a few times, or give the controller a shake, to shake the zombie off." (PlayStation pads hear Cross.) Otherwise it is as it was.
- **Docs:** changelog, the player readme's game controller section, README.

## Not in it
- The gyroscope, tilt aiming, the touchpad, the DualSense's speaker and adaptive triggers: nothing else of the pad is used.
- No setting to turn shaking off: with a capable pad attached and a zombie holding you, a shake counts.
- No threshold row in the menus: constants, tuned by ear.

## Not verified
- How a shake reads on a real DualSense, wired and over Bluetooth, and what the threshold should be. Only the dev can judge that; the tests feed made-up samples.
- That SDL's sensor data arrives over Bluetooth on Windows with the dev's setup. The dev has an Xbox One pad, which has no sensor.
