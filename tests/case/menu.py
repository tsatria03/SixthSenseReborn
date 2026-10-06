"""The main menu: the rows, the free games and the voice-over toggle."""
from __future__ import annotations

import os
import plistlib
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import _scratch_save                                             # noqa: E402,F401  never the real save

from sixthsense import paths                                     # noqa: E402
from sixthsense.game.app_delegate import AppDelegate             # noqa: E402
from sixthsense.game.main_controller import ROWS, MainController  # noqa: E402
from sixthsense.platform import openal as al                     # noqa: E402
from sixthsense.platform import sound_trims, volume              # noqa: E402
from sixthsense.platform.defaults import UserDefaults            # noqa: E402
from sixthsense.platform.music import MusicPlayer                # noqa: E402
from sixthsense.platform.runloop import RunLoop                  # noqa: E402


class _Recorder:
    def __init__(self):
        self.said = []
        self.stopped = 0

    def speak(self, text, interrupt=True):
        self.said.append(text)
        return True

    def stop(self):
        self.stopped += 1


def _menu():
    d = UserDefaults.standardUserDefaults()
    d.setObject_forKey_('1', 'TUTORIAL')
    d.synchronize()
    app = AppDelegate.shared()
    if app.playback is None:
        app.didFinishLaunching()
    RunLoop.main().reset()
    m = MainController(speech=_Recorder())
    m.viewDidLoad()
    return m


def test_the_rows_are_the_originals():
    """The rows selectTapPointSoundStart (0x9825) claims, with their sounds and their
    original numbers, less the coins (1), ranking (5) and Game Center (8), the voice over
    row (7), which went on 2026-10-05 with the recorded voice, and the port's settings row
    (9), which has no recording.  Until 2026-10-06 the vibration and the two headshot
    settings were rows 9, 10 and 11 here; they moved behind the settings row
    (aidocks/project_settings_menu_plan.md)."""
    assert [r[0] for r in ROWS] == [2, 3, 4, 6, 9]
    assert [r[3] for r in ROWS] == ['title', 'start', 'tutorial', 'store', 'settings']
    assert [r[2] for r in ROWS] == [16, 17, 23, 18, None]
    # every one of them is a real entry with a WAV behind it
    sl = plistlib.load(open(paths.path_for_resource('SoundList', 'plist'), 'rb'))
    for _n, _f, sound, _a in ROWS:
        if sound is not None:                  # the settings row has no recording
            assert paths.path_for_resource(sl[sound], 'wav'), sound


def test_the_menu_music_plays_under_the_rows():
    """BGMusicStart is a port addition - the original's MainController never starts music
    (only -[Stage_1_E GameEndAction:] does, 0x330da) - so its gain is the port's to choose.
    It plays at volume.MENU_MUSIC_DB, no louder than the 0.2 every row is read at, instead
    of the 1.0 it started at, which talked over the rows."""
    app = AppDelegate.shared()
    if app.playback is None:
        app.didFinishLaunching()
    pb = app.playback
    calls = []
    pb.startBGPlayer_type_soundGain_Loop_ = lambda n, t, g, l: calls.append((n, g, l))
    try:
        app.BGMusicStart()
        assert calls == [('bgm_main_menu', volume.menu_music(), True)], calls
        assert volume.menu_music() <= 0.2, \
            'the menu music is louder than the rows it plays under'
    finally:
        del pb.startBGPlayer_type_soundGain_Loop_        # back to the real player


class _FakeAL:
    """Enough of platform/openal.AL for MusicPlayer, with nothing behind it."""

    def __init__(self):
        self.calls = []
        self.state = al.AL_PLAYING

    def gen_source(self):
        return 1

    def gen_buffer(self):
        return 2

    def buffer_data(self, *a):
        pass

    def delete_buffer(self, bid):
        self.calls.append(('delete', bid))

    def source_state(self, _sid):
        return self.state

    def alGetError(self):
        return 0

    def alSource3f(self, *a):
        pass

    def alSourcei(self, _sid, param, value):
        self.calls.append(('sourcei', param, value))

    def alSourcef(self, _sid, param, value):
        self.calls.append(('gain', value) if param == al.AL_GAIN else ('sourcef', param))

    def alSourceStop(self, _sid):
        self.calls.append(('stop',))

    def alSourcePlay(self, _sid):
        self.calls.append(('play',))


class _FakeOwner:
    def __init__(self):
        self.al = _FakeAL()


