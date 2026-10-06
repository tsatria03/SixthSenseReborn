"""``Stage_Tutorial`` - the ten scripted beats that teach the game.

``Stage_Tutorial`` (0x7d7cc..0x8d2b1) is a near-copy of ``Stage_1_E``: 252 methods
against 262, and only ``testWeapon``/``setTestWeapon:`` are its own.  What differs is
that the walk never starts - ``MapInitInBundle`` (0x7ddcc) loads the same three map
files, then calls ``tutorialOne`` directly and arms

    checkTutorialTimer = [NSTimer scheduledTimerWithTimeInterval:1.0 target:self
                             selector:@selector(CheckTutorial) userInfo:nil repeats:YES];

and the player stands still until every beat is done.

Each beat is five methods in the original (``tutorialOne``, ``...SoundStop``,
``...End``, ``...Restart``, ``...RestartFinger``), spelled out ten times over.  The
shape is always the same:

    tutorialN            play the instruction; hide every hint; show this beat's
                         finger and arrow
    tutorialNSoundStop   9.5 s later (6.5 for beat eight): stop the instruction and
                         spawn the monster the beat is about, if it has one
    CheckTutorial        every second, call ``...End`` on the first unfinished beat
                         of One to Six
    tutorialNEnd         if the flag is still clear, slide the finger and put it back
                         through ``...RestartFinger``; nothing is heard
    tutorialNRestart     the prompt again, when the beat's monster reaches you (never
                         sent for Six and Seven)
    NextTutorial         once the beat's action is done, stop the prompts and start
                         the first beat not yet done

So beats One to Six nag once a second until you do the thing.  Doing it moves on
through NextTutorial, and each action only counts once every beat before it is done
(``REQUIRES``), so the beats always come in order.

What the beats teach, and what marks each one done:

    beat        prompt                                  spawns   done by
    One    275  "if you make your finger 9"     9:00    type 1   killing it
    Two    276  "if you make your finger 10_30" 10:30   type 2   killing it
    Three  277  "if you make your finger 12"    12:00   type 3   killing it
    Four   278  "if you make your finger 1_30"  1:30    type 4   killing it
    Five   279  "if you make your finger 3"     3:00    type 5   killing it
    Five+  361  "stamina of zomblies increasingly"      type 63  killing it
    Six    280  "if you make your finger 6"     6:00    -        reloading
    Seven  281  "if you tab the screen with two"        -        changing weapon
    Eight  282  "if an animal zombie approaches"        type 73  shaking free
    Nine   284  "if you tab the screen using three finger twice"  -  the stop button

The clock positions *are* the five lanes, which is where the port's A/Q/W/E/D keys
come from, and beat six is the reload swipe (see ``Stage_1_E._lane_for_angle``).

Killing sets the flag by the dead monster's lane: ``-[Stage_Tutorial MonsterDamage]``
at 0x8a250 tests ``MovingType`` 1..5 and sets ``tutorialOne``..``tutorialFive``.

Beat Nine is the stop button itself, the three-finger double tap, which is P here.
``StopPlayAction:`` (0x83804) does nothing in the tutorial until beats One to Eight are
done (0x83926..0x8393c).  Then it ends the tutorial: ``TUTORIAL = 1``, ``tutorial
success`` (327), and 3.05 s later ``tutorialEnd:``.

Where that leads depends on how the tutorial was reached:

* From the Tutorial row, ``-[Stage_Tutorial tutorialEnd:]`` (0x83738) is
  ``GameEndAction:``, back to the menu.
* From a first Start, the original ran the tutorial inside ``Stage_1_E``, whose
  ``tutorialEnd:`` (0x33bec) reads 3, 2, 1 (``TTSNumber:321 type:1``) and 6.0 s later
  calls ``tutorialEndGameStart:`` (0x33d40): ``zombies are coming`` (328) and the 1.0 s
  walk timer - the real game, from the same standing start.  The port runs both in
  this class, and ``first_run`` picks the ending.

The port drives the ten beats from a table instead of ten copies of five methods.
Nothing about the behaviour changes.
"""
from __future__ import annotations

import logging

from ..platform.controller_names import button_names
from ..platform.defaults import UserDefaults
from ..platform.keymap import KeyMap, binding_text
from ..platform.runloop import RunLoop
from .stage_1_e import Stage_1_E

log = logging.getLogger('tutorial')

