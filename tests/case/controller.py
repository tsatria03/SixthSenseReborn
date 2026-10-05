"""A game controller on the menus: its events become the keys the screens already take.

A PORT ADDITION (aidocks/project_joystick_plan.md, phase 1).  The events are made up
here, so no pad need be attached; the SDL layer is opened on the dummy video driver.
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import _scratch_save                                             # noqa: E402,F401  never the real save

import pygame                                                    # noqa: E402

from sixthsense.ui.controller import STICK_PRESS, STICK_RELEASE, Controllers  # noqa: E402

pygame.display.init()
PAD = Controllers(pygame)


def _button(button, down=True):
    t = pygame.CONTROLLERBUTTONDOWN if down else pygame.CONTROLLERBUTTONUP
    return pygame.event.Event(t, button=button, instance_id=0)


def _axis(axis, value):
    return pygame.event.Event(pygame.CONTROLLERAXISMOTION, axis=axis, value=value,
                              instance_id=0)


def _keys(events):
    """The keys pressed, as names, ignoring the matching releases."""
    return [pygame.key.name(e.key) for e in events if e.type == pygame.KEYDOWN]


def test_the_buttons_are_the_menu_keys():
    want = {pygame.CONTROLLER_BUTTON_DPAD_UP: 'up',
            pygame.CONTROLLER_BUTTON_DPAD_DOWN: 'down',
            pygame.CONTROLLER_BUTTON_DPAD_LEFT: 'left',
            pygame.CONTROLLER_BUTTON_DPAD_RIGHT: 'right',
            pygame.CONTROLLER_BUTTON_A: 'return',
            pygame.CONTROLLER_BUTTON_B: 'escape'}
    for button, name in want.items():
        assert _keys(PAD.feed(_button(button))) == [name], name


def test_a_press_is_a_key_down_and_up():
    kinds = [e.type for e in PAD.feed(_button(pygame.CONTROLLER_BUTTON_A))]
    assert kinds == [pygame.KEYDOWN, pygame.KEYUP]


def test_releasing_a_button_and_other_buttons_do_nothing():
    assert PAD.feed(_button(pygame.CONTROLLER_BUTTON_A, down=False)) == []
    assert PAD.feed(_button(pygame.CONTROLLER_BUTTON_Y)) == []


def test_other_events_are_not_a_controllers():
    assert PAD.feed(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_UP)) is None
    assert PAD.feed(pygame.event.Event(pygame.QUIT)) is None


def test_the_stick_presses_once_per_lean():
    Y = pygame.CONTROLLER_AXIS_LEFTY
    assert PAD.feed(_axis(Y, 0.2)) == []                       # inside the dead zone
    assert _keys(PAD.feed(_axis(Y, -0.9))) == ['up']
    assert PAD.feed(_axis(Y, -1.0)) == []                      # still leaning: no repeat
    assert PAD.feed(_axis(Y, -0.5)) == []                      # not yet back to the middle
    assert PAD.feed(_axis(Y, 0.0)) == []                       # back
    assert _keys(PAD.feed(_axis(Y, 0.9))) == ['down']          # and the other way


def test_the_stick_reads_both_directions_of_both_axes():
    X, Y = pygame.CONTROLLER_AXIS_LEFTX, pygame.CONTROLLER_AXIS_LEFTY
    assert _keys(PAD.feed(_axis(X, -0.9))) == ['left']
    PAD.feed(_axis(X, 0.0))
    assert _keys(PAD.feed(_axis(X, 0.9))) == ['right']
    PAD.feed(_axis(X, 0.0))
    PAD.feed(_axis(Y, 0.0))


def test_a_stick_swung_straight_across_presses_the_other_way():
    X = pygame.CONTROLLER_AXIS_LEFTX
    assert _keys(PAD.feed(_axis(X, -0.9))) == ['left']
    assert _keys(PAD.feed(_axis(X, 0.9))) == ['right']
    PAD.feed(_axis(X, 0.0))


def test_the_stick_takes_raw_sdl_units_too():
    Y = pygame.CONTROLLER_AXIS_LEFTY
    assert _keys(PAD.feed(_axis(Y, -30000))) == ['up']
    PAD.feed(_axis(Y, 0))


def test_the_right_stick_and_triggers_are_ignored():
    for axis in (pygame.CONTROLLER_AXIS_RIGHTX, pygame.CONTROLLER_AXIS_RIGHTY,
                 pygame.CONTROLLER_AXIS_TRIGGERLEFT, pygame.CONTROLLER_AXIS_TRIGGERRIGHT):
        assert PAD.feed(_axis(axis, 1.0)) == []


def test_the_dead_zone_is_wider_than_the_release_point():
    assert 0 < STICK_RELEASE < STICK_PRESS < 1


def test_unplugging_forgets_the_lean():
    Y = pygame.CONTROLLER_AXIS_LEFTY
    assert _keys(PAD.feed(_axis(Y, -0.9))) == ['up']
    assert PAD.feed(pygame.event.Event(pygame.CONTROLLERDEVICEREMOVED, instance_id=0)) == []
    assert _keys(PAD.feed(_axis(Y, -0.9))) == ['up']           # a new pad starts fresh
    PAD.feed(_axis(Y, 0.0))


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
