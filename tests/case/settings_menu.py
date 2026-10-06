"""The Settings screen: every setting, and what the attached pad can and cannot do.

A PORT ADDITION (tunmi13productions, 2026-10-06; aidocks/completed/settings_menu_plan.md).
The vibration and the two headshot rows moved here out of the main menu, and the screen
gained the shake and the controller picker.  A row the pad cannot do stays where it is,
reads "not supported" and will not turn on.

Each test runs on a new, empty save folder of its own, and the pads are stand-ins: no real
controller is opened and nothing buzzes.
"""
from __future__ import annotations

import json
import os
import shutil
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import _scratch_save                                             # noqa: E402,F401  never the real save

from sixthsense import paths                                     # noqa: E402
from sixthsense.game.app_delegate import AppDelegate             # noqa: E402
from sixthsense.game.settings_screen import (BEEP_ROW, CONTROLLER_ROW,   # noqa: E402
                                             SHAKE_ROW, SKIP_INTRO_ROW, SPEECH_ROW,
                                             VIBRATION_ROW, SettingsController)
from sixthsense.platform.defaults import UserDefaults            # noqa: E402
from sixthsense.platform.runloop import RunLoop                  # noqa: E402



class _Recorder:
    def __init__(self):
        self.said = []

    def speak(self, text, interrupt=True):
        self.said.append(text)

    def stop(self):
        pass


class _Pad:
    def __init__(self, name):
        self.name = name
        self.buzzed = []

    def rumble(self, *a):
        self.buzzed.append(a)


class _Pads:
    """Stands in for ui/controller.Controllers: the names it reports and which pad is
    active, worked out the same way the real one does."""

    def __init__(self, *names, choice=lambda: ''):
        self._pads = [_Pad(n) for n in names]
        self._choice = choice

    @property
    def names(self):
        out = []
        for pad in self._pads:
            if pad.name not in out:
                out.append(pad.name)
        return out

    @property
    def active_pad(self):
        wanted = self._choice()
        if wanted:
            for pad in self._pads:
                if pad.name == wanted:
                    return pad
        return self._pads[0] if self._pads else None

    @property
    def active_name(self):
        pad = self.active_pad
        return None if pad is None else pad.name

    @property
    def active_pads(self):
        pad = self.active_pad
        return [] if pad is None else [pad]


class _NewSave:
    def __enter__(self):
        self.old = os.environ.get(paths.USER_DIR_ENV)
        self.top = tempfile.mkdtemp()
        os.environ[paths.USER_DIR_ENV] = os.path.join(self.top, 'SixthSense')
        UserDefaults._instance = None
        self.d = UserDefaults.standardUserDefaults()
        self.app = AppDelegate.shared()
        if self.app.playback is None:
            self.app.didFinishLaunching()
        RunLoop.main().reset()
        self.app.controllers = None
        self.app.shake = None
        self.app.vibration = None
        self.played = []
        self._real = self.app.playSound_Gain_Pos_z_reprats_
        self.app.playSound_Gain_Pos_z_reprats_ = self._play
        self.pages = []
        return self

    def _play(self, n, *a):
        self.played.append(n)
        return self._real(n, *a)

    def pads(self, *names):
        """Attach these pads, the save deciding which is active as the real one does."""
        self.app.controllers = _Pads(*names, choice=lambda: self.app.controller_choice)
        return self.app.controllers

    def can_shake(self, yes):
        self.app.can_shake = lambda: yes

    def page(self):
        p = SettingsController(speech=_Recorder())
        self.pages.append(p)
        return p

    def __exit__(self, *exc):
        for p in self.pages:
            p.teardown()
        self.app.__dict__.pop('playSound_Gain_Pos_z_reprats_', None)
        self.app.__dict__.pop('can_shake', None)
        self.app.controllers = None
        if self.old is None:
            os.environ.pop(paths.USER_DIR_ENV, None)
        else:
            os.environ[paths.USER_DIR_ENV] = self.old
        UserDefaults._instance = None
        shutil.rmtree(self.top, ignore_errors=True)


def test_the_rows_are_back_the_five_settings_and_the_picker():
    with _NewSave() as s:
        page = s.page()
        assert page.rows() == (1, 2, 3, 4, 5, 6, 7)
        assert page.title_text() == 'Settings.'
        assert page.row_text(1) == 'Back, Button'


