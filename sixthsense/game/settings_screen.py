"""PORT ADDITION: the Settings screen, where every setting the menu used to carry lives.

tunmi13productions, 2026-10-06 (aidocks/completed/settings_menu_plan.md).  The main menu
had grown three setting rows of its own - vibration and the two headshot settings - so
they moved in here behind one Settings row, and the screen gained two more: the shake,
and which controller the game plays with.  Controller support joined them on 2026-10-06
(aidocks/completed/controller_support_plan.md): off, the game opens no pad at all, so a
player with a pad plugged in for something else plays on the keyboard.

**A row the attached pad cannot do stays where it is and says so.**  It reads
"Vibration, not supported." and will not turn on; pressing it says why instead.
tunmi13productions asked for that rather than hiding the row: a row that disappears
leaves a player counting rows and wondering what they lost, where "not supported"
answers the question on the spot.  The setting keeps its saved value underneath, so a pad
that can do it later finds the player's old choice intact, and an unsupported row can
never switch something on that the pad cannot do.
"""
from __future__ import annotations

import logging

from .. import paths
from .blind_screen import BlindScreen
from .stage_1_e import SOUND_HEADSHOT_BEEP
from .store import BACK_TEXT

log = logging.getLogger('settings')

#: The rows, named so that inserting one is a matter of the numbers here and nowhere else.
#: The ones that need no pad come first, so the ones that can read "not supported" are
#: always at the end of the list.
BACK_ROW = 1
#: first of all, from source only: a build has no such row (tsatria03, 2026-10-07,
#: aidocks/completed/debug_setting_plan.md)
DEBUG_ROW = 2
SKIP_INTRO_ROW = 3
SPEECH_ROW = 4
BEEP_ROW = 5
#: the gate for the three rows after it, which is why it comes before them and needs no
#: pad itself (2026-10-06, aidocks/completed/controller_support_plan.md)
CONTROLLER_SUPPORT_ROW = 6
VIBRATION_ROW = 7
SHAKE_ROW = 8
#: the picker, which is not a toggle
CONTROLLER_ROW = 9

#: row -> (what it is called, the attribute that reads it, the attribute that sets it)
TOGGLES = {
    DEBUG_ROW: ('Debug mode', 'debug', 'set_debug'),
    SKIP_INTRO_ROW: ('Skip the opening screens', 'skip_intro_on', 'set_skip_intro'),
    SPEECH_ROW: ('Spoken headshot', 'headshot_speech_on', 'set_headshot_speech'),
    BEEP_ROW: ('Headshot beep', 'headshot_beep_on', 'set_headshot_beep'),
    CONTROLLER_SUPPORT_ROW: ('Controller support', 'controller_support',
                             'set_controller_support'),
    VIBRATION_ROW: ('Vibration', 'vibration_on', 'set_vibration'),
    SHAKE_ROW: ('Shake to break free', 'shake_on', 'set_shake'),
}
#: the rows that need a controller for there to be anything to change
NEED_PAD = (VIBRATION_ROW, SHAKE_ROW, CONTROLLER_ROW)


