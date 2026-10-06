"""PORT ADDITION: the Settings screen, where every setting the menu used to carry lives.

tunmi13productions, 2026-10-06 (aidocks/project_settings_menu_plan.md).  The main menu
had grown three setting rows of its own - vibration and the two headshot settings - so
they moved in here behind one Settings row, and the screen gained two more: the shake,
and which controller the game plays with.

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

from .blind_screen import BlindScreen
from .store import BACK_TEXT

log = logging.getLogger('settings')

SOUND_BACK = 13
SOUND_HEADSHOT_BEEP = 374           # PORT ADDITION: the dev's own, as the menu played it

#: row -> (what it is called, the attribute that reads it, the attribute that sets it).
#: The two that need no pad come first, so the ones that can read "not supported" are
#: always at the end of the list.
TOGGLES = {
    2: ('Spoken headshot', 'headshot_speech_on', 'set_headshot_speech'),
    3: ('Headshot beep', 'headshot_beep_on', 'set_headshot_beep'),
    4: ('Vibration', 'vibration_on', 'set_vibration'),
    5: ('Shake to break free', 'shake_on', 'set_shake'),
}
#: the picker, which is not a toggle
CONTROLLER_ROW = 6


class SettingsController(BlindScreen):
    """Back, the four toggles, then the controller picker."""

    ROWS = (1, 2, 3, 4, 5, CONTROLLER_ROW)
    ROW_SOUND = {1: SOUND_BACK}
    TITLE_TEXT = 'Settings.'

    def __init__(self, speech=None):
        BlindScreen.__init__(self, speech=speech)
        self.selectMenu = 1
        self.message = ''                   # for anyone who can see the window

    # ---- what the attached pad can do -------------------------------------------------
    def _names(self):
        """The pads attached, each name once.  None attached is an empty list."""
        pads = self.app.controllers
        return list(getattr(pads, 'names', []) or []) if pads is not None else []

    def why_not(self, row):
        """Why a row cannot be used, or None when it can be.

        A row needing a pad with nothing attached, and the shake on a pad with no motion
        sensor, are the two cases.  The picker is a third: one pad is nothing to choose
        between.
        """
        names = self._names()
        if row in (4, 5, CONTROLLER_ROW) and not names:
            return 'No controller is attached.'
        if row == 5 and not self.app.can_shake():
            return 'This controller cannot sense a shake.'
        if row == CONTROLLER_ROW and len(names) < 2:
            return 'This is the only controller attached.'
        return None

    def supported(self, row):
        """Whether the row can be changed at all.  The picker with one pad is *supported*
        but has nothing to change, so it still reads its name; only a row that cannot work
        at all reads "not supported"."""
        if row == CONTROLLER_ROW:
            return bool(self._names())
        return row not in (4, 5) or self.why_not(row) is None

    # ---- the rows ---------------------------------------------------------------------
    def row_text(self, row):
        if row == 1:
            return BACK_TEXT
        if row == CONTROLLER_ROW:
            name = self.app.controllers.active_name if self.app.controllers else None
            return 'Controller, %s.' % (name or 'none attached')
        label, reads, _writes = TOGGLES[row]
        if not self.supported(row):
            return '%s, not supported.' % label
        return '%s, currently %s.' % (label, 'on' if getattr(self.app, reads) else 'off')

    def activate(self):
        self.StopElseSpeak()
        row = self.selectMenu
        if row == 1:
            self.goBackAction_()
        elif row == CONTROLLER_ROW:
            self.nextControllerAction_()
        elif row in TOGGLES:
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
            if row == 4:
                self.app.vibrate_effect('confirm')
            elif row == 3:
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