def test_the_defaults_are_what_they_were_before_the_screen_existed():
    """Spoken headshot on, the beep off, vibration on, and the shake on, which is how it
    worked before there was a setting (aidocks/completed/controller_shake_plan.md)."""
    with _NewSave() as s:
        s.pads('Xbox Wireless Controller')
        s.can_shake(True)
        page = s.page()
        assert page.row_text(SKIP_INTRO_ROW) == 'Skip the opening screens, currently off.'
        assert page.row_text(SPEECH_ROW) == 'Spoken headshot, currently on.'
        assert page.row_text(BEEP_ROW) == 'Headshot beep, currently off.'
        assert page.row_text(VIBRATION_ROW) == 'Vibration, currently on.'
        assert page.row_text(SHAKE_ROW) == 'Shake to break free, currently on.'
        assert s.app.shake_on and s.app.can_shake_now()
        assert not s.app.skip_intro_on, 'the opening screens were skipped by default'


def test_a_new_settings_json_shows_every_setting():
    """2026-10-06: the toggles and the pad are written on the first start, as the volumes
    are, so settings.json lists every setting in the dev's order.  Writing them changes
    nothing a player hears, and a value already there is never replaced."""
    from sixthsense.game.app_delegate import SETTING_DEFAULTS, fill_settings
    from sixthsense.platform import volume
    from sixthsense.platform.defaults import SETTINGS_KEYS
    readers = ('vibration_on', 'headshot_speech_on', 'headshot_beep_on', 'shake_on',
               'skip_intro_on', 'controller_choice')
    with _NewSave() as s:
        for key in SETTING_DEFAULTS:
            s.d.removeObjectForKey_(key)
        s.d.setObject_forKey_('0', 'HEADSHOTSPEECH')        # the player's own, kept
        before = {r: getattr(s.app, r) for r in readers}
        volume.load(s.d)
        assert fill_settings(s.d), 'nothing was written'
        s.d.synchronize()
        assert {r: getattr(s.app, r) for r in readers} == before, 'a default changed play'
        assert s.d.stringForKey_('HEADSHOTSPEECH') == '0', "the player's value was replaced"
        with open(os.path.join(paths.user_dir(), 'settings.json'), encoding='utf-8') as fh:
            assert list(json.load(fh)) == list(SETTINGS_KEYS)
        assert not fill_settings(s.d), 'a complete file was filled again'


def test_each_toggle_flips_saves_and_says_the_new_state():
    with _NewSave() as s:
        s.pads('Xbox Wireless Controller')
        s.can_shake(True)
        page = s.page()
        for row, key, label, was in ((SKIP_INTRO_ROW, 'SKIPINTRO',
                                      'Skip the opening screens', False),
                                     (SPEECH_ROW, 'HEADSHOTSPEECH', 'Spoken headshot', True),
                                     (BEEP_ROW, 'HEADSHOTBEEP', 'Headshot beep', False),
                                     (VIBRATION_ROW, 'VIBRATION', 'Vibration', True),
                                     (SHAKE_ROW, 'SHAKE', 'Shake to break free', True)):
            page.selectMenu = row
            page.activate()
            assert s.d.stringForKey_(key) == ('0' if was else '1'), key
            assert page.speech.said[-1] == '%s, %s.' % (label, 'off' if was else 'on')
            page.activate()
            assert s.d.stringForKey_(key) == ('1' if was else '0'), key
        s.d.synchronize()
        with open(s.d.settings.path, encoding='utf-8') as fh:
            saved = json.load(fh)
        assert 'SHAKE' in saved, 'SHAKE is not in settings.json'
        assert saved['SKIPINTRO'] == '0', 'SKIPINTRO is not in settings.json'
        assert 'CONTROLLER' not in saved or saved['CONTROLLER'] == ''


def test_turning_a_setting_on_proves_itself():
    """The menu's rows buzzed once when vibration went on and played the beep once when the
    beep went on; the screen keeps both."""
    with _NewSave() as s:
        pads = s.pads('Xbox Wireless Controller')
        s.can_shake(True)

        class _Buzzer:
            def __init__(self):
                self.played = []

            def play(self, name):
                self.played.append(name)

            def stop(self):
                pass

        buzz = _Buzzer()
        s.app.vibration = buzz
        page = s.page()
        page.selectMenu = VIBRATION_ROW
        page.activate()                              # off
        assert buzz.played == []
        page.activate()                              # on again
        assert buzz.played == ['confirm'], buzz.played
        s.played.clear()
        page.selectMenu = BEEP_ROW
        page.activate()                              # on
        assert 374 in s.played, s.played
        s.played.clear()
        page.activate()                              # off
        assert 374 not in s.played, 'the beep played when it was turned off'
        assert pads.active_name == 'Xbox Wireless Controller'
        s.app.vibration = None


