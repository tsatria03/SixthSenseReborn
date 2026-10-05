---
name: project_controller_shake_plan
description: "Planned 2026-10-05. A game controller with a motion sensor (a DualSense; not an Xbox pad) can shake the animal zombie off by being shaken, beside the A button, and the tutorial offers it only when the attached pad can. SDL's accelerometer is read through ctypes on the SDL2 library pygame ships, only while a zombie holds you."
metadata:
  type: project
---

**Status: built 2026-10-05, not yet confirmed.** `platform/motion.py`, `ui/shake.py`, `AppDelegate.shake` and `can_shake()`, the frame loop's `shake.tick`, and lesson Eight's `EightShake` callout. Tests: shake 10, tutorial 23. The real SDL library loads here and a missing pad is quietly nothing; no real DualSense was available, so the threshold and the sensor on a real pad, and the library lookup in the frozen Linux and macOS builds, are untried. Asked for by tunmi13productions, after asking whether Xbox or DualSense pads can detect shaking: "I'd say support both. but only offer shaking if the controller is capable". Support both means A and a shake both work where the pad can sense one; Xbox pads keep only A. Builds on [[joystick_plan]] and [[project_tutorial_controller_callouts_plan]].

## Found with a real DualSense, 2026-10-05
- The dev: "it seems like it hates my dual sense controller". Starting the game with the pad attached ended it at once: `pygame.event.get()` raised `SystemError` from a `KeyError: 0`. On Windows SDL lists a DualSense twice at start (the first listing is removed when its own driver takes the pad), and pygame cannot map the removal of a pad it never tabled. `ui/controller.read_events` now catches that one error, logs it and carries on; the rest of that batch (only device events at start) is lost.
- pygame's `Controller.id` is the device index (0), not SDL's instance id (1 for that pad). The lost-pad check (`_close` by the event's `instance_id`) and the shake's sensor lookup both used `pad.id`, so a DualSense would never have been noticed as unplugged and never found capable. `ui/controller.instance_id(pad)` reads the real id from `pad.as_joystick().get_instance_id()`, and `Controllers._pads` is keyed by it (`pad_ids`). The dev's Xbox pad was index 0 and instance 0, which is why it worked.
- Checked on the dev's DualSense, silently: SDL reports it as a PS5 controller (type 7) with an accelerometer and a gyroscope, and the accelerometer reads about 10.3 m/s² at rest, so `Shake.capable()` is true. A sensor read straight after switching it on is 0.0 until its first report, which stays under the shake threshold.
- Tests: controller 25, shake 11.

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
