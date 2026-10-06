"""PORT ADDITION: the order the weapons come in, which you set yourself.

tunmi13productions, 2026-10-06 (aidocks/completed/weapon_order_plan.md).  The original has one
order and it is the slot number: ``-[Stage_1_E weaponInit]`` (0x35008) fills
``weaponSource[i]`` from ``WEAPON_FILES[i]``, and ``-[Stage_1_E gunChangeAction:]``
(0x35a08) walks ``w = (w + step) % 8``, stepping over whatever is not equipped.

``WEAPON_ORDER`` in save.json replaces that walk: a list of the eight slot numbers in
the order you want them.  Nothing else changes, because a slot number is still a slot
number -- ``gamePlayer.useWepon`` indexes ``weaponSource`` as it always did, and only
the order it is walked in comes from here.

All eight are kept, equipped or not, so a weapon you unequip keeps its place and comes
back to it when you equip it again.  ``equipped`` gives the order with the unequipped
left out, which is what the reorder screen lists and what a game cycles through.
"""
from __future__ import annotations

import logging

from .weapon_stats import NAMES

log = logging.getLogger('weapon_order')

KEY = 'WEAPON_ORDER'
#: The order out of the box: colt, shotgun, M4A1, AK47, MG80, Japanese sword, grenade,
#: knife.  That is the original's own cycle, turned round to begin at the colt, so a save
#: that has never touched this plays exactly as the original did: ``startWeapon``
#: (0x3572a) hands you the colt, and ``gunChangeAction:`` (0x35a08) then walks the slots
#: in their own order and comes round to the grenade and the knife last.  Slot order
#: itself would have started a game on the grenade, which has no magazine.
DEFAULT_ORDER = [2, 3, 4, 5, 6, 7, 0, 1]
#: the slots a save has to hold, every one exactly once
SLOTS = sorted(range(len(NAMES)))


def _usable(value):
    """``value`` as an order, or None when it is not one: it has to be every slot
    exactly once, in some order."""
    if not isinstance(value, (list, tuple)):
        return None
    order = []
    for slot in value:
        if isinstance(slot, bool) or not isinstance(slot, int):
            return None
        order.append(slot)
    return order if sorted(order) == SLOTS else None


def _defaults(defaults):
    if defaults is None:
        from ..platform.defaults import UserDefaults
        defaults = UserDefaults.standardUserDefaults()
    return defaults


def fill(defaults):
    """Write the order when it is missing or unusable.  True when it was written."""
    have = defaults.objectForKey_(KEY)
    if _usable(have) is not None:
        return False
    if have is not None:
        log.warning('%s was %r, which it cannot use; put back to %r',
                    KEY, have, DEFAULT_ORDER)
    defaults.setObject_forKey_(list(DEFAULT_ORDER), KEY)
    return True


def order(defaults=None):
    """The eight slots, in the player's order."""
    good = _usable(_defaults(defaults).objectForKey_(KEY))
    return list(DEFAULT_ORDER) if good is None else good


def equipped(app, defaults=None):
    """The player's order with the weapons that are not equipped left out: what the
    reorder screen lists, and what a game cycles through."""
    use = app.useWeapon
    return [slot for slot in order(defaults)
            if slot < len(use) and use[slot] == '1']


def first_equipped(app, defaults=None):
    """The slot a game starts you on: the first equipped weapon in your order, or None
    when nothing is equipped.

    DIVERGENCE: ``-[Stage_1_E startWeapon]`` (0x3572a) reads ``COLTUSE`` before anything
    else and hands you the colt whenever it is equipped.  Putting a weapon first is the
    point of the order, so the order decides (the dev, 2026-10-06).
    """
    carried = equipped(app, defaults)
    return carried[0] if carried else None


def move(slot, step, app, defaults=None):
    """Move ``slot`` one place up (``step`` -1) or down (1) among the equipped weapons,
    and save the new order.

    Returns the slot it swapped with, or None when it is already at that end.  An
    unequipped weapon between the two keeps its place in the saved order; only the two
    equipped ones trade.
    """
    d = _defaults(defaults)
    current = order(d)
    carried = equipped(app, d)
    if slot not in carried:
        return None
    at = carried.index(slot)
    to = at + step
    if to < 0 or to >= len(carried):
        return None
    other = carried[to]
    here, there = current.index(slot), current.index(other)
    current[here], current[there] = current[there], current[here]
    d.setObject_forKey_(current, KEY)
    d.synchronize()
    return other
