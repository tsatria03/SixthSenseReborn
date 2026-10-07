"""``NSUserDefaults`` - JSON files in folders inside ``%APPDATA%\\SixthSenseReborn``.

The keys are the ones the binary writes, with the classes that own them:

    TUTORIAL        int    ``-[Stage_1_E viewDidLoad]``     0 until the tutorial is finished
    GOLD            int    ``AppDelegate.haveGold``
    (FIREST, COIN, COIN_TIMER and COIN_TIMER_START belonged to the coins, which are gone:
    games are free.  An old save's are dropped, as RETIRED_KEYS.)
    GRENADECOUNT    int    ``-[Stage_1_E MovingShot:]``     grenades in hand
    STAGE           int    ``-[MainController ...]``        highest stage unlocked
    SHOTGUN, M4, AK47, MG80, JAPAN
                    int    owned weapons, ``-[AppDelegate weaponHave]``
    GRENADEUSE, KNIFEUSE, COLTUSE, SHOTGUNUSE, M4USE, AK47USE, MG80USE, JAPANUSE
                    int    equipped weapons
    (EYEMODE, the voice-over row, is gone: the game is always read by the screen reader.)
    TOPSCORE, TOPSCOREWEEK, WEEKTIME, NOWRANK, REVIEWCOUNT
                           the result panel's records, ``-[Stage_1_E SuccessOrFailMission]``

and the port's own: the settings (``SETTINGS_KEYS``), each weapon's stats, with
underscores: ``<W>_AMMO_CAPACITY``, ``<W>_RANGE`` (in centimetres), ``<W>_DAMAGE`` and
``<W>_PRICE``, which the game reads and plays with, and ``WEAPON_STATS_REAL``, set once an
older save's shop numbers were replaced by the real ones (``game/weapon_stats.py``),
``GOLD_PER_KILL`` and ``GOLD_PER_HEADSHOT``, the gold a game pays (``game/gold_rates.py``),
the upgrades: ``<W>_LEVEL``, ``<W>_MAX_LEVEL`` and five ``UPGRADE_...`` settings for every
weapon (``game/weapon_upgrades.py``), and ``WEAPON_ORDER`` (``game/weapon_order.py``).

``synchronize`` writes the files; the original's does the same thing.

PORT ADDITION: the original keeps everything in one plist.  The port split it into
save.json and settings.json on 2026-09-25 (aidocks/completed/save_split_plan.md), and into
short files in folders on 2026-10-06, tsatria03's layout
(aidocks/completed/save_folders_plan.md):

    saves/save.json          progress, and any key not named below, the safe place for a
                             key added later
    config/settings.json     SETTINGS_KEYS, written in that order
    config/keys.json         the key bindings (``keymap.py``)
    store/shop.json          the shop's rules: SHOP_KEYS, in lowercase
    store/inventory.json     gold, grenades, and the weapons owned, equipped and in order,
                             as lists of weapon names
    weapons/<name>.json      one weapon's numbers under short names: ammo_capacity, range,
                             damage, price, level, max_level

**Nothing that uses ``UserDefaults`` has to know which file a key lives in, or what it is
called there.**  The game asks for ``'SHOTGUN_DAMAGE'``, ``'GOLD'`` or ``'M4USE'`` as it
always did, and gets the value in the form it always had (``GOLD`` as text, ``M4USE`` as
"1" or "0", ``WEAPON_ORDER`` as slot numbers); the files hold names a player can read.

**An old layout moves over by itself, once.**  The flat save.json and settings.json beside
the folders, every save before 2026-10-06 (and a defaults.json from before 2026-09-25's
split), are read into the new files the first time the game starts without a
saves/save.json, and kept as ``<file>.old``.  And on every start, a key found in a file it
does not belong in is moved to its own, unless that already has it - which also sorts out
a save moved into the folders by hand.

PORT ADDITION: a file that cannot be read is never written over.  It is kept as
``<file>.damaged``, and the game carries on from ``<file>.bak``, the copy before the last
write, which every ``synchronize`` keeps.  An empty file is a new one, not a damaged one.
"""
from __future__ import annotations

