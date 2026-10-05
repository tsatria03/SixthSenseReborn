"""PORT ADDITION: a game controller in place of the keyboard, on the menus.

Built on SDL's game controller layer (``pygame._sdl2.controller``), which gives every pad
the same standard layout on Windows, Linux and macOS, never XInput or raw joystick button
numbers.  aidocks/project_joystick_plan.md has the plan.

Phase 1 is the menus and the screens that work like them.  A controller event becomes the
keyboard event the screen already takes, so no screen changes:

    D-pad, left stick     Up, Down, Left, Right
    A                     Enter
    B                     Escape

The stage reads the controller itself (``Input.controller``), except for the pause and
result panels, which take these keys.  Nothing is translated while the key bindings screen
is open, where a key press would be captured as a binding.
"""
from __future__ import annotations

import logging

log = logging.getLogger('controller')


def read_events(pygame):
    """``pygame.event.get()``, kept from crashing on a device event pygame cannot map.

    A DualSense on Windows is listed twice at start: SDL finds it, then lets its own driver
    take it over, so the first listing is removed again.  The removal arrives for a pad that
    pygame never put in its table, and ``pygame.event.get()`` raises ``SystemError`` (from a
    ``KeyError``) before it returns anything, which ended the game as it started.  The
    event is lost with the rest of that one batch, which is only device events at start, and
    the next call goes on from the queue.  Found with a DualSense, 2026-10-05.
    """
    try:
        return pygame.event.get()
    except SystemError:
        log.warning('pygame could not read a device event, so it was skipped', exc_info=True)
        return []


def instance_id(pad):
    """SDL's instance id for an open pad, which is what its events carry.

    pygame's ``Controller.id`` is the device index the pad was opened with.  It is the
    instance id only until a device has come and gone: the DualSense above is index 0 and
    instance 1, so its removal could not be matched to it by ``pad.id``.  A stand-in with no
    joystick is its ``id``."""
    try:
        return pad.as_joystick().get_instance_id()
    except Exception:
        return pad.id

#: PORT ADDITION: the sounds for a controller found and lost, their entries in
#: SoundList.plist, and the short buzz that follows the first (low motor, high motor,
#: milliseconds).
SOUND_DETECTED = 372
SOUND_NOT_DETECTED = 373
CONNECT_BUZZ = (0.5, 0.5, 200)

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


def axis_value(value):
    """An axis event's value as -1.0 to 1.0, whether pygame gave it so or in SDL's raw
    units."""
    value = float(value)
    return value / 32768.0 if abs(value) > 1.0 else value


class Controllers:
    """Opens the attached pads and turns their events into key events."""

    def __init__(self, pygame, app=None, sdl=None):
        """``sdl`` is pygame's controller module; the tests pass a stand-in, so they never
        open or buzz a real pad."""
        self.pygame = pygame
        self.app = app                  # plays the sounds; none, none are played
        self._pads = {}                  # instance id -> pygame Controller
        self._lean = {}                  # (instance id, axis) -> -1, 0 or 1
        self._buttons = {getattr(pygame, b): getattr(pygame, k) for b, k in _BUTTON_KEYS}
        self._axes = {getattr(pygame, a): (getattr(pygame, n), getattr(pygame, p))
                      for a, n, p in _STICK_AXES}
        self.just_lost = False          # the last event took away a pad that was open
        self._sdl = None
        try:
            controller = sdl
            if controller is None:
                from pygame._sdl2 import controller
            controller.init()
            self._sdl = controller
            for index in range(controller.get_count()):
                self._open(index, announce=False)
        except Exception:
            log.exception('controller support is off')

    def announce_attached(self):
        """The pads already attached when the game started are found now, once the sounds
        can play."""
        for pad in self.pads:
            self._found(pad)

    def _play(self, number):
        if self.app is None:
            return
        try:
            self.app.playSound_Gain_Pos_z_reprats_(number, 1.0, (0.0, 0.0), 0, False)
        except Exception:
            log.exception('playing sound %s', number)

    def _found(self, pad):
        """A controller was found and opened: its sound, then a short buzz."""
        self._play(SOUND_DETECTED)
        if self.app is not None and not getattr(self.app, 'vibration_on', True):
            return                      # the player has vibration off
        try:
            pad.rumble(*CONNECT_BUZZ)
        except Exception:
            log.debug('%s did not buzz', pad.name)

    @property
    def pads(self):
        """The controllers that are attached, oldest first."""
        return list(self._pads.values())

    @property
    def pad_ids(self):
        """Their SDL instance ids, in the same order."""
        return list(self._pads)

    def _open(self, index, announce=True):
        try:
            if not self._sdl.is_controller(index):
                return
            pad = self._sdl.Controller(index)
        except Exception:
            log.exception('opening controller %s', index)
            return
        ident = instance_id(pad)
        if ident in self._pads:
            return                      # SDL announces what start-up already found
        self._pads[ident] = pad
        log.info('controller: %s', pad.name)
        if announce:
            self._found(pad)

    def _close(self, instance_id):
        if self._pads.pop(instance_id, None) is not None:
            self.just_lost = True
            self._play(SOUND_NOT_DETECTED)
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
        self.just_lost = False
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
        value = axis_value(value)
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
