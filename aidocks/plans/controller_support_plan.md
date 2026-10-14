---
name: controller_support_plan
description: "2026-10-06, tunmi13productions: only the pad the game plays with pauses a game when it is unplugged, and a Controller support row in Settings that ignores every pad when it is off, looking for them again and playing the found sound when it is turned back on."
metadata:
  node_type: memory
  type: project
---

**Two changes to which pads the game cares about, both asked for by tunmi13productions on 2026-10-06, on top of the chosen-pad work in [[settings_menu_plan]].**

## 1. Only the pad in your hands stops a game

Before this, unplugging *any* open pad paused the game, let go of the aim and the D-pad and ended a burst (`Controllers.just_lost` was true for every pad, and `Input.controller` acted on every `CONTROLLERDEVICEREMOVED`). With two pads attached, taking away the one nobody was playing with interrupted the game.

- `Controllers.just_lost` becomes `Controllers.lost_active`: the last event took away **the pad the game plays with**, not just any pad.
- `_close` asks whether the id was active **before** dropping it, since dropping it hands the title to the next pad attached.
- A pad whose **name** is still attached has not really gone: that is SDL's double listing of a DualSense on Windows ([[controller_shake_plan]]), and two identical pads are one pad to the game anyway, which is all a saved name can tell apart (`Controllers.names`). So losing one listing of a pair with the same name is not losing the pad.
- `Input.controller` returns at once on a removal that is not the active pad's: it neither pauses nor resets the stick, the D-pad or a burst.
- The found and lost **sounds** still play for any listing that comes or goes, as they always did; only the pause follows the chosen pad.

## 2. A Controller support row in Settings

Some players have a pad plugged in and do not want to play with it. `CONTROLLERSUPPORT` in `config/settings.json`, '1' or '0', default **on**, so nothing changes for a save that has never set it.

**Turned off:** the lost sound plays once if any pad was attached (tunmi13productions, 2026-10-06), since those pads have just gone as far as the game is concerned; once, not once a pad, because what went is the support rather than a particular pad, and nothing at all with no pad attached. After that, no pad is opened, so the game cannot tell a pad is there. Every path that asks (`pads`, `names`, `active_pad`, vibration, the shake, the tutorial's controller callouts, the reorder screen's instructions) reads "no controller" with nothing of its own to change, because the gate is at the one place a pad is opened. Controller events are swallowed, the keyboard plays the game, and no found or lost sound ever plays.

**Turned back on:** the game looks for the pads attached, exactly as it does at startup, and plays the traditional found sound and buzz for each one it finds.

- `app.controller_support` / `set_controller_support(on)`, beside the other settings in `app_delegate.py`, with `'CONTROLLERSUPPORT': '1'` in its `SETTING_DEFAULTS` so the first start writes it like the rest. Turning it off silences the motors and lets go of the pads; turning it on opens and announces them.
- `Controllers` reads the setting live, like `_chosen_name`: `_open` refuses while it is off, `feed` returns no keys for a controller event, and `refresh()` opens and announces, or releases in silence.
- `release()` lets go of every pad and plays the lost sound once if there was one to let go of.
- The Settings row sits **before** the pad rows (vibration, shake, the picker), since it is the gate for them and needs no pad itself. While it is off those three read **"not supported"** and say **"Controller support is off."** when pressed, instead of "No controller is attached.", which would be a lie with a pad plugged in.

## Finished

**FINISHED 2026-10-06, confirmed by tunmi13productions:** "controller system is entirely complete... we've got full controller support now." Written before the code, as the repo asks ([[feedback_record_plans_first]]).