import json
import logging
import os
import shutil

from .. import paths

log = logging.getLogger('defaults')

SAVE_FILE = os.path.join('saves', 'save.json')
SETTINGS_FILE = os.path.join('config', 'settings.json')
KEYS_FILE = os.path.join('config', 'keys.json')
SHOP_FILE = os.path.join('store', 'shop.json')
INVENTORY_FILE = os.path.join('store', 'inventory.json')
WEAPONS_FOLDER = 'weapons'
#: The layout before 2026-10-06: both files beside where the folders now are.  Settings
#: first, so a setting a save.json also held takes settings.json's value.
FLAT_FILES = ('settings.json', 'save.json')
#: The one file everything was kept in before 2026-09-25.
OLD_FILE = 'defaults.json'
#: What an old file is kept as once it has been moved over.
OLD_SUFFIX = '.old'
OLD_KEPT = OLD_FILE + OLD_SUFFIX

#: The keys that are settings rather than progress, in the order settings.json lists them
#: (tsatria03, 2026-09-25).  A setting added later goes where it belongs in this list.
SETTINGS_KEYS = ('DEBUG', 'MASTERVOLUME', 'MENUMUSICVOLUME', 'LEVELMUSICVOLUME', 'AMBIENCEVOLUME',
                 'GAMEPLAYGAIN', 'WEAPONVOLUME', 'PLAYERVOLUME', 'VIBRATION',
                 'HEADSHOTSPEECH', 'HEADSHOTBEEP', 'SHAKE', 'CONTROLLERSUPPORT',
                 'CONTROLLER', 'SKIPINTRO')
#: Keys the game no longer reads, dropped when the save is opened, so an old value cannot
#: linger.  ENTITYVOLUME went on 2026-09-28: the zombies are always at full volume
#: (aidocks/completed/entity_full_volume_plan.md).  EYEMODE went on 2026-10-05 with the voice
#: over row (aidocks/completed/screen_reader_only_plan.md).  The four coin keys went on
#: 2026-10-06; games had been free since 2026-10-05 (aidocks/completed/free_games_plan.md),
#: but an old save still carried them.
RETIRED_KEYS = ('ENTITYVOLUME', 'EYEMODE', 'FIREST', 'COIN', 'COIN_TIMER', 'COIN_TIMER_START')

#: store/shop.json: the game's names; the file's are the same in lowercase, in this order.
SHOP_KEYS = ('GOLD_PER_KILL', 'GOLD_PER_HEADSHOT', 'UPGRADE_START_PRICE',
             'UPGRADE_PRICE_GROWTH', 'UPGRADE_AMMO_SHARE', 'UPGRADE_DAMAGE_SHARE',
             'UPGRADE_RANGE_SHARE')
#: Each weapon slot's name in the save's keys and its file's name: slot 0 is the grenade.
WEAPONS = (('GRENADE', 'grenade'), ('KNIFE', 'knife'), ('COLT', 'colt'),
           ('SHOTGUN', 'shotgun'), ('M4', 'm4a1'), ('AK47', 'ak47'), ('MG80', 'mg80'),
           ('JAPAN', 'sword'))
SLOT_NAMES = tuple(name for _key, name in WEAPONS)
#: weapons/<name>.json: what follows ``<W>_`` in the game's keys; the file's are lowercase.
WEAPON_STATS = ('AMMO_CAPACITY', 'RANGE', 'DAMAGE', 'PRICE', 'LEVEL', 'MAX_LEVEL')
#: store/inventory.json, in this order.
INVENTORY_ORDER = ('gold', 'grenades', 'owned', 'equipped', 'order')
COUNTS = {'GOLD': 'gold', 'GRENADECOUNT': 'grenades'}
OWNED = {'SHOTGUN': 'shotgun', 'M4': 'm4a1', 'AK47': 'ak47', 'MG80': 'mg80', 'JAPAN': 'sword'}
EQUIPPED = {key + 'USE': name for key, name in WEAPONS}
ORDER_KEY = 'WEAPON_ORDER'


