"""Shaking a game controller to shake the animal zombie off.

A PORT ADDITION (aidocks/completed/controller_shake_plan.md).  The pads, the SDL library and the clock
are stand-ins, so no real pad is opened or read.
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import _scratch_save                                             # noqa: E402,F401  never the real save

from sixthsense.game.app_delegate import AppDelegate             # noqa: E402
from sixthsense.platform.motion import Motion, load_sdl          # noqa: E402
from sixthsense.ui.shake import GRAVITY, SHAKE_GAP, SHAKE_THRESHOLD, Shake  # noqa: E402


class _FakeSDL:
    """The four SDL calls, for pads by instance id: ``has`` says which have a sensor, ``reading``
    what each gives."""

    def __init__(self, has=(), reading=None, fail=False):
        self.has, self.reading, self.fail = set(has), dict(reading or {}), fail
        self.enabled = {}
        self.log = []

    def SDL_GameControllerFromInstanceID(self, i):
        self.log.append(('from', i))
        if self.fail:
            raise OSError('no library')
        return i + 1000 if i in self.has or i in self.reading else 0

    def SDL_GameControllerHasSensor(self, pad, kind):
        assert kind == 1, 'only the accelerometer is asked for'
        return 1 if (pad - 1000) in self.has else 0

    def SDL_GameControllerSetSensorEnabled(self, pad, kind, on):
        assert kind == 1
        self.enabled[pad - 1000] = bool(on)
        return 0

    def SDL_GameControllerGetSensorData(self, pad, kind, buf, n):
        assert kind == 1 and n == 3
        values = self.reading.get(pad - 1000)
        if values is None:
            return -1
        for k, v in enumerate(values):
            buf[k] = v
        return 0


class _Pad:
    def __init__(self, ident):
        self.id = ident
        self.name = 'pad %d' % ident


class _Pads:
    def __init__(self, *ids):
        self.pads = [_Pad(i) for i in ids]


class _Clock:
    def __init__(self):
        self.now = 100.0

    def __call__(self):
        return self.now


STILL = (0.0, GRAVITY, 0.0)
FLICK = (0.0, GRAVITY + SHAKE_THRESHOLD + 3.0, 0.0)


def _shake(sdl, pads, clock=None):
    return Shake(_Pads(*pads), Motion(sdl), clock or _Clock())


def test_a_pad_with_an_accelerometer_is_capable_and_one_without_is_not():
    sdl = _FakeSDL(has={1}, reading={1: STILL, 2: STILL})
    assert _shake(sdl, [1]).capable() is True
    assert _shake(sdl, [2]).capable() is False, 'an Xbox pad has no sensor'
    assert _shake(sdl, [2, 1]).capable() is True, 'one capable pad among others is enough'
    assert _shake(sdl, []).capable() is False


def test_no_sdl_library_means_no_motion_and_no_errors():
    motion = Motion(_FakeSDL(fail=True))
    assert motion.has_accelerometer(1) is False
    assert motion.enable(1, True) is False
    assert motion.acceleration(1) is None
    bare = Motion.__new__(Motion)
    bare.lib = None
    assert bare.has_accelerometer(1) is False and bare.acceleration(1) is None and bare.enable(1, True) is False
    shake = Shake(_Pads(1), bare)
    assert shake.capable() is False
    assert shake.tick(True, lambda: 1 / 0) == 0, 'a pad that cannot shake never calls for one'


def test_the_real_library_loads_and_a_missing_pad_is_quietly_nothing():
    lib = load_sdl()
    assert lib is None or hasattr(lib, 'SDL_GameControllerHasSensor')
    motion = Motion()
    assert motion.has_accelerometer(987654) is False
    assert motion.acceleration(987654) is None


def test_a_shake_is_the_reading_leaving_gravity_by_the_threshold():
    sdl = _FakeSDL(has={1}, reading={1: STILL})
    shake, clock, got = _shake(sdl, [1]), _Clock(), []
    shake.clock = clock
    assert shake.tick(True, lambda: got.append(1)) == 0 and got == [], 'a pad lying still'
    sdl.reading[1] = (0.0, GRAVITY + SHAKE_THRESHOLD - 0.5, 0.0)
    assert shake.tick(True, lambda: got.append(1)) == 0, 'a little under the threshold'
    sdl.reading[1] = FLICK
    assert shake.tick(True, lambda: got.append(1)) == 1 and got == [1]
    sdl.reading[1] = (0.0, 0.0, 0.0)            # free fall alone is not a shake
    clock.now += SHAKE_GAP + 0.01
    assert shake.tick(True, lambda: got.append(1)) == 0 and got == [1]
    sdl.reading[1] = (GRAVITY + SHAKE_THRESHOLD + 3.0, 0.0, 0.0)   # a flick the other way
    clock.now += SHAKE_GAP + 0.01
    assert shake.tick(True, lambda: got.append(1)) == 1 and got == [1, 1]


def test_one_shake_is_one_press_however_long_it_lasts():
    sdl = _FakeSDL(has={1}, reading={1: FLICK})
    clock, got = _Clock(), []
    shake = Shake(_Pads(1), Motion(sdl), clock)
    for _frame in range(10):                     # ten frames of the same flick, 16 ms apart
        shake.tick(True, lambda: got.append(1))
        clock.now += 0.016
    assert got == [1], got
    clock.now += SHAKE_GAP
    shake.tick(True, lambda: got.append(1))
    assert got == [1, 1], 'the next flick counts once the gap has passed'


def test_the_sensor_is_on_only_while_a_zombie_holds_you():
    sdl = _FakeSDL(has={1}, reading={1: STILL})
    shake = _shake(sdl, [1])
    shake.tick(False, lambda: None)
    assert sdl.enabled == {}, 'the sensor was switched on with nothing holding you'
    shake.tick(True, lambda: None)
    assert sdl.enabled == {1: True}
    shake.tick(False, lambda: None)
    assert sdl.enabled == {1: False}, 'the sensor was left on after the grab'
    sdl.log.clear()
    shake.tick(False, lambda: None)
    assert ('from', 1) not in sdl.log, 'it kept asking about a pad when nothing was holding you'


def test_a_pad_without_a_sensor_is_never_enabled_or_read():
    sdl = _FakeSDL(has=set(), reading={2: FLICK})
    shake, got = _shake(sdl, [2]), []
    assert shake.tick(True, lambda: got.append(1)) == 0 and got == []
    assert sdl.enabled == {}


def test_losing_the_pad_forgets_it():
    sdl = _FakeSDL(has={1}, reading={1: FLICK})
    pads = _Pads(1)
    shake, got = Shake(pads, Motion(sdl), _Clock()), []
    shake.tick(True, lambda: got.append(1))
    assert got == [1]
    pads.pads = []
    assert shake.capable() is False
    assert shake.tick(True, lambda: got.append(1)) == 0
    assert 1 not in shake._can and 1 not in shake._listening


def test_every_capable_pad_can_be_shaken():
    sdl = _FakeSDL(has={1, 2}, reading={1: STILL, 2: FLICK})
    shake, got = _shake(sdl, [1, 2]), []
    assert shake.tick(True, lambda: got.append(1)) == 1


def test_the_sensor_is_asked_for_by_the_sdl_instance_id():
    """A DualSense opened at device index 0 can be SDL's instance 1; asking for 0 finds nothing."""
    class _Joy:
        def get_instance_id(self):
            return 1

    class _Opened:
        id, name = 0, 'DualSense Wireless Controller'

        def as_joystick(self):
            return _Joy()
    from sixthsense.ui.controller import Controllers
    pads = Controllers(__import__('pygame'), sdl=_NoSdl())
    pads._pads[1] = _Opened()
    sdl = _FakeSDL(has={1}, reading={1: FLICK})
    shake, got = Shake(pads, Motion(sdl), _Clock()), []
    assert shake.capable() is True
    assert shake.tick(True, lambda: got.append(1)) == 1 and sdl.enabled == {1: True}