# -[Stage_Tutorial StopPlayAction:] 0x83926..0x8393c - the stop button is ignored
# until these are done.  FiveHalf and Nine are not tested.
STOP_NEEDS = ('One', 'Two', 'Three', 'Four', 'Five', 'Six', 'Seven', 'Eight')
ENDING_DELAY = 3.05                 # 0x83ab4: 0x4008666660000000
COUNTDOWN_SECONDS = 4.0             # 0x33c28 waited 6.0 s for the digits, one a second

# What each action needs done before it counts, from the guards in front of each
# flag it sets.  A kill needs nothing: only the beat's own monster is ever out.
REQUIRES = {
    'Six': ('One', 'Two', 'Three', 'Four', 'Five', 'FiveHalf'),     # 0x84cfa..0x84d16
    'Seven': ('One', 'Two', 'Three', 'Four', 'Five', 'Six'),        # 0x853c0..0x853e6
    'Eight': ('One', 'Two', 'Three', 'Four', 'Five', 'Six', 'Seven'),  # 0x8b420..0x8b4b4
}
# How long after the action NextTutorial starts the next beat: GunReloadAction: calls
# it at once (0x84d5a), gunChangeAction: and shakingFind wait 1.5 s (0x8542e,
# 0x8b4f4), and a kill calls it at once (0x8a372).
NEXT_DELAY = {'Seven': 1.5, 'Eight': 1.5}
# -[Stage_Tutorial CheckTutorial] 0x8c678 sends tutorialNEnd for the first of One to Six
# not yet done; that only moves the hint finger, so no prompt is replayed by it.
NAGGED = ('One', 'Two', 'Three', 'Four', 'Five', 'FiveHalf', 'Six')

# name, what the screen reader says first, the monster it sends in (or None).
# PORT DIVERGENCE (tunmi13productions, 2026-10-05; aidocks/completed/screen_reader_only_plan.md):
# the original played a recording (275..284, 361) and sent the monster in 9.5 s later (6.5
# for Eight), the recording's length.  Here a beat that sends one in says its words, the keys
# or the controller's buttons (KEY_HINTS, CONTROLLER_HINTS) and then waits for Enter (a pad's
# A); the other beats only speak.
BEATS = [
    ('One', "This game uses a clock face to decide where to shoot. Start with this zombie, which is coming from 9 o'clock.", 1),
    ('Two', 'A zombie is coming from 10:30.', 2),
    ('Three', "A zombie is coming from 12 o'clock.", 3),
    ('Four', 'A zombie is coming from 1:30.', 4),
    ('Five', "A zombie is coming from 3 o'clock.", 5),
    ('FiveHalf', "Zombies get tougher as the game goes on, and some take more than one shot to kill. Here comes one from 12 o'clock. Tip: if you shoot a zombie while it is not breathing, you get a headshot, which is useful against zombies with lots of health.", 63),
    ('Six', "Unlike in this tutorial, you will not have endless bullets in the real game, so let's practice reloading.", None),
    ('Seven', 'You can change weapons at any time. You start with only a Colt and grenades, but you can buy more weapons later.', None),
    ('Eight', "An animal zombie is coming. You can shoot it, but later on it may move too fast for you to get a shot in, so shaking it off is the best way to deal with it. Try it.", 73),
    ('Nine', 'Congratulations! You are ready to play the game.', None),
]
BEAT_NAMES = [b[0] for b in BEATS]

#: PORT ADDITION: what the screen reader says after a beat's words, naming the player's own
#: keys for the gesture it teaches.  FiveHalf teaches no new gesture, so it has none.
KEY_HINTS = {
    'One': ('lane1', "Press {} to shoot toward 9 o'clock."),
    'Two': ('lane2', 'Press {} to shoot toward 10:30.'),
    'Three': ('lane3', "Press {} to shoot toward 12 o'clock."),
    'Four': ('lane4', 'Press {} to shoot toward 1:30.'),
    'Five': ('lane5', "Press {} to shoot toward 3 o'clock."),
    'Six': ('reload', 'Press {} to reload.'),
    'Seven': ('next_weapon', 'Press {} to change to the next weapon.'),
    'Eight': ('shake', 'Press {} a few times to shake the zombie off.'),
    'Nine': ('pause', 'Press {} to end the tutorial.'),
}

