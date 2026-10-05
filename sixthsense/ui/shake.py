"""PORT ADDITION: shaking a game controller to shake a zombie off.

The animal zombie that grabs you is shaken off by pressing the shake key a few times
(``Stage_1_E.shake_step``); in the original it was the phone that was shaken.  A pad with an
accelerometer, a DualSense for one, can be shaken for the same effect, beside A.  An Xbox pad
has no sensor, so it only has A, and the tutorial only offers the shake when ``capable``
(aidocks/project_controller_shake_plan.md).

The sensor is only switched on and read while a zombie holds you, so nothing is read, and no pad
is kept busy, the rest of the time.  ``Shake.tick`` is called once a frame by the game's loop.
The pads and the clock are stand-ins in the tests.
"""
from __future__ import annotations

import math
import time

from ..platform.motion import Motion

#: A pad lying still reads this, in m/s^2.
GRAVITY = 9.80665
#: A shake is the reading leaving gravity by this much, about 1.2 g: a firm flick, which a pad
#: being carried or set down does not reach.  To be tuned by ear on a real pad.
SHAKE_THRESHOLD = 12.0
#: One shake is one press: the next counts only after this many seconds.
SHAKE_GAP = 0.25


class Shake:
    def __init__(self, controllers, motion=None, clock=time.monotonic):
        self.controllers = controllers
        self.motion = motion if motion is not None else Motion()
        self.clock = clock
        self._can = {}                      # instance id -> has an accelerometer
        self._listening = set()             # the pads whose sensor is on
        self._last = {}                     # instance id -> when it last shook

    def _ids(self):
        return [pad.id for pad in self.controllers.pads if hasattr(pad, 'id')]

    def _capable_ids(self):
        ids = self._ids()
        for gone in [i for i in self._can if i not in ids]:
            del self._can[gone]
            self._listening.discard(gone)
            self._last.pop(gone, None)
        for i in ids:
            if i not in self._can:
                self._can[i] = self.motion.has_accelerometer(i)
        return [i for i in ids if self._can[i]]

    def capable(self) -> bool:
        """Whether an attached pad can sense a shake."""
        return bool(self._capable_ids())

    def tick(self, active, on_shake) -> int:
        """Once a frame.  While ``active`` (a zombie holds you), listen, and call ``on_shake()``
        for each shake; otherwise make sure no sensor is on.  Returns the shakes this frame."""
        if not active:
            for i in list(self._listening):
                self.motion.enable(i, False)
            self._listening.clear()
            return 0
        shakes = 0
        for i in self._capable_ids():
            if i not in self._listening:
                self.motion.enable(i, True)
                self._listening.add(i)
            a = self.motion.acceleration(i)
            if a is None:
                continue
            now = self.clock()
            if (abs(math.sqrt(a[0] * a[0] + a[1] * a[1] + a[2] * a[2]) - GRAVITY) >= SHAKE_THRESHOLD
                    and now - self._last.get(i, -1e9) >= SHAKE_GAP):
                self._last[i] = now
                shakes += 1
                on_shake()
        return shakes
