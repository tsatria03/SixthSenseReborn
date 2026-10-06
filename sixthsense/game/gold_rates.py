"""PORT ADDITION: how much gold a game pays, kept in save.json where it can be edited.

The original pays ``12 * kills + 2 * headshots`` when a game ends (``Stage_1_E.
ObtainedGold``, 0x3c616).  Since 2026-10-05 the two rates are save keys, raised a little
so weapons are easier to get (tsatria03; aidocks/completed/gold_rates_plan.md):

    GOLD_PER_KILL      gold for every zombie killed, 15 (the original's 12)
    GOLD_PER_HEADSHOT  gold for every headshot hit, killing or not, 5 (the original's 2)

``fill`` runs on every start (``AppDelegate.didFinishLaunching``): a missing rate, or one
that is not a whole number of 0 or more, is put back to its default.
"""
from __future__ import annotations

import logging

from .weapon_stats import _usable

log = logging.getLogger('gold_rates')

PER_KILL = 'GOLD_PER_KILL'
PER_HEADSHOT = 'GOLD_PER_HEADSHOT'
DEFAULTS = {PER_KILL: 15, PER_HEADSHOT: 5}


def fill(defaults):
    """Put each rate that is missing or unusable back to its default.  True when anything
    was written."""
    wrote = False
    for key, default in DEFAULTS.items():
        have = defaults.objectForKey_(key)
        good = _usable(have)
        if good is None:
            if have is not None:
                log.warning('%s was %r, which is not a whole number of 0 or more; '
                            'put back to %d', key, have, default)
            defaults.setInteger_forKey_(default, key)
            wrote = True
        elif type(have) is not int:
            defaults.setInteger_forKey_(good, key)        # 15.0 is written back as 15
            wrote = True
    return wrote


def rate(key, defaults=None):
    """The rate the game pays: the save's, or the default when the save has none it can
    use."""
    if defaults is None:
        from ..platform.defaults import UserDefaults
        defaults = UserDefaults.standardUserDefaults()
    good = _usable(defaults.objectForKey_(key))
    return DEFAULTS[key] if good is None else good


def gold_for(kills, headshots, defaults=None):
    """What a game with these kills and headshots pays."""
    return (kills * rate(PER_KILL, defaults)
            + headshots * rate(PER_HEADSHOT, defaults))
