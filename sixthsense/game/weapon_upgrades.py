"""PORT ADDITION: weapon upgrades, one level per weapon, every number in save.json.

tsatria03, 2026-10-05 (aidocks/completed/weapon_upgrades_plan.md).  Each weapon has a level,
``<W>_LEVEL``, from 0 up to its cap, ``<W>_MAX_LEVEL`` (10).  One upgrade button raises
it by one, and the level adds to the weapon's own stats (``weapon_stats.py``): damage,
ammo capacity and range all at once.  The grenade, the knife and the sword have no
magazine, so they gain damage and range only.

What a level adds grows: level 1 adds the step and each level after adds
``UPGRADE_GROWTH`` times the one before, so the total at level n is

    step * (growth ** n - 1) / (growth - 1)        (step * n when growth is 1)

rounded half up, with the steps ``UPGRADE_DAMAGE`` (10), ``UPGRADE_AMMO`` (10) and
``UPGRADE_RANGE`` (100 cm), and the growth 1.2.  Level n costs

    UPGRADE_START_PRICE * UPGRADE_PRICE_GROWTH ** (n - 1)

rounded half up, from 100 growing 1.2 times a level: 100, 120, 144, 173 ... 516, 2,596
to reach level 10.  The six settings are for all weapons at once; the level and the cap
are each weapon's.  ``fill`` writes them on every start where missing or unusable.
"""
from __future__ import annotations

import logging
import math

from .weapon_stats import NAMES, REAL, STATS, _usable, key

log = logging.getLogger('weapon_upgrades')

START_PRICE = 'UPGRADE_START_PRICE'
PRICE_GROWTH = 'UPGRADE_PRICE_GROWTH'
GROWTH = 'UPGRADE_GROWTH'
#: the stat each step raises, by its key
STEPS = {'damage': 'UPGRADE_DAMAGE', 'ammo_capacity': 'UPGRADE_AMMO',
         'range': 'UPGRADE_RANGE'}

#: the six settings for all weapons, and their defaults
SETTINGS = {START_PRICE: 100, PRICE_GROWTH: 1.2, STEPS['damage']: 10,
            STEPS['ammo_capacity']: 10, STEPS['range']: 100, GROWTH: 1.2}
#: the two that may be fractions
GROWTHS = (PRICE_GROWTH, GROWTH)
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
    return wrote


def _defaults(defaults):
    if defaults is None:
        from ..platform.defaults import UserDefaults
        defaults = UserDefaults.standardUserDefaults()
    return defaults


def setting(k, defaults=None):
    """One of the six settings, or its default when the save has none it can use."""
    good = _check(k, _defaults(defaults).objectForKey_(k))
    return SETTINGS[k] if good is None else good


def level(name, defaults=None):
    good = _usable(_defaults(defaults).objectForKey_(level_key(name)))
    return 0 if good is None else good


def max_level(name, defaults=None):
    good = _usable(_defaults(defaults).objectForKey_(max_key(name)))
    return MAX_LEVEL if good is None else good


def _half_up(x):
    return min(CEILING, int(math.floor(x + 0.5)))


def total(step, growth, n):
    """What n levels add, the first adding ``step`` and each after ``growth`` times the
    last, rounded half up."""
    if n <= 0 or step == 0:
        return 0
    try:
        if growth == 1:
            return _half_up(step * n)
        return _half_up(step * (growth ** n - 1) / (growth - 1))
    except OverflowError:
        return CEILING


def added(name, stat, defaults=None, at=None):
    """What the weapon's level (or level ``at``) adds to one of its stats; 0 for a stat
    it has none of (the grenade's and the blades' ammo) or the price."""
    if stat not in STEPS or REAL[name][STATS.index(stat)] is None:
        return 0
    d = _defaults(defaults)
    n = level(name, d) if at is None else at
    return total(setting(STEPS[stat], d), setting(GROWTH, d), n)


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
