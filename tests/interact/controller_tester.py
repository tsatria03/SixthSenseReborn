#!/usr/bin/env python
"""PORT ADDITION, for testing by ear: say what a game controller does.  Not a test, and not
part of the game: the tests are in ``tests\\case``, and this is one of the tools in
``tests\\interact`` that you play.

    python tests\\interact\\controller_tester.py

It opens a small window (keep it focused) and speaks through the screen reader, and prints
the same words.  Press a button, lean a stick or squeeze a trigger and it says which, using
the standard layout SDL gives every pad, so the same words are right on Windows, Linux and
macOS.  For the buttons the menus use it adds what the game turns that into.

Keyboard, in the window:

    1    a light buzz in the low (heavy) motor
    2    a light buzz in the high (light) motor
    3    both motors at full strength for one second
    4    a pattern: three short pulses
    5    both motors at half strength for three seconds
    V    the game's next vibration, named: zombie 1's punch, zombie 2's scratching and so
         on, then the girl; Shift+V goes back one
    Z    turns the zombie's own hit sound with V on and off, so you can judge the timing of
         a vibration against its sound; it starts on, and the girl has no sound
    S    stop the vibration
    C    the checklist: which buttons, sticks and triggers you have not used yet
    I    the pad's name and how many are attached
    Escape   quit, saying how many of the controls you used

The checklist counts the fifteen buttons, the two sticks (each of the four directions) and
the two triggers, so a pad that registers everything ends on "all controls used".

**Your save is never touched, and the game's screens are not started.**  It uses the same
``Controllers`` the game's menus use, so what it says is what the menus would get.
"""
from __future__ import annotations

import os
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
# the window need not be focused for a pad to be heard, and nothing here may reach a save
os.environ.setdefault('SDL_JOYSTICK_ALLOW_BACKGROUND_EVENTS', '1')
os.environ.setdefault('SIXTHSENSE_USER_DIR', tempfile.mkdtemp(prefix='sixthsense_controller_'))

#: What the game does with the buttons the menus use (``ui/controller.py``).
MENU_KEYS = {'DPAD_UP': 'Up', 'DPAD_DOWN': 'Down', 'DPAD_LEFT': 'Left',
             'DPAD_RIGHT': 'Right', 'A': 'Enter', 'B': 'Escape'}

BUTTONS = (('A', 'A'), ('B', 'B'), ('X', 'X'), ('Y', 'Y'),
           ('BACK', 'Back'), ('GUIDE', 'Guide'), ('START', 'Start'),
           ('LEFTSTICK', 'Left stick click'), ('RIGHTSTICK', 'Right stick click'),
           ('LEFTSHOULDER', 'Left bumper'), ('RIGHTSHOULDER', 'Right bumper'),
           ('DPAD_UP', 'D-pad up'), ('DPAD_DOWN', 'D-pad down'),
           ('DPAD_LEFT', 'D-pad left'), ('DPAD_RIGHT', 'D-pad right'))

#: (axis name, spoken name, the two directions), for the sticks; triggers have one.
STICKS = (('LEFTX', 'Left stick', ('left', 'right')), ('LEFTY', 'Left stick', ('up', 'down')),
          ('RIGHTX', 'Right stick', ('left', 'right')), ('RIGHTY', 'Right stick', ('up', 'down')))
TRIGGERS = (('TRIGGERLEFT', 'Left trigger'), ('TRIGGERRIGHT', 'Right trigger'))

PRESS, RELEASE = 0.5, 0.3      # how far an axis goes to count, and how far back to count again

#: (low motor, high motor, milliseconds); a pattern is a list of them with the gap in ms.
BUZZES = {'1': (1.0, 0.0, 500), '2': (0.0, 1.0, 500), '3': (1.0, 1.0, 1000),
          '5': (0.5, 0.5, 3000)}
PULSES = ((1.0, 1.0, 150), 250)         # the pulse, and the time to each next one
PULSE_COUNT = 3


#: What V plays, in order: (what is said, the effect in ``ui/vibration.EFFECTS``).
GAME_EFFECTS = (('Zombie 1, the punch', 'punch'), ('Zombie 2 and 4, scratching', 'scratch'),
                ('Zombie 3, 5 and 7, mauling', 'maul'), ('Zombie 6, the pounce', 'pounce'),
                ('Zombie 8, not shaken off', 'grab'), ('Zombie 9, the smash', 'smash'),
                ('Zombie 10, the chainsaw', 'chainsaw'),
                ('The girl, shot by mistake', 'girl'), ('Dying', 'death'))


