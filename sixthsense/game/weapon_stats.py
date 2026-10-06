"""PORT ADDITION: each weapon's stats, kept in save.json and read back by the game.

A weapon's page reads four numbers aloud: ammo capacity, effective range, damage and
price.  Since 2026-10-05 they are the real ones, and the game plays with what the save
holds (aidocks/completed/real_weapon_stats_plan.md):

    AMMO_CAPACITY  the magazine: what starting, reloading and the test range fill to
    RANGE          in centimetres: a zombie further away cannot be hit, by the grenade too
    DAMAGE         what a hit takes off; a gun's headshot still doubles it
    PRICE          what the shop charges

The original's pages spoke numbers typed into its code (``store.SHOP``,
``inventory.SLOTS``, which disagree with each other) while play read the weapon plists;
the numbers here are the plists' damage, range and magazine, and the shop's price, the one
buying always charged.  From 2026-09-25 to 2026-10-05 the save held the shop's numbers and
nothing read them (aidocks/completed/weapon_stats_in_save_plan.md).

The keys are the weapon's own save name and the stat, in capitals with underscores
between the words (tsatria03, 2026-10-05), easier to read than the original's
run-together style: ``SHOTGUN_AMMO_CAPACITY``, ``SHOTGUN_RANGE``, ``SHOTGUN_DAMAGE``,
``SHOTGUN_PRICE``.  A weapon has no key where nothing could use it: the grenade's count is
``GRENADECOUNT``, the knife and the sword spend no ammo, and the shop does not sell the
knife or the colt.

``fill`` runs on every start (``AppDelegate.weaponHave``), and for all eight weapons,
owned or not, so a price can be changed before buying.  The keys' two earlier names
(``SHOTGUNRANGE``, then briefly ``shotgun_range``) are renamed first, values kept.  A
missing or unusable value is put back to the real one; once only, an older save's shop
numbers are all replaced.
"""
from __future__ import annotations

import logging

log = logging.getLogger('weapon_stats')

#: The eight weapons in slot order (``AppDelegate.haveWeapon``, ``.useWeapon`` and
#: ``Stage_1_E.weaponSource``), by the name their owned and equipped keys use.
NAMES = ('GRENADE', 'KNIFE', 'COLT', 'SHOTGUN', 'M4', 'AK47', 'MG80', 'JAPAN')

STATS = ('ammo_capacity', 'range', 'damage', 'price')
#: The same stats as the keys were named until 2026-10-05: ``SHOTGUNRANGE``.
OLD_STATS = ('AMMOCAPACITY', 'RANGE', 'DAMAGE', 'PRICE')


def key(name, stat):
    """The save key for one weapon's stat: ``key('MG80', 'range')`` is ``MG80_RANGE``."""
    return ('%s_%s' % (name, stat)).upper()


def _old_keys(name, stat):
    """The names the same key had before: ``MG80RANGE``, then ``mg80_range``."""
    return (name + OLD_STATS[STATS.index(stat)], key(name, stat).lower())

#: Each weapon's real numbers, as ammo capacity, range in centimetres, damage and price;
#: None where it has no key.  The plists' indices 7, 5 and 3 (``Grenage.plist`` to
#: ``Japanese.plist``) and ``store.SHOP``'s prices.
REAL = {
    'GRENADE': (None, 1600, 150, 1000),
    'KNIFE': (None, 200, 30, None),
    'COLT': (7, 1000, 30, None),
    'SHOTGUN': (10, 1000, 35, 7000),
    'M4': (25, 1300, 40, 13000),
    'AK47': (30, 1300, 40, 15000),
    'MG80': (50, 1600, 45, 45000),
    'JAPAN': (None, 300, 100, 50000),
}

#: Set in save.json once an older save's shop numbers have been replaced by the real
#: ones, so that is done only once and a later hand edit stays.
REAL_MARKER = 'WEAPON_STATS_REAL'
OLD_REAL_MARKERS = ('WEAPONSTATSREAL', 'weapon_stats_real')


def stats(name):
    """``{key: real value}`` for one weapon, leaving out the stats it has no key for."""
    return {key(name, stat): value for stat, value in zip(STATS, REAL[name])
            if value is not None}


def _rename_old_keys(defaults):
    """Move keys under their earlier names (``MG80RANGE``, ``mg80_range``) to the current
    ones (``MG80_RANGE``), values kept; where both are there, the current one wins.  True
    when any moved."""
    moved = False
    pairs = [(old, REAL_MARKER) for old in OLD_REAL_MARKERS]
    pairs += [(old, key(name, stat)) for name in NAMES for stat in STATS
              for old in _old_keys(name, stat)]
    for old, new in pairs:
        have = defaults.objectForKey_(old)
        if have is None:
            continue
        if defaults.objectForKey_(new) is None:
            defaults.setObject_forKey_(have, new)
        defaults.removeObjectForKey_(old)
        moved = True
    return moved


def _usable(value):
    """A whole number of 0 or more, as JSON gives it; None when it is not one."""
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value if value >= 0 else None
    if isinstance(value, float) and value.is_integer() and value >= 0:
        return int(value)
    return None


def fill(defaults):
    """Write every weapon's real stats where the save has none or an unusable one, drop
    keys no weapon has, and the first time, replace them all.  True when anything was
    written."""
    wrote = _rename_old_keys(defaults)
    first = defaults.objectForKey_(REAL_MARKER) is None
    for name in NAMES:
        for stat in STATS:
            k = key(name, stat)
            real = REAL[name][STATS.index(stat)]
            have = defaults.objectForKey_(k)
            if real is None:
                if have is not None:
                    defaults.removeObjectForKey_(k)
                    wrote = True
                continue
            good = _usable(have)
            if first or good is None:
                if have is not None and not first:
                    log.warning('%s was %r, which is not a whole number of 0 or more; '
                                'put back to %d', k, have, real)
                if have != real:
                    defaults.setInteger_forKey_(real, k)
                    wrote = True
            elif good != have or type(have) is not int:
                defaults.setInteger_forKey_(good, k)      # 45.0 is written back as 45
                wrote = True
    if first:
        defaults.setInteger_forKey_(1, REAL_MARKER)
        wrote = True
    return wrote


def value(name, stat, defaults=None):
    """The number the game uses: the save's, or the real one when the save has none it
    can use.  None for a stat the weapon has no key for."""
    real = REAL[name][STATS.index(stat)]
    if real is None:
        return None
    if defaults is None:
        from ..platform.defaults import UserDefaults
        defaults = UserDefaults.standardUserDefaults()
    good = _usable(defaults.objectForKey_(key(name, stat)))
    return real if good is None else good


def apply(weapon, slot, defaults=None):
    """Give a loaded ``WeaponControl`` the save's damage, range and magazine.  A weapon
    with no ammo capacity key (the grenade, the blades) keeps its plist's."""
    name = NAMES[slot]
    weapon.Damage = value(name, 'damage', defaults)
    weapon.Range = value(name, 'range', defaults)
    ammo = value(name, 'ammo_capacity', defaults)
    if ammo is not None:
        weapon.AmmoCapacity = ammo
        weapon.BulletCount = ammo


def range_text(cm):
    """A range in centimetres as metres: at most two decimals, no trailing zeros."""
    metres = '%d.%02d' % divmod(cm, 100)
    metres = metres.rstrip('0').rstrip('.')
    return '%s metre' % metres if metres == '1' else '%s metres' % metres
