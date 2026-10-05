"""PORT ADDITION: where a sound is placed, which is not quite where its zombie is.

The lanes at 10:30 and 1:30 stand 33 degrees either side of straight ahead, which is a lot
to hear apart from the lanes at 9 and 3 and from 12.  The sound is placed nearer 12
(tunmi13productions, 2026-10-05): the angle only, never the distance, so the zombie and
the shot that hits it are still in the same lane.  A bearing is in degrees from 3 o'clock
through 12 (90) to 9 (180), as ``MonsterControl`` has it; ``oal_playback`` hands every
position to ``heard`` just before OpenAL.  Nothing the game works out uses it.
"""
from __future__ import annotations

import math

#: (the bearing the game has, the bearing OpenAL is given).  Lane 4 is 57 and lane 2 is
#: 123; between the points the move fades out, so a zombie that zig-zags between lanes
#: never jumps.  The lanes at 3, 12 and 9 stay where they are.
POINTS = ((0.0, 0.0), (57.0, 70.0), (90.0, 90.0), (123.0, 110.0), (180.0, 180.0))


def heard_bearing(degrees):
    """``degrees`` as it is placed; anything behind you (below 0 or past 180) is left."""
    if not 0.0 <= degrees <= 180.0:
        return degrees
    for (a0, h0), (a1, h1) in zip(POINTS, POINTS[1:]):
        if degrees <= a1:
            return h0 + (h1 - h0) * (degrees - a0) / (a1 - a0)
    return degrees


def heard(pos):
    """``(x, y)`` moved to ``heard_bearing`` at the same distance from the listener."""
    x, y = float(pos[0]), float(pos[1])
    r = math.hypot(x, y)
    if r < 1e-9:
        return x, y
    rad = math.radians(heard_bearing(math.degrees(math.atan2(y, x))))
    return r * math.cos(rad), r * math.sin(rad)
