"""``MainController`` - the main menu. Ported from 0x81f0..0xccb0.

The original's menu spoke from the game's own WAVs, and it is built for a finger rather
than a cursor: ``-[MainController selectTapPointSoundStart]`` (0x9825) maps the *Y
coordinate* of a touch to a row, sets ``selectMenu``, raises that row's flag and plays
its name; a double tap then activates whatever ``selectMenu`` is on
(``-[MainController tapCount]`` 0x9350). The whole blind path is gated on
``[AppDelegate mode]`` - ``-[MainController Menu:]`` returns immediately when it is 0,
which is the sighted button layout.  The port's rows are spoken by the screen reader,
``ROW_TEXT`` (aidocks/completed/screen_reader_only_plan.md).

The original's eight rows, in screen order, with the flag and sound each one owned:

    selectMenu  flag              sound
     1          coin_flag         334  "number of coins"
         (gone with the coins: games are free in the port)
     2          main_title_flag    16  "Six Sense _ The Zombies"
     3          start_game_flag    17  "Game Start Button"
     4          tutorial_flag      23  "Tutorial Button"
     5          ranking_flag      333  "ranking button"
     6          store_flag         18  "Store Button"
     7          modechange_flag   331  "voice over on button" / 332 "...off button"
         (the port has no such row since 2026-10-05: the game is always read by the
         screen reader, so the row that switched the recordings on is gone)
     8          gamecenter_flag   367  "game center button10"

**DIVERGENCE:** rows 5 and 8, ranking and Game Center, are left out.  Both opened
online services (the publisher's ranking server and Apple's Game Center) that the
Windows port does not have, so the menu goes 4, 6, 7 and wraps.  The rest keep the
original's numbers.

``exit_flag`` and ``Exit:`` exist and ``exitButton`` is in the nib, but no row in
``selectTapPointSoundStart`` claims it and no code plays sound 20 - so Exit is not
reachable from the blind menu at all. Reproduced: the port has no Exit row either, and
Escape quits.

**PORT DIVERGENCE: games are free.** In the original a game cost a coin:
``-[MainController StartGameAction:]`` (0xb2ed) spent one, or played 358 "no coin" when
there were none, and the coins came back one every 1800 s up to five
(``coinTiemrControlStart`` 0xbe01, ``coinUpTimer`` 0xc0b1, and for time away
``viewDidLoad`` 0x8aca-0x8b14), kept in ``COIN``, ``COIN_TIMER`` and
``COIN_TIMER_START``.  None of that is ported (aidocks/completed/free_games_plan.md), and
an old save's coin keys are dropped (``defaults.RETIRED_KEYS``).
"""
from __future__ import annotations

import logging

from ..platform.defaults import UserDefaults
from ..platform.runloop import RunLoop
from .app_delegate import AppDelegate

log = logging.getLogger('menu')

SOUND_UI_SELECT = 10

# selectMenu, flag, what it does
ROWS = (
    (2, 'main_title_flag', 'title'),
    (3, 'start_game_flag', 'start'),
    (4, 'tutorial_flag', 'tutorial'),
    (6, 'store_flag', 'store'),
    # PORT ADDITION: the settings row.  Until 2026-10-06 the vibration and the two
    # headshot settings were three rows of their own here; they moved behind this one
    # (aidocks/completed/settings_menu_plan.md).
    (9, 'settings_flag', 'settings'),
)
#: PORT ADDITION: what the screen reader says for each row.  The rows that are a setting are
#: made in ``row_text``.
ROW_TEXT = {
    'title': 'Sixth Sense Reborn: The Zombies',
    'start': 'Game start, Button',
    'tutorial': 'Tutorial, Button',
    'store': 'Store, Button',
    'settings': 'Settings, Button',
}


