"""A saved game: saves/continue.json, the main menu's Continue row, and a game continued at
the start of the section it was saved in (aidocks/project_save_game_plan.md)."""
from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import _scratch_save                                             # noqa: E402,F401  never the real save

from sixthsense.game import debug                                # noqa: E402
from sixthsense.game import saved_game                           # noqa: E402
from sixthsense.game import stage_1_e as S1E                     # noqa: E402
from sixthsense.game.app_delegate import AppDelegate             # noqa: E402
from sixthsense.game.main_controller import MainController       # noqa: E402
from sixthsense.game.stage_1_e import Stage_1_E                  # noqa: E402
from sixthsense.platform.defaults import UserDefaults            # noqa: E402
from sixthsense.platform.runloop import RunLoop                  # noqa: E402

SECTIONS = [680, 601, 500, 400, 300, 200, 99, 34]


class _Recorder:
    def __init__(self):
        self.said = []

    def speak(self, text, interrupt=True):
        self.said.append(text)
        return True

    def stop(self):
        pass


def _new_stage():
    S1E.LOADING_SECONDS = 0.0
    d = UserDefaults.standardUserDefaults()
    d.setObject_forKey_('1', 'TUTORIAL')
    d.synchronize()
    app = AppDelegate.shared()
    if app.playback is None:
        app.didFinishLaunching()
    RunLoop.main().reset()
    st = Stage_1_E()
    st.speech = _Recorder()
    st.viewDidLoad()
    return st


def _loaded(st):
    RunLoop.main().pump()                       # fire the (zeroed) loading delay
    return st


def _menu():
    app = AppDelegate.shared()
    if app.playback is None:
        app.didFinishLaunching()
    RunLoop.main().reset()
    m = MainController(speech=_Recorder())
    m.viewDidLoad()
    return m


def _a_save(**over):
    data = {'level': 3, 'section': 5, 'area': 'forest', 'toughness': 2.25, 'hearts': 2,
            'weapon': 'shotgun', 'rounds': {'colt': 4, 'shotgun': 1},
            'tally': {'killMonsterCount': 40, 'HeadShotCount': 7,
                      'killMonster3count': 12},
            'girls': 4}
    data.update(over)
    return data


def test_every_level_has_eight_sections():
    """The rows whose action cell is 9 on the walk, read from game/a_CH1_E.txt: the
    dev's eight from debug mode, the last the boss's, before the alarm (29) and the boss
    (23)."""
    assert saved_game.section_rows() == SECTIONS
    assert SECTIONS[-1] > 29


def test_a_row_is_in_the_last_section_it_has_passed():
    rows = saved_game.section_rows()
    assert saved_game.section_of(680, rows) == 1
    assert saved_game.section_of(650, rows) == 1
    assert saved_game.section_of(601, rows) == 2
    assert saved_game.section_of(301, rows) == 4
    assert saved_game.section_of(300, rows) == 5
    assert saved_game.section_of(34, rows) == 8
    assert saved_game.section_of(23, rows) == 8


def test_debug_f2_finds_the_same_sections():
    st = _loaded(_new_stage())
    try:
        assert debug.sections(st) == SECTIONS
    finally:
        st.teardown()


def test_the_file_is_written_read_back_and_deleted():
    saved_game.delete()
    assert not saved_game.exists() and saved_game.read() is None
    saved_game.write(_a_save())
    assert saved_game.path().endswith(os.path.join('saves', 'continue.json'))
    assert saved_game.exists()
    assert saved_game.read() == _a_save()
    with open(saved_game.path(), encoding='utf-8') as f:
        assert list(json.load(f))[:3] == ['level', 'section', 'area'], 'not in its order'
    saved_game.write(_a_save(level=4))
    assert os.path.exists(saved_game.path() + '.bak'), 'the second write kept no backup'
    saved_game.delete()
    assert not os.path.exists(saved_game.path())
    assert not os.path.exists(saved_game.path() + '.bak'), 'the backup outlived the save'
    assert not saved_game.exists()


def test_a_save_that_makes_no_sense_is_no_save():
    for bad in ({}, _a_save(level=0), _a_save(area='moon'), _a_save(hearts=0),
                _a_save(weapon='laser'), _a_save(rounds=[]), _a_save(toughness='x')):
        saved_game.delete()
        saved_game.write(bad)
        assert saved_game.read() is None, bad
    saved_game.delete()


def test_a_damaged_save_is_kept_aside_and_the_backup_carries_on():
    saved_game.delete()
    saved_game.write(_a_save(level=2))
    saved_game.write(_a_save(level=3))           # level 2 is now the backup
    with open(saved_game.path(), 'w', encoding='utf-8') as f:
        f.write('{ not json')
    try:
        assert saved_game.read()['level'] == 2
        assert os.path.exists(saved_game.path() + '.damaged')
    finally:
        saved_game.delete()
        try:
            os.remove(saved_game.path() + '.damaged')
        except FileNotFoundError:
            pass


