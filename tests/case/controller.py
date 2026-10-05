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

from sixthsense.ui.controller import (CONNECT_BUZZ, SOUND_DETECTED,    # noqa: E402
                                      SOUND_NOT_DETECTED, STICK_PRESS, STICK_RELEASE,
                                      Controllers)

pygame.display.init()


class _NoSdl:
    """Stands in for pygame._sdl2.controller with no pad attached: the tests never open or
    buzz a real controller."""

    def init(self):
        pass

    def get_count(self):
        return 0

    def is_controller(self, index):
        return False


PAD = Controllers(pygame, sdl=_NoSdl())


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


# ------------------------------------------------- the sounds for finding and losing one
class _App:
    def __init__(self):
        self.played = []

    def playSound_Gain_Pos_z_reprats_(self, num, gain, pos, z, repeats):
        self.played.append(num)


class _FakePad:
    def __init__(self, ident, name='Fake pad'):
        self.id, self.name, self.buzzed = ident, name, []

    def rumble(self, low, high, ms):
        self.buzzed.append((low, high, ms))
        return True


class _FakeSdl(_NoSdl):
    """Stands in for pygame._sdl2.controller: ``pads`` maps a device index to a pad."""

    def __init__(self, pads=()):
        self.pads = dict(enumerate(pads))

    def get_count(self):
        return len(self.pads)

    def is_controller(self, index):
        return index in self.pads

    def Controller(self, index):                                # noqa: N802
        return self.pads[index]


def _with(*pads):
    app = _App()
    c = Controllers(pygame, app, sdl=_FakeSdl())
    c._sdl = _FakeSdl(pads)
    return c, app


def _added(c, index):
    return c.feed(pygame.event.Event(pygame.CONTROLLERDEVICEADDED, device_index=index))


def _removed(c, ident):
    return c.feed(pygame.event.Event(pygame.CONTROLLERDEVICEREMOVED, instance_id=ident))


def test_finding_a_controller_plays_its_sound_and_buzzes():
    pad = _FakePad(7)
    c, app = _with(pad)
    _added(c, 0)
    assert app.played == [SOUND_DETECTED], app.played
    assert pad.buzzed == [CONNECT_BUZZ], pad.buzzed
    assert [p.id for p in c.pads] == [7]


def test_no_controller_found_plays_nothing():
    c, app = _with()                                 # nothing attached
    _added(c, 0)
    c.announce_attached()
    assert app.played == [] and c.pads == []


def test_an_unplayable_device_is_not_a_controller():
    c, app = _with(_FakePad(1))
    _added(c, 5)                                     # an index with no controller
    assert app.played == [] and c.pads == []


def test_losing_a_controller_plays_the_other_sound():
    c, app = _with(_FakePad(3))
    _added(c, 0)
    _removed(c, 3)
    assert app.played == [SOUND_DETECTED, SOUND_NOT_DETECTED], app.played
    assert c.pads == []


def test_losing_something_that_was_never_found_plays_nothing():
    c, app = _with()
    _removed(c, 9)
    assert app.played == []


def test_the_pads_attached_at_start_are_announced_once():
    pad = _FakePad(4)
    c, app = _with()
    c._pads[4] = pad                                 # opened at start, quietly
    c.announce_attached()
    assert app.played == [SOUND_DETECTED] and pad.buzzed == [CONNECT_BUZZ]
    c._sdl = _FakeSdl([pad])
    _added(c, 0)                                     # SDL announces it again at start-up
    assert app.played == [SOUND_DETECTED], 'it was announced twice'


def test_without_an_app_nothing_is_played_and_nothing_breaks():
    pad = _FakePad(2)
    c = Controllers(pygame, sdl=_FakeSdl())
    c._sdl = _FakeSdl([pad])
    _added(c, 0)
    _removed(c, 2)
    assert c.pads == []


def test_a_pad_that_cannot_vibrate_is_still_found():
    class _Dead(_FakePad):
        def rumble(self, *a):
            raise RuntimeError('no motors')
    c, app = _with(_Dead(8))
    _added(c, 0)
    assert app.played == [SOUND_DETECTED]


def test_the_sounds_are_named_in_the_sound_list():
    import plistlib

    from sixthsense import paths
    with open(paths.path_for_resource('SoundList', 'plist'), 'rb') as f:
        sl = plistlib.load(f)
    assert sl[SOUND_DETECTED] == 'ctrl_detected'
    assert sl[SOUND_NOT_DETECTED] == 'ctrl_not_detected'


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