def test_with_no_pad_the_rows_stay_but_say_not_supported():
    """tunmi13productions, 2026-10-06: "show the rows, but say something like vibration.
    not supported. so it won't let you toggle it on"."""
    with _NewSave() as s:
        page = s.page()
        assert page.rows() == (1, 2, 3, 4, 5, 6, 7), 'a row went missing'
        assert page.row_text(VIBRATION_ROW) == 'Vibration, not supported.'
        assert page.row_text(SHAKE_ROW) == 'Shake to break free, not supported.'
        assert page.row_text(CONTROLLER_ROW) == 'Controller, none attached.'
        # and the two that need no pad are untouched
        assert page.row_text(SPEECH_ROW) == 'Spoken headshot, currently on.'
        assert page.row_text(BEEP_ROW) == 'Headshot beep, currently off.'


def test_an_unsupported_row_will_not_turn_anything_on():
    with _NewSave() as s:
        s.d.setObject_forKey_('0', 'VIBRATION')
        s.d.setObject_forKey_('0', 'SHAKE')
        page = s.page()
        for row in (VIBRATION_ROW, SHAKE_ROW, CONTROLLER_ROW):
            page.selectMenu = row
            assert page.activate() == row
            assert page.speech.said[-1] == 'No controller is attached.', row
        assert s.d.stringForKey_('VIBRATION') == '0', 'vibration was turned on anyway'
        assert s.d.stringForKey_('SHAKE') == '0', 'the shake was turned on anyway'
        assert s.d.stringForKey_('CONTROLLER') in (None, ''), 'a pad was chosen'


def test_a_pad_with_no_sensor_says_why_the_shake_will_not_turn_on():
    with _NewSave() as s:
        s.pads('Xbox Wireless Controller')
        s.can_shake(False)
        s.d.setObject_forKey_('0', 'SHAKE')
        page = s.page()
        assert page.row_text(SHAKE_ROW) == 'Shake to break free, not supported.'
        assert page.row_text(VIBRATION_ROW) == 'Vibration, currently on.', 'vibration needs no sensor'
        page.selectMenu = SHAKE_ROW
        page.activate()
        assert page.speech.said[-1] == 'This controller cannot sense a shake.'
        assert s.d.stringForKey_('SHAKE') == '0'
        # the saved choice is kept underneath, so a pad that can sense one finds it again
        s.d.setObject_forKey_('1', 'SHAKE')
        assert page.row_text(SHAKE_ROW) == 'Shake to break free, not supported.'
        s.can_shake(True)
        assert page.row_text(SHAKE_ROW) == 'Shake to break free, currently on.'


def test_the_shake_setting_keeps_its_value_while_unsupported():
    """The setting is saved either way, so a DualSense plugged in later finds the player's
    old choice rather than a default."""
    with _NewSave() as s:
        s.pads('Xbox Wireless Controller')
        s.can_shake(True)
        page = s.page()
        page.selectMenu = SHAKE_ROW
        page.activate()
        assert s.d.stringForKey_('SHAKE') == '0'
        s.can_shake(False)                           # the pad is swapped for one with no sensor
        assert page.row_text(SHAKE_ROW) == 'Shake to break free, not supported.'
        s.can_shake(True)
        assert page.row_text(SHAKE_ROW) == 'Shake to break free, currently off.', 'it was reset'


def test_one_pad_reads_its_name_but_there_is_nothing_to_choose():
    with _NewSave() as s:
        s.pads('Xbox Wireless Controller')
        page = s.page()
        assert page.row_text(CONTROLLER_ROW) == 'Controller, Xbox Wireless Controller.'
        page.selectMenu = CONTROLLER_ROW
        page.activate()
        assert page.speech.said[-1] == 'This is the only controller attached.'
        assert s.d.stringForKey_('CONTROLLER') in (None, ''), 'it saved a choice anyway'


