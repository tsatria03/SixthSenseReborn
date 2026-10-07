"""The shop and the inventory: rows, prices, buying and equipping.

Checked against ``-[mainStoreController ...]`` (0x1c8c8), ``-[StoreController ...]``
(0x12f88), ``-[DetailStoreController ...]`` (0x18b20), ``-[InventoryController ...]``
(0x2415c) and ``-[DetailInventoryController ...]`` (0x274a0).
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import _scratch_save                                             # noqa: E402,F401  never the real save

from sixthsense.game.app_delegate import AppDelegate              # noqa: E402
from sixthsense.game.blind_screen import MESSAGE_TEXT             # noqa: E402
from sixthsense.game.inventory import (SLOTS, DetailInventoryController,  # noqa: E402
                                       InventoryController)
from sixthsense.game.store import (SHOP, DetailStoreController,   # noqa: E402
                                   MainStoreController, StoreController)
from sixthsense.platform.defaults import UserDefaults             # noqa: E402
from sixthsense.platform.runloop import RunLoop                   # noqa: E402

OWNED = ('SHOTGUN', 'M4', 'AK47', 'MG80', 'JAPAN')
EQUIPPED = ('GRENADEUSE', 'KNIFEUSE', 'COLTUSE', 'SHOTGUNUSE',
            'M4USE', 'AK47USE', 'MG80USE', 'JAPANUSE')


class _Recorder:
    def __init__(self):
        self.said = []
        self.stopped = 0

    def speak(self, text, interrupt=True):
        self.said.append(text)
        return True

    def stop(self):
        self.stopped += 1


def _app(gold=0, grenades=0):
    d = UserDefaults.standardUserDefaults()
    for key in OWNED:
        d.removeObjectForKey_(key)
    for key in EQUIPPED:
        d.removeObjectForKey_(key)
    d.setObject_forKey_('%d' % gold, 'GOLD')
    d.setObject_forKey_('%d' % grenades, 'GRENADECOUNT')
    d.synchronize()
    app = AppDelegate.shared()
    if app.playback is None:
        app.didFinishLaunching()
    app.haveGold = gold
    app.weaponHave()
    RunLoop.main().reset()
    return app


def test_the_gold_shop_row_is_unreachable():
    """selectMenu is never set to 3 anywhere in mainStoreController, so sound 236
    Gold shop Button is never played - even though glodShopAction: and its tbb case
    both exist."""
    _app()
    m = MainStoreController()
    try:
        assert m.GOLD_SHOP_ROW not in m.rows()
        assert hasattr(m, 'glodShopAction_'), 'the action itself should still be here'
    finally:
        m.teardown()


def test_the_shop_menu_pushes_the_two_screens_that_work():
    _app()
    m = MainStoreController(speech=_Recorder())
    try:
        m.select(2)
        m.activate()
        assert m.next_screen == ('store_weapons', None)
        m.next_screen = None
        m.select(4)
        m.activate()
        assert m.next_screen == ('inventory', None)
    finally:
        m.teardown()


def test_moving_away_from_a_spoken_row_stops_its_speech():
    """StopElseSpeak must cut the sentence off, or it talks over whatever row the
    player moves to next.  The gold row says the gold."""
    app = _app(gold=1250)
    s = StoreController(speech=_Recorder())
    try:
        s.select(2)
        assert s.speech.said and '1,250' in s.speech.said[-1]
        before = s.speech.stopped
        s.select(1)                          # move to another row
        assert s.speech.stopped > before, 'moving away did not stop the speech'
    finally:
        s.teardown()


def test_there_are_no_in_app_purchase_rows_in_the_shop():
    """The coin store (row 5) and restore purchases (row 6) were Apple in-app
    purchases, which no longer exist, so the shop leaves them out, and moving never
    lands on them.  The shop is back, the weapon shop and the inventory."""
    _app()
    m = MainStoreController(speech=_Recorder())
    try:
        assert m.rows() == (1, 2, 4)
        for _ in range(10):
            assert m.move(1) in (1, 2, 4)
        assert not hasattr(m, 'coinShopAction_')
    finally:
        m.teardown()


def test_there_is_no_purchase_all_weapons_row():
    """Row 9 of the weapon list bought every weapon as one in-app purchase.  It is
    left out; each weapon is still bought on its own for gold."""
    _app()
    s = StoreController(speech=_Recorder())
    try:
        assert s.rows() == (1, 2, 3, 4, 5, 6, 7, 8)
        for _ in range(12):
            assert s.move(1) != 9
        assert not hasattr(s, 'ItemAllAction_')
    finally:
        s.teardown()


def test_the_weapon_list_opens_each_weapons_page():
    """0x15a90 and its copies: Item1..Item6Action pass 1, 2, 3, 4, 5 and 0."""
    _app()
    s = StoreController(speech=_Recorder())
    try:
        assert s.ROW_WEAPON == {3: 1, 4: 2, 5: 3, 6: 4, 7: 5, 8: 0}
        s.select(3)
        s.activate()
        assert s.next_screen == ('store_detail', 1)
        s.next_screen = None
        s.select(8)
        s.activate()
        assert s.next_screen == ('store_detail', 0)      # the grenade
    finally:
        s.teardown()


def test_a_weapon_page_reads_its_own_numbers():
    """The shotgun's real numbers, since 2026-10-05: 10 rounds, 1000 cm, 35 damage and
    the 7000 gold buying charges (the original's page said 50 and 45, 0x19318)."""
    app = _app()
    p = DetailStoreController(1)
    try:
        assert (p.ammocapacity, p.effetiverange, p.power, p.price) == \
            (10, 1000, 35, 7000)
        assert p.row_text(4) == 'Effective range, 10 metres', p.row_text(4)
        assert p.row_text(2) == 'Shotgun, Image', p.row_text(2)
        assert p.row_text(3) == 'Ammo capacity, 10', p.row_text(3)
        assert p.row_text(6) == 'Price, 7,000', p.row_text(6)
        assert p.selectMenu == 1                        # 0x19b90
    finally:
        p.teardown()
    assert app is not None


def test_the_grenade_page_counts_instead_of_a_magazine():
    """0x19ea4 reads GRENADECOUNT, and 0x1b00c reads it as a count, not a capacity."""
    _app(grenades=4)
    p = DetailStoreController(0)
    try:
        assert p.ammocapacity == 4
        assert p.row_text(3) == 'Number of grenades, 4', p.row_text(3)
        assert p.price == 1000
    finally:
        p.teardown()


def test_buying_a_weapon_spends_the_gold_and_equips_it():
    app = _app(gold=20000)
    p = DetailStoreController(3)                        # AK47, 15000
    d = UserDefaults.standardUserDefaults()
    try:
        assert p.buyAction_() is True
        assert app.haveGold == 5000
        assert d.intForKey_('GOLD') == 5000
        assert d.intForKey_('AK47') == 1
        assert d.intForKey_('AK47USE') == 1, 'a bought weapon is equipped, 0x1be08'
        assert app.haveWeapon[5] == '1'
        assert p.message == 'Purchase has completed.'
        assert MESSAGE_TEXT[260] == p.message, 'the screen reader says the window\'s words'
        # 0x1bb58: buying it again is refused, and costs nothing
        assert p.buyAction_() is False
        assert app.haveGold == 5000
        assert p.message == 'This weapon has been purchased.'
    finally:
        p.teardown()


def test_every_press_of_buy_clicks():
    """tsatria03, 2026-10-07: Buy plays ui_select (10), as Back, Try and the upgrade button
    do, whether it buys, lacks the gold or finds the weapon already bought."""
    app = _app(gold=8000)
    played = []
    real = app.playSound_Gain_Pos_z_reprats_
    app.playSound_Gain_Pos_z_reprats_ = lambda n, *a: (played.append(n), real(n, *a))
    p = DetailStoreController(1, speech=_Recorder())    # shotgun, 7000
    try:
        for want in (True, False):                      # bought, then already bought
            del played[:]
            assert p.buyAction_() is want
            assert played[:1] == [10], played
        app.haveGold = 0
        q = DetailStoreController(2, speech=_Recorder())   # M4A1, more than nothing
        try:
            del played[:]
            assert q.buyAction_() is False
            assert played[:1] == [10], played
        finally:
            q.teardown()
    finally:
        del app.playSound_Gain_Pos_z_reprats_
        p.teardown()


def test_buying_without_the_gold_is_refused():
    app = _app(gold=100)
    p = DetailStoreController(4)                        # MG80, 45000
    try:
        assert p.buyAction_() is False
        assert app.haveGold == 100
        assert p.message == 'Gold is lacking.'
        assert UserDefaults.standardUserDefaults().intForKey_('MG80') == 0
    finally:
        p.teardown()


def test_a_thousand_gold_buys_one_grenade():
    """0x1c144, `adds r3, r0, #1`."""
    app = _app(gold=2500, grenades=2)
    p = DetailStoreController(0)
    d = UserDefaults.standardUserDefaults()
    try:
        assert p.buyAction_() is True
        assert d.intForKey_('GRENADECOUNT') == 3
        assert app.haveGold == 1500
        assert p.ammocapacity == 3, 'the page did not update its own count'
        assert p.buyAction_() is True                   # grenades stack
        assert d.intForKey_('GRENADECOUNT') == 4
    finally:
        p.teardown()


def test_the_try_button_opens_the_test_range_with_that_weapon():
    """0x1c1c0 pushes Stage_1_TEST holding the page's weapon: weaponType 1..5, the
    shotgun to the sword, are slots 3..7 (0x1c1d8..0x1c204), and the grenade is 0."""
    _app()
    for weaponType, slot in ((1, 3), (2, 4), (3, 5), (4, 6), (5, 7), (0, 0)):
        p = DetailStoreController(weaponType, speech=_Recorder())
        try:
            p.select(8)
            p.activate()
            assert p.next_screen == ('weapon_test', slot), (weaponType, p.next_screen)
        finally:
            p.teardown()


def test_the_inventory_lists_all_eight_slots():
    """0x25c72 .. 0x2687a: Item1..Item8Action pass 0 through 7."""
    _app()
    inv = InventoryController()
    try:
        assert inv.ROW_WEAPON == {2: 0, 3: 1, 4: 2, 5: 3, 6: 4, 7: 5, 8: 6, 9: 7}
        assert len(SLOTS) == 8
        inv.select(2)
        inv.activate()
        assert inv.next_screen == ('inventory_detail', 0)
    finally:
        inv.teardown()


def test_equipping_writes_the_key_the_stage_reads():
    app = _app()
    d = UserDefaults.standardUserDefaults()
    d.setObject_forKey_('1', 'MG80')                    # bought, so it may be equipped
    d.synchronize()
    app.weaponHave()
    p = DetailInventoryController(6)                    # MG80
    try:
        assert p.used == 0
        assert p.row_text(8) == 'Equip, Button'
        assert p.equipToggleAction_() == 1
        assert d.intForKey_('MG80USE') == 1
        assert app.useWeapon[6] == '1'
        assert p.row_text(8) == 'Unequip, Button'       # now it offers to unequip
        assert p.equipToggleAction_() == 0
        assert d.intForKey_('MG80USE') == 0
        assert app.useWeapon[6] == '0'
    finally:
        p.teardown()


def test_a_weapon_you_have_not_bought_cannot_be_equipped():
    """DIVERGENCE.  The original never checks: equipToggleAction: (0x2a618) reads only the
    ...USE keys, the itemN_have_flags only decide a button's rounded corners (0x2424c), and
    Stage_1_E reads useWeapon alone (0x35724, 0x35b54, 0x35be0).  Every weapon in the shop
    could therefore be carried for nothing.  Unequipping is still allowed, so an old save
    that has one switched on can be cleared."""
    app = _app()
    d = UserDefaults.standardUserDefaults()
    rec = _Recorder()
    p = DetailInventoryController(7, speech=rec)        # the sword, not bought
    try:
        assert not p.owned
        assert p.equipToggleAction_() == 0, 'an unowned weapon was equipped'
        assert d.intForKey_('JAPANUSE') == 0
        assert app.useWeapon[7] == '0'
        assert 'not bought' in p.message, p.message
        assert any('weapon shop' in s for s in rec.said), rec.said

        # switched on by an older save, it can still be switched off
        d.setObject_forKey_('1', 'JAPANUSE')
        d.synchronize()
        app.weaponHave()
        q = DetailInventoryController(7, speech=rec)
        assert q.used == 1
        assert q.equipToggleAction_() == 0, 'unequipping was refused too'
        assert d.intForKey_('JAPANUSE') == 0
        q.teardown()

        # and the knife, which nobody has to buy, still equips
        k = DetailInventoryController(1, speech=rec)
        assert k.owned
        k.teardown()
    finally:
        p.teardown()


def test_a_screen_says_which_one_it_is():
    """DIVERGENCE.  The original's startRead plays sound 13 and nothing else
    (-[mainStoreController startRead] 0x1d124 is three lines long), so four screens in a
    row opened by saying "back button".  Each one now says its own name through the
    screen reader first, then row 1 behind it."""
    _app()
    for cls, title in ((MainStoreController, 'Store.'),
                       (StoreController, 'Weapon shop.'),
                       (InventoryController, 'Inventory.')):
        rec = _Recorder()
        scr = cls(speech=rec)
        try:
            scr.startRead()
            assert rec.said[0] == title, '%s opened with %r' % (cls.__name__, rec.said)
            assert rec.said[1] == scr.row_text(scr.ROWS[0]), rec.said
        finally:
            scr.teardown()

    # a weapon's page names the weapon
    rec = _Recorder()
    p = DetailStoreController(2, speech=rec)                  # M4A1
    try:
        p.startRead()
        assert rec.said[0] == 'M4A1.', rec.said
    finally:
        p.teardown()


def test_the_inventory_and_the_shop_agree():
    """The original's two pages hard-coded different numbers for the same weapons (the
    shotgun's price 7000 and 50000, the sword's damage 100 and 80).  Since 2026-10-05
    both read the save, so every weapon's page says the same in both."""
    _app()
    for weapon_type, item in SHOP.items():
        slot = next(w for w, s in SLOTS.items() if s['use'] == item['use'])
        shop, inv = DetailStoreController(weapon_type), DetailInventoryController(slot)
        try:
            for row in (3, 4, 5, 6):
                assert shop.row_text(row) == inv.row_text(row), (item['name'], row)
        finally:
            shop.teardown()
            inv.teardown()


def test_escape_backs_out_of_every_screen():
    _app()
    for screen in (MainStoreController(), StoreController(),
                   DetailStoreController(1), InventoryController(),
                   DetailInventoryController(0)):
        try:
            assert screen.done is False
            screen.goBackAction_()
            assert screen.done is True, screen.__class__.__name__
        finally:
            screen.teardown()


def test_the_screens_speak_their_rows():
    """PORT ADDITION: each row goes to the screen reader, a button as "<name>, Button"
    and a number read whole with its label."""
    _app(gold=1250)
    try:
        m = MainStoreController(speech=_Recorder())
        m.startRead()
        assert m.speech.said == ['Store.', 'Back, Button'], m.speech.said
        m.select(2)
        assert m.speech.said[-1] == 'Weapon shop, Button'
        m.teardown()

        s = StoreController(speech=_Recorder())
        s.select(2)
        assert s.speech.said[-1] == 'Obtained gold, 1,250'
        s.select(3)
        assert s.speech.said[-1] == 'Shotgun, Button'
        s.teardown()

        p = DetailStoreController(1, speech=_Recorder())
        p.startRead()
        assert p.speech.said == ['Shotgun.', 'Back, Button'], p.speech.said
        p.select(2)
        assert p.speech.said[-1] == 'Shotgun, Image'
        p.select(6)
        assert p.speech.said[-1] == 'Price, 7,000'
        p.select(7)
        p.activate()                                    # 1,250 is not enough
        assert p.speech.said[-1] == 'Gold is lacking.'
        p.teardown()

        i = DetailInventoryController(1, speech=_Recorder())
        i.select(7)
        assert i.speech.said[-1] in ('State, equipped', 'State, not equipped')
        i.select(8)
        assert i.speech.said[-1] in ('Equip, Button', 'Unequip, Button')
        i.teardown()

        v = InventoryController(speech=_Recorder())
        v.select(2)
        assert v.speech.said[-1] == 'Grenade, Button'
        v.teardown()
    finally:
        pass


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
