"""Each weapon's stats in save.json: the real ones, read back by the pages and the stage.

A PORT ADDITION (tsatria03, 2026-09-25; made real 2026-10-05,
aidocks/completed/real_weapon_stats_plan.md).  All eight weapons have their ammo capacity,
range in centimetres, damage and price in the save from the start, except where nothing
could use one; a missing or unusable value is put back to the real one; an older save's
shop numbers are replaced once; and a hand edit changes what the pages say and what the
stage plays with.

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
from sixthsense.game import weapon_stats                         # noqa: E402
from sixthsense.game.app_delegate import AppDelegate             # noqa: E402
from sixthsense.game.inventory import DetailInventoryController  # noqa: E402
from sixthsense.game.stage_1_e import Stage_1_E                  # noqa: E402
from sixthsense.game.store import DetailStoreController          # noqa: E402
from sixthsense.game.weapon_control import WEAPON_FILES, WeaponControl  # noqa: E402
from sixthsense.platform.defaults import UserDefaults            # noqa: E402
from sixthsense.platform.runloop import RunLoop                  # noqa: E402

#: as ammo capacity, range in cm, damage and price; None where there is no key
EXPECTED = {
    'GRENADE': (None, 1600, 150, 1000),
    'KNIFE': (None, 200, 30, None),
    'COLT': (7, 1000, 30, None),
    'SHOTGUN': (10, 1000, 35, 7000),
    'M4': (25, 1300, 40, 13000),
    'AK47': (30, 1300, 40, 15000),
    'MG80': (50, 1600, 45, 45000),
    'JAPAN': (None, 300, 100, 50000),
}

#: what 2026-09-25's version wrote: the shop's numbers, and keys that are gone now
OLD_SHOP = {
    'SHOTGUN': (10, 50, 45, 7000),
    'KNIFE': (0, 2, 30, 0),
    'COLT': (7, 50, 30, 0),
}


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
        return self

    def __exit__(self, *exc):
        if self.old is None:
            os.environ.pop(paths.USER_DIR_ENV, None)
        else:
            os.environ[paths.USER_DIR_ENV] = self.old
        UserDefaults._instance = None
        shutil.rmtree(self.top, ignore_errors=True)

    def stats(self, name):
        return tuple(self.d.objectForKey_(weapon_stats.key(name, s))
                     for s in weapon_stats.STATS)

    def restart(self):
        """The game closed and started again: the save read afresh from its files."""
        self.d.synchronize()
        UserDefaults._instance = None
        self.d = UserDefaults.standardUserDefaults()
        self.app.weaponHave()


def test_the_real_numbers_match_the_weapon_files():
    """Damage, range and magazine are the plists' (indices 3, 5 and 7)."""
    assert weapon_stats.REAL == EXPECTED
    for slot, name in enumerate(weapon_stats.NAMES):
        w = WeaponControl()
        w.loadWeaponForGun_fileType_(WEAPON_FILES[slot])
        ammo, rng, damage, _price = EXPECTED[name]
        assert (w.Range, w.Damage) == (rng, damage), name
        if ammo is not None:
            assert w.BulletCount == ammo, name


def test_a_new_save_has_every_weapons_stats_and_no_others():
    with _NewSave() as s:
        s.app.weaponHave()                     # as every start does
        for name in weapon_stats.NAMES:
            assert s.stats(name) == EXPECTED[name], (name, s.stats(name))
        for key in ('GRENADE_AMMO_CAPACITY', 'KNIFE_AMMO_CAPACITY', 'JAPAN_AMMO_CAPACITY',
                    'KNIFE_PRICE', 'COLT_PRICE'):
            assert s.d.objectForKey_(key) is None, key
        with open(s.d.path, encoding='utf-8') as fh:
            saved = json.load(fh)
        assert saved['MG80_RANGE'] == 1600 and saved['WEAPON_STATS_REAL'] == 1, saved


