"""PORT ADDITION: what a game controller's motors do when something hits you.

The dev laid the effects out (2026-10-04; aidocks/project_joystick_plan.md).  Each zombie
has its own, started with its hit sound, so the times below are from the start of that
sound.  An effect is a list of segments, ``(start_ms, low, high, ms)``: from ``start_ms``
the low (heavy) motor runs at ``low`` and the high (light) motor at ``high``, each 0.0 to
1.0, for ``ms``.  pygame's ``rumble`` holds one setting at a time, so pulses and ramps are
a series of segments, and an effect that starts replaces the one still playing.

``Vibration.tick`` is called once a frame by the game's loop.  Nothing here touches a pad
unless one is attached, and the tests give it fake pads and a fake clock.
"""
from __future__ import annotations

import logging
import time

log = logging.getLogger('vibration')

#: How often a ramp changes, and how much each step overlaps the next so the motor never
#: drops out between them.
STEP_MS = 50
OVERLAP_MS = 15


def _ramp(start, end, low, high):
    """Segments from ``start`` to ``end`` ms, ``low`` and ``high`` each a (from, to) pair."""
    steps = max(1, round((end - start) / STEP_MS))
    out = []
    for i in range(steps):
        a = i / steps
        t0 = start + (end - start) * i / steps
        out.append((round(t0), round(low[0] + (low[1] - low[0]) * a, 3),
                    round(high[0] + (high[1] - high[0]) * a, 3),
                    round((end - start) / steps) + OVERLAP_MS))
    return out


def _pulses(first, last, every, low, high, ms):
    out, t = [], first
    while t <= last:
        out.append((t, low, high, ms))
        t += every
    return out


EFFECTS = {
    # zombie 1: a light punch after the wind-up
    'punch': [(803, 0.45, 0.25, 160)],
    # zombie 2, and 4: scratching, firm pulses spread out along the 3.6 s sound
    'scratch': _pulses(0, 3200, 520, 0.30, 0.55, 140),
    # zombie 3, and 5 and 7: mauling, a heavy rumble from 454 ms to the end of the 2.941 s
    'maul': [(454, 0.75, 0.45, 2941 - 454)],
    # zombie 6: a quick firm pounce
    'pounce': [(234, 0.80, 0.50, 170)],
    # zombie 8: it was not shaken off
    'grab': [(0, 0.70, 0.50, 750)],
    # zombie 9: a hard, big smash with a short tail
    'smash': [(227, 1.0, 0.90, 220), (447, 0.55, 0.35, 180)],
    # zombie 10, the chainsaw: revs up for 405 ms, saws solid, revs down from 2.219 s
    'chainsaw': (_ramp(0, 405, (0.15, 0.70), (0.10, 0.40))
                 + [(405, 0.70, 0.40, 2219 - 405)]
                 + _ramp(2219, 3198, (0.70, 0.0), (0.40, 0.0))),
    # the girl who heals you, shot by mistake: a long rumble, that was a bad move
    'girl': [(0, 0.60, 0.35, 1600)],
    # you die: two hard seconds, from the moment the game over music starts
    'death': [(0, 1.0, 0.80, 2000)],
}

#: ``MonsterControl.monsterNumber`` to its effect.  Zombies 4, 5 and 7 share the hit sound
#: of 2, 3 and 3 in the original, and the dev gave them those effects.
ZOMBIE_EFFECTS = {1: 'punch', 2: 'scratch', 3: 'maul', 4: 'scratch', 5: 'maul',
                  6: 'pounce', 7: 'maul', 8: 'grab', 9: 'smash', 10: 'chainsaw'}


class Vibration:
    def __init__(self, controllers, clock=time.monotonic):
        self.controllers = controllers
        self.clock = clock
        self._queue = []                    # (due time, low, high, ms), soonest first

    def play(self, name):
        """Start an effect by name, replacing the one playing.  Nothing happens without a
        pad or for a name that has no effect."""
        segments = EFFECTS.get(name)
        pads = self.controllers.pads
        if not segments or not pads:
            return False
        self.stop()
        now = self.clock()
        self._queue = [(now + start / 1000.0, low, high, ms)
                       for start, low, high, ms in segments]
        self.tick()                         # a segment at 0 starts now, not a frame late
        return True

    def play_zombie(self, kind):
        """The effect for a zombie's blow, by its ``monsterNumber``, if it has one."""
        name = ZOMBIE_EFFECTS.get(kind)
        return self.play(name) if name else False

    def tick(self):
        """Run what is due.  If a slow frame let several segments pass, only the latest
        matters."""
        if not self._queue:
            return
        now = self.clock()
        due = None
        while self._queue and self._queue[0][0] <= now:
            due = self._queue.pop(0)
        if due is None:
            return
        _t, low, high, ms = due
        for pad in self.controllers.pads:
            try:
                pad.rumble(low, high, ms)
            except Exception:
                log.debug('%s did not vibrate', getattr(pad, 'name', 'a pad'))

    def stop(self):
        """Cancel what is queued and silence the motors, for a pause, the end of a stage
        and a pad being lost."""
        had = bool(self._queue)
        self._queue = []
        for pad in self.controllers.pads:
            try:
                pad.stop_rumble()
            except Exception:
                pass
        return had