class _NoSdl:
    def init(self):
        pass

    def get_count(self):
        return 0


def test_the_game_asks_whether_a_pad_can_be_shaken():
    app = AppDelegate.shared()
    saved = app.shake
    try:
        app.shake = None
        assert app.can_shake() is False, 'without a controller, which is every test'
        app.shake = _shake(_FakeSDL(has={1}, reading={1: STILL}), [1])
        assert app.can_shake() is True
        app.shake = _shake(_FakeSDL(reading={2: STILL}), [2])
        assert app.can_shake() is False
    finally:
        app.shake = saved


# ------------------------------------- the Settings screen's shake (2026-10-06)
# aidocks/completed/settings_menu_plan.md

class _ActivePads(_Pads):
    """Stands in for ui/controller.Controllers once it can name the chosen pad: only that
    pad is read for a shake, so a pad SDL listed twice is read once."""

    def __init__(self, *ids, active=None):
        _Pads.__init__(self, *ids)
        self._active = ids[:1] if active is None else active

    @property
    def active_pad_ids(self):
        return list(self._active)


def test_the_shake_turned_off_reads_nothing_at_all():
    """Off is the same as no zombie holding you: no sensor is switched on, so nothing is
    read and no pad is kept busy."""
    sdl = _FakeSDL(has={1}, reading={1: FLICK})
    shake = Shake(_Pads(1), Motion(sdl), _Clock(), on=lambda: False)
    got = []
    assert shake.tick(True, lambda: got.append(1)) == 0
    assert got == [] and sdl.enabled == {}, sdl.enabled


def test_the_shake_turned_on_again_reads_as_before():
    sdl = _FakeSDL(has={1}, reading={1: FLICK})
    on = [False]
    shake = Shake(_Pads(1), Motion(sdl), _Clock(), on=lambda: on[0])
    got = []
    assert shake.tick(True, lambda: got.append(1)) == 0
    on[0] = True
    assert shake.tick(True, lambda: got.append(1)) == 1
    assert got == [1]


def test_without_an_on_switch_the_shake_is_on():
    """Every caller from before the setting existed, and the tests above, get a shake that
    works, so the setting could not quietly turn it off for them."""
    sdl = _FakeSDL(has={1}, reading={1: FLICK})
    shake = Shake(_Pads(1), Motion(sdl), _Clock())
    assert shake.tick(True, lambda: None) == 1


def test_only_the_chosen_pad_is_read_for_a_shake():
    sdl = _FakeSDL(has={1, 2}, reading={1: FLICK, 2: FLICK})
    shake = Shake(_ActivePads(1, 2, active=[2]), Motion(sdl), _Clock())
    got = []
    assert shake.tick(True, lambda: got.append('any')) == 1, 'the chosen pad did not read'
    assert 1 not in sdl.enabled, 'the pad that was not chosen had its sensor switched on'
    assert sdl.enabled == {2: True}, sdl.enabled


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