#: PORT ADDITION (tunmi13productions, 2026-10-05; aidocks/completed/tutorial_controller_callouts_plan.md):
#: with a game controller attached, what the screen reader says after a beat's recording, in
#: in place of the keyboard's hint.  {x}, {a}, {b}, {start} and {rb} are
#: the pad's own names for those buttons (platform/controller_names.py).
CONTROLLER_HINTS = {
    'One': "Push the left stick left to shoot toward 9 o'clock, or press D-pad left.",
    'Two': 'Push the left stick diagonally up and left to shoot toward 10:30, '
           'or press D-pad left and up together.',
    'Three': "Push the left stick up to shoot toward 12 o'clock, or press D-pad up.",
    'Four': 'Push the left stick diagonally up and right to shoot toward 1:30, '
            'or press D-pad right and up together.',
    'Five': "Push the left stick right to shoot toward 3 o'clock, or press D-pad right.",
    'Six': 'Pull the left stick down, or press {x}, to reload.',
    'Seven': 'Press {rb} to change to the next weapon.',
    'Eight': 'Press {a} a few times to shake the zombie off.',
    'EightShake': 'Press {a} a few times, or give the controller a shake, to shake the zombie off.',
    'Nine': 'Press {b} or {start} to end the tutorial.',
}

_SIDES = {'left': 'right', 'right': 'left'}
_SIDED = ('shift', 'ctrl', 'alt')


def _merge_sides(bindings):
    """Either Shift does, so a chord bound with Left Shift and again with Right Shift
    is said once, as "Shift".  Control and Alt likewise."""
    def split(k):
        side, _, key = k.partition(' ')
        return (side, key) if side in _SIDES and key in _SIDED else (None, k)

    def plain(b):
        return tuple(split(k)[1] for k in b)

    def mirror(b):
        return tuple(k if split(k)[0] is None else _SIDES[split(k)[0]] + ' ' + split(k)[1]
                     for k in b)

    return [plain(b) if mirror(b) != b and mirror(b) in bindings else b
            for b in bindings]


# PORT DIVERGENCE (2026-10-05): the recordings 'tutorial success' (327), '3, 2, 1' (321) and
# 'zombies are coming' (328) are said by the screen reader.
TEXT_TUTORIAL_SUCCESS = 'Tutorial success.'
TEXT_COUNTDOWN = '3, 2, 1.'
TEXT_ZOMBIES_COMING = 'Zombies are coming.'

# -[Stage_Tutorial MonsterDamage] 0x8a250 - a kill in lane N finishes beat N.
LANE_BEAT = {1: 'One', 2: 'Two', 3: 'Three', 4: 'Four', 5: 'Five'}