def _read(path):
    """The JSON object at ``path``, {} when it is empty, or None when it is missing or is
    not one.  A byte order mark, which Notepad may write, is allowed."""
    try:
        with open(path, 'r', encoding='utf-8-sig') as f:
            text = f.read()
    except FileNotFoundError:
        return None
    except Exception:
        log.exception('could not read %s', path)
        return None
    if not text.strip():
        return {}                   # made empty by hand: a new file, not a damaged one
    try:
        d = json.loads(text)
    except Exception:
        log.exception('could not read %s', path)
        return None
    if not isinstance(d, dict):
        log.error('%s is not a save: %s', path, type(d).__name__)
        return None
    return d


class _File:
    """One JSON file of keys, with its backup, kept aside when it is damaged."""

    def __init__(self, path, order=None):
        self.path = path
        self.backup = path + '.bak'
        self.order = order          # the key order to write in; sorted by name when None
        self.d = {}
        self.recovered = False      # read from the backup, so it wants writing back
        if not os.path.exists(path):
            return                  # a new save, or one deleted to start over
        d = _read(path)
        if d is None:
            damaged = path + '.damaged'
            try:
                os.replace(path, damaged)
                log.error('%s could not be read; kept as %s', path, damaged)
            except OSError:
                log.exception('could not set the damaged %s aside', path)
            d = _read(self.backup)
            if d is not None:
                log.warning('carrying on from %s', self.backup)
                self.recovered = True
        self.d = d or {}

    def ensure_backup(self):
        """Copy a file that read cleanly to its .bak when it has none yet (tsatria03,
        2026-10-06), so there is something to carry on from before its second write."""
        if self.recovered or os.path.exists(self.backup) or not os.path.exists(self.path):
            return
        try:
            shutil.copyfile(self.path, self.backup)
        except OSError:
            log.exception('could not back up %s', self.path)

    def ordered(self):
        if self.order is None:
            return dict(sorted(self.d.items()))
        first = [(k, self.d[k]) for k in self.order if k in self.d]
        rest = sorted((k, v) for k, v in self.d.items() if k not in self.order)
        return dict(first + rest)

    def write(self):
        try:
            os.makedirs(os.path.dirname(self.path), exist_ok=True)
            tmp = self.path + '.tmp'
            with open(tmp, 'w', encoding='utf-8') as f:
                json.dump(self.ordered(), f, indent=1)
                f.flush()
                os.fsync(f.fileno())
            if os.path.exists(self.path):
                shutil.copyfile(self.path, self.backup)
            os.replace(tmp, self.path)
        except Exception:
            log.exception('could not write %s', self.path)


def _weapon_key(key):
    """``('shotgun', 'damage')`` for ``'SHOTGUN_DAMAGE'``; None for a key no weapon file
    holds."""
    for prefix, name in WEAPONS:
        if key.startswith(prefix + '_') and key[len(prefix) + 1:] in WEAPON_STATS:
            return name, key[len(prefix) + 1:].lower()
    return None


def _on(value):
    """What ``intForKey_`` made of an owned or equipped key: on at 1 or more."""
    try:
        return int(value) >= 1
    except (TypeError, ValueError):
        return False


def _number(value):
    """Gold and grenades as plain numbers in inventory.json, though the game writes them as
    text; a value that is not a number is kept as given."""
    if isinstance(value, str):
        try:
            return int(value.strip())
        except ValueError:
            return value
    return value


def _order_names(order):
    """WEAPON_ORDER's slot numbers as weapon names; anything else is kept as given."""
    if isinstance(order, (list, tuple)) and all(
            isinstance(s, int) and not isinstance(s, bool) and 0 <= s < len(SLOT_NAMES)
            for s in order):
        return [SLOT_NAMES[s] for s in order]
    return order


def _order_slots(order):
    """inventory.json's order as WEAPON_ORDER's slot numbers; anything that is not a list of
    weapon names is handed over as it is, for weapon_order to judge."""
    if isinstance(order, list) and all(isinstance(n, str) and n in SLOT_NAMES for n in order):
        return [SLOT_NAMES.index(n) for n in order]
    return order