def test_the_picker_cycles_the_pads_and_saves_the_name():
    with _NewSave() as s:
        s.pads('Xbox Wireless Controller', 'PS5 Controller')
        page = s.page()
        assert page.row_text(CONTROLLER_ROW) == 'Controller, Xbox Wireless Controller.'
        page.selectMenu = CONTROLLER_ROW
        page.activate()
        assert s.d.stringForKey_('CONTROLLER') == 'PS5 Controller'
        assert page.speech.said[-1] == 'Controller, PS5 Controller.'
        assert page.row_text(CONTROLLER_ROW) == 'Controller, PS5 Controller.'
        page.activate()                              # and round again
        assert s.d.stringForKey_('CONTROLLER') == 'Xbox Wireless Controller'
        s.d.synchronize()
        with open(s.d.settings.path, encoding='utf-8') as fh:
            assert json.load(fh)['CONTROLLER'] == 'Xbox Wireless Controller'


def test_a_pad_sdl_has_listed_twice_is_one_entry():
    """On Windows SDL lists a DualSense twice until its own driver takes it
    (aidocks/completed/controller_shake_plan.md), and tunmi13productions asked for that not
    to show up as two controllers."""
    with _NewSave() as s:
        pads = s.pads('PS5 Controller', 'PS5 Controller')
        assert pads.names == ['PS5 Controller']
        page = s.page()
        assert page.row_text(CONTROLLER_ROW) == 'Controller, PS5 Controller.'
        page.selectMenu = CONTROLLER_ROW
        page.activate()
        assert page.speech.said[-1] == 'This is the only controller attached.'


def test_a_saved_name_that_is_not_attached_is_left_alone():
    """So plugging the preferred pad back in picks it up again with nothing to do."""
    with _NewSave() as s:
        s.d.setObject_forKey_('PS5 Controller', 'CONTROLLER')
        pads = s.pads('Xbox Wireless Controller')
        page = s.page()
        assert pads.active_name == 'Xbox Wireless Controller', 'it did not fall back'
        assert page.row_text(CONTROLLER_ROW) == 'Controller, Xbox Wireless Controller.'
        assert s.d.stringForKey_('CONTROLLER') == 'PS5 Controller', 'the choice was cleared'
        s.pads('Xbox Wireless Controller', 'PS5 Controller')
        assert s.app.controllers.active_name == 'PS5 Controller', 'it did not come back'


def test_the_real_keyboard_walks_and_flips():
    """Driving ScreenInput, the keyboard a pushed screen really uses: a screen whose rows
    are only ever called directly can ship unreachable (aidocks/completed/weapon_order_plan.md)."""
    from sixthsense.ui.screen_input import ScreenInput

    class _Pygame:
        KEYDOWN, KEYUP, QUIT = 1, 2, 3
        KMOD_SHIFT = 3

        class key:
            @staticmethod
            def name(k):
                return k

    class _Key:
        def __init__(self, name, mod=0):
            self.type = _Pygame.KEYDOWN
            self.key = name
            self.mod = mod

    with _NewSave() as s:
        s.pads('Xbox Wireless Controller')
        s.can_shake(True)
        page = s.page()
        page.startRead()
        assert page.speech.said[0] == 'Settings.'
        keys = ScreenInput(page)
        keys.handle(_Key('down'), _Pygame)
        keys.handle(_Key('down'), _Pygame)
        assert page.selectMenu == SPEECH_ROW
        assert page.speech.said[-1] == 'Spoken headshot, currently on.'
        keys.handle(_Key('return'), _Pygame)
        assert s.d.stringForKey_('HEADSHOTSPEECH') == '0'
        assert page.speech.said[-1] == 'Spoken headshot, off.'
        keys.handle(_Key('end'), _Pygame)
        assert page.selectMenu == CONTROLLER_ROW, 'End did not reach the last row'
        keys.handle(_Key('escape'), _Pygame)
        assert page.done, 'Escape did not go back'


if __name__ == '__main__':
    fns = [v for k, v in sorted(globals().items()) if k.startswith('test_')]
    bad = 0
    for fn in fns:
        try:
            fn()
            print('ok    %s' % fn.__name__)
        except AssertionError as e:
            bad += 1
            print('FAIL  %s: %s' % (fn.__name__, e))
        except Exception as e:
            bad += 1
            print('ERROR %s: %r' % (fn.__name__, e))
    print('%d/%d passed' % (len(fns) - bad, len(fns)))
    sys.exit(1 if bad else 0)
