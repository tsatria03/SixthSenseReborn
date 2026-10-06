"""PORT ADDITION: weapon upgrades, one level per weapon, every number in save.json.

tsatria03, 2026-10-05 (aidocks/completed/weapon_upgrades_plan.md).  Each weapon has a level,
``<W>_LEVEL``, from 0 up to its cap, ``<W>_MAX_LEVEL`` (10).  One upgrade button raises
it by one, and the level adds to the weapon's own stats (``weapon_stats.py``): damage,
ammo capacity and range all at once.  The grenade, the knife and the sword have no
magazine, so they gain damage and range only.

What a level adds is a share of the weapon's own stat, not a flat count, so each weapon
keeps its character: a maxed MG80 still out-ammos a maxed colt.  The total added at
level n is

    base * share / 100 * n

rounded half up, with the shares ``UPGRADE_DAMAGE_SHARE``, ``UPGRADE_AMMO_SHARE`` and
``UPGRADE_RANGE_SHARE`` all 15 per cent, so level 10 is two and a half times the weapon:
a colt of 7 rounds and 30 damage holds 18 and does 75.  The base is the save's own stat,
so one edited there scales with it.  The range is rounded to a whole metre rather than
to the centimetre (``ROUNDING``), since it is read out in metres and 14.95 of them is an
odd thing to hear.  Retuned this way on 2026-10-06, the dev having found a level 10 colt
holding 267 rounds: the shares were flat steps shared by all eight weapons, compounded
by a growth, and every weapon gained the same +260.  Level n costs

    UPGRADE_START_PRICE * UPGRADE_PRICE_GROWTH ** (n - 1)

rounded half up, from 100 growing 1.2 times a level: 100, 120, 144, 173 ... 516, 2,596
to reach level 10.  The five settings are for all weapons at once; the level and the cap
are each weapon's, and a level past the cap counts only up to it.  ``fill`` writes them on every start where missing or unusable, and
clears the keys the retune left behind.
"""
from __future__ import annotations

import logging
import math

from .weapon_stats import NAMES, REAL, STATS, _usable, key, value

log = logging.getLogger('weapon_upgrades')

START_PRICE = 'UPGRADE_START_PRICE'
PRICE_GROWTH = 'UPGRADE_PRICE_GROWTH'
#: the stat each share raises, by its key.  The names say share because the value is a
#: percentage of the weapon's own stat; until 2026-10-06 they were flat counts named
#: UPGRADE_DAMAGE, UPGRADE_AMMO and UPGRADE_RANGE, which fill() now clears.
SHARES = {'damage': 'UPGRADE_DAMAGE_SHARE', 'ammo_capacity': 'UPGRADE_AMMO_SHARE',
          'range': 'UPGRADE_RANGE_SHARE'}

#: the five settings for all weapons, and their defaults
SETTINGS = {START_PRICE: 100, PRICE_GROWTH: 1.2, SHARES['damage']: 15,
            SHARES['ammo_capacity']: 15, SHARES['range']: 15}
#: what a stat's gain is rounded to.  The range is in centimetres but read out in metres
#: (``weapon_stats.range_text``), so it moves a whole metre at a time: the dev, 2026-10-06,
#: "it might read a little odd to someone like 14.95. just say 15".  A short blade gains
#: nothing on some levels because of it, which the dev accepted.
ROUNDING = {'range': 100}
#: the one that may be a fraction
GROWTHS = (PRICE_GROWTH,)
#: what the retune of 2026-10-06 left in older saves, removed by fill(): the flat steps,
#: whose values mean something else as shares, and the growth the shares do without
STALE = ('UPGRADE_DAMAGE', 'UPGRADE_AMMO', 'UPGRADE_RANGE', 'UPGRADE_GROWTH')
MAX_LEVEL = 10
#: the most any total or price can be, so an absurd hand edit cannot overflow
CEILING = 10 ** 9


def level_key(name):
    return key(name, 'level')


def max_key(name):
    return key(name, 'max_level')


