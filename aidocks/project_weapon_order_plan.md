---
name: project_weapon_order_plan
description: "PLANNED 2026-10-06: a Reorder weapons button in the inventory opens a list of the equipped weapons; Up and Down walk it, Shift and an arrow move a weapon, and the order is what Tab cycles through in a game and what you start on. WEAPON_ORDER in save.json. On a pad the bumpers move a weapon, and the screen says whichever instructions fit what is attached."
metadata:
  type: project
---

**Status: planned.** Agreed with tunmi13productions on 2026-10-06 and recorded before any code ([[feedback_record_plans_first]]). Mark it finished only once they say it works, then move it to `completed/` ([[feedback_completed_projects]]).

The ask, in tunmi13productions' words: "I want to add the ability to rearrange weapon order. maybe a button in inventory called reorder. then in the list of equipped weapons, you use the up and down arrows to navigate between them. you can hold down shift to move a weapon up or down. and this is how they will appear during gameplay. when you move an item it will say something like, mg80 moved above colt, or mg80 moved below shotgun."

## Where the order lives now

The order is the slot number, 0 to 7, and nothing else: `Stage_1_E.weaponInit` (0x35008) fills `weaponSource[i]` from `WEAPON_FILES[i]`, and `gunChangeAction_` (0x35a08) walks `w = (w + step) % 8`, skipping whatever is not equipped. `startWeapon` (0x35708) prefers the colt, slot 2, whenever it is equipped. The eight `...USE` keys say what is equipped; `AppDelegate.weaponHave` (0x4ee8) reads them in slot order. So a saved order only has to replace the *walk*: `gamePlayer.useWepon` stays a slot number, since it indexes `weaponSource`.

## Decided with tunmi13productions, one question at a time

- **The list shows only the equipped weapons**, as the dev asked. The saved order covers all eight underneath, so an unequipped weapon keeps its place and comes back to it when it is equipped again. Moving one swaps it with the next *equipped* weapon, stepping over the hidden ones. Showing all eight was the alternative.
- **A game starts you on the first weapon in your order** that is equipped, in place of the colt. The dev took the recommendation: it is the point of putting a weapon first. **This is a divergence** from the original, which always reaches for the colt (0x3572a reads `COLTUSE` before anything else).
- **The inventory list itself stays in slot order**, Grenade to sword, so a weapon is always in the same row when you go looking for it. Only a game and the reorder screen use the order.
- **At the ends it says so:** moving the top weapon up says "MG80 is already first." and the bottom one down says "Japanese sword is already last." Rereading the row silently was the alternative.
- **On a pad the bumpers move a weapon**: left bumper up, right bumper down, as the dev proposed. One press and one hand, which beats a two-handed hold in an audio game, and bumpers as previous and next is an ordinary pad convention. Holding a trigger and pushing the stick, which would mirror Shift exactly, was offered and declined.
- **The screen says the instructions that fit what is attached**, as the tutorial does ([[tutorial_controller_callouts_plan]]): the controller wording while a pad is attached, the keyboard wording otherwise. tunmi13productions: "just like the tutorial, it should give the keyboard instructions about reordering if no controller is connected, and controller instructions if a controller is connected."
- **Every control a pad has is named in `controller_names.py`**, not only the ones the game says today. tunmi13productions, 2026-10-06: "I'd add all buttons and controls to the controller names, in case we ever use a lot of them. rright now it only contains what we use, which can be limiting if we plan to add more in the future." So both tables carry the four face buttons, Back, Start, Guide, both bumpers, both triggers, both stick clicks, both sticks, the D-pad and the touchpad.

## What the screen does

Rows: Back, then one row per equipped weapon, in the saved order.

- **Up and Down** walk the rows, as on every other screen, reading the weapon's name.
- **Shift and Up or Down** move the weapon under the cursor, and the cursor goes with it.
- On a pad, **the left stick or the D-pad** walks and **the bumpers** move.
- It opens saying its name, then the instructions, then row 1, as the other screens open with their name ([[screen_reader_mode]]).
  - No pad: "Reorder weapons. Up and Down to walk the list, Shift and Up or Down to move a weapon."
  - A pad: "Reorder weapons. The left stick to walk the list, the left bumper to move a weapon up, the right bumper to move it down." On a PlayStation pad the bumpers are L1 and R1 (`platform/controller_names.py`).
- **Moving says what happened**, in the dev's own words: "MG80 moved above Colt." going up, "MG80 moved below Shotgun." going down, naming the weapon it passed.
- **At an end:** "MG80 is already first." or "Japanese sword is already last."
- **With fewer than two equipped** there is nothing to move, so after the title it says "Only one weapon is equipped, so there is nothing to reorder.", or "No weapons are equipped." with none, and still lists what is there.