def test_the_menu_music_carries_on_when_the_menu_comes_back():
    """A menu is built fresh every time the player comes back from a stage, the shop or
    the tutorial, and each one calls BGMusicStart.  The music player leaves a source
    alone when it is asked for the file it is already playing, so the music carries on
    instead of jumping back to its first bar - it only takes the new gain."""
    owner = _FakeOwner()
    player = MusicPlayer(owner)
    song = paths.path_for_resource('bgm_main_menu', 'wav')
    other = paths.path_for_resource('bgm_cave', 'wav')
    assert song and other, 'the menu music or the cave music is missing'

    player.play(song, 0.2, -1)
    assert ('play',) in owner.al.calls, 'the first play did not start anything'

    owner.al.calls.clear()
    player.play(song, 0.1, -1)                    # the menu comes back
    assert ('stop',) not in owner.al.calls, 'the same file was stopped and rewound'
    assert ('play',) not in owner.al.calls, 'the same file was restarted'
    # the gain asked for, times the file's own trim (platform/sound_trims.py)
    assert ('gain', 0.1 * sound_trims.gain('bgm_main_menu')) in owner.al.calls, \
        'the new gain was not applied'
    assert player.volume == 0.1

    owner.al.calls.clear()
    player.play(other, 0.02, -1)                  # a different file still starts over
    assert ('play',) in owner.al.calls, 'a different file did not start'

    owner.al.calls.clear()
    owner.al.state = al.AL_STOPPED                # it ran out, so it plays again
    player.play(other, 0.02, -1)
    assert ('play',) in owner.al.calls, 'a finished file did not start again'


def test_changing_the_music_frees_the_file_it_had():
    """OpenAL refuses to delete a buffer that is still attached to a source, so the order
    matters: stop the source, take the buffer off it with AL_BUFFER 0, then delete.  The
    player used to delete first, which freed nothing and held a 2 to 3 MB file for the life
    of the process - and a level change swaps two of them."""
    owner = _FakeOwner()
    player = MusicPlayer(owner)
    song = paths.path_for_resource('bgm_main_menu', 'wav')
    other = paths.path_for_resource('bgm_cave', 'wav')
    assert song and other, 'the menu music or the cave music is missing'

    player.play(song, 0.2, -1)
    owner.al.calls.clear()
    player.play(other, 0.02, -1)

    order = [c for c in owner.al.calls
             if c[0] in ('stop', 'delete') or (c[0] == 'sourcei' and c[1] == al.AL_BUFFER)]
    assert order[0] == ('stop',), order
    assert order[1] == ('sourcei', al.AL_BUFFER, 0), 'the buffer was not detached first'
    assert order[2][0] == 'delete', 'the old buffer was not deleted'
    detach = order.index(('sourcei', al.AL_BUFFER, 0))
    delete = [i for i, c in enumerate(order) if c[0] == 'delete'][0]
    assert detach < delete, 'deleting before detaching frees nothing'


def test_there_is_no_exit_row():
    """exit_flag and Exit: exist, but no row claims them and nothing plays sound 20."""
    assert 'exit' not in [r[3] for r in ROWS]


def test_it_opens_on_the_title_and_wraps():
    m = _menu()
    try:
        assert m.selectMenu == 2                      # 0x85c1
        seen = []
        for _ in range(len(ROWS)):
            m.move(1)
            seen.append(m._row()[3])
        assert seen == ['start', 'tutorial', 'store', 'settings', 'title'], seen
        m.selectMenu = 2
        m.move(-1)
        assert m.selectMenu == 9, 'moving up off the top did not wrap'
    finally:
        m.teardown()


def test_a_game_is_free_and_there_are_no_coins():
    """-[MainController StartGameAction:] 0xb2ed spent a coin; the port's games are free
    (aidocks/completed/free_games_plan.md), and nothing counts coins or recharges them."""
    m = _menu()
    try:
        m.selectMenu = 3
        m.activate()
        assert m.next_screen == 'stage'
        for n in range(8):                           # as many starts as you like
            m.next_screen = None
            m.activate()
            assert m.next_screen == 'stage', 'start %d was refused' % n
        assert not hasattr(m.app, 'Coin') and not hasattr(m, 'coinTimer')
        assert 'coin' not in [r[3] for r in ROWS]
        d = UserDefaults.standardUserDefaults()
        assert d.objectForKey_('COIN_TIMER') is None, 'a recharge clock was written'
    finally:
        m.teardown()


def test_the_menu_never_plays_the_earphone_warning():
    """PORT ADDITION: the earphone warning (234) now plays once from the intro
    screen (see tests/case/intro.py), not from the menu at all - it used to play
    at menu load, talking over the title, then briefly from Start Game instead,
    which repeated every time a game was started."""
    played = []
    d = UserDefaults.standardUserDefaults()
    d.setObject_forKey_('1', 'TUTORIAL')
    d.synchronize()
    app = AppDelegate.shared()
    if app.playback is None:
        app.didFinishLaunching()
    RunLoop.main().reset()
    real_play = app.playSound_Gain_Pos_z_reprats_
    app.playSound_Gain_Pos_z_reprats_ = \
        lambda num, *a, **k: (played.append(num), real_play(num, *a, **k))[-1]
    m = MainController(speech=_Recorder())
    try:
        m.viewDidLoad()
        assert 234 not in played, 'the earphone warning played at menu load'
        m.selectMenu = 3
        m.activate()
        assert 234 not in played, 'the earphone warning played from Start Game'
    finally:
        app.playSound_Gain_Pos_z_reprats_ = real_play
        m.teardown()