class Tester:
    def __init__(self, pygame, controllers, say, vibration=None, play_sound=None):
        self.pg = pygame
        self.pads = controllers
        self.say = say
        self.vibration = vibration
        self.play_sound = play_sound        # name of an effect -> plays its hit sound, or None
        self.stop_sound = None              # silence what play_sound started
        self.with_sound = play_sound is not None
        self._effect = -1                   # the last of GAME_EFFECTS played
        self.used = set()                   # spoken names of the controls used
        self._lean = {}                     # (instance id, axis) -> -1, 0, 1
        self._pulses = []                   # when the next pulses are due (ms ticks)
        self.names = {getattr(pygame, 'CONTROLLER_BUTTON_' + b): n for b, n in BUTTONS}
        self.button_ids = {getattr(pygame, 'CONTROLLER_BUTTON_' + b): b for b, _ in BUTTONS}
        self.sticks = {getattr(pygame, 'CONTROLLER_AXIS_' + a): (n, d) for a, n, d in STICKS}
        self.triggers = {getattr(pygame, 'CONTROLLER_AXIS_' + a): n for a, n in TRIGGERS}

    # ---- the checklist ---------------------------------------------------
    def everything(self):
        names = [n for _, n in BUTTONS]
        for _, n, d in STICKS:
            names += ['%s %s' % (n, x) for x in d]
        return list(dict.fromkeys(names + [n for _, n in TRIGGERS]))

    def unused(self):
        return [n for n in self.everything() if n not in self.used]

    def checklist(self):
        left = self.unused()
        total = len(self.everything())
        if not left:
            return 'All %d controls used.' % total
        return '%d of %d used. Not yet: %s.' % (total - len(left), total, ', '.join(left))

    # ---- what a controller does ---------------------------------------------
    def event(self, e):
        pg = self.pg
        keys = self.pads.feed(e)
        if keys is None:
            return self.other(e)
        t = e.type
        if t == pg.CONTROLLERDEVICEADDED:
            self.say('Controller connected. %s' % self.info())
        elif t == pg.CONTROLLERDEVICEREMOVED:
            self._lean = {k: v for k, v in self._lean.items()
                          if k[0] != getattr(e, 'instance_id', None)}
            self.say('Controller disconnected. %s' % self.info())
        elif t == pg.CONTROLLERBUTTONDOWN:
            name = self.names.get(e.button)
            if name is None:
                self.say('An unknown button, number %s.' % e.button)
                return
            self.used.add(name)
            menu = MENU_KEYS.get(self.button_ids[e.button])
            self.say('%s pressed%s.' % (name, ', the menus take it as %s' % menu if menu else ''))
        elif t == pg.CONTROLLERBUTTONUP:
            name = self.names.get(e.button)
            if name:
                self.say('%s released.' % name)
        elif t == pg.CONTROLLERAXISMOTION:
            self.axis(e)

    def axis(self, e):
        value = float(e.value)
        if abs(value) > 1.0:
            value /= 32768.0
        key = (getattr(e, 'instance_id', 0), e.axis)
        lean = self._lean.get(key, 0)
        if e.axis in self.triggers:
            name = self.triggers[e.axis]
            if lean == 0 and value > PRESS:
                self._lean[key] = 1
                self.used.add(name)
                self.say('%s pressed, %d percent.' % (name, round(value * 100)))
            elif lean and value < RELEASE:
                self._lean[key] = 0
                self.say('%s released.' % name)
            return
        if e.axis not in self.sticks:
            return
        name, (neg, pos) = self.sticks[e.axis]
        if lean == 0:
            if abs(value) < PRESS:
                return
            lean = -1 if value < 0 else 1
            self._lean[key] = lean
            way = neg if lean < 0 else pos
            self.used.add('%s %s' % (name, way))
            self.say('%s %s.' % (name, way))
        elif abs(value) < RELEASE:
            self._lean[key] = 0
            self.say('%s centred.' % name)
        elif (value < 0) != (lean < 0) and abs(value) > PRESS:
            self._lean[key] = 0
            self.axis(e)

    def other(self, e):
        pg = self.pg
        if e.type != pg.KEYDOWN:
            return
        name = pg.key.name(e.key)
        if name in BUZZES:
            self.buzz(*BUZZES[name])
        elif name == '4':
            self.pulse()
        elif name == 'z':
            self.toggle_sound()
        elif name == 'v':
            self.game_effect(-1 if e.mod & self.pg.KMOD_SHIFT else 1)
        elif name == 's':
            self.stop()
        elif name == 'c':
            self.say(self.checklist())
        elif name == 'i':
            self.say(self.info())

    def info(self):
        pads = self.pads.pads
        if not pads:
            return 'No controller attached.'
        names = ', '.join(p.name for p in pads)
        return '%d controller%s: %s.' % (len(pads), '' if len(pads) == 1 else 's', names)

    # ---- vibration ---------------------------------------------------------
    def buzz(self, low, high, ms):
        pads = self.pads.pads
        if not pads:
            self.say('No controller attached.')
            return
        worked = 0
        for pad in pads:
            try:
                worked += bool(pad.rumble(low, high, ms))
            except Exception:
                pass
        if worked:
            self.say('Vibrating, low motor %d percent, high motor %d percent, %.1f seconds.'
                     % (round(low * 100), round(high * 100), ms / 1000))
        else:
            self.say('This controller did not vibrate. It may not support it here.')

    def game_effect(self, step):
        """V: play the game's next vibration, or with Shift the one before."""
        if self.vibration is None or not self.pads.pads:
            self.say('No controller attached.')
            return
        self._effect = (self._effect + step) % len(GAME_EFFECTS)
        said, name = GAME_EFFECTS[self._effect]
        if self.with_sound and self.play_sound is not None:
            self.play_sound(name)
        self.vibration.play(name)
        self.say('%s.' % said)

    def toggle_sound(self):
        """Z: V with the zombie's hit sound, or without it."""
        if self.play_sound is None:
            self.say('The game sounds are not available here.')
            return
        self.with_sound = not self.with_sound
        self.say('The zombie sound with the vibration is %s.' % ('on' if self.with_sound else 'off'))

    def pulse(self):
        self._pulses = [self.pg.time.get_ticks() + i * PULSES[1] for i in range(PULSE_COUNT)]
        self.say('Three pulses.')

    def stop(self):
        self._pulses = []
        if self.vibration is not None:
            self.vibration.stop()
        if self.stop_sound is not None:
            self.stop_sound()
        for pad in self.pads.pads:
            try:
                pad.stop_rumble()
            except Exception:
                pass
        self.say('Vibration stopped.')

    def tick(self):
        """Called every frame: fire the pulses that are due."""
        if self.vibration is not None:
            self.vibration.tick()
        now = self.pg.time.get_ticks()
        while self._pulses and now >= self._pulses[0]:
            self._pulses.pop(0)
            for pad in self.pads.pads:
                try:
                    pad.rumble(*PULSES[0])
                except Exception:
                    pass