def test_the_grenade_count_is_always_in_the_save():
    """GRENADECOUNT was written only on buying or throwing a grenade; a save without one
    now gets '0' on the start, and a count already there is kept."""
    with _NewSave() as s:
        s.app.weaponHave()
        assert s.d.objectForKey_('GRENADECOUNT') == '0'
        s.d.setObject_forKey_('4', 'GRENADECOUNT')
        s.restart()
        assert s.d.objectForKey_('GRENADECOUNT') == '4', 'the count was written over'
        with open(s.d.path, encoding='utf-8') as fh:
            assert json.load(fh)['GRENADECOUNT'] == '4'


def test_an_older_saves_shop_numbers_are_replaced_once():
    with _NewSave() as s:
        for name, numbers in OLD_SHOP.items():
            for stat, v in zip(weapon_stats.OLD_STATS, numbers):
                s.d.setObject_forKey_(v, name + stat)     # SHOTGUNRANGE, as then
        s.d.synchronize()
        s.app.weaponHave()                     # the first start of this version
        for name in OLD_SHOP:
            assert s.stats(name) == EXPECTED[name], (name, s.stats(name))
            for stat in weapon_stats.OLD_STATS:
                assert s.d.objectForKey_(name + stat) is None, name + stat
        assert s.d.objectForKey_('KNIFE_AMMO_CAPACITY') is None
        assert s.d.objectForKey_('COLT_PRICE') is None
        # the player then sets the shotgun back to 45 by hand: the next start keeps it
        s.d.setObject_forKey_(45, 'SHOTGUN_DAMAGE')
        s.restart()
        assert s.d.objectForKey_('SHOTGUN_DAMAGE') == 45, 'the edit was undone'


def test_the_earlier_key_names_are_renamed_with_their_values():
    """Saves from the first builds of the real stats, under MG80RANGE and WEAPONSTATSREAL
    or mg80_range and weapon_stats_real, keep every value, edits included, under
    MG80_RANGE and WEAPON_STATS_REAL, and are not replaced again."""
    for marker, edit, rng, ammo in (
            ('WEAPONSTATSREAL', 'SHOTGUNDAMAGE', 'MG80RANGE', 'COLTAMMOCAPACITY'),
            ('weapon_stats_real', 'shotgun_damage', 'mg80_range', 'colt_ammo_capacity')):
        with _NewSave() as s:
            s.d.setObject_forKey_(1, marker)
            s.d.setObject_forKey_(60, edit)               # the player's edit
            s.d.setObject_forKey_(1600, rng)
            s.d.setObject_forKey_(3, ammo)
            s.restart()
            assert s.d.objectForKey_('SHOTGUN_DAMAGE') == 60, ('the edit was lost', edit)
            assert s.d.objectForKey_('MG80_RANGE') == 1600
            assert s.d.objectForKey_('COLT_AMMO_CAPACITY') == 3
            assert s.d.objectForKey_('WEAPON_STATS_REAL') == 1
            for old in (marker, edit, rng, ammo):
                assert s.d.objectForKey_(old) is None, old
            with open(s.d.path, encoding='utf-8') as fh:
                saved = json.load(fh)
            stats_keys = [k for k in saved if k.endswith(('RANGE', 'DAMAGE', 'PRICE',
                                                          'CAPACITY', 'REAL'))]
            assert all('_' in k and k == k.upper() for k in stats_keys), stats_keys
            assert not [k for k in saved if k != k.upper()], saved


def test_a_missing_or_unusable_value_is_put_back():
    with _NewSave() as s:
        s.app.weaponHave()
        s.d.removeObjectForKey_('M4_RANGE')
        for key, bad in (('SHOTGUN_DAMAGE', 'lots'), ('AK47_PRICE', -5),
                         ('MG80_AMMO_CAPACITY', 12.5), ('COLT_RANGE', True),
                         ('JAPAN_DAMAGE', None)):
            s.d.setObject_forKey_(bad, key)
        s.d.setObject_forKey_(60.0, 'M4_DAMAGE')    # a whole number written as 60.0
        s.d.setObject_forKey_(0, 'GRENADE_DAMAGE')  # 0 is allowed
        s.restart()
        assert s.d.objectForKey_('M4_RANGE') == 1300
        assert s.d.objectForKey_('SHOTGUN_DAMAGE') == 35
        assert s.d.objectForKey_('AK47_PRICE') == 15000
        assert s.d.objectForKey_('MG80_AMMO_CAPACITY') == 50
        assert s.d.objectForKey_('COLT_RANGE') == 1000
        assert s.d.objectForKey_('JAPAN_DAMAGE') == 100
        got = s.d.objectForKey_('M4_DAMAGE')
        assert got == 60 and type(got) is int, got
        assert s.d.objectForKey_('GRENADE_DAMAGE') == 0


