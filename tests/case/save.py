"""The save files: ``UserDefaults`` never writes over a save it could not read, keeps each
kind of key in its own file under the save folder's folders, translates the names, and
moves an old layout over.

The layout is tsatria03's (2026-10-06, aidocks/completed/save_folders_plan.md):
saves/save.json, config/settings.json and keys.json, store/shop.json and inventory.json,
and weapons/<name>.json.  Every test points ``SIXTHSENSE_USER_DIR`` at a throwaway folder
of its own, so the real save is never read or written.
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
from sixthsense.platform.defaults import SETTINGS_KEYS, UserDefaults   # noqa: E402

SAVE = os.path.join('saves', 'save.json')
SETTINGS = os.path.join('config', 'settings.json')
KEYS = os.path.join('config', 'keys.json')
SHOP = os.path.join('store', 'shop.json')
INVENTORY = os.path.join('store', 'inventory.json')
WEAPONS = ('grenade', 'knife', 'colt', 'shotgun', 'm4a1', 'ak47', 'mg80', 'sword')


def weapon(name):
    return os.path.join('weapons', name + '.json')


class _Folder:
    """A fresh save folder for one test, put back afterwards."""

    def __enter__(self):
        self.old = os.environ.get(paths.USER_DIR_ENV)
        self.top = tempfile.mkdtemp()
        self.dir = os.path.join(self.top, 'SixthSense')
        os.environ[paths.USER_DIR_ENV] = self.dir
        return self

    def __exit__(self, *exc):
        if self.old is None:
            os.environ.pop(paths.USER_DIR_ENV, None)
        else:
            os.environ[paths.USER_DIR_ENV] = self.old
        shutil.rmtree(self.top, ignore_errors=True)

    def file(self, name=SAVE):
        return os.path.join(self.dir, name)

    def read(self, name=SAVE):
        with open(self.file(name), encoding='utf-8') as fh:
            return json.load(fh)

    def write(self, name, text):
        os.makedirs(os.path.dirname(self.file(name)), exist_ok=True)
        with open(self.file(name), 'w', encoding='utf-8') as fh:
            fh.write(text)


def _save(**keys):
    d = UserDefaults()
    for k, v in keys.items():
        d.setObject_forKey_(v, k)
    d.synchronize()
    return d


# ---- damage, backups and starting over ---------------------------------------------------

def test_each_save_keeps_the_one_before_as_a_backup():
    with _Folder() as f:
        _save(TOPSCORE='5', GOLD='5000')
        _save(TOPSCORE='6', GOLD='6000')
        with open(f.file(SAVE + '.bak'), encoding='utf-8') as fh:
            assert json.load(fh)['TOPSCORE'] == '5'
        with open(f.file(INVENTORY + '.bak'), encoding='utf-8') as fh:
            assert json.load(fh)['gold'] == 5000, 'the inventory kept no backup'
        assert UserDefaults().intForKey_('TOPSCORE') == 6


def test_a_damaged_save_is_kept_and_the_backup_carries_on():
    with _Folder() as f:
        _save(TOPSCORE='5', TUTORIAL='1')
        _save(TOPSCORE='6', TUTORIAL='1')
        with open(f.file(), 'w', encoding='utf-8') as fh:
            fh.write('{"TOPSCORE": "6')               # cut off mid-write
        d = UserDefaults()
        assert d.intForKey_('TOPSCORE') == 5, 'the backup was not loaded'
        assert d.intForKey_('TUTORIAL') == 1, 'the progress was lost'
        with open(f.file(SAVE + '.damaged'), encoding='utf-8') as fh:
            assert fh.read() == '{"TOPSCORE": "6', 'the damaged save was not kept as it was'
        assert f.read()['TOPSCORE'] == '5', 'the recovered save was not written back'


def test_a_damaged_inventory_carries_on_from_its_backup():
    with _Folder() as f:
        _save(GOLD='5000', SHOTGUN='1')
        _save(GOLD='6000', SHOTGUN='1')
        f.write(INVENTORY, '{"gold": 60')
        d = UserDefaults()
        assert d.intForKey_('GOLD') == 5000 and d.intForKey_('SHOTGUN') == 1
        assert os.path.exists(f.file(INVENTORY + '.damaged'))


def test_a_save_that_is_not_an_object_does_not_crash():
    with _Folder() as f:
        f.write(SAVE, '[1, 2, 3]')
        d = UserDefaults()
        assert d.intForKey_('TOPSCORE') == 0
        d.setObject_forKey_('12', 'TOPSCORE')
        d.synchronize()
        with open(f.file(SAVE + '.damaged'), encoding='utf-8') as fh:
            assert fh.read() == '[1, 2, 3]', 'the damaged save was written over'


def test_an_empty_file_is_a_new_one_not_a_damaged_one():
    """The dev made the store and weapon files empty by hand before the code read them."""
    with _Folder() as f:
        for name in (SAVE, SHOP, INVENTORY) + tuple(weapon(w) for w in WEAPONS):
            f.write(name, '')
        f.write(SETTINGS, '\n')
        d = UserDefaults()
        assert d.objectForKey_('GOLD') is None and d.objectForKey_('COLT_DAMAGE') is None
        assert not [n for n in os.listdir(f.file('store')) if n.endswith('.damaged')]
        assert not [n for n in os.listdir(f.file('weapons')) if n.endswith('.damaged')]


def test_a_byte_order_mark_from_notepad_is_read():
    with _Folder() as f:
        os.makedirs(os.path.dirname(f.file(SHOP)), exist_ok=True)
        with open(f.file(SHOP), 'w', encoding='utf-8-sig') as fh:
            fh.write('{"gold_per_kill": 20}')
        assert UserDefaults().objectForKey_('GOLD_PER_KILL') == 20


def test_a_deleted_save_starts_over():
    """Deleting the save is how a player starts their progress again, so the backup must
    not bring it back."""
    with _Folder() as f:
        _save(TOPSCORE='5')
        _save(TOPSCORE='6')
        os.remove(f.file())
        assert UserDefaults().intForKey_('TOPSCORE') == 0


# ---- the folders: each key in its own file, under its own name ------------------------

def test_each_file_holds_its_own_keys_under_its_own_names():
    """aidocks/completed/save_folders_plan.md: short names in the weapon files, lowercase in
    the store files with the weapons as lists of names, and the rest as they were."""
    with _Folder() as f:
        _save(TUTORIAL='1', TOPSCORE='3', WEAPON_STATS_REAL=1,
              MASTERVOLUME=80, VIBRATION='0',
              GOLD_PER_KILL=15, UPGRADE_PRICE_GROWTH=1.2,
              GOLD='7000', GRENADECOUNT='2', SHOTGUN='1', AK47='1',
              GRENADEUSE='1', KNIFEUSE='0', COLTUSE='1', SHOTGUNUSE='1',
              WEAPON_ORDER=[2, 3, 4, 5, 6, 7, 0, 1],
              SHOTGUN_AMMO_CAPACITY=10, SHOTGUN_RANGE=1000, SHOTGUN_DAMAGE=35,
              SHOTGUN_PRICE=7000, SHOTGUN_LEVEL=2, SHOTGUN_MAX_LEVEL=10,
              JAPAN_DAMAGE=100, M4_LEVEL=1)
        assert f.read() == {'TOPSCORE': '3', 'TUTORIAL': '1', 'WEAPON_STATS_REAL': 1}
        assert f.read(SETTINGS) == {'MASTERVOLUME': 80, 'VIBRATION': '0'}
        assert f.read(SHOP) == {'gold_per_kill': 15, 'upgrade_price_growth': 1.2}
        inventory = f.read(INVENTORY)
        assert inventory == {'gold': 7000, 'grenades': 2, 'owned': ['shotgun', 'ak47'],
                             'equipped': ['grenade', 'colt', 'shotgun'],
                             'order': ['colt', 'shotgun', 'm4a1', 'ak47', 'mg80', 'sword',
                                       'grenade', 'knife']}, inventory
        assert list(inventory) == ['gold', 'grenades', 'owned', 'equipped', 'order']
        shotgun = f.read(weapon('shotgun'))
        assert list(shotgun.items()) == [('ammo_capacity', 10), ('range', 1000), ('damage', 35),
                                         ('price', 7000), ('level', 2), ('max_level', 10)]
        assert f.read(weapon('sword')) == {'damage': 100}, 'JAPAN is the sword'
        assert f.read(weapon('m4a1')) == {'level': 1}, 'M4 is the m4a1'


def test_the_game_reads_every_key_back_as_it_always_did():
    """The files hold names; the game still gets text gold, "1" and "0" and slot numbers."""
    with _Folder():
        _save(GOLD='7000', GRENADECOUNT='2', SHOTGUN='1', COLTUSE='1', KNIFEUSE='0',
              WEAPON_ORDER=[2, 3, 4, 5, 6, 7, 0, 1], SHOTGUN_DAMAGE=35)
        d = UserDefaults()
        assert d.objectForKey_('GOLD') == '7000' and d.intForKey_('GOLD') == 7000
        assert d.objectForKey_('GRENADECOUNT') == '2'
        assert d.objectForKey_('SHOTGUN') == '1' and d.objectForKey_('M4') is None
        assert d.objectForKey_('COLTUSE') == '1' and d.objectForKey_('KNIFEUSE') == '0'
        assert d.objectForKey_('MG80USE') == '0', 'one not in the list is not equipped'
        assert d.objectForKey_('WEAPON_ORDER') == [2, 3, 4, 5, 6, 7, 0, 1]
        assert d.objectForKey_('SHOTGUN_DAMAGE') == 35
        d.removeObjectForKey_('SHOTGUN')
        d.setObject_forKey_('0', 'COLTUSE')
        assert d.objectForKey_('SHOTGUN') is None and d.objectForKey_('COLTUSE') == '0'
    with _Folder():
        d = UserDefaults()
        assert d.objectForKey_('COLTUSE') is None, 'a new save has nothing equipped yet'


def test_a_hand_edited_inventory_is_read_as_written():
    """A player can type the names; one the game does not know is left for weapon_order to
    turn down, as any unusable value is."""
    with _Folder() as f:
        f.write(INVENTORY, json.dumps({'gold': 50, 'owned': ['mg80'],
                                       'equipped': ['knife', 'mg80'],
                                       'order': ['mg80', 'knife', 'colt', 'grenade',
                                                 'shotgun', 'm4a1', 'ak47', 'sword']}))
        d = UserDefaults()
        assert d.intForKey_('GOLD') == 50 and d.intForKey_('MG80') == 1
        assert d.intForKey_('MG80USE') == 1 and d.intForKey_('COLTUSE') == 0
        assert d.objectForKey_('WEAPON_ORDER') == [6, 1, 2, 0, 3, 4, 5, 7]
        f.write(INVENTORY, json.dumps({'order': ['mg80', 'laser']}))
        assert UserDefaults().objectForKey_('WEAPON_ORDER') == ['mg80', 'laser']


def test_every_setting_goes_to_settings_json_and_nothing_else_does():
    """The routing, whole: each of SETTINGS_KEYS lands in settings.json and never anywhere
    else, and nothing else lands there (2026-10-06)."""
    others = {'GOLD': '7', 'TUTORIAL': '1', 'COLT_LEVEL': 2, 'UPGRADE_DAMAGE_SHARE': 15,
              'WEAPON_ORDER': [2, 0, 1, 3, 4, 5, 6, 7]}
    with _Folder() as f:
        _save(**{k: '1' for k in SETTINGS_KEYS}, **others)
        settings = f.read(SETTINGS)
        assert list(settings) == list(SETTINGS_KEYS), list(settings)
        for name in (SAVE, SHOP, INVENTORY, weapon('colt')):
            assert not set(SETTINGS_KEYS) & set(f.read(name)), name
        back = UserDefaults().flat()
        for key, value in others.items():
            assert back[key] == value, (key, back.get(key))


def test_a_new_key_is_progress():
    """Anything not named as a setting, the shop, the inventory or a weapon's number is kept
    in the save, the safe place for it."""
    with _Folder() as f:
        _save(SOMETHINGNEW='1')
        assert f.read()['SOMETHINGNEW'] == '1'
        assert 'SOMETHINGNEW' not in f.read(SETTINGS)


def test_settings_json_is_written_in_its_own_order():
    """Not sorted by name: the order SETTINGS_KEYS gives."""
    with _Folder() as f:
        _save(VIBRATION='1', MENUMUSICVOLUME=100)
        with open(f.file(SETTINGS), encoding='utf-8') as fh:
            text = fh.read()
        order = [k for k in SETTINGS_KEYS if k in text]
        assert sorted(order, key=text.index) == order, text


# ---- keys the game no longer reads -------------------------------------------------------

def test_the_old_entity_volume_is_dropped():
    """ENTITYVOLUME went on 2026-09-28; a lowered one from before is taken out of the file,
    and the settings beside it are kept."""
    with _Folder() as f:
        f.write(SAVE, json.dumps({'TUTORIAL': '1'}))
        f.write(SETTINGS, json.dumps({'MASTERVOLUME': 80, 'ENTITYVOLUME': 20}))
        d = UserDefaults()
        assert d.objectForKey_('ENTITYVOLUME') is None
        assert f.read(SETTINGS) == {'MASTERVOLUME': 80}
        assert f.read() == {'TUTORIAL': '1'}


def test_the_old_voice_over_setting_is_dropped():
    """EYEMODE went on 2026-10-05 with the voice over row; a saved one from before is
    taken out of settings.json, and the settings beside it are kept."""
    with _Folder() as f:
        f.write(SAVE, json.dumps({'TUTORIAL': '1'}))
        f.write(SETTINGS, json.dumps({'MASTERVOLUME': 80, 'EYEMODE': '0'}))
        d = UserDefaults()
        assert d.objectForKey_('EYEMODE') is None
        assert f.read(SETTINGS) == {'MASTERVOLUME': 80}


def test_the_old_coins_are_dropped():
    """The coins went on 2026-10-05; a save from before keeps its other progress."""
    with _Folder() as f:
        f.write(SAVE, json.dumps({'TUTORIAL': '1', 'FIREST': '1', 'COIN': '3',
                                  'COIN_TIMER': '2026-10-01 12:00:00',
                                  'COIN_TIMER_START': '1'}))
        d = UserDefaults()
        for key in ('FIREST', 'COIN', 'COIN_TIMER', 'COIN_TIMER_START'):
            assert d.objectForKey_(key) is None, key
        assert f.read() == {'TUTORIAL': '1'}


def test_the_keys_nothing_used_are_dropped():
    """The original's stage select, its ranking server's week and rank and its App Store
    review count went on 2026-10-07 (aidocks/completed/unused_save_keys_plan.md); a save from
    before keeps its progress and its top score."""
    with _Folder() as f:
        f.write(SAVE, json.dumps({'TUTORIAL': '1', 'TOPSCORE': '4200', 'WEAPON_STATS_REAL': 1,
                                  'STAGE': '11', 'TOPSCOREWEEK': '3000',
                                  'WEEKTIME': '20261012000000', 'NOWRANK': '17',
                                  'REVIEWCOUNT': '42'}))
        d = UserDefaults()
        for key in ('STAGE', 'TOPSCOREWEEK', 'WEEKTIME', 'NOWRANK', 'REVIEWCOUNT'):
            assert d.objectForKey_(key) is None, key
        assert f.read() == {'TOPSCORE': '4200', 'TUTORIAL': '1', 'WEAPON_STATS_REAL': 1}


# ---- moving an old layout over -----------------------------------------------------------

FLAT_SAVE = {'TUTORIAL': '1', 'GOLD': '7000', 'GRENADECOUNT': '0', 'M4': '1',
             'GRENADEUSE': '1', 'KNIFEUSE': '1', 'COLTUSE': '1', 'M4USE': '1',
             'WEAPON_ORDER': [2, 3, 4, 5, 6, 7, 0, 1], 'GOLD_PER_KILL': 15,
             'UPGRADE_START_PRICE': 100, 'M4_DAMAGE': 40, 'M4_LEVEL': 3, 'KNIFE_RANGE': 200,
             'WEAPON_STATS_REAL': 1}


def _check_moved_over(f):
    assert f.read() == {'TUTORIAL': '1', 'WEAPON_STATS_REAL': 1}, f.read()
    assert f.read(SHOP) == {'gold_per_kill': 15, 'upgrade_start_price': 100}
    assert f.read(INVENTORY) == {'gold': 7000, 'grenades': 0, 'owned': ['m4a1'],
                                 'equipped': ['grenade', 'knife', 'colt', 'm4a1'],
                                 'order': ['colt', 'shotgun', 'm4a1', 'ak47', 'mg80', 'sword',
                                           'grenade', 'knife']}, f.read(INVENTORY)
    assert f.read(weapon('m4a1')) == {'damage': 40, 'level': 3}
    assert f.read(weapon('knife')) == {'range': 200}
    assert UserDefaults().flat() == dict(
        FLAT_SAVE, MASTERVOLUME=70, SHOTGUNUSE='0', AK47USE='0', MG80USE='0',
        JAPANUSE='0'), 'a key was lost on the way'


def test_the_flat_layout_moves_into_the_folders_once():
    """Every save before 2026-10-06 is save.json and settings.json in the folder itself.
    The first start moves them in and keeps each as .old; later starts leave them."""
    with _Folder() as f:
        f.write('save.json', json.dumps(FLAT_SAVE))
        f.write('settings.json', json.dumps({'MASTERVOLUME': 70}))
        d = UserDefaults()
        assert d.intForKey_('GOLD') == 7000 and d.objectForKey_('MASTERVOLUME') == 70
        assert f.read(SETTINGS) == {'MASTERVOLUME': 70}
        _check_moved_over(f)
        for name in ('save.json', 'settings.json'):
            assert not os.path.exists(f.file(name)), name + ' was left in place'
            assert os.path.exists(f.file(name + '.old')), name + ' was not kept'
        f.write('save.json', json.dumps({'GOLD': '1'}))      # a stray one later
        assert UserDefaults().intForKey_('GOLD') == 7000, 'it was moved over again'


def test_a_save_moved_into_the_folders_by_hand_is_sorted_out():
    """The dev's own save, 2026-10-06: the whole flat save.json moved into saves/ by hand,
    beside empty store and weapon files.  Each key goes to its own file."""
    with _Folder() as f:
        f.write(SAVE, json.dumps(FLAT_SAVE))
        f.write(SETTINGS, json.dumps({'MASTERVOLUME': 70}))
        for name in (SHOP, INVENTORY) + tuple(weapon(w) for w in WEAPONS):
            f.write(name, '')
        UserDefaults()
        _check_moved_over(f)


def test_a_key_already_in_its_own_file_wins_over_a_stray_copy():
    with _Folder() as f:
        f.write(INVENTORY, json.dumps({'gold': 50}))
        f.write(SAVE, json.dumps({'GOLD': '9999', 'TUTORIAL': '1'}))
        assert UserDefaults().intForKey_('GOLD') == 50
        assert f.read() == {'TUTORIAL': '1'}, 'the stray copy was kept'


def test_an_old_defaults_json_is_moved_over_and_kept():
    with _Folder() as f:
        f.write('defaults.json', json.dumps({'GOLD': '7000', 'COIN': '3', 'M4': '1',
                                              'VIBRATION': '0', 'MENUMUSICVOLUME': 40}))
        d = UserDefaults()
        assert d.intForKey_('GOLD') == 7000 and d.intForKey_('M4') == 1
        assert d.intForKey_('VIBRATION') == 0 and d.objectForKey_('MENUMUSICVOLUME') == 40
        assert d.objectForKey_('COIN') is None, 'the old coins were carried over'
        assert f.read(INVENTORY) == {'gold': 7000, 'owned': ['m4a1']}
        assert f.read(SETTINGS) == {'MENUMUSICVOLUME': 40, 'VIBRATION': '0'}
        assert not os.path.exists(f.file('defaults.json')), 'the old file was left in place'
        assert json.loads(open(f.file('defaults.json.old'), encoding='utf-8').read())['GOLD'] \
            == '7000', 'the old file was not kept'
        # and the next start reads the folders, not the old one again
        assert UserDefaults().intForKey_('GOLD') == 7000


def test_a_damaged_old_defaults_json_moves_its_backup_over():
    with _Folder() as f:
        f.write('defaults.json', '{"GOLD": "70')
        f.write('defaults.json.bak', json.dumps({'GOLD': '6500', 'VIBRATION': '0'}))
        d = UserDefaults()
        assert d.intForKey_('GOLD') == 6500, 'the old backup was not used'
        assert d.intForKey_('VIBRATION') == 0
        with open(f.file('defaults.json.damaged'), encoding='utf-8') as fh:
            assert fh.read() == '{"GOLD": "70', 'the damaged old save was not kept'
        assert f.read(INVENTORY)['gold'] == 6500


def test_an_old_defaults_json_beside_a_save_is_left_alone():
    with _Folder() as f:
        _save(GOLD='100')
        f.write('defaults.json', json.dumps({'GOLD': '9999'}))
        assert UserDefaults().intForKey_('GOLD') == 100
        assert os.path.exists(f.file('defaults.json')), 'it was moved over a save'


def test_a_damaged_settings_json_carries_on_from_its_backup():
    with _Folder() as f:
        _save(VIBRATION='0')
        _save(VIBRATION='1')
        f.write(SETTINGS, '{"EYEMO')
        d = UserDefaults()
        assert d.intForKey_('VIBRATION') == 0, 'the settings backup was not loaded'
        with open(f.file(SETTINGS + '.damaged'), encoding='utf-8') as fh:
            assert fh.read() == '{"EYEMO'


def test_the_settings_and_the_keys_always_have_a_backup():
    """tsatria03, 2026-10-06: a .bak for the keys and the settings, made where there is none
    yet, not only from their second write on."""
    from sixthsense.platform.keymap import KeyMap
    with _Folder() as f:
        f.write(SETTINGS, json.dumps({'MASTERVOLUME': 80}))
        f.write(KEYS, json.dumps({'pause': [['f12']]}))
        UserDefaults()
        KeyMap()
        assert f.read(SETTINGS + '.bak') == {'MASTERVOLUME': 80}
        assert f.read(KEYS + '.bak')['pause'] == [['f12']]


def test_a_key_save_keeps_the_one_before_as_a_backup():
    from sixthsense.platform.keymap import KeyMap
    with _Folder() as f:
        km = KeyMap()
        km.set_binding('pause', ('f12',))
        km.set_binding('pause', ('f10',))
        assert f.read(KEYS)['pause'] == [['f10']]
        assert f.read(KEYS + '.bak')['pause'] == [['f12']]


def test_damaged_keys_carry_on_from_the_backup_and_never_overwrite_it():
    from sixthsense.platform.keymap import KeyMap
    with _Folder() as f:
        KeyMap().set_binding('pause', ('f12',))
        KeyMap().set_binding('pause', ('f10',))       # the backup now holds f12
        f.write(KEYS, '{"pause": [["f1')
        km = KeyMap()
        assert km.bindings['pause'] == [('f12',)], 'the backup was not used'
        with open(f.file(KEYS), encoding='utf-8') as fh:
            assert fh.read() == '{"pause": [["f1', 'the damaged file was written over'
        km.set_binding('lane1', ('z',))               # a rebind writes the file again
        assert f.read(KEYS + '.bak')['pause'] == [['f12']], 'the damaged file became the backup'
        assert f.read(KEYS)['lane1'] == [['z']]


def test_the_key_bindings_move_into_config_once():
    from sixthsense.platform.keymap import KeyMap
    with _Folder() as f:
        f.write('keys.json', json.dumps({'pause': [['f12']]}))
        km = KeyMap()
        assert km.path == f.file(KEYS)
        assert km.bindings['pause'] == [('f12',)], 'the old bindings were lost'
        assert f.read(KEYS)['pause'] == [['f12']]
        assert not os.path.exists(f.file('keys.json'))
        assert os.path.exists(f.file('keys.json.old'))
        f.write('keys.json', json.dumps({'pause': [['f1']]}))
        assert KeyMap().bindings['pause'] == [('f12',)], 'it was moved over again'


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