def test_the_first_start_goes_to_the_tutorial():
    """0xb2ed never reads TUTORIAL: Start pushes Stage_1_E, which runs the tutorial
    inline first.  The port sends the first run to Stage_Tutorial, told to count down
    into the game when it ends."""
    m = _menu()
    d = UserDefaults.standardUserDefaults()
    d.setObject_forKey_('0', 'TUTORIAL')
    d.synchronize()
    try:
        m.selectMenu = 3
        m.activate()
        assert m.next_screen == ('tutorial', True), m.next_screen
    finally:
        m.teardown()


def test_there_is_no_voice_over_row():
    """The game is always read by the screen reader since 2026-10-05, so the row that
    switched the recorded voice on is gone, with its sounds and its saved setting."""
    from sixthsense.game import main_controller as MC
    assert 'modechange' not in [r[3] for r in MC.ROWS]
    assert not hasattr(MC.MainController, 'ModeChageAction_')
    assert not hasattr(AppDelegate.shared(), 'mode')


def test_there_is_no_ranking_or_game_center_row():
    """Rows 5 and 8 opened the publisher's ranking server and Apple's Game Center,
    which the port does not have, so they are left out, and moving never lands on
    them."""
    actions = [r[3] for r in ROWS]
    assert 'ranking' not in actions and 'gamecenter' not in actions
    m = _menu()
    try:
        for _ in range(2 * len(ROWS)):
            m.move(1)
            assert m.selectMenu not in (5, 8), m.selectMenu
        for _ in range(2 * len(ROWS)):
            m.move(-1)
            assert m.selectMenu not in (5, 8), m.selectMenu
    finally:
        m.teardown()


def test_the_store_row_opens_the_shop():
    """-[MainController StoreAction:] 0xb6d0 pushes mainStoreController."""
    m = _menu()
    try:
        m.selectMenu = 6
        m.activate()
        assert m.next_screen == 'store'
    finally:
        m.teardown()


def test_the_settings_row_opens_the_settings_screen():
    """PORT ADDITION (2026-10-06): the vibration and headshot rows moved behind this one
    (aidocks/project_settings_menu_plan.md)."""
    from sixthsense.game import main_controller as MC
    m = _menu()
    played = []
    real = m.app.playSound_Gain_Pos_z_reprats_
    m.app.playSound_Gain_Pos_z_reprats_ = lambda n, *a: (played.append(n), real(n, *a))[-1]
    try:
        m.selectMenu = 9
        m.blindModeSelectedMenu()
        assert m.speech.said[-1] == 'Settings, Button'
        m.activate()
        assert m.next_screen == 'settings'
        assert played == [MC.SOUND_UI_SELECT], played
    finally:
        m.app.__dict__.pop('playSound_Gain_Pos_z_reprats_', None)
        m.teardown()


def test_start_and_store_click_first():
    """tapCount sends StartGame: (0x9420) and Store: (0x9438), which click (10 at 0.2,
    0xad32 and 0xb6a8) before StartGameAction: and StoreAction:.  The port clicked only
    when a coin was spent, and never for the Store row."""
    from sixthsense.game import main_controller as MC
    m = _menu()
    app = m.app
    played = []
    app.playSound_Gain_Pos_z_reprats_ = lambda n, *a: played.append(n)
    try:
        m.selectMenu = next(n for n, _f, _s, a in MC.ROWS if a == 'start')
        m.activate()
        assert played == [10], played
        m.selectMenu = next(n for n, _f, _s, a in MC.ROWS if a == 'store')
        played.clear()
        m.activate()
        assert played == [10], played
        assert m.next_screen == 'store'
    finally:
        del app.playSound_Gain_Pos_z_reprats_
        m.teardown()


def test_the_rows_speak_through_the_screen_reader():
    """The menu says each row as the player moves, whatever an old save says."""
    d = UserDefaults.standardUserDefaults()
    m = _menu()
    try:
        m.move(-1)
        assert m.speech.said[-1] == 'Settings, Button'
        m.move(-1)
        assert m.speech.said[-1] == 'Store, Button'
        m.move(-2)                  # tutorial, start
        assert m.speech.said[-1] == 'Game start, Button', m.speech.said[-1]
        m.move(-1)
        assert m.speech.said[-1] == 'Sixth Sense Reborn: The Zombies'
    finally:
        m.teardown()