class UserDefaults:
    _instance = None

    @classmethod
    def standardUserDefaults(cls):
        if cls._instance is None:
            cls._instance = UserDefaults()
        return cls._instance

    def __init__(self):
        folder = paths.user_dir()
        self.folder = folder
        self.path = os.path.join(folder, SAVE_FILE)
        self.backup = self.path + '.bak'
        flat = self._take_flat_save(folder)
        self.save = _File(self.path)
        self.settings = _File(os.path.join(folder, SETTINGS_FILE), order=SETTINGS_KEYS)
        self.shop = _File(os.path.join(folder, SHOP_FILE),
                          order=[k.lower() for k in SHOP_KEYS])
        self.inventory = _File(os.path.join(folder, INVENTORY_FILE), order=INVENTORY_ORDER)
        self.weapons = {name: _File(os.path.join(folder, WEAPONS_FOLDER, name + '.json'),
                                    order=[s.lower() for s in WEAPON_STATS])
                        for name in SLOT_NAMES}
        changed = False
        if flat is not None:
            # what the old files held, where the new ones do not have it yet
            present = set(self.inventory.d)
            for key, value in flat.items():
                self._place(key, value, present)
            changed = True
        for f in (self.save, self.settings):
            for key in RETIRED_KEYS:
                changed = f.d.pop(key, None) is not None or changed
        changed = self._sort_misplaced() or changed
        if changed or any(f.recovered for f in self._files()):
            self.synchronize()      # or the next launch finds no save at all
        # the settings always have a backup, even before their second write
        self.settings.ensure_backup()

    def _files(self):
        return [self.save, self.settings, self.shop, self.inventory] + list(self.weapons.values())

    def _take_flat_save(self, folder):
        """The keys of the flat layout - save.json and settings.json beside the folders, or
        a defaults.json from before those - when there is no saves/save.json yet; None
        otherwise.  Each old file is kept as ``<file>.old``, or, when it cannot be read, as
        ``<file>.damaged`` with its backup used."""
        if os.path.exists(os.path.join(folder, SAVE_FILE)):
            return None
        names = [n for n in FLAT_FILES if os.path.exists(os.path.join(folder, n))]
        if not names and os.path.exists(os.path.join(folder, OLD_FILE)):
            names = [OLD_FILE]
        if not names:
            return None
        merged = {}
        for name in names:
            f = _File(os.path.join(folder, name))   # a damaged one is set aside here
            for key, value in f.d.items():
                merged.setdefault(key, value)
            if os.path.exists(f.path):
                try:
                    os.replace(f.path, f.path + OLD_SUFFIX)
                except OSError:
                    log.exception('could not keep %s as %s', f.path, name + OLD_SUFFIX)
        log.warning('moved %s into the save folders', ', '.join(names))
        return merged

    def _sort_misplaced(self):
        """Move each key in save.json or settings.json that belongs in another file to its
        own, unless that file has it already.  True when anything moved."""
        moved = False
        present = set(self.inventory.d)
        for f in (self.save, self.settings):
            for key in list(f.d):
                if self._home(key) is f:
                    continue
                self._place(key, f.d.pop(key), present)
                moved = True
        if moved:
            log.warning('moved keys out of save.json and settings.json into their own files')
        return moved

    def _place(self, key, value, present):
        """Put a key moved from an old file into its own, unless that already had it.
        ``present`` is what inventory.json held before the move began: one equipped weapon
        moved in makes the others read "0", not missing, so for the inventory's own fields
        it is what was there before that counts."""
        home = self._home(key)
        if home is self.inventory:
            field = (COUNTS.get(key) or ('owned' if key in OWNED else None)
                     or ('equipped' if key in EQUIPPED else 'order'))
            if field in present:
                return
        elif self.objectForKey_(key) is not None:
            return
        self.setObject_forKey_(value, key)

    def _home(self, key):
        """The file a key lives in."""
        if key in SETTINGS_KEYS:
            return self.settings
        if key in SHOP_KEYS:
            return self.shop
        weapon = _weapon_key(key)
        if weapon:
            return self.weapons[weapon[0]]
        if key in COUNTS or key in OWNED or key in EQUIPPED or key == ORDER_KEY:
            return self.inventory
        return self.save

    # ---- inventory.json's lists ----------------------------------------------------
    def _names(self, field):
        v = self.inventory.d.get(field)
        return v if isinstance(v, list) else []

    def _mark(self, field, name, on):
        """Put ``name`` in the list ``field`` or take it out, keeping slot order."""
        have = self._names(field)
        wanted = (set(have) | {name}) if on else (set(have) - {name})
        known = [n for n in SLOT_NAMES if n in wanted]
        self.inventory.d[field] = known + [n for n in have if n in wanted and n not in known]

    # NSUserDefaults returns nil for a missing key and the game does
    # [[defaults objectForKey:k] intValue], which is 0 for nil.
    def objectForKey_(self, key):
        home = self._home(key)
        if home is self.settings or home is self.save:
            return home.d.get(key)
        if home is self.shop:
            return self.shop.d.get(key.lower())
        if home is not self.inventory:
            return home.d.get(_weapon_key(key)[1])
        if key in COUNTS:
            v = self.inventory.d.get(COUNTS[key])
            # the text form the game has always written and read
            return str(v) if isinstance(v, int) and not isinstance(v, bool) else v
        if key in OWNED:
            return '1' if OWNED[key] in self._names('owned') else None
        if key in EQUIPPED:
            if 'equipped' not in self.inventory.d:
                return None
            return '1' if EQUIPPED[key] in self._names('equipped') else '0'
        return _order_slots(self.inventory.d.get('order'))

    def intForKey_(self, key):
        v = self.objectForKey_(key)
        if v is None:
            return 0
        try:
            return int(v)
        except (TypeError, ValueError):
            return 0

    def stringForKey_(self, key):
        v = self.objectForKey_(key)
        return None if v is None else str(v)

    def setObject_forKey_(self, value, key):
        home = self._home(key)
        if home is self.settings or home is self.save:
            home.d[key] = value
        elif home is self.shop:
            self.shop.d[key.lower()] = value
        elif home is not self.inventory:
            home.d[_weapon_key(key)[1]] = value
        elif key in COUNTS:
            self.inventory.d[COUNTS[key]] = _number(value)
        elif key in OWNED:
            self._mark('owned', OWNED[key], _on(value))
        elif key in EQUIPPED:
            self._mark('equipped', EQUIPPED[key], _on(value))
        else:
            self.inventory.d['order'] = _order_names(value)

    def setInteger_forKey_(self, value, key):
        self.setObject_forKey_(int(value), key)

    def removeObjectForKey_(self, key):
        home = self._home(key)
        if home is self.settings or home is self.save:
            home.d.pop(key, None)
        elif home is self.shop:
            self.shop.d.pop(key.lower(), None)
        elif home is not self.inventory:
            home.d.pop(_weapon_key(key)[1], None)
        elif key in COUNTS:
            self.inventory.d.pop(COUNTS[key], None)
        elif key in OWNED:
            self._mark('owned', OWNED[key], False)
        elif key in EQUIPPED:
            self._mark('equipped', EQUIPPED[key], False)
        else:
            self.inventory.d.pop('order', None)

    def flat(self):
        """Every key the save holds, under the game's names and in the forms the game reads,
        whichever file it is in: what save.json alone held before the folders."""
        out = dict(self.save.d)
        out.update(self.settings.d)
        for key in SHOP_KEYS:
            if key.lower() in self.shop.d:
                out[key] = self.shop.d[key.lower()]
        for prefix, name in WEAPONS:
            for stat in WEAPON_STATS:
                if stat.lower() in self.weapons[name].d:
                    out['%s_%s' % (prefix, stat)] = self.weapons[name].d[stat.lower()]
        for key in list(COUNTS) + list(OWNED) + list(EQUIPPED) + [ORDER_KEY]:
            v = self.objectForKey_(key)
            if v is not None:
                out[key] = v
        return out

    def synchronize(self):
        for f in self._files():
            f.write()
        return True


def standard() -> UserDefaults:
    return UserDefaults.standardUserDefaults()