class MainController:
    """The menu. ``next_screen`` is what the frame loop should put up next."""

    def __init__(self, speech=None):
        self.app = AppDelegate.shared()
        self.selectMenu = 2                 # 0x85c1 viewDidLoad starts on the title
        self.tapCount = 0
        self.next_screen = None             # 'stage' | 'tutorial' | None
        self.quit = False
        self.speech = speech
        self.message = ''                   # maskLabel1
        self._flags = {f: False for _n, f, _a in ROWS}

    # ================================================================ entry
    # -[MainController viewDidLoad] 0x85c1
    def viewDidLoad(self):
        self.app.BGMusicStart()
        self.selectMenu = 2
        self.blindModeSelectedMenu()

    # -[MainController StopElseSpeak] 0x96e9 - silence every menu voice; the original's
    # were recordings, the port's is the screen reader
    def StopElseSpeak(self):
        if self.speech is not None:
            self.speech.stop()

    # =============================================================== moving
    def _row(self, n=None):
        n = self.selectMenu if n is None else n
        for row in ROWS:
            if row[0] == n:
                return row
        return ROWS[0]

    def row_text(self, n=None):
        """What the screen reader says for a row."""
        return ROW_TEXT[self._row(n)[2]]

    # -[MainController blindModeSelectedMenu] 0x90d0 - highlight the row and say it
    def blindModeSelectedMenu(self):
        num, flag, action = self._row()
        for f in self._flags:
            self._flags[f] = False
        self.StopElseSpeak()
        self._flags[flag] = True
        self._say(self.row_text())
        log.info('menu: %s', action)

    def move(self, delta):
        """Up and Down walk the rows in order and wrap, skipping the numbers the port
        leaves out."""
        nums = [r[0] for r in ROWS]
        if self.selectMenu in nums:
            i = (nums.index(self.selectMenu) + delta) % len(nums)
        else:
            i = 0 if delta > 0 else len(nums) - 1
        self.selectMenu = nums[i]
        self.blindModeSelectedMenu()

    def jump(self, last=False):
        """PORT ADDITION: Home and End in the screen reader mode, the first row or the
        last, as a screen reader's own lists go."""
        nums = [r[0] for r in ROWS]
        self.selectMenu = nums[-1] if last else nums[0]
        self.blindModeSelectedMenu()

    # ============================================================ activating
    # -[MainController tapCount] 0x9350 - a double tap runs the selected row
    def activate(self):
        action = self._row()[2]
        if action == 'title':
            self.blindModeSelectedMenu()
            return
        # tapCount sends StartGame: (0x9420) and Store: (0x9438), the two wrappers that
        # click first; Tutorial and the mode change are sent their actions directly.
        if action == 'start':
            self.StartGame_(None)
        elif action == 'tutorial':
            self.TutorialAction_(None)
        elif action == 'settings':
            self.SettingsAction_(None)
        elif action == 'store':
            self.Store_(None)

    # -[MainController StartGame:] 0xac50
    def StartGame_(self, *_):
        """Stop what is speaking, click (0xad32, 10 at 0.2) and go on to
        ``StartGameAction:``.  The headphone and VoiceOver checks in front (0xac60..0xacfa) belong
        to the phone and are left out."""
        self.StopElseSpeak()
        self.app.playSound_Gain_Pos_z_reprats_(SOUND_UI_SELECT, 0.2, (0.0, 0.0), 0, False)
        self.StartGameAction_(None)

    # -[MainController Store:] 0xb67c
    def Store_(self, *_):
        """Click (0xb6a8, 10 at 0.2), then ``StoreAction:``."""
        self.app.playSound_Gain_Pos_z_reprats_(SOUND_UI_SELECT, 0.2, (0.0, 0.0), 0, False)
        self.StoreAction_(None)

    def _say(self, text):
        """The one place the menu needs words the bundle has no recording for."""
        if self.speech is None:
            from ..platform.speech import Speech
            self.speech = Speech.shared()
        self.speech.speak(text)

    # -[MainController StoreAction:] 0xb6d0
    def StoreAction_(self, *_):
        """Push ``mainStoreController``.  Only two of its rows were purchases; the
        weapon shop spends the gold a run pays, which is a local key.

        0xb6d0 plays nothing of its own - the shop's first row reads itself as soon
        as it comes up."""
        self.StopElseSpeak()
        self.next_screen = 'store'

    # -[MainController StartGameAction:] 0xb2ed
    def StartGameAction_(self, *_):
        """Start a game.  PORT DIVERGENCE: it is free.  The original spent one of five
        coins that came back every 30 minutes and said "no coin" when there were none
        (0xb324..0xb5a0); aidocks/completed/free_games_plan.md has why that is gone.

        0xb3f8 always pushes Stage_1_E, whose MapInitInBundle (0x2e08e-0x2e0dc) runs the
        tutorial inline while TUTORIAL is 0.  The port runs that tutorial in
        Stage_Tutorial, which counts down into the game when it ends.  No click here:
        the click is StartGame:'s, before it."""
        self.StopElseSpeak()
        d = UserDefaults.standardUserDefaults()
        if d.intForKey_('TUTORIAL') == 0:
            self.next_screen = ('tutorial', True)
        else:
            self.next_screen = 'stage'

    # -[MainController TutorialAction:] 0xad5d
    def TutorialAction_(self, *_):
        self.StopElseSpeak()
        self.app.playSound_Gain_Pos_z_reprats_(
            SOUND_UI_SELECT, 0.2, (0.0, 0.0), 0, False)
        self.next_screen = 'tutorial'

    def SettingsAction_(self, *_):
        """PORT ADDITION (2026-10-06): push the Settings screen, as ``StoreAction:`` pushes
        the shop.  The vibration and headshot rows that used to be here live on it now
        (aidocks/completed/settings_menu_plan.md)."""
        self.StopElseSpeak()
        self.app.playSound_Gain_Pos_z_reprats_(SOUND_UI_SELECT, 0.2, (0.0, 0.0), 0, False)
        self.next_screen = 'settings'

    # ================================================================= misc
    def teardown(self):
        RunLoop.main().cancelPerform(self)
        self.StopElseSpeak()
