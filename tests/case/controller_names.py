"""What a controller's buttons are called in the words the game says.

A PORT ADDITION (aidocks/project_tutorial_controller_callouts_plan.md).  Pure: no pad, no pygame.
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import _scratch_save                                             # noqa: E402,F401  never the real save

from sixthsense.platform.controller_names import button_names, is_playstation  # noqa: E402


def test_the_playstation_pads_are_known_by_their_names():
    for name in ('PS5 Controller', 'PS4 Controller', 'PS3 Controller', 'DualSense Wireless Controller',
                 'Sony DualShock 4', 'PlayStation Controller', 'ps5 controller'):
        assert is_playstation(name), name


def test_other_pads_and_no_name_are_not():
    for name in ('Xbox One Controller', 'Controller (Xbox One For Windows)', 'Xbox 360 Controller',
                 '8BitDo Pro 2', 'Logitech F310', '', None):
        assert not is_playstation(name), name


def test_an_xbox_pad_hears_the_xbox_names():
    names = button_names('Xbox One Controller')
    assert names == {'a': 'A', 'b': 'B', 'x': 'X', 'y': 'Y', 'start': 'Start', 'rb': 'the right bumper'}
    assert button_names(None) == names, 'an unnamed pad is the layout the game was made on'


def test_a_playstation_pad_hears_the_printed_names():
    names = button_names('PS5 Controller')
    assert names == {'a': 'Cross', 'b': 'Circle', 'x': 'Square', 'y': 'Triangle', 'start': 'Options', 'rb': 'R1'}


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
