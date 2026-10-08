"""PORT ADDITION: a game saved part way and continued later, in ``saves/continue.json``.

The original has no saving: a run lives in memory, and the pause panel's Main menu
(``-[Stage_1_E GameEndAction:]`` 0x32fe1) drops it.  tsatria03 decided every part of this on
2026-10-07 (aidocks/project_save_game_plan.md):

- The file is ``saves/continue.json``, beside save.json, and exists only while there is a
  game to continue, so whether it can be read is the whole test for the main menu's
  Continue row.  It is one object of its own, not loose ``UserDefaults`` keys, which
  defaults.py would send to save.json.  It is written the way the other save files are: a
  temporary file, then replaced, with a ``.bak``; a file that cannot be read is kept as
  ``.damaged`` and the game carries on from the ``.bak``.
- A game resumes at the start of the section it was saved in.  Every level is the same
  corridor of eight sections, each opening on a quiet stretch (action cell 9); the last is
  the boss's, which starts at row 34, before the alarm at 29 and the boss at 23, so
  continuing in it always brings the boss back.  The zombies on the field are not kept.
- What it holds: the level, the area, the zombies' toughness, the section, the hearts, the
  weapon in hand, each gun's rounds and the run's tally, from which the score and the gold
  are worked out.  Gold and grenades are not in it; both live in store/inventory.json.
- That game's game over deletes it, so the run's gold is paid once.
"""
from __future__ import annotations

import logging
import os

from .. import paths
from ..platform.defaults import SLOT_NAMES, _File
from .make_maps import MakeMaps
from .weapon_control import WEAPON_SLOTS

log = logging.getLogger('saved_game')

FILE = os.path.join('saves', 'continue.json')
#: The order the file lists its fields in.
ORDER = ('level', 'section', 'area', 'toughness', 'hearts', 'weapon', 'rounds', 'tally', 'girls')
#: ``gameMode``'s three areas, by the names the file uses.
AREAS = {1: 'cave', 2: 'forest', 3: 'rain'}
#: Each weapon slot by the name the file uses, as store/inventory.json does; 0 is the grenade.
SLOTS = SLOT_NAMES
#: The ``PlayerControl`` counts the file keeps, under the same names.
TALLY = ('killMonsterCount', 'HeadShotCount', 'gunEggCountAll', 'gunEggCountShot',
         'gunEggCout') + tuple('killMonster%dcount' % n for n in range(1, 12)) + (
             'killMonster5000count',)
#: Where the walk is: the corridor's column and the row every level starts on.
COLUMN = 20
START_ROW = 680
#: How much tougher each level's zombies are, ``ChangeLevel:`` 0x32314.
LEVEL_GAIN = 1.5

_rows = None


def path():
    return os.path.join(paths.user_dir(), FILE)


def section_rows(stage=None):
    """The rows each section of the corridor starts on, top of the corridor first: the rows
    on the walk whose action cell is 9, the quiet stretch that opens each one.  The last is
    the boss's.  ``stage`` is a loaded ``MakeMaps``; without one the map is read once."""
    global _rows
    if stage is None:
        if _rows is None:
            _rows = section_rows(_load_map())
        return list(_rows)
    return [y for y in range(START_ROW, 0, -1)
            if stage.movePlayActionState_PlotY_(COLUMN, y) == 9]


def _load_map():
    def read(name, ext=None):
        with open(paths.path_for_resource(name, ext), 'r', encoding='utf-8',
                  errors='replace') as f:
            return f.read()
    return MakeMaps().initWithMapGroundFileString_soundPosFileName_actionPosFileName_(
        read('g_CH1_E'), read('s_CH1_E', 'txt'), read('a_CH1_E', 'txt'))


def section_of(row, rows):
    """The section, 1 to len(rows), a walk at ``row`` is in: the last start it has passed."""
    passed = [i for i, start in enumerate(rows) if start >= row]
    return passed[-1] + 1 if passed else 1


# ------------------------------------------------------------------ the file
def exists():
    """Whether there is a game to continue."""
    return read() is not None


def read():
    """The saved game, checked, or None when there is none or it makes no sense."""
    if not os.path.exists(path()):
        return None
    data = _File(path()).d
    return data if _valid(data) else None


def _valid(data):
    try:
        return (int(data['level']) >= 1 and int(data['section']) >= 1
                and data['area'] in AREAS.values() and float(data['toughness']) > 0
                and int(data['hearts']) >= 1 and data['weapon'] in SLOTS
                and isinstance(data['rounds'], dict) and isinstance(data['tally'], dict))
    except (KeyError, TypeError, ValueError):
        return False


def write(data):
    f = _File(path(), ORDER)
    f.d = dict(data)
    f.write()


def delete():
    """No game to continue any more: the file and its backup both go."""
    for name in (path(), path() + '.bak'):
        try:
            os.remove(name)
        except FileNotFoundError:
            pass
        except OSError:
            log.exception('could not delete %s', name)


# --------------------------------------------------------------- the stage
def snapshot(st):
    """What ``st`` saves: its section's start, not the exact spot.  Saved while the next
    level is on its way (``_level_transition`` has raised the level and changed the area,
    and ``ChangeLevel:`` is still due), it is the start of that next level."""
    p = st.gamePlayer
    rows = section_rows(st.stage)
    toughness = st.monsterHPGain
    if getattr(st, 'levelChanging', False):
        section, toughness = 1, toughness * LEVEL_GAIN
    else:
        section = section_of(p.playerYplot, rows)
    rounds = {}
    for slot, weapon in enumerate(st.weaponSource[:WEAPON_SLOTS]):
        if weapon is not None and slot < len(SLOTS):
            rounds[SLOTS[slot]] = int(weapon.BulletCount)
    return {
        'level': int(st.LVUP),
        'section': section,
        'area': AREAS.get(st.gameMode, 'cave'),
        'toughness': toughness,
        'hearts': int(p.HP),
        'weapon': SLOTS[p.useWepon] if 0 <= p.useWepon < len(SLOTS) else 'colt',
        'rounds': rounds,
        'tally': {name: int(getattr(p, name, 0)) for name in TALLY},
        'girls': int(getattr(st, 'GirlMonsterNumber', 0)),
    }


def resume(st, data):
    """Put a stage that has just run ``viewDidLoad`` where ``data`` left off: before its
    map loads, so ``MapInitInBundle`` starts the saved area's ambience, and the walk's first
    step reads the section's own quiet cell, as walking there would."""
    p = st.gamePlayer
    rows = section_rows()
    section = min(int(data['section']), len(rows))
    st.LVUP = int(data['level'])
    st.gameMode = {name: mode for mode, name in AREAS.items()}[data['area']]
    st.monsterHPGain = float(data['toughness'])
    st.GirlMonsterNumber = int(data.get('girls', 0))
    p.HP = int(data['hearts'])
    p.playerYplot = rows[section - 1]
    for name in TALLY:
        try:
            setattr(p, name, max(0, int(data['tally'].get(name, 0))))
        except (TypeError, ValueError):
            pass
    for slot, name in enumerate(SLOTS):
        weapon = st.weaponSource[slot] if slot < len(st.weaponSource) else None
        if weapon is None or name not in data['rounds']:
            continue
        try:
            weapon.BulletCount = max(0, min(int(data['rounds'][name]), weapon.ReloadGun()))
        except (TypeError, ValueError):
            pass
    p.useWepon = SLOTS.index(data['weapon'])
    st.ownsSave = True
    st.resumed = True
    log.info('continued at level %d, section %d of %d', st.LVUP, section, len(rows))
