"""Weapon upgrades: one level per weapon, adding to its stats, every number in save.json.

A PORT ADDITION (tsatria03, 2026-10-05; aidocks/completed/weapon_upgrades_plan.md).  The
totals and prices are checked against the tables the dev agreed: damage and ammo from 10,
range from 100 cm, growing 1.2 times a level; prices from 100, growing 1.2 times.

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
from sixthsense.game import weapon_upgrades as U                 # noqa: E402
from sixthsense.game.app_delegate import AppDelegate             # noqa: E402
from sixthsense.game.inventory import DetailInventoryController  # noqa: E402
from sixthsense.game.stage_1_e import Stage_1_E                  # noqa: E402
from sixthsense.game.store import (LEVEL_ROW, UPGRADE_ROW,       # noqa: E402
                                   DetailStoreController)
from sixthsense.platform.defaults import UserDefaults            # noqa: E402
from sixthsense.platform.runloop import RunLoop                  # noqa: E402

#: the agreed tables, levels 1 to 10
TOTALS = [10, 22, 36, 54, 74, 99, 129, 165, 208, 260]
RANGE_TOTALS = [100, 220, 364, 537, 744, 993, 1292, 1650, 2080, 2596]
PRICES = [100, 120, 144, 173, 207, 249, 299, 358, 430, 516]


class _Recorder:
    def __init__(self):
        self.said = []

    def speak(self, text, interrupt=True):
        self.said.append(text)

    def stop(self):
        pass


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
        U.fill(self.d)
        self.app.weaponHave()
        self.app.haveGold = 0
        self.pages = []
        return self

    def page(self, cls, weapon_type):
        p = cls(weapon_type, speech=_Recorder())
        self.pages.append(p)
        return p

    def __exit__(self, *exc):
        for p in self.pages:
            p.teardown()
        if self.old is None:
            os.environ.pop(paths.USER_DIR_ENV, None)
        else:
            os.environ[paths.USER_DIR_ENV] = self.old
        UserDefaults._instance = None
        shutil.rmtree(self.top, ignore_errors=True)


def test_the_tables_are_the_agreed_ones():
    assert [U.total(10, 1.2, n) for n in range(1, 11)] == TOTALS
    assert [U.total(100, 1.2, n) for n in range(1, 11)] == RANGE_TOTALS
    with _NewSave():
        assert [U.price(n) for n in range(1, 11)] == PRICES
        assert sum(PRICES) == 2596
    assert U.total(10, 1.2, 0) == 0
    assert U.total(10, 1, 4) == 40, 'a growth of 1 is an even step'


def test_a_new_save_has_every_setting_level_and_cap():
    with _NewSave() as s:
        s.d.synchronize()
        with open(s.d.path, encoding='utf-8') as fh:
            saved = json.load(fh)
        assert saved['UPGRADE_START_PRICE'] == 100 and saved['UPGRADE_PRICE_GROWTH'] == 1.2
        assert saved['UPGRADE_DAMAGE'] == 10 and saved['UPGRADE_AMMO'] == 10
        assert saved['UPGRADE_RANGE'] == 100 and saved['UPGRADE_GROWTH'] == 1.2
        for name in ('GRENADE', 'KNIFE', 'COLT', 'SHOTGUN', 'M4', 'AK47', 'MG80', 'JAPAN'):
            assert saved[name + '_LEVEL'] == 0 and saved[name + '_MAX_LEVEL'] == 10, name
        assert U.fill(s.d) is False, 'a second start wrote again'


def test_unusable_values_are_put_back_and_edits_kept():
    with _NewSave() as s:
        for k, bad in (('UPGRADE_GROWTH', 0), ('UPGRADE_PRICE_GROWTH', 'fast'),
                       ('UPGRADE_DAMAGE', -1), ('COLT_LEVEL', 1.5),
                       ('KNIFE_MAX_LEVEL', True)):
            s.d.setObject_forKey_(bad, k)
        s.d.setObject_forKey_(1.5, 'UPGRADE_GROWTH')
        s.d.setObject_forKey_(0, 'UPGRADE_GROWTH')
        assert U.fill(s.d) is True
        assert s.d.objectForKey_('UPGRADE_GROWTH') == 1.2
        assert s.d.objectForKey_('UPGRADE_PRICE_GROWTH') == 1.2
        assert s.d.objectForKey_('UPGRADE_DAMAGE') == 10
        assert s.d.objectForKey_('COLT_LEVEL') == 0
        assert s.d.objectForKey_('KNIFE_MAX_LEVEL') == 10
        s.d.setObject_forKey_(1.05, 'UPGRADE_GROWTH')          # a fraction is fine here
        s.d.setObject_forKey_(3, 'COLT_MAX_LEVEL')
        assert U.fill(s.d) is False
        assert U.setting('UPGRADE_GROWTH', s.d) == 1.05


def test_upgrading_pays_and_raises_the_level_up_to_the_cap():
    with _NewSave() as s:
        s.d.setObject_forKey_(2, 'COLT_MAX_LEVEL')
        s.app.haveGold = 250
        assert U.upgrade('COLT', s.app) == 1
        assert s.app.haveGold == 150 and s.d.intForKey_('GOLD') == 150
        assert s.d.objectForKey_('COLT_LEVEL') == 1
        assert U.upgrade('COLT', s.app) == 2                  # 120 more
        assert s.app.haveGold == 30
        assert U.upgrade('COLT', s.app) == 'max'
        assert s.app.haveGold == 30, 'the cap took gold'
        s.d.setObject_forKey_(10, 'COLT_MAX_LEVEL')
        assert U.upgrade('COLT', s.app) == 'gold'             # 144 for level 3
        assert s.app.haveGold == 30 and s.d.objectForKey_('COLT_LEVEL') == 2


def test_the_level_adds_to_what_the_stage_plays_with():
    with _NewSave() as s:
        s.d.setObject_forKey_(2, 'COLT_LEVEL')
        s.d.setObject_forKey_(3, 'KNIFE_LEVEL')
        s.d.setObject_forKey_(1, 'GRENADE_LEVEL')
        st = Stage_1_E()
        try:
            st.weaponInit()
            colt, knife, grenade = st.weaponSource[2], st.weaponSource[1], st.weaponSource[0]
            assert (colt.Damage, colt.Range, colt.ReloadGun()) == (30 + 22, 1000 + 220, 7 + 22)
            assert (knife.Damage, knife.Range) == (30 + 36, 200 + 364)
            assert knife.AmmoCapacity is None, 'a blade gained a magazine'
            assert (grenade.Damage, grenade.Range) == (160, 1700)
            shotgun = st.weaponSource[3]
            assert (shotgun.Damage, shotgun.Range) == (35, 1000), 'level 0 added something'
        finally:
            st.teardown()


def test_the_shop_page_swaps_buy_for_upgrade_once_owned():
    with _NewSave() as s:
        shotgun = s.page(DetailStoreController, 1)
        assert 7 in shotgun.rows() and UPGRADE_ROW not in shotgun.rows()
        assert shotgun.row_text(LEVEL_ROW) == 'Level, 0 of 10'
        s.app.haveGold = 7000
        shotgun.selectMenu = 7
        shotgun.activate()
        assert 7 not in shotgun.rows() and UPGRADE_ROW in shotgun.rows()
        assert shotgun.selectMenu == UPGRADE_ROW, 'the cursor stayed on the gone Buy'
        assert shotgun.rows().index(UPGRADE_ROW) < shotgun.rows().index(8), 'Try came first'
        grenade = s.page(DetailStoreController, 0)
        rows = grenade.rows()
        assert 7 in rows and UPGRADE_ROW in rows, 'the grenade lost Buy or Upgrade'


def test_the_inventory_page_upgrades_owned_weapons_only():
    with _NewSave() as s:
        knife = s.page(DetailInventoryController, 1)
        colt = s.page(DetailInventoryController, 2)
        m4 = s.page(DetailInventoryController, 4)
        assert UPGRADE_ROW in knife.rows() and UPGRADE_ROW in colt.rows()
        assert UPGRADE_ROW not in m4.rows(), 'an unbought weapon can be upgraded'
        assert colt.rows()[-1] == UPGRADE_ROW, 'Upgrade is not after Equip'


def test_the_button_says_what_it_does_and_the_page_reads_the_new_numbers():
    with _NewSave() as s:
        colt = s.page(DetailInventoryController, 2)
        assert colt.row_text(UPGRADE_ROW) == 'Upgrade stats to level 1 for 100 gold, Button'
        colt.selectMenu = UPGRADE_ROW
        colt.activate()
        assert colt.speech.said[-1] == 'Gold is lacking.', colt.speech.said
        s.app.haveGold = 1000
        colt.activate()
        assert colt.speech.said[-1] == 'Upgraded to level 1.', colt.speech.said
        assert colt.row_text(3) == 'Ammo capacity, 17'
        assert colt.row_text(4) == 'Effective range, 11 metres'
        assert colt.row_text(5) == 'Damage, 40'
        assert colt.row_text(LEVEL_ROW) == 'Level, 1 of 10'
        assert colt.row_text(UPGRADE_ROW) == 'Upgrade stats to level 2 for 120 gold, Button'
        s.d.setObject_forKey_(1, 'COLT_MAX_LEVEL')
        assert colt.row_text(UPGRADE_ROW) == 'Fully upgraded, Button'
        colt.activate()
        assert colt.speech.said[-1] == 'Fully upgraded.'
        knife = s.page(DetailInventoryController, 1)
        assert knife.row_text(3) == 'Ammo capacity, none', 'a blade gained a magazine'


def test_a_bought_weapons_shop_and_inventory_pages_agree():
    with _NewSave() as s:
        s.d.setObject_forKey_('1', 'AK47')
        s.app.weaponHave()
        s.d.setObject_forKey_(4, 'AK47_LEVEL')
        shop, inv = s.page(DetailStoreController, 3), s.page(DetailInventoryController, 5)
        for row in (3, 4, 5, LEVEL_ROW, UPGRADE_ROW):
            assert shop.row_text(row) == inv.row_text(row), row
        assert shop.row_text(5) == 'Damage, %d' % (40 + 54)


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
