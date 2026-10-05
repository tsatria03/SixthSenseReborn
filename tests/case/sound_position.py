"""Where a sound is placed: the lanes at 10:30 and 1:30 are heard nearer 12.

A PORT ADDITION (tunmi13productions, 2026-10-05).  Pure arithmetic plus one read-back of a
real source on OpenAL's null driver, so nothing is heard.
"""
from __future__ import annotations

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import _scratch_save                                             # noqa: E402,F401  never the real save

import pygame                                                    # noqa: E402

from sixthsense.game.app_delegate import AppDelegate             # noqa: E402
from sixthsense.platform.runloop import RunLoop                  # noqa: E402
from sixthsense.platform.sound_position import heard, heard_bearing  # noqa: E402


def _at(bearing, r=400.0):
    rad = math.radians(bearing)
    return r * math.cos(rad), r * math.sin(rad)


def _bearing(pos):
    return math.degrees(math.atan2(pos[1], pos[0]))


def test_the_lanes_at_10_30_and_1_30_move_towards_12():
    assert heard_bearing(57) > 57 and heard_bearing(57) < 90
    assert heard_bearing(123) < 123 and heard_bearing(123) > 90
    assert abs((heard_bearing(123) - 90) - (90 - heard_bearing(57))) < 1e-9, 'both sides alike'


def test_3_12_and_9_stay_put():
    for b in (0, 90, 180):
        assert abs(heard_bearing(b) - b) < 1e-9, b


def test_the_distance_never_changes():
    for b in (0, 30, 57, 75, 90, 123, 150, 180):
        for r in (20.0, 400.0, 1000.0):
            x, y = heard(_at(b, r))
            assert abs(math.hypot(x, y) - r) < 1e-6, (b, r)


def test_the_move_never_jumps_and_keeps_the_order_of_the_lanes():
    last = -1.0
    for tenth in range(0, 1801):
        h = heard_bearing(tenth / 10.0)
        assert h >= last, tenth
        assert abs(h - last) < 0.5 or last < 0, tenth
        last = h


def test_behind_you_and_the_listener_are_left_alone():
    assert heard((0.0, 0.0)) == (0.0, 0.0)
    for b in (185, 200, 270, -30, -175):
        x, y = _at(b)
        hx, hy = heard((x, y))
        assert abs(hx - x) < 1e-6 and abs(hy - y) < 1e-6, b


def test_a_zombie_in_lane_2_is_really_placed_nearer_12():
    if not pygame.get_init():
        pygame.init()
    app = AppDelegate.shared()
    if app.playback is None:
        app.didFinishLaunching()
    RunLoop.main().reset()
    pb = app.playback
    try:
        for lane_bearing, want in ((123.0, heard_bearing(123.0)), (57.0, heard_bearing(57.0)),
                                   (90.0, 90.0)):
            app.playSound_Gain_Pos_z_reprats_(93, 1.0, _at(lane_bearing, 500.0), 40, False)
            i = app.CheckSoundBuf_(93)
            x, _h, y = pb.al.source_position(pb._sources[i].sourceId)
            assert abs(_bearing((x, y)) - want) < 0.01, (lane_bearing, _bearing((x, y)))
            assert abs(math.hypot(x, y) - 500.0) < 0.01
            app.stopSoundBufNumber_(93)
    finally:
        RunLoop.main().reset()


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