class Stage_Tutorial(Stage_1_E):
    """The tutorial run.  Same stage, same monsters, no walking until it is over."""

    #: Escape leaves for the menu here instead of pausing: the stop button skips the
    #: tutorial (``tutorial_skip``), so it cannot stand in for a pause.
    ESCAPE_LEAVES = True

    def __init__(self, first_run=False):
        super().__init__()
        #: Reached from a first Start: the ending counts down into
        #: the real game.  From the Tutorial row it goes back to the menu.
        self.first_run = first_run
        self.ending = False                   # between P and the menu or the game
        self.checkTutorialTimer = None
        self.tutorialTimer = None
        self.beat_done = {n: False for n in BEAT_NAMES}
        self.beat_flag = {n: False for n in BEAT_NAMES}   # the oneFlag..nineFlag pair
        self.current_beat = None
        #: the beat whose words are said and that waits for Enter before its zombie
        #: comes in, or None
        self.waiting = None
        self.line = ''             # what it said, for repeating
        self.told_repeat = False   # the first wait also says how to hear it again
        self.finished = False
        #: PORT ADDITION: the real game that follows a first run's countdown, which this
        #: stage object goes on to play; it is the game, not the tutorial, from then on
        self.real_game = False
        self.warn_if_not_walking = False      # standing still is the point here

    # ---- the flags, under the names the original gives them ---------------
    def __getattr__(self, name):
        if name.startswith('tutorial') and name[8:] in BEAT_NAMES:
            return self.__dict__['beat_done'][name[8:]]
        raise AttributeError(name)

    # =============================================================== loading
    # -[Stage_Tutorial MapInitInBundle] 0x7ddcc
    def MapInitInBundle(self):
        # 0x7cfd8: the original forces isTutorial to 0 here, since a tutorial run
        # is never "already finished" no matter what the save says. Without this,
        # replaying the tutorial from the menu with TUTORIAL already "1" reads as
        # finished: the parent (below) starts the walk timer instead of standing
        # still, and StopPlayAction_ (P) runs the ordinary pause instead of
        # tutorial_skip, since isTutorial is what it branches on.
        if self.real_game:
            # A restart from the result panel of the first run's game: the game again, which
            # walks (isTutorial is set), not the tutorial's first lesson.
            self.isTutorial = 1
            super().MapInitInBundle()
            return
        self.isTutorial = 0
        super().MapInitInBundle()
        if self.MotionSamplingTimer is not None and self.MotionSamplingTimer.isValid():
            self.MotionSamplingTimer.invalidate()
        self.MotionSamplingTimer = None

        # -[Stage_1_E viewDidLoad] already held MapInitInBundle back by
        # LOADING_SECONDS, so Now Loading has had time to finish by the time this
        # runs - beat One can start right away.
        self.tutorial_beat('One')                       # 0x7e2fa, called directly
        self.checkTutorialTimer = RunLoop.main().scheduledTimer(
            1.0, self, 'CheckTutorial', None, True)     # 0x7e338

    # ================================================================ beats
    def _beat(self, name):
        return BEATS[BEAT_NAMES.index(name)]

    # -[Stage_Tutorial tutorialN] - say the instruction, show the hint
    def tutorial_beat(self, name, restart=False):
        _n, text, spawn = self._beat(name)
        self.current_beat = name
        self.beat_flag[name] = False           # the prompt is said again
        RunLoop.main().cancelPerform(self, 'tutorial_sound_stop')
        # The animal zombie is already on you when its beat is said again (the grab
        # landed), and the pad's A, which would continue, is what shakes it off.
        waits = spawn is not None and not (restart and name == 'Eight')
        parts = [text]
        hint = self.callout(name)
        if hint is not None:
            parts.append(hint)
        if waits:
            parts.append(self.continue_prompt())
        self.line = ' '.join(parts)
        self.waiting = name if waits else None
        self._say(self.line)
        if not waits:
            self.tutorial_sound_stop(name, send=False)
        self.tutorialHiddenView()
        log.info('tutorial %s: %s', name, self.line)

    def continue_prompt(self):
        """How to go on, and the first time how to hear the beat again."""
        pad = self.app.controller_name()
        if pad is not None:
            names = button_names(pad)
            prompt = 'Press %s to continue' % names['a']
            again = ', or %s to hear this again.' % names['y']
        else:
            prompt = 'Press Enter to continue'
            again = ', or any other key to hear this again.'
        if self.told_repeat:
            return prompt + '.'
        self.told_repeat = True
        return prompt + again

    def tutorial_advance(self):
        """Enter, or a pad's A, on a beat that waits: cut the speech and send its zombie."""
        name = self.waiting
        if name is None or self.finished:
            return False
        self.waiting = None
        if self.speech is not None:
            self.speech.stop()
        self.tutorial_sound_stop(name)
        return True

    def tutorial_repeat(self):
        """Any other key, or a pad's Y, on a beat that waits: say it again."""
        if self.waiting is None or self.finished:
            return False
        self._say(self.line)
        return True

    # -[Stage_Tutorial tutorialNSoundStop] - send in the monster
    def tutorial_sound_stop(self, name=None, send=True):
        name = name or self.current_beat
        if name is None:
            return
        _n, _text, spawn = self._beat(name)
        if name == 'Eight':
            # 0x8e1a8: the animal zombie is not to be shot; it is there to grab you.
            self.noAtt = True
        self.beat_flag[name] = True            # PORT: the prompt has finished
        if send and spawn is not None:
            self.MonsterInit_(spawn)

    def controller_hint(self, name):
        """PORT ADDITION: this beat's gesture on the attached controller, or None with no controller or for a beat that teaches nothing."""
        pad = self.app.controller_name()
        if pad is None or name not in CONTROLLER_HINTS:
            return None
        # only offered when the pad can sense one and the player has it on
        if name == 'Eight' and self.app.can_shake_now():
            name = 'EightShake'
        return CONTROLLER_HINTS[name].format(**button_names(pad))

    def callout(self, name):
        """What is said after a beat's words: the controller's way when one is attached,
        otherwise the keys."""
        hint = self.controller_hint(name)
        return hint if hint is not None else self.key_hint(name)

    def key_hint(self, name):
        """PORT ADDITION: the keys for this beat's gesture."""
        if name not in KEY_HINTS:
            return None
        action, text = KEY_HINTS[name]
        keys = []
        for b in _merge_sides(KeyMap.shared().bindings.get(action, [])):
            if binding_text(b) not in keys:
                keys.append(binding_text(b))
        if not keys:
            return None
        if len(keys) > 2:
            keys = [', '.join(keys[:-1]) + ',', keys[-1]]
        return text.format(' or '.join(keys))

    # -[Stage_Tutorial CheckTutorial] 0x8c678 - once a second
    def CheckTutorial(self, timer=None):
        """Nag about the first unfinished beat, then let any monster that has reached
        you act, unless one is already holding you (0x8c754..0x8c770).  That last step
        is the only place anything reaches you in the tutorial, since the stage's own
        clock does not run."""
        if self.finished:
            return
        for name in NAGGED:
            if not self.beat_done[name]:
                self.tutorial_beat_end(name)
                break
        if not self.isShake:
            self.MonsterAttPlayer()

    # -[Stage_Tutorial tutorialNEnd] 0x8cb60 (One) .. 0x8dd78 (Six)
    def tutorial_beat_end(self, name):
        """Silent.  While the beat is not done, the original only slides the hint finger
        across the screen (UIView beginAnimations .. setFrame: .. commitAnimations) and
        sends ``tutorialNRestartFinger``, which puts the finger back - it plays nothing.
        A prompt is heard again only from ``tutorialNRestart``, when the beat's monster
        reaches you, and ``tutorialSixRestart`` and ``tutorialSevenRestart`` are never
        sent at all.  The port has no finger, so there is nothing to do here.  It used
        to replay the prompt, so the reload lesson (Six), which has no monster to hold
        the replay back, said its instruction again about every ten seconds."""
        return

    # -[Stage_Tutorial tutorialNRestart] - the prompt again, and its monster after it
    def tutorial_restart(self, name):
        if not self.finished and not self.beat_done[name]:
            self.tutorial_beat(name, restart=True)

    # -[Stage_Tutorial MonsterAttPlayer] 0x8a908, the tail at 0x3b3b2: no heart is
    # lost; the beat for the monster's lane starts again.
    def _tutorial_monster_reached(self, m):
        name = LANE_BEAT.get(m.MovingType)
        if m.MovingType == 3 and self.beat_done['Three']:
            name = 'FiveHalf'                  # 0x3b3de: threeFlag, then fiveHalfFlag
        if name is not None:
            self.tutorial_restart(name)

    # -[Stage_Tutorial NonShaking] 0x8b1f2 - the grab landed, so beat Eight again.
    def _tutorial_grab_landed(self):
        self.tutorial_restart('Eight')

    # -[Stage_Tutorial tutorialHiddenView] 0x3d0a8 - hides the arrows and the finger
    def tutorialHiddenView(self):
        pass

    def _complete(self, name):
        """Mark a beat done, but only once the beats before it are (``REQUIRES``), then
        start the next one.  Reloading or changing weapon early used to finish those
        lessons before they were taught, so the tutorial skipped them."""
        if self.finished or self.beat_done.get(name):
            return
        if not all(self.beat_done[n] for n in REQUIRES.get(name, ())):
            return
        self.beat_done[name] = True
        self.beat_flag[name] = False
        log.info('tutorial %s done', name)
        delay = NEXT_DELAY.get(name, 0.0)
        if delay:
            RunLoop.main().perform(self, 'NextTutorial', None, delay)
        else:
            self.NextTutorial()

    # -[Stage_Tutorial NextTutorial] 0x8c89c - stop the prompts, then start the first
    # beat not yet done, in the order One to Nine.
    def NextTutorial(self, *_):
        if self.finished:
            return
        if self.speech is not None:
            self.speech.stop()                                 # tutorialSoundStop
        for name in BEAT_NAMES:
            if not self.beat_done[name]:
                self.tutorial_beat(name)
                return

    # ================================================== what finishes a beat
    # -[Stage_Tutorial MonsterDamage] 0x8a250 - by the dead monster's lane.  It
    # listens on _kill_seen rather than MonsterKillCount_, which --debug skips so that
    # no kill counts; the lesson still has to see the zombie die.
    def _kill_seen(self, m):
        if self.finished:
            return
        name = LANE_BEAT.get(m.MovingType)
        if name and not self.beat_done[name]:
            self._complete(name)
        elif not self.beat_done['FiveHalf'] and all(
                self.beat_done[n] for n in ('One', 'Two', 'Three', 'Four', 'Five')):
            self._complete('FiveHalf')

    # -[Stage_Tutorial GunReloadAction:] 0x84b80 - only a reload that starts counts.
    def GunReloadAction_(self, *a):
        super().GunReloadAction_(*a)
        if self.gamePlayer.useWepon != 0 and self.weaponSource[self.gamePlayer.useWepon]:
            self._complete('Six')

    # -[Stage_Tutorial gunChangeAction:]
    def gunChangeAction_(self, step=1):
        super().gunChangeAction_(step)
        self._complete('Seven')

    # -[Stage_Tutorial shakingFind] - shaking the grabber off
    def shakingFind(self, timer=None):
        super().shakingFind(timer)
        if not self.isShake:
            self._complete('Eight')

    # -[Stage_Tutorial StopPlayAction:] 0x83804 - P while the tutorial is running.
    def StopPlayAction_(self, *a):
        if self.ending:
            # PORT DIVERGENCE: the original set isTutorial on the way out, so a second
            # stop during the 3.05 s wait paused a stage about to be left or started.
            return False
        return super().StopPlayAction_(*a)

    def tutorial_skip(self):
        """0x838b0..0x83aba: nothing until beats One to Eight are done.  Then stop the
        prompt, write ``TUTORIAL``, stop both timers, play ``tutorial success`` and
        call ``tutorialEnd:`` 3.05 s later.  Doing this is beat Nine."""
        if self.finished or not all(self.beat_done[n] for n in STOP_NEEDS):
            return
        self.finished = True
        self.waiting = None
        self.ending = True
        self.beat_done['Nine'] = True
        if self.checkTutorialTimer is not None and self.checkTutorialTimer.isValid():
            self.checkTutorialTimer.invalidate()
        self.checkTutorialTimer = None
        RunLoop.main().cancelPerform(self, 'NextTutorial')
        if self.speech is not None:
            self.speech.stop()
        d = UserDefaults.standardUserDefaults()
        d.setObject_forKey_('1', 'TUTORIAL')                   # 0x839d4
        d.synchronize()
        self._say(TEXT_TUTORIAL_SUCCESS)                       # 0x83a92
        RunLoop.main().perform(self, 'tutorialEnd_', None, ENDING_DELAY)
        log.info('tutorial finished; TUTORIAL = 1')

    # ================================================================== end
    # -[Stage_Tutorial tutorialEnd:] 0x83738, or -[Stage_1_E tutorialEnd:] 0x33bec on
    # a first run.
    def tutorialEnd_(self, *_):
        if not self.first_run:
            self.ending = False
            self.GameEndAction_()                              # back to the menu
            return
        self._say(TEXT_COUNTDOWN)                              # 0x33c0e: 3, 2, 1
        RunLoop.main().perform(self, 'tutorialEndGameStart_', None, COUNTDOWN_SECONDS)

    # -[Stage_1_E tutorialEndGameStart:] 0x33d40, the same as Stage_Tutorial's own
    # 0x8374c, which nothing calls.
    def tutorialEndGameStart_(self, *_):
        self.ending = False
        self.real_game = True
        # Escape pauses the game as it does in any other, instead of leaving for the menu
        # as it does in the tutorial.
        self.ESCAPE_LEAVES = False
        self.noAtt = False                     # 0x83774
        self.shotFlag = False                  # 0x83782
        self.isTutorial = 1                    # 0x83786
        self._say(TEXT_ZOMBIES_COMING)                         # 0x837ae
        self.MotionSamplingTimer = RunLoop.main().scheduledTimer(
            1.0, self, 'MainControl', None, True)              # 0x837ea

    def teardown(self):
        if self.checkTutorialTimer is not None and self.checkTutorialTimer.isValid():
            self.checkTutorialTimer.invalidate()
        self.checkTutorialTimer = None
        # Escape (or any other way out) must not leave a beat's words to run out on
        # their own, right over the menu.
        if self.speech is not None:
            self.speech.stop()
        super().teardown()