def main():
    import pygame

    from sixthsense.platform.speech import Speech
    from sixthsense.ui.controller import Controllers

    speech = Speech.shared()

    def say(text):
        print(text, flush=True)
        speech.speak(text, interrupt=True)

    pygame.display.init()
    pygame.display.set_caption('Controller tester (Escape quits)')
    pygame.display.set_mode((480, 120))
    from sixthsense.ui.vibration import Vibration
    pads = Controllers(pygame)
    tester = Tester(pygame, pads, say, Vibration(pads))
    try:
        from sixthsense.game.app_delegate import AppDelegate
        from sixthsense.game.stage_1_e import MONSTER_SOUNDS
        from sixthsense.ui.vibration import ZOMBIE_EFFECTS
        app = AppDelegate.shared()
        app.didFinishLaunching()
        # each effect's zombie, the lowest number first, and that zombie's hit sound
        first = {}
        for kind in sorted(ZOMBIE_EFFECTS):
            first.setdefault(ZOMBIE_EFFECTS[kind], kind)
        hit = {name: MONSTER_SOUNDS[kind][4][0] for name, kind in first.items()}

        def play_sound(name):
            if name in hit:                 # the girl's shot has no sound of its own here
                app.stopSoundBufNumber_(hit[name])
                app.playSound_Gain_Pos_z_reprats_(hit[name], 1.0, (0.0, 0.0), 40, False)

        tester.play_sound, tester.with_sound = play_sound, True
        tester.stop_sound = lambda: [app.stopSoundBufNumber_(n) for n in hit.values()]
    except Exception as e:                  # no audio device: the vibrations still work
        print('The game sounds are not available: %r' % (e,), flush=True)
    say('Controller tester. Press a button, lean a stick or squeeze a trigger. '
        '1 to 5 and V vibrate, S stops, C is the checklist, I says what is attached, '
        'Escape quits. %s' % tester.info())

    clock = pygame.time.Clock()
    running = True
    while running:
        for e in pygame.event.get():
            if e.type == pygame.QUIT or (e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE):
                running = False
                break
            tester.event(e)
        tester.tick()
        clock.tick(60)
    tester.stop()
    say(tester.checklist())
    pygame.time.wait(1500)
    pygame.quit()
    return 0


if __name__ == '__main__':
    sys.exit(main())
