"""Keyboard in place of the iPhone's touchscreen and accelerometer.

The original has four inputs, all of them on the device:

    UIPanGestureRecognizer          -> -[Stage_1_E MovingShot:]          attack, by angle
    UITapGestureRecognizer, 2 touch -> -[Stage_1_E doubleTapChangeWeapon:]
    UITapGestureRecognizer, 3 touch -> -[Stage_1_E threeTapChangeWeapon:]
    UIAccelerometer                 -> -[Stage_1_E accelerometer:didAccelerate:]
                                       (shaking free of a zombie that has grabbed you)

``MovingAccelerometer`` would turn you on a tilt, but nothing in the binary creates one
or sends ``setListenerRotation:``, so the original never turns you, and neither does
the port.

Windows gets the same inputs on the keyboard, through ``platform/keymap.py``, which holds
the bindings and resolves chords. The defaults put the five lanes on the arrow keys in
the shape the tutorial describes - it teaches them as clock positions, and the arrows
are a clock face:

        9 o'clock   Left        10:30  Left+Up      12  Up
        1:30  Right+Up          3      Right        6   Down = reload

with A Q W E D S bound alongside for a one-handed grip. F1 opens the binding screen; F1 and Escape are the two
keys that cannot be rebound.

Escape pauses a stage, as P does, and on the pause panel it resumes, as Continue does.
In the tutorial, where the stop button skips the lessons, Escape still leaves for the
menu.

The lane keys replace the swipe rather than simulating it, which loses nothing:
``-[Stage_1_E MovingShot:]`` quantises its angle into five bands and a reload sector
before anything else looks at it, so a key hands the stage the band directly.

There is no mouse. Everything is reachable without leaving the home row or the arrow
cluster, which is the point for a game meant to be played with the screen off.
"""
from __future__ import annotations

import logging
import math
import time

from ..game.weapon_control import MG80_NUMBER
from ..platform import volume
from ..platform.keymap import CHORD_WINDOW, KeyMap
from .controller import STICK_PRESS, STICK_RELEASE, axis_value

log = logging.getLogger('input')

# The bearing at the centre of each lane, from MOVING_TYPE_ANGLE in monster_control.
# These are the clock positions the tutorial names.
LANE_ANGLE = {1: 180.0, 2: 123.0, 3: 90.0, 4: 57.0, 5: 0.0}
LANE_ACTIONS = {'lane1': 1, 'lane2': 2, 'lane3': 3, 'lane4': 4, 'lane5': 5}

#: PORT ADDITION (tunmi13productions, 2026-09-26): Page Up and Page Down during play, on their own
#: for the gameplay gain and with a modifier for a group.  Fixed, like the menu's.
#: aidocks/project_gameplay_gain_plan.md has the plan.
VOLUME_STEP_KEYS = {'page up': 1, 'page down': -1}
#: (the pygame modifier, its setting, what is said), tried in this order.
VOLUME_MODIFIERS = (('KMOD_SHIFT', volume.WEAPON_KEY, 'Weapons'),
                    ('KMOD_ALT', volume.PLAYER_KEY, 'Player'))
#: Control set the entities until tunmi13productions removed that on 2026-09-28; they are
#: always at full volume, and Control with either key now does nothing.
IGNORED_MODIFIER = 'KMOD_CTRL'


def gameplay_volume_key(name, mod, stage, pygame):
    """Page Up or Page Down in play: step the gain, or with Shift or Alt the weapons or
    the player, and say the new value in either speech mode, since no recording says it.
    True when ``name`` was one of the two keys."""
    if name not in VOLUME_STEP_KEYS:
        return False
    if mod & getattr(pygame, IGNORED_MODIFIER, 0):
        return True
    key, what = volume.GAMEPLAY_GAIN_KEY, None
    for flag, setting, label in VOLUME_MODIFIERS:
        if mod & getattr(pygame, flag, 0):
            key, what = setting, label
            break
    value = stage.app.change_gameplay_volume(key, VOLUME_STEP_KEYS[name])
    if what is None:
        stage._say('Gain %d decibel%s' % (value, '' if value == 1 else 's'))
    else:
        stage._say('%s volume %d%%' % (what, value))
    return True


#: PORT ADDITION: how long a lean of the stick waits before it fires, so a push toward a
#: diagonal, whose two axes arrive as separate events, is read as the diagonal and not as
#: the first axis alone.  The stick's version of the keyboard's chord window.
AIM_SETTLE = 0.06


