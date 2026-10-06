#!/usr/bin/env python
"""PORT ADDITION, for testing by ear: a game where every gun hit is a headshot, so you can
hear what a headshot does with the spoken headshot and the headshot beep on or off.  Not
a test, and not part of the game: the tests are in ``tests\\case``, and this is one of
the tools in ``tests\\interact`` that you play.

    python tests\\interact\\headshot_tester.py                    asks for both settings
    python tests\\interact\\headshot_tester.py --speech on --beep on
    python tests\\interact\\headshot_tester.py --speech off --beep on

Each setting is on, off, or left out for the one in your own settings.json.  In the
game, a headshot says "Headshot!" when the spoken headshot is on and plays the beep
where the zombie is when the beep is on, and both when both are (``Stage_1_E.
MonsterDamage``).  Here every shot from a gun that hits a zombie counts as a headshot,
whether or not the zombie's head was open; the knife, the sword and the grenade have no
headshots, as in the game.

**Your save is never touched.**  It plays on its own save in
``%APPDATA%\\SixthSenseReborn\\headshot_tester``, marked as past the tutorial, and takes
a fresh copy of your key bindings and settings each time it starts.

Everything else is the real game: Escape pauses and resumes, and the pause panel's Main
menu row goes back to the menu, where Start Game starts the tester again.
"""
from __future__ import annotations

import argparse
import os
import shutil
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)

CHOICES = ('on', 'off')


def _own_save():
    """Point APPDATA at the tester's own folder, before anything reads it."""
    real = os.path.join(os.environ.get('APPDATA') or os.path.expanduser('~'),
                        'SixthSenseReborn')
    mine = os.path.join(real, 'headshot_tester')
    os.makedirs(os.path.join(mine, 'SixthSenseReborn'), exist_ok=True)
    # your key bindings and your settings, but never your save
    for name in ('keys.json', 'settings.json'):
        yours = os.path.join(real, name)
        if os.path.exists(yours):
            shutil.copyfile(yours, os.path.join(mine, 'SixthSenseReborn', name))
    os.environ['APPDATA'] = mine


def _ask(question):
    """Ask until the answer is on, off or Enter alone ('').  With no console to ask on,
    the answer is ''."""
    while True:
        try:
            answer = input(question + ' ').strip().lstrip('﻿').lower()
        except EOFError:
            return ''
        if answer in ('',) + CHOICES:
            return answer
        print('Sorry, please type on or off, or press Enter.')


def _questions():
    """Opened with nothing after its name, the tester asks instead."""
    argv = []
    for flag, what in (('--speech', 'Spoken headshot'), ('--beep', 'Headshot beep')):
        answer = _ask('%s: on or off (Enter for your own setting):' % what)
        if answer:
            argv += [flag, answer]
    return argv


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:] or _questions()
    ap = argparse.ArgumentParser(
        description='Play SixthSense Reborn with every gun hit a headshot.')
    ap.add_argument('--speech', choices=CHOICES,
                    help='the spoken "Headshot!"; left out, your own setting')
    ap.add_argument('--beep', choices=CHOICES,
                    help='the headshot beep; left out, your own setting')
    ap.add_argument('-v', '--verbose', action='store_true')
    args = ap.parse_args(argv)

    _own_save()

    import SixthSenseReborn
    from sixthsense.game.app_delegate import AppDelegate
    from sixthsense.game.stage_1_e import Stage_1_E
    from sixthsense.platform.defaults import UserDefaults

    d = UserDefaults.standardUserDefaults()
    d.setObject_forKey_('1', 'TUTORIAL')      # the stage only walks once it is set
    if args.speech:
        d.setObject_forKey_('1' if args.speech == 'on' else '0', 'HEADSHOTSPEECH')
    if args.beep:
        d.setObject_forKey_('1' if args.beep == 'on' else '0', 'HEADSHOTBEEP')
    d.synchronize()

    class HeadshotStage(Stage_1_E):
        """The stage, with the head of every zombie a gun finds always open."""

        def monsterHitHeadFind(self):
            m = super().monsterHitHeadFind()
            if m is not None and self.gamePlayer.useWepon not in (0, 1, 7):
                m.isHeadShot = True           # the grenade and the blades have none
            return m

    def new_stage():
        st = HeadshotStage()
        st.viewDidLoad()
        return st

    SixthSenseReborn._new_stage = new_stage
    app = AppDelegate.shared()
    print('Every gun hit is a headshot.  Spoken headshot %s, headshot beep %s.  '
          'Your own save is not used.'
          % ('on' if app.headshot_speech_on else 'off',
             'on' if app.headshot_beep_on else 'off'))
    return SixthSenseReborn.main(['--stage'] + (['-v'] if args.verbose else []))


if __name__ == '__main__':
    sys.exit(main())
