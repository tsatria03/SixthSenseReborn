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


def _paused():
    st = _loaded(_new_stage())
    st.StopPlayAction_()
    assert st.gameState == 1 and st.bStop
    return st


def _choose(st, row):
    st.pause_select(row)
    return st.pause_activate()


def test_the_paused_panel_reads_resume_then_the_save_rows():
    """Continue is Resume on the panel, then Restart, Save, Save and quit and Main menu
    (tsatria03, 2026-10-07)."""
    st = _paused()
    try:
        rows = st.pause_rows()
        assert rows[-5:] == (6, 7, 11, 12, 8), rows
        said = []
        for row in rows[-5:]:
            st.pause_select(row)
            said.append(st.speech.said[-1])
        assert said == ['Resume, Button', 'Restart, Button', 'Save, Button',
                        'Save and quit, Button', 'Main menu, Button'], said
    finally:
        st.teardown()


def test_there_is_nothing_to_save_after_the_game_ends_or_while_a_death_is_held():
    st = _paused()
    try:
        for state in (2, 3):
            st.gameState = state
            assert not ({11, 12} & set(st.pause_rows())), state
        st.gameState = 1
        st.DieFlag = True
        assert not ({11, 12} & set(st.pause_rows())), 'saving a death'
        st.DieFlag = False
        assert {11, 12} <= set(st.pause_rows())
    finally:
        st.teardown()


def test_nothing_is_saved_in_the_tutorial_or_the_weapon_test_range():
    from sixthsense.game.stage_1_test import Stage_1_TEST
    from sixthsense.game.stage_tutorial import Stage_Tutorial
    tutorial = Stage_Tutorial()
    assert not tutorial.can_save, 'a lesson can be saved'
    tutorial.real_game = True
    assert tutorial.can_save, 'the first real game after the lessons cannot be saved'
    assert not Stage_1_TEST.can_save


def test_save_saves_says_so_and_carries_on_playing():
    saved_game.delete()
    st = _paused()
    try:
        st.gamePlayer.playerYplot = 450
        _choose(st, 11)
        assert saved_game.exists() and saved_game.read()['section'] == 3
        assert st.ownsSave
        assert st.gameState == 0 and not st.bStop, 'the game did not carry on'
        assert st.speech.said[-1] == 'Game saved.', st.speech.said
        assert st.running
    finally:
        st.teardown()
        saved_game.delete()


def test_save_and_quit_saves_and_the_menu_says_so_first():
    saved_game.delete()
    st = _paused()
    try:
        _choose(st, 12)
        assert saved_game.exists() and not st.running, 'it did not save and quit'
        assert AppDelegate.shared().menuNotice == 'Game saved.'
    finally:
        st.teardown()
    m = _menu()
    try:
        assert m.speech.said[0] == 'Game saved. Sixth Sense Reborn: The Afterlife', \
            m.speech.said
        assert AppDelegate.shared().menuNotice == '', 'the notice was said twice'
        assert 'continue' in [r[2] for r in m.rows()]
    finally:
        m.teardown()
        saved_game.delete()


def test_main_menu_leaves_an_older_save_alone():
    saved_game.write(_a_save(level=2))
    st = _paused()
    try:
        _choose(st, 8)
        assert not st.running
        assert saved_game.read()['level'] == 2, 'Main menu saved or deleted'
    finally:
        st.teardown()
        saved_game.delete()


def test_a_game_that_saved_deletes_its_save_when_it_is_over():
    saved_game.write(_a_save(level=2))           # an older game's
    st = _paused()
    try:
        _choose(st, 11)                          # this game's own replaces it
        assert saved_game.read()['level'] == 1
        st.missionFailTell_()
        assert not saved_game.exists()
    finally:
        st.teardown()
        saved_game.delete()


def test_l_says_the_level_and_section_and_can_be_rebound():
    from sixthsense.platform import keymap
    assert keymap.DEFAULTS['location'] == [('l',)]
    assert keymap.LABELS['location'] == 'Say the level and section'
    assert 'location' not in keymap.DEBUG_IDS, 'L would be a debug key'
    st = _loaded(_new_stage())
    try:
        for row, words in ((680, 'Level 1, section 1 of 8'), (450, 'Level 1, section 3 of 8'),
                           (34, 'Level 1, section 8 of 8')):
            st.gamePlayer.playerYplot = row
            assert st.location_text() == words, (row, st.location_text())
        st.LVUP = 4
        st.gamePlayer.playerYplot = 99
        assert st.location_text() == 'Level 4, section 7 of 8'
        st.levelChanging = True
        assert st.location_text() == 'Level 4, section 1 of 8', 'the next level'
        st.levelChanging = False
        from sixthsense.ui.input import Input
        Input(st).perform('location')
        assert st.speech.said[-1] == 'Level 4, section 7 of 8', st.speech.said
    finally:
        st.teardown()


def test_l_has_no_level_to_report_in_the_tutorial_or_the_test_range():
    from sixthsense.game.stage_1_test import Stage_1_TEST
    from sixthsense.game.stage_tutorial import Stage_Tutorial
    tutorial = Stage_Tutorial()
    assert tutorial.location_text() == 'No level to report.'
    assert Stage_1_TEST.location_text(Stage_1_TEST.__new__(Stage_1_TEST)) == \
        'No level to report.'


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