## Save key

- `WEAPON_ORDER` in **save.json** (not `SETTINGS_KEYS`: it belongs with the `...USE` and weapon keys, which are progress), a list of the eight slot numbers.
- **Out of the box it is `[2, 3, 4, 5, 6, 7, 0, 1]`**: colt, shotgun, M4A1, AK47, MG80, Japanese sword, grenade, knife. That is the original's own cycle turned round to begin at the colt, so a save that has never touched it plays exactly as the original did, start and cycle alike. Plain slot order would have started every game on the grenade, which has no magazine, since the colt is slot 2 and `weaponHave` (0x52xx) equips the grenade, the knife and the colt on a fresh save. Caught by `gameplay.py` and `input.py` during the build.
- Written on every start where it is missing, and put back to the default when it is not a list of all eight numbers exactly once each, as the other keys are put back. It is editable by hand like the rest.

## The build

- **`sixthsense/game/weapon_order.py`**: `KEY`, `DEFAULT`, `fill(defaults)`, `order(defaults)` (the eight slots), `equipped(app, defaults)` (the order with the unequipped left out) and `move(slot, step, app, defaults)`, which swaps a weapon with the next equipped one and returns the slot it passed, or None at an end. Pure of any screen, so the tests can drive it.
- **`AppDelegate.didFinishLaunching`** calls `weapon_order.fill`, beside `weapon_upgrades.fill`.
- **`inventory.py`**: a `ReorderController(BlindScreen)`, and a "Reorder weapons, Button" row at the end of `InventoryController` (row 10, after the sword), which pushes it. Registered in `SixthSenseReborn.py`'s screen table and `PUSHED`, with its rows in the window's row names.
- **`ui/menu_input.py`**: `move_weapon_key`, which reads Shift with Up or Down (`event.mod` and `pygame.KMOD_SHIFT`) and the two bumpers, and calls the screen's `move_weapon`. **`ui/screen_input.py` calls it too, and that is the one that matters**: the shop and inventory screens, the reorder screen among them, use `ScreenInput`, not `MenuInput`. The first build wired it into `MenuInput` alone, so nothing moved in the real game, which tunmi13productions found by ear ("trying to reorder doesn't work, neither on keyboard or controller") because every test drove the screen's methods directly. `tests/case/weapon_order.py` now drives `ScreenInput` itself.
- **`ui/controller.py`**: the two bumpers mapped, which nothing used before (only the D-pad, A, B and the left stick were). They arrive as **F13 and F14**: no keyboard here has those keys and nothing else in the game reads them, so a bumper does nothing at all anywhere else. Page Up and Page Down would have been the obvious choice and were wrong, because they already set the menu music's volume on every one of these screens.
- **`platform/controller_names.py`**: every control SDL reports, in four families. Xbox is what an unknown pad hears; PlayStation, Nintendo and the Steam Deck are told apart by the name SDL gives. Amazon Luna, Google Stadia, NVIDIA Shield and the third-party pads print the Xbox names, so they fall through to it, and "Steam Virtual Gamepad" is deliberately left out of the Steam words because it is Steam presenting some other pad as an Xbox 360 one. **The face buttons are safe to name as SDL gives them**: SDL2's `SDL_HINT_GAMECONTROLLER_USE_BUTTON_LABELS` defaults to 1, so a face button comes back by its printed label and not its position, and `CONTROLLER_BUTTON_A` on a Switch Pro really is the button printed A (checked 2026-10-06; pygame 2.6.1 here carries SDL 2.28.4). On SDL3, where the buttons are always positional, the Nintendo table's A and B, and X and Y, would have to trade places.
- **`stage_1_e.py`**: `gunChangeAction_` walks the saved order rather than 0 to 7, in debug mode too; `startWeapon` takes the first equipped weapon in the order.
- **Tests**: a new `tests/case/weapon_order.py` (the default and what is put back, the moves and what each says, the ends, a weapon that is not equipped keeping its place, the order after equipping and unequipping), and additions to `inventory.py`, `gameplay.py` (Tab following the order, and the weapon a game starts on) and `input.py` (Shift with an arrow, and the bumpers).
- **Docs**: a changelog line; `docks/readme.txt` and `README.md` for the new screen, its keys and `WEAPON_ORDER`; the todo item once the dev confirms it.

## Not in it

- The shop and the inventory list keep their slot order.
- The F1 key bindings screen is unchanged: it binds the stage's keys, and the menus' keys have never been rebindable (`platform/keymap.py`'s `ACTIONS` is stage actions only).
- Nothing about which weapons are equipped changes; this only says what order they come in.
