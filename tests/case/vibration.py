"""What the controller's motors do when something hits you.

A PORT ADDITION (aidocks/project_joystick_plan.md).  The pads and the clock are fakes, so
nothing real ever vibrates and nothing waits.
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import _scratch_save                                             # noqa: E402,F401  never the real save

import pygame                                                    # noqa: E402

from sixthsense.game import stage_1_e as S1E                     # noqa: E402
from sixthsense.game.app_delegate import AppDelegate             # noqa: E402
from sixthsense.game.monster_control import MonsterControl       # noqa: E402
from sixthsense.game.stage_1_e import Stage_1_E                  # noqa: E402
from sixthsense.platform.defaults import UserDefaults            # noqa: E402
from sixthsense.platform.runloop import RunLoop                  # noqa: E402
from sixthsense.ui.vibration import EFFECTS, ZOMBIE_EFFECTS, Vibration  # noqa: E402


class _Pad:
    def __init__(self):
        self.calls = []                 # ('rumble', low, high, ms) and ('stop',)

    def rumble(self, low, high, ms):
        self.calls.append(('rumble', low, high, ms))
        return True

    def stop_rumble(self):
        self.calls.append(('stop',))


class _Pads:
    def __init__(self, *pads):
        self.pads = list(pads)


class _Clock:
    def __init__(self):
        self.now = 100.0

    def __call__(self):
        return self.now

    def advance(self, ms):
        self.now += ms / 1000.0


def _vib(with_pad=True):
    pad = _Pad()
    clock = _Clock()
    return Vibration(_Pads(pad) if with_pad else _Pads(), clock), pad, clock


def _rumbles(pad):
    return [c for c in pad.calls if c[0] == 'rumble']


def _run(vib, clock, total_ms, step=10):
    """Tick through ``total_ms``, as the frame loop would."""
    for _ in range(total_ms // step + 1):
        vib.tick()
        clock.advance(step)


def test_every_zombie_the_dev_named_has_an_effect():
    assert sorted(ZOMBIE_EFFECTS) == list(range(1, 11))
    for kind, name in ZOMBIE_EFFECTS.items():
        assert name in EFFECTS, (kind, name)
    assert 'girl' in EFFECTS


def test_the_shared_zombies_use_the_effects_the_dev_gave_them():
    z = ZOMBIE_EFFECTS
    assert z[4] == z[2] and z[5] == z[3] and z[7] == z[3]
    assert len({z[1], z[2], z[3], z[6], z[8], z[9], z[10]}) == 7


def test_every_strength_is_a_real_motor_setting():
    for name, segments in EFFECTS.items():
        for start, low, high, ms in segments:
            assert 0.0 <= low <= 1.0 and 0.0 <= high <= 1.0 and ms > 0 and start >= 0, name


def test_the_wind_ups_are_waited_out():
    """Zombie 1 at 803 ms, zombie 3 at 454, zombie 6 at 234, zombie 9 at 227."""
    for kind, wait in ((1, 803), (3, 454), (6, 234), (9, 227)):
        vib, pad, clock = _vib()
        vib.play_zombie(kind)
        _run(vib, clock, wait - 30)
        assert _rumbles(pad) == [], 'zombie %d vibrated before %d ms' % (kind, wait)
        _run(vib, clock, 80)
        assert _rumbles(pad), 'zombie %d did not vibrate after %d ms' % (kind, wait)


def test_zombie_1_is_one_light_thump():
    vib, pad, clock = _vib()
    vib.play_zombie(1)
    _run(vib, clock, 2000)
    r = _rumbles(pad)
    assert len(r) == 1 and r[0][1] < 0.6 and r[0][3] < 300, r


def test_zombie_3_is_a_heavy_rumble_to_the_end_of_its_sound():
    vib, pad, clock = _vib()
    vib.play_zombie(3)
    _run(vib, clock, 3500)
    (_k, low, high, ms), = _rumbles(pad)
    assert low >= 0.6 and 454 + ms == 2941, (low, high, ms)


def test_zombie_2_is_pulses_spread_along_its_sound():
    vib, pad, clock = _vib()
    vib.play_zombie(2)
    _run(vib, clock, 3700)
    r = _rumbles(pad)
    assert len(r) >= 5, r
    assert all(ms <= 200 for _k, _l, _h, ms in r), 'a pulse should be short'


def test_zombie_4_is_zombie_2s_and_5_and_7_are_zombie_3s():
    got = {}
    for kind in (2, 4, 3, 5, 7):
        vib, pad, clock = _vib()
        vib.play_zombie(kind)
        _run(vib, clock, 3700)
        got[kind] = _rumbles(pad)
    assert got[2] == got[4] and got[3] == got[5] == got[7]


def test_zombie_8_is_a_firm_three_quarters_of_a_second():
    vib, pad, clock = _vib()
    vib.play_zombie(8)
    _run(vib, clock, 100)
    (_k, low, _h, ms), = _rumbles(pad)
    assert ms == 750 and low >= 0.6


def test_zombie_9_is_the_hardest_and_short():
    peaks = {}
    for kind in (1, 3, 6, 8, 9):
        vib, pad, clock = _vib()
        vib.play_zombie(kind)
        _run(vib, clock, 3500)
        peaks[kind] = max(low + high for _k, low, high, _ms in _rumbles(pad))
    assert peaks[9] == max(peaks.values())
    assert sum(ms for _s, _l, _h, ms in EFFECTS['smash']) < 600


def test_the_chainsaw_revs_up_saws_and_revs_down():
    vib, pad, clock = _vib()
    vib.play_zombie(10)
    _run(vib, clock, 3300)
    strength = [low for _k, low, _h, _ms in _rumbles(pad)]
    assert strength[0] < 0.3, 'it should start soft'
    peak = max(strength)
    assert peak >= 0.7
    up = strength.index(peak)
    assert strength[:up] == sorted(strength[:up]), 'it should rise over the rev up'
    down = len(strength) - 1 - strength[::-1].index(peak)
    assert strength[down:] == sorted(strength[down:], reverse=True), 'then fall away'
    assert strength[-1] < 0.1, 'and be nearly still at the end'
    # the solid saw runs from 405 ms to 2.219 s, and the rev down starts there
    solid = [c for c in EFFECTS['chainsaw'] if c[0] == 405]
    assert solid and solid[0][0] + solid[0][3] == 2219


def test_the_girl_is_a_long_rumble():
    vib, pad, clock = _vib()
    vib.play('girl')
    _run(vib, clock, 100)
    (_k, _l, _h, ms), = _rumbles(pad)
    assert ms >= 1200


def test_dying_is_two_hard_seconds():
    vib, pad, clock = _vib()
    vib.play('death')
    _run(vib, clock, 100)
    (_k, low, high, ms), = _rumbles(pad)
    assert ms == 2000 and low >= 0.9 and high >= 0.7, (low, high, ms)


def test_a_new_effect_replaces_the_one_playing():
    vib, pad, clock = _vib()
    vib.play_zombie(2)
    _run(vib, clock, 600)
    before = len(pad.calls)
    vib.play_zombie(8)
    assert ('stop',) in pad.calls[before:], 'the old one was not stopped'
    _run(vib, clock, 4000)
    later = [c for c in pad.calls[before:] if c[0] == 'rumble']
    assert [ms for _k, _l, _h, ms in later] == [750], 'the scratching went on under the grab'


def test_stop_silences_the_motors_and_cancels_what_is_queued():
    vib, pad, clock = _vib()
    vib.play_zombie(1)
    vib.stop()
    assert pad.calls[-1] == ('stop',)
    _run(vib, clock, 2000)
    assert _rumbles(pad) == []


def test_without_a_pad_nothing_happens_and_nothing_breaks():
    vib, pad, clock = _vib(with_pad=False)
    assert vib.play_zombie(3) is False
    vib.tick()
    vib.stop()
    assert pad.calls == []


def test_a_zombie_with_no_effect_does_not_vibrate():
    vib, pad, clock = _vib()
    for kind in (11, 12, 21, 22, 5000, 5001):
        assert vib.play_zombie(kind) is False
    _run(vib, clock, 500)
    assert pad.calls == []


def test_a_pad_that_cannot_vibrate_is_skipped():
    class _Dead(_Pad):
        def rumble(self, *a):
            raise RuntimeError('no motors')
    vib = Vibration(_Pads(_Dead()), _Clock())
    assert vib.play('girl')
    vib.tick()


def test_a_late_frame_plays_only_the_latest_segment():
    vib, pad, clock = _vib()
    vib.play_zombie(10)                 # the first soft step starts at once
    assert len(_rumbles(pad)) == 1
    clock.advance(1500)
    vib.tick()
    assert len(_rumbles(pad)) == 2, 'a late frame should play one segment, not every missed one'


# ------------------------------------------------ the hooks in the game
class _Recorder:
    def __init__(self):
        self.played, self.stopped = [], 0

    def play_zombie(self, kind):
        self.played.append(('zombie', kind))

    def play(self, name):
        self.played.append(('effect', name))

    def stop(self):
        self.stopped += 1


def _stage():
    if not pygame.get_init():
        pygame.init()
        pygame.display.set_mode((64, 64))
    S1E.LOADING_SECONDS = 0.0
    d = UserDefaults.standardUserDefaults()
    d.setObject_forKey_('1', 'TUTORIAL')
    d.synchronize()
    app = AppDelegate.shared()
    if app.playback is None:
        app.didFinishLaunching()
    RunLoop.main().reset()
    st = Stage_1_E()
    st.viewDidLoad()
    RunLoop.main().pump()
    return st, app


def test_a_zombie_that_hits_you_vibrates_with_its_own_effect():
    st, app = _stage()
    rec = _Recorder()
    try:
        app.vibration = rec
        m = MonsterControl()
        m.monsterNumber = 6
        m.app = app
        m.playerHitSound = 177
        m.dieSoundTime = 1.0
        m.hitPlayer()
        assert rec.played == [('zombie', 6)], rec.played
    finally:
        app.vibration = None
        st.teardown()


def test_pausing_and_leaving_the_stage_silence_the_motors():
    st, app = _stage()
    rec = _Recorder()
    try:
        app.vibration = rec
        st.StopPlayAction_()
        assert st.gameState == 1 and rec.stopped >= 1, 'pausing did not stop it'
        before = rec.stopped
        st.teardown()
        assert rec.stopped > before, 'leaving the stage did not stop it'
    finally:
        app.vibration = None


def test_shooting_the_girl_rumbles():
    st, app = _stage()
    rec = _Recorder()
    try:
        app.vibration = rec
        m = MonsterControl()
        m.monsterNumber = S1E.MONSTER_GIRL
        st._monster_killed(m)
        assert ('effect', 'girl') in rec.played, rec.played
    finally:
        app.vibration = None
        st.teardown()


def test_dying_vibrates():
    st, app = _stage()
    rec = _Recorder()
    try:
        app.vibration = rec
        st.playerDie_()
        assert ('effect', 'death') in rec.played, rec.played
    finally:
        app.vibration = None
        st.teardown()


def test_without_a_controller_the_game_hooks_do_nothing():
    st, app = _stage()
    try:
        assert app.vibration is None
        app.vibrate_effect('girl')
        app.vibrate_zombie(3)
        app.vibrate_stop()
    finally:
        st.teardown()


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