#: PORT ADDITION: the D-pad in play is the arrow keys' clock face: Left 9, Left+Up 10:30,
#: Up 12, Right+Up 1:30, Right 3, Down reload.  The three that can grow into a diagonal wait
#: out the keyboard's chord window; Down and the diagonals fire at once.
DPAD_LANES = {frozenset(('left',)): 1, frozenset(('left', 'up')): 2, frozenset(('up',)): 3,
              frozenset(('right', 'up')): 4, frozenset(('right',)): 5,
              frozenset(('down',)): 'reload'}
DPAD_EXTENDABLE = (frozenset(('left',)), frozenset(('up',)), frozenset(('right',)))


class Input:
    """Turns pygame key events into the calls the stage expects."""

    def __init__(self, stage, keymap=None):
        self.stage = stage
        self.keymap = keymap or KeyMap.shared()
        self.quit = False
        self.open_bindings = False        # the frame loop watches this for F1
        self._pending_at = None           # when the chord window closes
        self.last_lane = 3                # where --debug's F5 spawns
        self._auto_lane = None            # the lane a held key keeps firing down
        self._dpad = set()                # the D-pad directions held: 'up', 'left', ...
        self._dpad_due = None             # when the D-pad's chord window closes
        self._stick = {}                  # the left stick: axis -> -1.0 to 1.0
        self._aiming = False              # leaned out and not yet back to the middle
        self._aim_fired = False
        self._aim_due = 0.0               # when the lean settles and fires
        self._aim_peak = (0.0, 0.0)       # the furthest it went, for a flick
        # The keymap is shared, and a key that was down when the last screen went away
        # never had its key-up delivered here.  Left held, it makes the next stage read
        # chords nobody is pressing.
        self.keymap.clear_held()

    # ---- the actions -----------------------------------------------------
    def attack_lane(self, lane):
        """What the pan gesture ends in: ``-[Stage_1_E MovingShot:]`` with the bearing
        of the lane, which is the band the original would have quantised to."""
        if lane in LANE_ANGLE:
            self.last_lane = lane
            self._auto_lane = lane
            self.stage.MovingShot_(LANE_ANGLE[lane])

    def _auto_fire(self):
        """PORT ADDITION: the MG80 keeps firing down the lane while its key is held.
        ``MovingShot_`` ignores a press while ``shotFlag`` is up, so asking every frame
        fires at the weapon's ``ShotTime``.  Every other weapon stays one shot per press."""
        st = self.stage
        weapon = st.weaponSource[st.gamePlayer.useWepon]
        if (weapon is None or weapon.WeaponNumber != MG80_NUMBER
                or (weapon.BulletCount <= 0 and not st.app.debug)):
            self._auto_lane = None      # empty: no click on every frame
            return
        st.MovingShot_(LANE_ANGLE[self._auto_lane])

    # ---- the controller (PORT ADDITION, aidocks/project_joystick_plan.md) -------
    def controller(self, event, pygame, keys, lost=False):
        """A controller event, with the key events ``Controllers.feed`` made of it, and
        ``lost``: it took away a pad that was open.  The panels take those keys, as the
        menus do.  In play the left stick aims like the swipe, and the buttons are reload,
        weapon change, shake and pause; losing the pad pauses, so nothing happens to you
        while you plug it back in.  The tutorial has no pause and is left running."""
        st = self.stage
        if event.type == pygame.CONTROLLERDEVICEREMOVED:
            self._stick = {}
            self._aim_reset()
            self._dpad_reset()
            if lost and st.gameState == 0 and not getattr(st, 'ESCAPE_LEAVES', False):
                st.StopPlayAction_()
        if st.gameState != 0:
            self._aim_reset()
            self._dpad_reset()
            for key in keys:
                self.handle(key, pygame)
            return
        way = {pygame.CONTROLLER_BUTTON_DPAD_UP: 'up', pygame.CONTROLLER_BUTTON_DPAD_DOWN: 'down',
               pygame.CONTROLLER_BUTTON_DPAD_LEFT: 'left',
               pygame.CONTROLLER_BUTTON_DPAD_RIGHT: 'right'}.get(getattr(event, 'button', None))
        if way and event.type == pygame.CONTROLLERBUTTONDOWN:
            self._dpad_down(way)
        elif way and event.type == pygame.CONTROLLERBUTTONUP:
            self._dpad_up(way)
        elif event.type == pygame.CONTROLLERBUTTONDOWN:
            action = {pygame.CONTROLLER_BUTTON_X: 'reload',
                      pygame.CONTROLLER_BUTTON_RIGHTSHOULDER: 'next_weapon',
                      pygame.CONTROLLER_BUTTON_LEFTSHOULDER: 'prev_weapon',
                      pygame.CONTROLLER_BUTTON_A: 'shake',
                      pygame.CONTROLLER_BUTTON_B: 'escape',
                      pygame.CONTROLLER_BUTTON_START: 'escape'}.get(event.button)
            if action == 'escape':
                self.escape()
            else:
                self.perform(action)
        elif event.type == pygame.CONTROLLERAXISMOTION and event.axis in (
                pygame.CONTROLLER_AXIS_LEFTX, pygame.CONTROLLER_AXIS_LEFTY):
            self._stick[event.axis == pygame.CONTROLLER_AXIS_LEFTY] = axis_value(event.value)
            self._aim_step()

    def _dpad_fire(self):
        """Act on the D-pad as it stands: the lane or the reload it names, if any."""
        what = DPAD_LANES.get(frozenset(self._dpad))
        if what == 'reload':
            self.stage.ReloadGesture()
        elif what is not None:
            self.attack_lane(what)

    def _dpad_down(self, way):
        self._dpad.add(way)
        held = frozenset(self._dpad)
        if held in DPAD_EXTENDABLE:
            self._dpad_due = time.monotonic() + CHORD_WINDOW   # might become a diagonal
        else:
            self._dpad_due = None
            self._dpad_fire()

    def _dpad_up(self, way):
        if self._dpad_due is not None:          # let go before the window closed
            self._dpad_due = None
            self._dpad_fire()
        self._dpad.discard(way)
        self._auto_lane = None                  # any key up ends a burst, as on the keyboard

    def _dpad_reset(self):
        self._dpad.clear()
        self._dpad_due = None

    def _vector(self):
        return self._stick.get(False, 0.0), self._stick.get(True, 0.0)

    def _aim_step(self):
        """The stick moved: start a lean, grow its peak, or end it.  Y is down."""
        x, y = self._vector()
        size = math.hypot(x, y)
        if not self._aiming:
            if size >= STICK_PRESS:
                self._aiming, self._aim_fired = True, False
                self._aim_due = time.monotonic() + AIM_SETTLE
                self._aim_peak = (x, y)
        elif size < STICK_RELEASE:
            if not self._aim_fired:
                self._aim_fire(self._aim_peak)      # a flick let go before it settled
            self._aim_reset()
        elif size > math.hypot(*self._aim_peak):
            self._aim_peak = (x, y)

    def _aim_fire(self, vector):
        """Fire where the stick points: its angle, up being 12 o'clock, through the lane
        bands the swipe uses.  Down is the reload sector."""
        st = self.stage
        self._aim_fired = True
        angle = math.degrees(math.atan2(-vector[1], vector[0])) % 360.0
        weapon = st.weaponSource[st.gamePlayer.useWepon]
        melee = weapon is not None and weapon.WeaponNumber in (1, 7)
        lane = st._lane_for_angle(angle, melee=melee)
        if lane == 'reload':
            st.ReloadGesture()
        else:
            self.attack_lane(lane)

    def _aim_reset(self):
        """The lean is over: no burst goes on."""
        if self._aiming:
            self._auto_lane = None
        self._aiming = False
        self._aim_fired = False

    def perform(self, action):
        if action is None:
            return
        st = self.stage
        lane = LANE_ACTIONS.get(action)
        if lane is not None:
            self.attack_lane(lane)
        elif action == 'reload':
            st.ReloadGesture()
        elif action == 'next_weapon':
            st.doubleTapChangeWeapon_()
        elif action == 'prev_weapon':
            st.threeTapChangeWeapon_()
        elif action == 'shake':
            st.shake_step()
        elif action == 'pause':
            st.StopPlayAction_()
        elif action.startswith('debug_'):
            from ..game import debug
            debug.perform(st, action, self.last_lane)

    def escape(self):
        """PORT ADDITION: pause and resume.  On the panel after a mission or a death
        there is nothing to resume, so it does nothing; the Main menu row leaves."""
        st = self.stage
        if getattr(st, 'ESCAPE_LEAVES', False):
            self.quit = True
        elif st.gameState == 0:
            st.StopPlayAction_()
        elif st.gameState == 1:
            st.StopElseSpeak()
            st.continueAction_()

    # ---- the pause and result panel ---------------------------------------
    def handle_panel(self, event, pygame):
        """``gameState`` is not 0, so the panel is up and it owns the keyboard.

        ``-[Stage_1_E selectTapPointSoundStart]`` reads whichever row the finger is
        over and ``-[Stage_1_E tapCount]`` runs it on a double tap, so Up and Down
        walk the same rows in the same order and Enter is the double tap - the way
        the main menu was ported.  The lane keys are not attacks while it is up:
        nothing in the original reaches ``MovingShot:`` from the panel either, because
        the pan recogniser is swapped for the tap recogniser at 0x34f96.
        """
        if event.type != pygame.KEYDOWN:
            return
        name = pygame.key.name(event.key)
        st = self.stage
        if gameplay_volume_key(name, getattr(event, 'mod', 0), st, pygame):
            return
        if name == 'escape':
            self.escape()
        elif name == 'f1':
            self.open_bindings = True
        elif name == 'up':
            st.pause_move(-1)
        elif name == 'down':
            st.pause_move(1)
        elif name in ('return', 'enter', 'space'):
            if st.selectMenu:
                st.pause_activate()
            else:
                st.pause_move(1)          # nothing chosen yet: start at the top
        elif name in ('home', 'end') and st.app.screen_reader:
            # the screen reader mode: the first row or the last, as its lists go
            st.pause_jump(last=(name == 'end'))
        elif name in ('left', 'right') and st.app.screen_reader:
            # ...and Left and Right as VoiceOver's flicks: right is the next row
            st.pause_move(1 if name == 'right' else -1)
        else:
            st.blindModeSelectedMenu()

    # ---- events ----------------------------------------------------------
    def handle(self, event, pygame):
        if event.type == pygame.QUIT:
            self.quit = True
            return
        # Alt+Tab away with a key down and its key-up goes to whatever took the focus,
        # so forget what is held rather than leave it stuck.
        if event.type in (getattr(pygame, 'WINDOWFOCUSLOST', -1),
                          getattr(pygame, 'ACTIVEEVENT', -1)):
            self.reset()
            return
        if self.stage.gameState != 0:
            self.reset()
            self.handle_panel(event, pygame)
            return
        if event.type == pygame.KEYDOWN:
            name = pygame.key.name(event.key)
            if name == 'escape':
                self.escape()
                return
            if name == 'f1':
                self.open_bindings = True
                return
            if gameplay_volume_key(name, getattr(event, 'mod', 0), self.stage, pygame):
                return
            held_already = name in self.keymap.held
            action, pending = self.keymap.press(name)
            if action == 'shake' and held_already:
                return                  # a held key's repeat is not another shake
            if action is not None:
                self._pending_at = None
                self.perform(action)
            elif pending:
                # might still become a longer chord; decide when the window closes
                self._pending_at = time.monotonic() + CHORD_WINDOW
        elif event.type == pygame.KEYUP:
            name = pygame.key.name(event.key)
            if self._pending_at is not None and name in self.keymap.held:
                # let go before the window closed - take it as it stands
                action = self.keymap.settle()
                self._pending_at = None
                self.perform(action)
            self.keymap.release(name)
            self._auto_lane = None      # any key up ends the burst; press again to resume

    def pump(self):
        """Called once a frame, to close an open chord window and keep a held MG80 firing."""
        if self.stage.gameState != 0:
            self._pending_at = None
            self._auto_lane = None
            self._aim_reset()
            self._dpad_reset()
            return
        if self._dpad_due is not None and time.monotonic() >= self._dpad_due:
            self._dpad_due = None
            self._dpad_fire()
        if self._aiming and not self._aim_fired and time.monotonic() >= self._aim_due:
            x, y = self._vector()
            self._aim_fire((x, y) if math.hypot(x, y) >= STICK_PRESS else self._aim_peak)
        if self._pending_at is not None and time.monotonic() >= self._pending_at:
            self._pending_at = None
            self.perform(self.keymap.settle())
        elif self._auto_lane is not None:
            self._auto_fire()

    def reset(self):
        self._pending_at = None
        self._auto_lane = None
        self._aim_reset()
        self._dpad_reset()
        self.keymap.clear_held()
