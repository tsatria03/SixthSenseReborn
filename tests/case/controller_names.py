"""What a controller's buttons are called in the words the game says.

A PORT ADDITION (aidocks/completed/tutorial_controller_callouts_plan.md).  Pure: no pad, no pygame.
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import _scratch_save                                             # noqa: E402,F401  never the real save

from sixthsense.platform.controller_names import (FAMILIES, NINTENDO, PLAYSTATION,  # noqa: E402
                                                  STEAM, XBOX, button_names, family,
                                                  is_playstation)


def test_the_playstation_pads_are_known_by_their_names():
    for name in ('PS5 Controller', 'PS4 Controller', 'PS3 Controller', 'DualSense Wireless Controller',
                 'Sony DualShock 4', 'PlayStation Controller', 'ps5 controller'):
        assert is_playstation(name), name


def test_other_pads_and_no_name_are_not():
    for name in ('Xbox One Controller', 'Controller (Xbox One For Windows)', 'Xbox 360 Controller',
                 '8BitDo Pro 2', 'Logitech F310', '', None):
        assert not is_playstation(name), name


def test_the_nintendo_pads_are_known():
    for name in ('Nintendo Switch Pro Controller', 'Nintendo Switch Joy-Con (L)',
                 'Joy-Con (R)', 'Lic Pro Controller', 'Wii U Pro Controller',
                 'Nintendo GameCube Controller'):
        assert family(name) == 'nintendo', name


def test_the_steam_hardware_is_known_but_steams_virtual_pad_is_not():
    assert family('Steam Deck') == 'steam' and family('Steam Controller') == 'steam'
    # Steam presenting some other pad as an Xbox 360 one, so it hears the Xbox names
    assert family('Steam Virtual Gamepad') == 'xbox'


def test_the_xbox_like_pads_fall_through_to_xbox():
    """Luna, Stadia and Shield print the Xbox names, so they want no family of their own."""
    for name in ('Amazon Luna Controller', 'Google Stadia Controller', 'NVIDIA Controller',
                 'Xbox Series X Controller', 'XInput Controller #1', 'Logitech F310', '', None):
        assert family(name) == 'xbox', name


def test_an_xbox_pad_hears_the_xbox_names():
    names = button_names('Xbox One Controller')
    assert names == XBOX
    assert (names['a'], names['b'], names['x'], names['y']) == ('A', 'B', 'X', 'Y')
    assert names['lb'] == 'the left bumper' and names['rb'] == 'the right bumper'
    assert names['lt'] == 'the left trigger' and names['rt'] == 'the right trigger'
    assert button_names(None) == names, 'an unnamed pad is the layout the game was made on'


def test_a_playstation_pad_hears_the_printed_names():
    names = button_names('PS5 Controller')
    assert names == PLAYSTATION
    assert (names['a'], names['b'], names['x'], names['y']) == ('Cross', 'Circle', 'Square', 'Triangle')
    assert names['lb'] == 'L1' and names['rb'] == 'R1'
    assert names['lt'] == 'L2' and names['rt'] == 'R2'
    assert names['ls'] == 'L3' and names['rs'] == 'R3'


def test_every_control_is_named_in_every_family():
    """Each table names every control SDL reports, so a screen that starts talking about
    one has the word for it already (tunmi13productions, 2026-10-06)."""
    wanted = {'a', 'b', 'x', 'y', 'back', 'start', 'guide', 'lb', 'rb', 'lt', 'rt',
              'ls', 'rs', 'left_stick', 'right_stick', 'dpad', 'touchpad'}
    for which, table in FAMILIES.items():
        assert set(table) == wanted, which
        for control in wanted:
            assert table[control], (which, control)


def test_a_nintendo_pad_hears_the_printed_names():
    names = button_names('Nintendo Switch Pro Controller')
    assert names == NINTENDO
    assert names['lb'] == 'L' and names['rb'] == 'R'
    assert names['lt'] == 'ZL' and names['rt'] == 'ZR'
    assert (names['back'], names['start'], names['guide']) == ('Minus', 'Plus', 'Home')
    # SDL2's USE_BUTTON_LABELS defaults to 1, so a face button comes back by its printed
    # label, not its position: CONTROLLER_BUTTON_A really is the button printed A.
    assert (names['a'], names['b'], names['x'], names['y']) == ('A', 'B', 'X', 'Y')


def test_a_steam_deck_hears_its_own_names():
    names = button_names('Steam Deck')
    assert names == STEAM
    assert names['lb'] == 'L1' and names['rt'] == 'R2'
    assert (names['back'], names['start']) == ('View', 'Menu')
    assert (names['a'], names['b']) == ('A', 'B'), 'the Deck prints the Xbox face names'


def test_the_caller_cannot_change_the_tables():
    button_names('PS5 Controller')['a'] = 'Banana'
    assert button_names('PS4 Controller')['a'] == 'Cross'


if __name__ == '__main__':
    fns = [v for k, v in sorted(globals().items()) if k.startswith('test_')]
    bad = 0
    for fn in fns:
        try:
            fn()
            print('ok    %s' % fn.__name__)
        except AssertionError as e:
            bad += 1
            print('FAIL  %s: %s' % (fn.__name__, e))
        except Exception as e:
            bad += 1
            print('ERROR %s: %r' % (fn.__name__, e))
    print('%d/%d passed' % (len(fns) - bad, len(fns)))
    sys.exit(1 if bad else 0)