class SettingsController(BlindScreen):
    """Back, Debug mode when run from source, the five toggles, then the controller
    picker."""

    ROWS = (BACK_ROW, DEBUG_ROW, SKIP_INTRO_ROW, SPEECH_ROW, BEEP_ROW,
            CONTROLLER_SUPPORT_ROW, VIBRATION_ROW, SHAKE_ROW, CONTROLLER_ROW)
    TITLE_TEXT = 'Settings.'

    def __init__(self, speech=None):
        BlindScreen.__init__(self, speech=speech)
        self.selectMenu = 1
        self.message = ''                   # for anyone who can see the window

    def rows(self):
        """Every row, less Debug mode in a build, where players have no debug mode."""
        if paths.FROZEN:
            return tuple(r for r in self.ROWS if r != DEBUG_ROW)
        return self.ROWS

    # ---- what the attached pad can do -------------------------------------------------
    def _names(self):
        """The pads attached, each name once.  None attached is an empty list."""
        pads = self.app.controllers
        return list(getattr(pads, 'names', []) or []) if pads is not None else []

    def why_not(self, row):
        """Why a row cannot be used, or None when it can be.

        A row needing a pad with nothing attached, and the shake on a pad with no motion
        sensor, are the two cases.  The picker is a third: one pad is nothing to choose
        between.  Controller support being off is a fourth, and it answers before the
        others: with the support off no pad is open, so "No controller is attached." would
        be a lie to a player who has one plugged in (2026-10-06).
        """
        if row in NEED_PAD and not self.app.controller_support:
            return 'Controller support is off.'
        names = self._names()
        if row in NEED_PAD and not names:
            return 'No controller is attached.'
        if row == SHAKE_ROW and not self.app.can_shake():
            return 'This controller cannot sense a shake.'
        if row == CONTROLLER_ROW and len(names) < 2:
            return 'This is the only controller attached.'
        return None

    def supported(self, row):
        """Whether the row can be changed at all.  The picker with one pad is *supported*
        but has nothing to change, so it still reads its name; only a row that cannot work
        at all reads "not supported"."""
        if row == CONTROLLER_ROW:
            return self.app.controller_support and bool(self._names())
        return row not in NEED_PAD or self.why_not(row) is None

    # ---- the rows ---------------------------------------------------------------------
    def row_text(self, row):
        if row == BACK_ROW:
            return BACK_TEXT
        if row == CONTROLLER_ROW:
            if not self.app.controller_support:
                # with the support off it reads like the three rows above it, rather than
                # "none attached", which would be a lie with a pad plugged in
                return 'Controller, not supported.'
            name = self.app.controllers.active_name if self.app.controllers else None
            return 'Controller, %s.' % (name or 'none attached')
        label, reads, _writes = TOGGLES[row]
        if not self.supported(row):
            return '%s, not supported.' % label
        return '%s, currently %s.' % (label, 'on' if getattr(self.app, reads) else 'off')

    def activate(self):
        self.StopElseSpeak()
        row = self.selectMenu
        if row == BACK_ROW:
            self.goBackAction_()
        elif row == CONTROLLER_ROW:
            self.nextControllerAction_()
        elif row in TOGGLES and row in self.rows():
            self.toggleAction_(row)
        return row

    def toggleAction_(self, row):
        """Flip a setting and say what it is now.  A row the pad cannot do says why and
        changes nothing, so it can never switch on something the pad cannot do."""
        why = self.why_not(row)
        if why is not None:
            self.message = why
            self.say(why)
            return None
        self.ui_select()
        label, reads, writes = TOGGLES[row]
        now = not getattr(self.app, reads)
        getattr(self.app, writes)(now)
        self.message = ''
        self.say('%s, %s.' % (label, 'on' if now else 'off'))
        if now:
            # the same proof the menu's rows gave: vibration buzzes once, and the beep
            # plays once, so the player hears what they just chose
            if row == VIBRATION_ROW:
                self.app.vibrate_effect('confirm')
            elif row == BEEP_ROW:
                self.app.playSound_Gain_Pos_z_reprats_(
                    SOUND_HEADSHOT_BEEP, 1.0, (0.0, 0.0), 0, False)
        log.info('%s %s', label, 'on' if now else 'off')
        return now

    def nextControllerAction_(self):
        """Move to the next attached pad and say its name.

        The choice is saved by name, never by an id: unplug the pad on id 0 and the next
        one plugged in takes that id (tunmi13productions, 2026-10-06).  A pad SDL has
        listed twice is one name, so it is one stop in the list.
        """
        why = self.why_not(CONTROLLER_ROW)
        if why is not None:
            self.message = why
            self.say(why)
            return None
        self.ui_select()
        names = self._names()
        now = self.app.controllers.active_name
        at = names.index(now) if now in names else -1
        name = names[(at + 1) % len(names)]
        self.app.set_controller_choice(name)
        self.message = ''
        self.say('Controller, %s.' % name)
        return name
