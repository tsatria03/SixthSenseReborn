"""PORT ADDITION: a game controller's motion sensor, read through SDL.

A DualSense (and a DualShock 4, a Switch Pro pad and Joy-Cons) has an accelerometer; an Xbox
pad has none.  pygame 2.6 does not wrap SDL's sensor calls, so they are made here through
ctypes on the SDL2 library pygame itself ships, which is the one that has the pad open.  The
accelerometer comes in metres per second squared with gravity in it, so a pad lying still
reads about 9.81.

Everything here fails quietly: no library, an old SDL or a pad with no sensor means no motion,
never an error (aidocks/completed/controller_shake_plan.md).  ``library`` stands in for the SDL
library in the tests, which never touch a real pad.
"""
from __future__ import annotations

import ctypes
import glob
import logging
import os
import sys

log = logging.getLogger('motion')

#: SDL_SENSOR_ACCEL.
ACCELEROMETER = 1

_FUNCTIONS = (
    ('SDL_GameControllerFromInstanceID', ctypes.c_void_p, (ctypes.c_int32,)),
    ('SDL_GameControllerHasSensor', ctypes.c_int, (ctypes.c_void_p, ctypes.c_int)),
    ('SDL_GameControllerSetSensorEnabled', ctypes.c_int, (ctypes.c_void_p, ctypes.c_int, ctypes.c_int)),
    ('SDL_GameControllerGetSensorData', ctypes.c_int,
     (ctypes.c_void_p, ctypes.c_int, ctypes.POINTER(ctypes.c_float), ctypes.c_int)),
)


def _candidates():
    """Where pygame keeps its SDL2: beside it on Windows, in ``pygame.libs`` on Linux, in
    ``.dylibs`` on macOS, or in the folder a frozen build unpacks to."""
    roots = []
    try:
        import pygame
        here = os.path.dirname(pygame.__file__)
        roots += [here, os.path.join(here, '.dylibs'), os.path.join(os.path.dirname(here), 'pygame.libs')]
    except Exception:
        pass
    frozen = getattr(sys, '_MEIPASS', None)
    if frozen:
        roots += [frozen, os.path.join(frozen, 'pygame'), os.path.join(frozen, 'pygame', '.dylibs'),
                  os.path.join(frozen, 'pygame.libs')]
    found = []
    for root in roots:
        for pattern in ('SDL2.dll', 'libSDL2-2*', 'libSDL2*.dylib', 'libSDL2.so*'):
            found += sorted(glob.glob(os.path.join(root, pattern)))
    return found


def load_sdl():
    """SDL2 with the four sensor calls typed, or None.  Loading a path pygame already loaded
    gives the same library, with the same pads open."""
    for path in _candidates():
        try:
            lib = ctypes.CDLL(path)
            for name, result, args in _FUNCTIONS:
                function = getattr(lib, name)
                function.restype, function.argtypes = result, list(args)
            return lib
        except (OSError, AttributeError):
            continue
    return None


class Motion:
    def __init__(self, library=None):
        self.lib = library if library is not None else load_sdl()
        if self.lib is None:
            log.info('motion: no SDL library with sensors, so no shaking')

    def _pad(self, instance_id):
        try:
            return self.lib.SDL_GameControllerFromInstanceID(instance_id)
        except Exception:
            return None

    def has_accelerometer(self, instance_id) -> bool:
        """Whether the open pad with this instance id reports an accelerometer."""
        if self.lib is None:
            return False
        try:
            pad = self._pad(instance_id)
            return bool(pad) and bool(self.lib.SDL_GameControllerHasSensor(pad, ACCELEROMETER))
        except Exception:
            return False

    def enable(self, instance_id, on: bool) -> bool:
        """Switch the accelerometer on or off; a pad only sends it while it is on."""
        if self.lib is None:
            return False
        try:
            pad = self._pad(instance_id)
            return bool(pad) and self.lib.SDL_GameControllerSetSensorEnabled(
                pad, ACCELEROMETER, 1 if on else 0) == 0
        except Exception:
            return False

    def acceleration(self, instance_id):
        """``(x, y, z)`` in m/s^2, or None when the pad gives none."""
        if self.lib is None:
            return None
        try:
            pad = self._pad(instance_id)
            if not pad:
                return None
            data = (ctypes.c_float * 3)()
            if self.lib.SDL_GameControllerGetSensorData(pad, ACCELEROMETER, data, 3) != 0:
                return None
            return float(data[0]), float(data[1]), float(data[2])
        except Exception:
            return None
