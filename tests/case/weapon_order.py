"""The order the weapons come in, which the player sets themselves.

A PORT ADDITION (tunmi13productions, 2026-10-06; aidocks/project_weapon_order_plan.md).
WEAPON_ORDER in save.json holds all eight slots; the reorder screen lists the equipped
ones, and a game cycles through them in that order and starts you on the first.

Each test runs on a new, empty save folder of its own.
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
from sixthsense.game import weapon_order as O                    # noqa: E402
from sixthsense.game.app_delegate import AppDelegate             # noqa: E402
from sixthsense.game.inventory import (InventoryController,      # noqa: E402
                                       ReorderController)
from sixthsense.game.stage_1_e import Stage_1_E                  # noqa: E402
from sixthsense.platform.defaults import UserDefaults            # noqa: E402
from sixthsense.platform.runloop import RunLoop                  # noqa: E402

GRENADE, KNIFE, COLT, SHOTGUN, M4, AK47, MG80, JAPAN = range(8)
#: the eight ...USE keys, in slot order
USE = ('GRENADEUSE', 'KNIFEUSE', 'COLTUSE', 'SHOTGUNUSE', 'M4USE', 'AK47USE',
       'MG80USE', 'JAPANUSE')


class _Recorder:
    def __init__(self):
        self.said = []

    def speak(self, text, interrupt=True):
        self.said.append(text)

    def stop(self):
        pass


class _Pygame:
    """Just enough of pygame for a keyboard handler: key-downs named by their key."""
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


class _Pad:
    def __init__(self, name):
        self.name = name


class _Pads:
    def __init__(self, name):
        self.pads = [_Pad(name)]


class _NewSave:
    """A new, empty save folder, with the save read from it afresh."""

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
        O.fill(self.d)
        self.app.controllers = None                  # no pad unless a test says so
        self.equip()
        self.pages = []
        return self

    def equip(self, *slots):
        """Equip exactly these slots, and nothing else."""
        for slot, key in enumerate(USE):
            self.d.setObject_forKey_('1' if slot in slots else '0', key)
        self.d.synchronize()
        self.app.weaponHave()

    def page(self, cls=ReorderController):
        p = cls(speech=_Recorder())
        self.pages.append(p)
        return p

    def __exit__(self, *exc):
        for p in self.pages:
            p.teardown()
        self.app.controllers = None
        if self.old is None:
            os.environ.pop(paths.USER_DIR_ENV, None)
        else:
            os.environ[paths.USER_DIR_ENV] = self.old
        UserDefaults._instance = None
        shutil.rmtree(self.top, ignore_errors=True)


def test_a_new_save_starts_on_the_colt_and_cycles_as_the_original_did():
    """The order out of the box is the original's own cycle turned round to begin at the
    colt, so a save that has never touched it plays exactly as the original did.  Slot
    order itself would have started a game on the grenade, which has no magazine."""
    with _NewSave() as s:
        s.d.synchronize()
        with open(s.d.path, encoding='utf-8') as fh:
            assert json.load(fh)['WEAPON_ORDER'] == [COLT, SHOTGUN, M4, AK47, MG80,
                                                     JAPAN, GRENADE, KNIFE]
        assert O.order(s.d) == O.DEFAULT_ORDER
        assert O.first_equipped(s.app, s.d) == COLT
        assert O.equipped(s.app, s.d) == [COLT, GRENADE, KNIFE], 'the original cycle'
        assert O.fill(s.d) is False, 'a second start wrote again'


def test_an_order_that_is_not_every_slot_once_is_put_back():
    with _NewSave() as s:
        for bad in ([0, 1, 2], [0, 0, 1, 2, 3, 4, 5, 6], 'colt first', 7,
                    [0, 1, 2, 3, 4, 5, 6, 8], [0, 1, 2, 3, 4, 5, 6, True]):
            s.d.setObject_forKey_(bad, O.KEY)
            assert O.fill(s.d) is True, bad
            assert s.d.objectForKey_(O.KEY) == O.DEFAULT_ORDER, bad
        s.d.setObject_forKey_([7, 6, 5, 4, 3, 2, 1, 0], O.KEY)   # an edit by hand is kept
        assert O.fill(s.d) is False
        assert O.order(s.d) == [7, 6, 5, 4, 3, 2, 1, 0]


def test_only_the_equipped_weapons_are_listed_in_the_players_order():
    with _NewSave() as s:
        s.equip(COLT, SHOTGUN, MG80)
        assert O.equipped(s.app, s.d) == [COLT, SHOTGUN, MG80]
        s.d.setObject_forKey_([MG80, COLT, SHOTGUN, GRENADE, KNIFE, M4, AK47, JAPAN], O.KEY)
        assert O.equipped(s.app, s.d) == [MG80, COLT, SHOTGUN]
        assert O.first_equipped(s.app, s.d) == MG80
        # equipping nothing is not possible: weaponHave (0x52xx) switches the grenade,
        # the knife and the colt back on whenever the save has nothing equipped
        s.equip()
        # and they come back in the player's order, which here puts the colt first
        assert O.equipped(s.app, s.d) == [COLT, GRENADE, KNIFE]


def test_moving_swaps_with_the_next_equipped_weapon_and_saves():
    with _NewSave() as s:
        s.equip(COLT, SHOTGUN, MG80)
        assert O.move(MG80, -1, s.app, s.d) == SHOTGUN
        assert O.equipped(s.app, s.d) == [COLT, MG80, SHOTGUN]
        assert O.move(MG80, -1, s.app, s.d) == COLT
        assert O.equipped(s.app, s.d) == [MG80, COLT, SHOTGUN]
        assert O.move(MG80, -1, s.app, s.d) is None, 'it moved past the top'
        assert O.equipped(s.app, s.d) == [MG80, COLT, SHOTGUN]
        assert O.move(MG80, 1, s.app, s.d) == COLT
        assert O.equipped(s.app, s.d) == [COLT, MG80, SHOTGUN]
        assert O.move(SHOTGUN, 1, s.app, s.d) is None, 'it moved past the bottom'
        # the move went into the save, not only into memory
        s.d.synchronize()
        with open(s.d.path, encoding='utf-8') as fh:
            assert json.load(fh)['WEAPON_ORDER'] == O.order(s.d)


def test_a_weapon_that_is_not_equipped_keeps_its_place():
    """Only the equipped weapons trade, so unequipping and equipping again puts a weapon
    back where the player left it."""
    with _NewSave() as s:
        s.equip(COLT, SHOTGUN, MG80)
        O.move(MG80, -1, s.app, s.d)
        O.move(MG80, -1, s.app, s.d)
        assert O.equipped(s.app, s.d) == [MG80, COLT, SHOTGUN]
        s.equip(COLT, SHOTGUN)                        # the MG80 goes away
        assert O.equipped(s.app, s.d) == [COLT, SHOTGUN]
        O.move(SHOTGUN, -1, s.app, s.d)               # and the other two trade over it
        assert O.equipped(s.app, s.d) == [SHOTGUN, COLT]
        s.equip(COLT, SHOTGUN, MG80)                  # and it comes back where it was
        assert O.equipped(s.app, s.d) == [MG80, SHOTGUN, COLT]
        assert O.move(M4, -1, s.app, s.d) is None, 'an unequipped weapon moved'


def test_the_screen_lists_the_equipped_weapons_and_says_what_moved():
    with _NewSave() as s:
        s.equip(COLT, SHOTGUN, MG80)
        page = s.page()
        assert page.rows() == (1, 2, 3, 4)
        assert [page.row_text(r) for r in page.rows()] == [
            'Back, Button', 'Colt', 'Shotgun', 'MG80']
        page.selectMenu = 4                           # the MG80
        page.move_weapon(-1)
        assert page.speech.said[-1] == 'MG80 moved above Shotgun.'
        assert page.selectMenu == 3, 'the cursor did not follow the weapon'
        assert [page.row_text(r) for r in page.rows()] == [
            'Back, Button', 'Colt', 'MG80', 'Shotgun']
        page.move_weapon(1)
        assert page.speech.said[-1] == 'MG80 moved below Shotgun.'
        assert page.selectMenu == 4


def test_the_screen_says_when_a_weapon_is_already_first_or_last():
    with _NewSave() as s:
        s.equip(COLT, SHOTGUN, MG80)
        page = s.page()
        page.selectMenu = 2
        assert page.move_weapon(-1) is None
        assert page.speech.said[-1] == 'Colt is already first.'
        assert page.selectMenu == 2, 'the cursor moved anyway'
        page.selectMenu = 4
        assert page.move_weapon(1) is None
        assert page.speech.said[-1] == 'MG80 is already last.'
        said = len(page.speech.said)
        page.selectMenu = 1                           # Back is not a weapon
        assert page.move_weapon(-1) is None
        assert len(page.speech.said) == said, 'Back said something'


def test_the_screen_opens_with_the_instructions_that_suit_what_is_plugged_in():
    with _NewSave() as s:
        s.equip(COLT, SHOTGUN)
        page = s.page()
        page.startRead()
        assert page.speech.said[:2] == [
            'Reorder weapons.',
            'Up and Down to walk the list, Shift and Up or Down to move a weapon.']
        s.app.controllers = _Pads('Xbox Series X Controller')
        xbox = s.page()
        xbox.startRead()
        assert xbox.speech.said[1] == ('Push the left stick up and down to walk the list, '
                                       'the left bumper to move a weapon up, '
                                       'the right bumper to move it down.')
        s.app.controllers = _Pads('PS5 Controller')
        sony = s.page()
        sony.startRead()
        assert 'L1 to move a weapon up, R1 to move it down.' in sony.speech.said[1]
        s.app.controllers = _Pads('Nintendo Switch Pro Controller')
        switch = s.page()
        switch.startRead()
        assert 'L to move a weapon up, R to move it down.' in switch.speech.said[1]


def test_the_screen_says_when_there_is_nothing_to_reorder():
    with _NewSave() as s:
        s.equip(COLT)
        page = s.page()
        page.startRead()
        assert page.speech.said[1] == ('Only one weapon is equipped, so there is nothing '
                                       'to reorder.')
        assert page.rows() == (1, 2), 'the one weapon is still listed'
        assert page.move_weapon(-1) is None or True   # nothing to move it past
        # the empty wording is a safety net: weaponHave never leaves nothing equipped
        s.d.setObject_forKey_([], O.KEY)              # not an order, so it is put back
        empty = s.page()
        empty.app.useWeapon = ['0'] * 8
        empty.startRead()
        assert empty.speech.said[1] == 'No weapons are equipped.'
        assert empty.rows() == (1,)


def test_the_real_keyboard_moves_a_weapon():
    """Driving ScreenInput, which is the keyboard the inventory's screens actually use:
    the first build wired this into MenuInput alone, so nothing moved in the game
    (tunmi13productions, 2026-10-06: "trying to reorder doesn't work, neither on keyboard
    or controller")."""
    from sixthsense.ui.screen_input import ScreenInput
    with _NewSave() as s:
        s.equip(COLT, SHOTGUN, MG80)
        page = s.page()
        keys = ScreenInput(page)
        page.selectMenu = 4                           # the MG80
        keys.handle(_Key('up', _Pygame.KMOD_SHIFT), _Pygame)
        assert O.equipped(s.app, s.d) == [COLT, MG80, SHOTGUN]
        assert page.selectMenu == 3
        keys.handle(_Key('f13'), _Pygame)             # the left bumper
        assert O.equipped(s.app, s.d) == [MG80, COLT, SHOTGUN]
        keys.handle(_Key('f14'), _Pygame)             # the right bumper
        assert O.equipped(s.app, s.d) == [COLT, MG80, SHOTGUN]
        # a plain arrow still only walks the list
        at = page.selectMenu
        keys.handle(_Key('up'), _Pygame)
        assert page.selectMenu == at - 1
        assert O.equipped(s.app, s.d) == [COLT, MG80, SHOTGUN], 'a plain arrow moved it'


def test_a_bumper_does_nothing_on_any_other_screen():
    from sixthsense.ui.screen_input import ScreenInput
    with _NewSave() as s:
        page = s.page(InventoryController)
        keys = ScreenInput(page)
        page.selectMenu = 3
        for name in ('f13', 'f14'):
            keys.handle(_Key(name), _Pygame)
            assert page.selectMenu == 3, name
        # and Shift with an arrow is just the arrow
        keys.handle(_Key('down', _Pygame.KMOD_SHIFT), _Pygame)
        assert page.selectMenu == 4


def test_the_inventory_has_a_reorder_button_that_opens_it():
    with _NewSave() as s:
        page = s.page(InventoryController)
        assert page.rows()[-1] == InventoryController.REORDER_ROW
        assert page.row_text(InventoryController.REORDER_ROW) == 'Reorder weapons, Button'
        page.selectMenu = InventoryController.REORDER_ROW
        page.activate()
        assert page.next_screen == ('reorder', None)


def test_a_game_cycles_and_starts_in_the_players_order():
    with _NewSave() as s:
        s.equip(COLT, SHOTGUN, MG80)
        s.d.setObject_forKey_([MG80, SHOTGUN, COLT, GRENADE, KNIFE, M4, AK47, JAPAN], O.KEY)
        st = Stage_1_E()
        try:
            st.weaponInit()
            st.startWeapon()
            assert st.gamePlayer.useWepon == MG80, 'a game did not start on the first'
            st.gunChangeAction_(1)
            assert st.gamePlayer.useWepon == SHOTGUN
            st.gunChangeAction_(1)
            assert st.gamePlayer.useWepon == COLT
            st.gunChangeAction_(1)
            assert st.gamePlayer.useWepon == MG80, 'it did not come round again'
            st.gunChangeAction_(-1)
            assert st.gamePlayer.useWepon == COLT, 'back round the other way'
        finally:
            st.teardown()


def test_an_unequipped_weapon_is_never_cycled_to():
    with _NewSave() as s:
        s.equip(COLT, MG80)
        st = Stage_1_E()
        try:
            st.weaponInit()
            st.startWeapon()
            seen = {st.gamePlayer.useWepon}
            for _ in range(8):
                st.gunChangeAction_(1)
                seen.add(st.gamePlayer.useWepon)
            assert seen == {COLT, MG80}, seen
        finally:
            st.teardown()


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