class _Pygame:
    """Just enough of pygame for a keyboard handler: key-downs named by their key."""
    KEYDOWN, KEYUP, QUIT = 1, 2, 3

    class key:
        @staticmethod
        def name(k):
            return k


class _Key:
    def __init__(self, name):
        self.type = _Pygame.KEYDOWN
        self.key = name


class _Buzzer:
    def __init__(self):
        self.played, self.stopped = [], 0

    def play(self, name):
        self.played.append(name)

    def play_zombie(self, kind):
        pass

    def stop(self):
        self.stopped += 1


# The vibration and headshot rows moved to the Settings screen on 2026-10-06, and
# their tests with them: see tests/case/settings_menu.py
# (aidocks/project_settings_menu_plan.md).

def test_vibration_off_stops_the_effects_and_the_connect_buzz():
    import pygame

    from sixthsense.ui.controller import Controllers
    from sixthsense.ui.vibration import Vibration

    class _Pad:
        def __init__(self):
            self.calls = []
            self.id, self.name = 1, 'pad'

        def rumble(self, *a):
            self.calls.append(a)

        def stop_rumble(self):
            pass

    class _Sdl:
        def init(self):
            pass

        def get_count(self):
            return 0

    d = UserDefaults.standardUserDefaults()
    m = _menu()
    try:
        pads = Controllers(pygame, m.app, sdl=_Sdl())
        pad = _Pad()
        pads._pads[1] = pad
        vib = Vibration(pads, enabled=lambda: m.app.vibration_on)
        d.setObject_forKey_('0', 'VIBRATION')
        assert vib.play('girl') is False and pad.calls == []
        pads._found(pad)
        assert pad.calls == [], 'the connect buzz ignored the setting'
        d.setObject_forKey_('1', 'VIBRATION')
        assert vib.play('girl') is True and pad.calls
        pad.calls.clear()
        pads._found(pad)
        assert pad.calls, 'the connect buzz should play with vibration on'
    finally:
        d.removeObjectForKey_('VIBRATION')
        m.teardown()


def test_home_and_end_in_the_screen_reader_mode():
    """Home and End go to the first row and the last, in the main menu and in the shop,
    as a screen reader's own lists do."""
    from sixthsense.game.main_controller import ROWS
    from sixthsense.game.store import MainStoreController
    from sixthsense.ui.menu_input import MenuInput
    from sixthsense.ui.screen_input import ScreenInput
    m = _menu()
    shop = MainStoreController(speech=_Recorder())
    try:
        keys = MenuInput(m)
        keys.handle(_Key('end'), _Pygame)
        assert m.selectMenu == ROWS[-1][0], 'End went to row %d' % m.selectMenu
        keys.handle(_Key('home'), _Pygame)
        assert m.selectMenu == ROWS[0][0], 'Home went to row %d' % m.selectMenu

        rows = shop.rows()
        keys = ScreenInput(shop)
        keys.handle(_Key('end'), _Pygame)
        assert shop.selectMenu == rows[-1], 'End went to row %d' % shop.selectMenu
        assert shop.speech.said, 'End did not read the row'
        keys.handle(_Key('home'), _Pygame)
        assert shop.selectMenu == rows[0], 'Home went to row %d' % shop.selectMenu
    finally:
        shop.teardown()
        m.teardown()


def test_left_and_right_move_like_voiceovers_flicks_in_the_screen_reader_mode():
    """Right goes to the next row and Left to the previous one, in the main menu and in
    the shop, as VoiceOver's flicks did."""
    from sixthsense.game.main_controller import ROWS
    from sixthsense.game.store import MainStoreController
    from sixthsense.ui.menu_input import MenuInput
    from sixthsense.ui.screen_input import ScreenInput
    m = _menu()
    shop = MainStoreController(speech=_Recorder())
    nums = [r[0] for r in ROWS]
    try:
        keys = MenuInput(m)
        m.selectMenu = nums[1]
        keys.handle(_Key('right'), _Pygame)
        assert m.selectMenu == nums[2], 'Right went to row %d' % m.selectMenu
        keys.handle(_Key('left'), _Pygame)
        keys.handle(_Key('left'), _Pygame)
        assert m.selectMenu == nums[0], 'Left went to row %d' % m.selectMenu
        keys.handle(_Key('left'), _Pygame)
        assert m.selectMenu == nums[-1], 'Left did not wrap to the last row'

        rows = shop.rows()
        keys = ScreenInput(shop)
        shop.select(rows[0])
        shop.speech.said.clear()
        keys.handle(_Key('right'), _Pygame)
        assert shop.selectMenu == rows[1], 'Right went to row %d' % shop.selectMenu
        assert shop.speech.said, 'Right did not read the row'
        keys.handle(_Key('left'), _Pygame)
        assert shop.selectMenu == rows[0], 'Left went to row %d' % shop.selectMenu
    finally:
        shop.teardown()
        m.teardown()


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
