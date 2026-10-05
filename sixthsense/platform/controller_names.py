"""PORT ADDITION: what a game controller's buttons are called, for the words the game says.

SDL gives every pad the same layout (the bottom face button is its "A", whatever is printed on
it), but a player knows the buttons by what is printed on theirs.  A pad that says PlayStation
gets those names; every other pad gets the Xbox ones, which is the layout the game was made on.
Nintendo pads are not told apart: how SDL labels their buttons has not been checked.
"""
from __future__ import annotations

#: Words in a pad's name that mean a PlayStation pad: SDL calls a DualSense "PS5 Controller".
PLAYSTATION_WORDS = ('ps3', 'ps4', 'ps5', 'dualshock', 'dualsense', 'playstation', 'sony')

#: What each button is called, by the SDL name the game uses for it.
XBOX = {'a': 'A', 'b': 'B', 'x': 'X', 'start': 'Start', 'rb': 'the right bumper'}
PLAYSTATION = {'a': 'Cross', 'b': 'Circle', 'x': 'Square', 'start': 'Options', 'rb': 'R1'}


def is_playstation(name) -> bool:
    """Whether a pad's name, as SDL reports it, says it is a PlayStation pad."""
    lowered = (name or '').lower()
    return any(word in lowered for word in PLAYSTATION_WORDS)


def button_names(name) -> dict:
    """The names of the buttons the game talks about, for the pad called ``name``."""
    return dict(PLAYSTATION if is_playstation(name) else XBOX)
