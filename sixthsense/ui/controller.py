"""PORT ADDITION: a game controller in place of the keyboard, on the menus.

Built on SDL's game controller layer (``pygame._sdl2.controller``), which gives every pad
the same standard layout on Windows, Linux and macOS, never XInput or raw joystick button
numbers.  aidocks/project_joystick_plan.md has the plan.

Phase 1 is the menus and the screens that work like them.  A controller event becomes the
keyboard event the screen already takes, so no screen changes:

    D-pad, left stick     Up, Down, Left, Right
    A                     Enter
    B                     Escape

The stage is not translated yet (phase 2), and nothing is while the key bindings screen
is open, where a key press would be captured as a binding.
"""
from __future__ import annotations

import logging

log = logging.getLogger('controller')

#: How far the left stick must lean to count as a press, and how far back it must come
#: before it can press again.  The gap keeps a stick resting near the edge from repeating.
STICK_PRESS = 0.6
STICK_RELEASE = 0.3

_BUTTON_KEYS = (('CONTROLLER_BUTTON_DPAD_UP', 'K_UP'),
                ('CONTROLLER_BUTTON_DPAD_DOWN', 'K_DOWN'),
                ('CONTROLLER_BUTTON_DPAD_LEFT', 'K_LEFT'),
                ('CONTROLLER_BUTTON_DPAD_RIGHT', 'K_RIGHT'),
                ('CONTROLLER_BUTTON_A', 'K_RETURN'),
                ('CONTROLLER_BUTTON_B', 'K_ESCAPE'))

#: (the axis, its key when pushed negative, its key when pushed positive)
_STICK_AXES = (('CONTROLLER_AXIS_LEFTX', 'K_LEFT', 'K_RIGHT'),
               ('CONTROLLER_AXIS_LEFTY', 'K_UP', 'K_DOWN'))


class Controllers:
    """Opens the attached pads and turns their events into key events."""

    def __init__(self, pygame):
        self.pygame = pygame
        self._pads = {}                  # instance id -> pygame Controller
        self._lean = {}                  # (instance id, axis) -> -1, 0 or 1
        self._buttons = {getattr(pygame, b): getattr(pygame, k) for b, k in _BUTTON_KEYS}
        self._axes = {getattr(pygame, a): (getattr(pygame, n), getattr(pygame, p))
                      for a, n, p in _STICK_AXES}
        self._sdl = None
        try:
            from pygame._sdl2 import controller
            controller.init()
            self._sdl = controller
            for index in range(controller.get_count()):
                self._open(index)
        except Exception:
            log.exception('controller support is off')

    @property
    def pads(self):
        """The controllers that are attached, oldest first."""
        return list(self._pads.values())

    def _open(self, index):
        try:
            if not self._sdl.is_controller(index):
                return
            pad = self._sdl.Controller(index)
        except Exception:
            log.exception('opening controller %s', index)
            return
        self._pads[pad.id] = pad
        log.info('controller: %s', pad.name)

    def _close(self, instance_id):
        self._pads.pop(instance_id, None)
        for key in [k for k in self._lean if k[0] == instance_id]:
            del self._lean[key]

    def _key(self, key, down):
        pg = self.pygame
        return pg.event.Event(pg.KEYDOWN if down else pg.KEYUP, key=key, mod=0, unicode='')

    def _press(self, key):
        return [self._key(key, True), self._key(key, False)]

    def feed(self, event):
        """Returns ``None`` for an event that is not a controller's, else the key events
        it stands for (possibly none).  Device changes are handled here."""
        pg = self.pygame
        t = event.type
        if t == pg.CONTROLLERDEVICEADDED:
            if self._sdl is not None and getattr(event, 'device_index', None) is not None:
                self._open(event.device_index)
            return []
        if t == pg.CONTROLLERDEVICEREMOVED:
            self._close(getattr(event, 'instance_id', None))
            return []
        if t == pg.CONTROLLERBUTTONDOWN:
            key = self._buttons.get(event.button)
            return self._press(key) if key is not None else []
        if t == pg.CONTROLLERBUTTONUP:
            return []
        if t == pg.CONTROLLERAXISMOTION:
            keys = self._axes.get(event.axis)
            if keys is None:
                return []
            return self._stick(getattr(event, 'instance_id', 0), event.axis,
                               event.value, keys)
        return None

    def _stick(self, pad, axis, value, keys):
        value = float(value)
        if abs(value) > 1.0:
            value /= 32768.0                    # raw SDL units
        lean = self._lean.get((pad, axis), 0)
        if lean == 0:
            if abs(value) < STICK_PRESS:
                return []
            lean = -1 if value < 0 else 1
            self._lean[(pad, axis)] = lean
            return self._press(keys[0] if lean < 0 else keys[1])
        if abs(value) < STICK_RELEASE or (value < 0) != (lean < 0):
            self._lean[(pad, axis)] = 0
            return self._stick(pad, axis, value, keys) if abs(value) >= STICK_PRESS else []
        return []
