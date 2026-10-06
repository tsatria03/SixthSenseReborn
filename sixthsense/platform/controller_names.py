"""PORT ADDITION: what a game controller's buttons are called, for the words the game says.

A player knows the buttons by what is printed on theirs, so the game says the names from
their own pad.  Four families are told apart by the name SDL reports: PlayStation,
Nintendo, the Steam Deck, and Xbox for everything else, which is the layout the game was
made on and what an unknown pad hears.  Amazon Luna, Google Stadia, NVIDIA Shield and the
third-party pads all print the Xbox names, so they want no family of their own.

**The face buttons are safe to name as SDL gives them.**  SDL2's
``SDL_HINT_GAMECONTROLLER_USE_BUTTON_LABELS`` defaults to 1, so a face button is reported
by the label printed on it and not by where it sits: on a Switch Pro,
``CONTROLLER_BUTTON_A`` is the button printed A, over on the right, not the bottom one.
So "press A" sends a Nintendo player to the right button.  (pygame 2.6.1 here carries SDL
2.28.4.)  Were that hint ever turned off, or were this moved to SDL3, where the buttons
are always positional and named south, east, west and north, the Nintendo table's A and
B, and X and Y, would have to trade places.

**Every control SDL reports is named, not only the ones the game says today**
(tunmi13productions, 2026-10-06: "add all buttons and controls to the controller names, in
case we ever use a lot of them" and "let's check for any other controllers sdl knows so we
cover as much as we can"), so a screen that starts talking about a trigger or a stick click
has the word for it already.

A name carries its own article where a sentence needs one, so it drops into "press %s" as
it stands: "press A", "press the right bumper".  The sticks and the D-pad are named as
things rather than presses, for "push %s up".
"""
from __future__ import annotations

#: Words in a pad's name that mean each family, as SDL reports the name.  SDL calls a
#: DualSense "PS5 Controller" and a Switch Pro "Nintendo Switch Pro Controller".
#: "Steam Virtual Gamepad" is deliberately not here: it is Steam presenting some other pad
#: as an Xbox 360 one, so it should hear the Xbox names.
PLAYSTATION_WORDS = ('ps3', 'ps4', 'ps5', 'dualshock', 'dualsense', 'playstation', 'sony')
NINTENDO_WORDS = ('nintendo', 'switch', 'joy-con', 'joycon', 'pro controller',
                  'wii', 'gamecube')
STEAM_WORDS = ('steam deck', 'steam controller')

#: What each control is called: the four face buttons, Back/Start/Guide, the two bumpers,
#: the two triggers, the two stick clicks, the two sticks, the D-pad and the touchpad.
XBOX = {
    'a': 'A', 'b': 'B', 'x': 'X', 'y': 'Y',
    'back': 'Back', 'start': 'Start', 'guide': 'the Xbox button',
    'lb': 'the left bumper', 'rb': 'the right bumper',
    'lt': 'the left trigger', 'rt': 'the right trigger',
    'ls': 'the left stick click', 'rs': 'the right stick click',
    'left_stick': 'the left stick', 'right_stick': 'the right stick',
    'dpad': 'the D-pad', 'touchpad': 'the touchpad',
}
PLAYSTATION = {
    'a': 'Cross', 'b': 'Circle', 'x': 'Square', 'y': 'Triangle',
    'back': 'Create', 'start': 'Options', 'guide': 'the PS button',
    'lb': 'L1', 'rb': 'R1',
    'lt': 'L2', 'rt': 'R2',
    'ls': 'L3', 'rs': 'R3',
    'left_stick': 'the left stick', 'right_stick': 'the right stick',
    'dpad': 'the D-pad', 'touchpad': 'the touchpad',
}
NINTENDO = {
    'a': 'A', 'b': 'B', 'x': 'X', 'y': 'Y',
    'back': 'Minus', 'start': 'Plus', 'guide': 'Home',
    'lb': 'L', 'rb': 'R',
    'lt': 'ZL', 'rt': 'ZR',
    'ls': 'the left stick click', 'rs': 'the right stick click',
    'left_stick': 'the left stick', 'right_stick': 'the right stick',
    'dpad': 'the D-pad', 'touchpad': 'the touchpad',
}
STEAM = {
    'a': 'A', 'b': 'B', 'x': 'X', 'y': 'Y',
    'back': 'View', 'start': 'Menu', 'guide': 'the Steam button',
    'lb': 'L1', 'rb': 'R1',
    'lt': 'L2', 'rt': 'R2',
    'ls': 'L3', 'rs': 'R3',
    'left_stick': 'the left stick', 'right_stick': 'the right stick',
    'dpad': 'the D-pad', 'touchpad': 'the right trackpad',
}

#: family -> its names.  'xbox' is the one an unknown pad hears.
FAMILIES = {'xbox': XBOX, 'playstation': PLAYSTATION, 'nintendo': NINTENDO, 'steam': STEAM}
#: checked in this order; the first whose words appear in the pad's name wins
_WORDS = (('playstation', PLAYSTATION_WORDS), ('nintendo', NINTENDO_WORDS),
          ('steam', STEAM_WORDS))


def family(name) -> str:
    """Which family a pad belongs to, by the name SDL reports: 'playstation',
    'nintendo', 'steam', or 'xbox' for everything else and for no pad at all."""
    lowered = (name or '').lower()
    for which, words in _WORDS:
        if any(word in lowered for word in words):
            return which
    return 'xbox'


def is_playstation(name) -> bool:
    """Whether a pad's name says it is a PlayStation pad."""
    return family(name) == 'playstation'


def button_names(name) -> dict:
    """The names of the controls the game talks about, for the pad called ``name``."""
    return dict(FAMILIES[family(name)])