def test_continue_is_offered_only_with_a_saved_game():
    saved_game.delete()
    m = _menu()
    try:
        assert 'continue' not in [r[2] for r in m.rows()]
    finally:
        m.teardown()
    saved_game.write(_a_save())
    m = _menu()
    try:
        actions = [r[2] for r in m.rows()]
        assert actions[:3] == ['title', 'continue', 'start'], actions
        m.move(1)
        assert m.speech.said[-1] == 'Continue, Button', m.speech.said
        m.activate()
        assert m.next_screen == 'continue'
        m.next_screen = None
        m.move(1)
        m.activate()
        assert m.next_screen == 'stage', 'Game start did not start a fresh game'
        assert saved_game.exists(), 'Game start touched the save'
    finally:
        m.teardown()
        saved_game.delete()


def test_a_game_saved_part_way_continues_at_its_sections_start():
    st = _loaded(_new_stage())
    try:
        p = st.gamePlayer
        st.LVUP, st.gameMode, st.monsterHPGain = 4, 2, 1.5 ** 3
        p.playerYplot = 350                     # part way through section 4
        p.HP = 2
        p.killMonsterCount, p.HeadShotCount, p.killMonster7count = 33, 5, 9
        st.GirlMonsterNumber = 6
        colt = st.weaponSource[2]
        colt.BulletCount = 3
        p.useWepon = 2
        data = saved_game.snapshot(st)
    finally:
        st.teardown()
    assert data['level'] == 4 and data['section'] == 4 and data['area'] == 'forest'
    assert data['hearts'] == 2 and data['weapon'] == 'colt' and data['rounds']['colt'] == 3
    assert data['tally']['killMonsterCount'] == 33 and data['tally']['killMonster7count'] == 9
    saved_game.write(data)

    st = _new_stage()
    try:
        saved_game.resume(st, saved_game.read())
        _loaded(st)
        p = st.gamePlayer
        assert (st.LVUP, st.gameMode) == (4, 2)
        assert abs(st.monsterHPGain - 1.5 ** 3) < 1e-9
        assert p.playerYplot == SECTIONS[3], 'not at the start of section 4'
        assert p.HP == 2 and p.useWepon == 2 and st.weaponSource[2].BulletCount == 3
        assert (p.killMonsterCount, p.HeadShotCount, p.killMonster7count) == (33, 5, 9)
        assert st.GirlMonsterNumber == 6
        assert st.ownsSave and st.resumed
        assert st.MonsterBuffer == [], 'zombies came back with the save'
    finally:
        st.teardown()
        saved_game.delete()


def test_saved_while_the_level_changes_it_is_the_next_levels_start():
    """_level_transition has already raised the level and changed the area; ChangeLevel:
    has not yet made the zombies tougher."""
    st = _loaded(_new_stage())
    try:
        st.LVUP, st.gameMode, st.monsterHPGain = 3, 1, 1.5
        st.gamePlayer.playerYplot = 22
        st.levelChanging = True
        data = saved_game.snapshot(st)
        assert data['level'] == 3 and data['section'] == 1
        assert abs(data['toughness'] - 2.25) < 1e-9
    finally:
        st.levelChanging = False
        st.teardown()


def test_a_rounds_count_is_never_more_than_the_magazine():
    saved_game.write(_a_save(rounds={'colt': 9999}, weapon='colt'))
    st = _new_stage()
    try:
        saved_game.resume(st, saved_game.read())
        colt = st.weaponSource[2]
        assert colt.BulletCount == colt.ReloadGun()
    finally:
        st.teardown()
        saved_game.delete()


def test_only_its_own_game_over_deletes_the_save():
    saved_game.write(_a_save())
    st = _loaded(_new_stage())
    try:
        assert not st.ownsSave
        st.missionFailTell_()
        assert saved_game.exists(), "a fresh game's game over deleted an older save"
    finally:
        st.teardown()
    st = _new_stage()
    try:
        saved_game.resume(st, saved_game.read())
        _loaded(st)
        st.missionFailTell_()
        assert not saved_game.exists(), "the continued game's game over kept its save"
    finally:
        st.teardown()
        saved_game.delete()


def test_a_restart_is_a_fresh_game_that_leaves_the_save_alone():
    saved_game.write(_a_save())
    st = _new_stage()
    try:
        saved_game.resume(st, saved_game.read())
        _loaded(st)
        st.bStop = True
        st.gameReplayAction_()
        assert not st.ownsSave and not st.resumed
        st.missionFailTell_()
        assert saved_game.exists(), "the restarted game's game over deleted the save"
    finally:
        st.teardown()
        saved_game.delete()


if __name__ == '__main__':
    fns = [v for k, v in sorted(globals().items()) if k.startswith('test_')]
    bad = 0
    for fn in fns:
        try:
            fn()
            print('ok    %s' % fn.__name__)
        except Exception as e:
            bad += 1
            import traceback
            traceback.print_exc()
            print('FAIL  %s: %s' % (fn.__name__, e))
    print('%d/%d passed' % (len(fns) - bad, len(fns)))
    sys.exit(1 if bad else 0)