def test_range_reads_in_metres():
    for cm, said in ((1000, '10 metres'), (1600, '16 metres'), (162, '1.62 metres'),
                     (2505, '25.05 metres'), (150, '1.5 metres'), (100, '1 metre'),
                     (5, '0.05 metres'), (0, '0 metres'), (2500, '25 metres')):
        assert weapon_stats.range_text(cm) == said, (cm, weapon_stats.range_text(cm))


def test_the_pages_read_the_save():
    with _NewSave() as s:
        s.app.weaponHave()
        for key, v in (('SHOTGUN_DAMAGE', 99), ('SHOTGUN_RANGE', 162),
                       ('SHOTGUN_AMMO_CAPACITY', 12), ('SHOTGUN_PRICE', 500)):
            s.d.setObject_forKey_(v, key)
        shop, inv = DetailStoreController(1), DetailInventoryController(3)
        try:
            for page in (shop, inv):
                assert page.row_text(3) == 'Ammo capacity, 12', page.row_text(3)
                assert page.row_text(4) == 'Effective range, 1.62 metres'
                assert page.row_text(5) == 'Damage, 99'
                assert page.row_text(6) == 'Price, 500'
        finally:
            shop.teardown()
            inv.teardown()


def test_the_blades_have_no_ammo_and_the_starting_weapons_are_free():
    with _NewSave() as s:
        s.app.weaponHave()
        pages = [DetailInventoryController(1), DetailInventoryController(7),
                 DetailStoreController(5), DetailInventoryController(2)]
        try:
            knife, sword, sword_shop, colt = pages
            for page in (knife, sword, sword_shop):
                assert page.row_text(3) == 'Ammo capacity, none', page.row_text(3)
            assert knife.row_text(6) == 'Price, free'
            assert colt.row_text(6) == 'Price, free'
            assert colt.row_text(3) == 'Ammo capacity, 7'
            assert sword_shop.row_text(6) == 'Price, 50,000'
        finally:
            for page in pages:
                page.teardown()


def test_the_shop_charges_the_saves_price():
    with _NewSave() as s:
        s.app.weaponHave()
        s.d.setObject_forKey_(100, 'SHOTGUN_PRICE')
        s.app.haveGold = 150
        page = DetailStoreController(1)
        try:
            assert page.buyAction_() is True
            assert s.app.haveGold == 50
        finally:
            page.teardown()


def test_the_stage_plays_with_the_saves_numbers():
    with _NewSave() as s:
        s.app.weaponHave()
        for key, v in (('SHOTGUN_DAMAGE', 99), ('SHOTGUN_RANGE', 400),
                       ('SHOTGUN_AMMO_CAPACITY', 3), ('GRENADE_RANGE', 500),
                       ('JAPAN_DAMAGE', 7)):
            s.d.setObject_forKey_(v, key)
        st = Stage_1_E()
        try:
            st.weaponInit()
            shotgun, grenade, sword = st.weaponSource[3], st.weaponSource[0], st.weaponSource[7]
            assert (shotgun.Damage, shotgun.Range, shotgun.BulletCount) == (99, 400, 3)
            shotgun.BulletCount = 0
            assert shotgun.ReloadGun() == 3, 'a reload does not fill to the save'
            assert grenade.Range == 500
            assert sword.Damage == 7
            colt = st.weaponSource[2]
            assert (colt.Damage, colt.Range, colt.ReloadGun()) == (30, 1000, 7)
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