def _growth(value):
    """A growth: a number above 0, as JSON gives it; None when it is not one."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    if not math.isfinite(value) or value <= 0:
        return None
    return value


def _check(name, value):
    return _growth(value) if name in GROWTHS else _usable(value)


def fill(defaults):
    """Write each setting, level and cap that is missing or unusable.  True when anything
    was written."""
    wanted = dict(SETTINGS)
    for name in NAMES:
        wanted[level_key(name)] = 0
        wanted[max_key(name)] = MAX_LEVEL
    wrote = False
    for k, default in wanted.items():
        have = defaults.objectForKey_(k)
        if _check(k, have) is None:
            if have is not None:
                log.warning('%s was %r, which it cannot use; put back to %r',
                            k, have, default)
            defaults.setObject_forKey_(default, k)
            wrote = True
    for k in STALE:
        if defaults.objectForKey_(k) is not None:
            # the value is no use: a step of 100 cm is not a share of 100 per cent
            log.info('%s is from before the upgrade retune; removing it', k)
            defaults.removeObjectForKey_(k)
            wrote = True
    return wrote


def _defaults(defaults):
    if defaults is None:
        from ..platform.defaults import UserDefaults
        defaults = UserDefaults.standardUserDefaults()
    return defaults


def setting(k, defaults=None):
    """One of the five settings, or its default when the save has none it can use."""
    good = _check(k, _defaults(defaults).objectForKey_(k))
    return SETTINGS[k] if good is None else good


def level(name, defaults=None):
    """The weapon's level, counted only up to its cap (tsatria03, 2026-10-06: "Count only
    up to the cap").  A level edited past the cap stays in the save as written, so raising
    the cap later lets it count again."""
    d = _defaults(defaults)
    good = _usable(d.objectForKey_(level_key(name)))
    return min(0 if good is None else good, max_level(name, d))


def max_level(name, defaults=None):
    good = _usable(_defaults(defaults).objectForKey_(max_key(name)))
    return MAX_LEVEL if good is None else good


def _half_up(x):
    return min(CEILING, int(math.floor(x + 0.5)))


def total(base, share, n, unit=1):
    """What n levels add to a stat of ``base``, each adding ``share`` per cent of it,
    rounded half up to a multiple of ``unit``.  At the default 15 per cent, level 10 is
    two and a half times the stat."""
    if n <= 0 or base == 0 or share == 0:
        return 0
    try:
        return min(CEILING, _half_up(base * share / 100.0 * n / unit) * unit)
    except OverflowError:
        return CEILING


def added(name, stat, defaults=None, at=None):
    """What the weapon's level (or level ``at``) adds to one of its stats; 0 for a stat
    it has none of (the grenade's and the blades' ammo) or the price.  The share is of
    the save's own number, so a stat edited there scales with it."""
    if stat not in SHARES or REAL[name][STATS.index(stat)] is None:
        return 0
    d = _defaults(defaults)
    n = level(name, d) if at is None else at
    return total(value(name, stat, d), setting(SHARES[stat], d), n,
                 ROUNDING.get(stat, 1))


def price(n, defaults=None):
    """What reaching level n costs."""
    d = _defaults(defaults)
    try:
        return _half_up(setting(START_PRICE, d) * setting(PRICE_GROWTH, d) ** (n - 1))
    except OverflowError:
        return CEILING


def upgrade(name, app, defaults=None):
    """Raise the weapon one level, paying from ``app.haveGold``.  Returns 'max' at the
    cap, 'gold' when there is too little gold, or the new level."""
    d = _defaults(defaults)
    n = level(name, d)
    if n >= max_level(name, d):
        return 'max'
    cost = price(n + 1, d)
    if app.haveGold < cost:
        return 'gold'
    app.haveGold -= cost
    d.setObject_forKey_('%d' % app.haveGold, 'GOLD')
    d.setInteger_forKey_(n + 1, level_key(name))
    d.synchronize()
    return n + 1
