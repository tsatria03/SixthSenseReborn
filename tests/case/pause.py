"""The pause and result panel: the rows, the dispatch table and the three buttons.

Everything here is checked against ``-[Stage_1_E selectTapPointSoundStart]`` (0x30168),
``-[Stage_1_E tapCount]`` (0x2fec8) and the four action methods behind them.
"""
from __future__ import annotations

import os
import plistlib
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import _scratch_save                                             # noqa: E402,F401  never the real save

from sixthsense import paths                                    # noqa: E402
from sixthsense.game import stage_1_e as S1E                    # noqa: E402
from sixthsense.game.app_delegate import AppDelegate            # noqa: E402
from sixthsense.game.stage_1_e import Stage_1_E                 # noqa: E402
from sixthsense.platform.defaults import UserDefaults           # noqa: E402
from sixthsense.platform import runloop                         # noqa: E402
from sixthsense.platform.runloop import RunLoop                 # noqa: E402


def _new_stage():
    S1E.LOADING_SECONDS = 0.0
    d = UserDefaults.standardUserDefaults()
    d.setObject_forKey_('1', 'TUTORIAL')
    d.removeObjectForKey_('TOPSCORE')
    d.removeObjectForKey_('TOPSCOREWEEK')
    d.removeObjectForKey_('NOWRANK')
    d.synchronize()
    app = AppDelegate.shared()
    if app.playback is None:
        app.didFinishLaunching()
    RunLoop.main().reset()
    st = Stage_1_E()
    st.viewDidLoad()
    RunLoop.main().pump()                       # fire the (zeroed) loading delay
    return app, st


def test_the_rows_are_the_bands_of_the_panel():
    """0x308b6..0x311ec, top to bottom: header, the five readouts, top score, then the
    three buttons.  The rank (9) is left out: its ranking server is gone."""
    assert Stage_1_E.PAUSE_ROWS == (1, 2, 3, 4, 5, 10, 6, 7, 8)
    sl = plistlib.load(open(paths.path_for_resource('SoundList', 'plist'), 'rb'))
    for sound in (229, 223, 226, 354):
        assert paths.path_for_resource(sl[sound], 'wav'), sound


def test_the_header_and_the_first_button_follow_the_state():
    """0x308e4 and 0x30efc: the two rows whose label depends on gameState, now spoken
    through the screen reader (2026-10-05)."""
    _app, st = _new_stage()
    st.speech = _Recorder()
    try:
        st.gameState = 1
        st.pause_select(1)
        assert st.speech.said[-1] == 'Paused'
        st.pause_select(6)
        assert st.speech.said[-1] == 'Continue, Button'
        st.gameState = 2
        st.pause_select(1)
        assert st.speech.said[-1] == 'Mission success'
        st.pause_select(6)
        assert st.speech.said[-1] == 'Next stage, Button'
        st.gameState = 3
        st.pause_select(1)
        assert st.speech.said[-1] == 'Game over'
    finally:
        st.teardown()


def test_there_is_no_continue_row_after_a_death():
    """0x30efe: gameState 3 leaves row 6 before it speaks."""
    _app, st = _new_stage()
    try:
        st.gameState = 1
        assert 6 in st.pause_rows()
        st.gameState = 3
        assert 6 not in st.pause_rows()
        assert st.pause_rows() == (1, 2, 3, 4, 5, 10, 7, 8)
    finally:
        st.teardown()


def test_up_and_down_walk_the_rows_and_wrap():
    _app, st = _new_stage()
    try:
        st.gameState = 1
        seen = [st.pause_move(1) for _ in range(len(Stage_1_E.PAUSE_ROWS))]
        assert seen == list(Stage_1_E.PAUSE_ROWS), seen
        st.selectMenu = 1
        assert st.pause_move(-1) == 8, 'moving up off the top did not wrap'
    finally:
        st.teardown()


def test_home_end_left_and_right_walk_the_panel():
    """Home and End go to the panel's first row and its last, and Left and Right to the
    previous row and the next."""
    from sixthsense.ui.input import Input

    class _Pygame:
        KEYDOWN, KEYUP, QUIT = 1, 2, 3

        class key:
            @staticmethod
            def name(k):
                return k

    class _Key:
        type = _Pygame.KEYDOWN

        def __init__(self, name):
            self.key = name

    app, st = _new_stage()
    said = []
    st._say = said.append                   # never the real screen reader
    try:
        st.gameState = 1
        rows = st.pause_rows()
        keys = Input(st)
        keys.handle(_Key('end'), _Pygame)
        assert st.selectMenu == rows[-1], 'End went to row %d' % st.selectMenu
        assert said, 'End did not read the row'
        keys.handle(_Key('home'), _Pygame)
        assert st.selectMenu == rows[0], 'Home went to row %d' % st.selectMenu
        keys.handle(_Key('right'), _Pygame)
        assert st.selectMenu == rows[1], 'Right went to row %d' % st.selectMenu
        keys.handle(_Key('right'), _Pygame)
        keys.handle(_Key('left'), _Pygame)
        assert st.selectMenu == rows[1], 'Left went to row %d' % st.selectMenu
    finally:
        st.teardown()


def test_selecting_a_readout_speaks_label_and_number_together():
    """The original played a row's label and read its number 2 s behind it; the port
    says both as one line and queues no reader."""
    _app, st = _new_stage()
    st.speech = _Recorder()
    loop = RunLoop.main()
    try:
        st.gameState = 2
        st.gamePlayer.killMonsterCount = 7
        st.pause_select(2)
        assert st.speech.said[-1] == 'Number of killed zombies, 7'
        assert not loop._performs, 'something was queued behind the row'
    finally:
        st.teardown()


def test_the_score_row_reads_the_score_aloud():
    """Landing on the score row says "Score, " and the whole number, and working the
    score out anywhere else says nothing."""
    _app, st = _new_stage()
    st.speech = _Recorder()
    try:
        st.gameState = 2
        p = st.gamePlayer
        p.killMonster1count, p.killMonster9count = 2, 1        # 300 + 300
        assert st.score_now() == 600 and st.speech.said == [], 'working it out spoke'
        st.pause_select(4)
        assert st.speech.said == ['Score, 600'], st.speech.said
    finally:
        st.teardown()


def test_choosing_a_result_row_rereads_that_row():
    """The original's ``tbb`` at 0x2ff32 (04 25 61 30 3b 4b 51 57) left row 3 silent,
    had row 4 read the headshots and could not reach the top score.  The port rereads
    the row chosen."""
    _app, st = _new_stage()
    st.speech = _Recorder()
    try:
        st.gameState = 2
        p = st.gamePlayer
        p.killMonsterCount, p.HeadShotCount = 5, 2
        p.killMonster1count = 4
        score = st.score_now()
        d = UserDefaults.standardUserDefaults()
        d.setObject_forKey_('9000', 'TOPSCORE')
        for row, text in ((2, 'Number of killed zombies, 5'), (3, 'Headshots, 2'),
                          (4, 'Score, %s' % S1E.whole(score)), (10, 'Top score, 9,000')):
            st.selectMenu = row
            st.pause_activate()
            assert st.speech.said[-1] == text, 'row %d said %r' % (row, st.speech.said[-1])
    finally:
        UserDefaults.standardUserDefaults().removeObjectForKey_('TOPSCORE')
        st.teardown()


def test_choosing_the_first_row_says_its_own_state():
    """Row 1 is "paused", "mission success" or "game over" by the state; the original
    replayed 229, "paused", whatever the state."""
    _app, st = _new_stage()
    st.speech = _Recorder()
    try:
        for state, text in ((1, 'Paused'), (2, 'Mission success'), (3, 'Game over')):
            st.gameState = state
            st.selectMenu = 1
            st.pause_activate()
            assert st.speech.said[-1] == text, 'state %d said %r' % (state, st.speech.said)
    finally:
        st.teardown()


def test_pausing_says_paused_half_a_second_after_the_click():
    """0x34710..0x34732: StopPlayAction: sends spaekMenu 0.5 s later, which now says
    "Paused." through the screen reader."""
    _app, st = _new_stage()
    st.speech = _Recorder()
    try:
        start = runloop.clock()
        assert st.StopPlayAction_() is True
        assert 'Paused.' not in st.speech.said
        RunLoop.main().pump(now=start + S1E.PAUSED_VOICE_DELAY - 0.1)
        assert 'Paused.' not in st.speech.said, 'paused came before half a second'
        RunLoop.main().pump(now=start + S1E.PAUSED_VOICE_DELAY + 0.1)
        assert st.speech.said[-1] == 'Paused.', st.speech.said
    finally:
        st.teardown()


def test_pausing_works_again_after_continue():
    """bStop is set at 0x33e48, and continueAction: clears it at 0x33960 (a
    conditional store the listings drop), so the game pauses as often as you like.
    Until continue, a second press does nothing."""
    _app, st = _new_stage()
    try:
        for _ in range(3):
            assert st.StopPlayAction_() is True, 'the pause did not come up'
            assert st.gameState == 1 and st.bStop is True
            assert st.MotionSamplingTimer is None, 'the walk timer kept running'
            assert st.walkXFlag is True and st.brearhFlag is True
            assert st.StopPlayAction_() is False, 'paused over its own panel'
            assert st.continueAction_() is True
            assert st.gameState == 0 and st.bStop is False
            assert st.MotionSamplingTimer is not None, 'the walk did not come back'
    finally:
        st.teardown()


def test_restart_clears_the_pause_too():
    """gameReplayAction: clears bStop at 0x3310c."""
    app, st = _new_stage()
    try:
        st.StopPlayAction_()
        st.gameReplayAction_()
        assert st.bStop is False
    finally:
        st.teardown()


def test_continue_puts_the_walk_back():
    _app, st = _new_stage()
    try:
        st.StopPlayAction_()
        assert st.continueAction_() is True
        assert st.gameState == 0
        assert st.walkXFlag is False and st.brearhFlag is False
        assert st.MotionSamplingTimer is not None, 'the walk timer did not come back'
        st.gameState = 2
        assert st.continueAction_() is False, 'it resumed from the result panel'
    finally:
        st.teardown()


def test_pausing_pauses_the_ambience_and_the_music_and_continue_carries_them_on():
    """DIVERGENCE: the original's pause leaves both players running and continue
    plays both again as notes over them.  Here each pauses on its own player and
    carries on there, and the music comes back only if it was playing."""
    app, st = _new_stage()
    pb = app.playback
    try:
        amb_path = pb.ambPlayer.path
        pb.startBGPlayer_type_soundGain_Loop_('bgm_cave', 'wav', 0.02, True)
        music_path = pb.bgPlayer.path
        assert pb.ambPlayer.playing and pb.bgPlayer.playing
        st.StopPlayAction_()
        assert not pb.ambPlayer.playing, 'the ambience plays on under the panel'
        assert not pb.bgPlayer.playing, 'the music plays on under the panel'
        st.continueAction_()
        assert pb.ambPlayer.playing and pb.ambPlayer.path == amb_path, \
            'the ambience did not come back on its own player'
        assert pb.bgPlayer.playing and pb.bgPlayer.path == music_path, \
            'the music did not come back on its own player'

        pb.backgroundSoundStop()                 # a section's quiet stretch
        st.StopPlayAction_()
        st.continueAction_()
        assert pb.ambPlayer.playing, 'the ambience did not come back'
        assert not pb.bgPlayer.playing, 'continue started music that was not playing'
    finally:
        st.teardown()

def _walk_timers(st):
    return [t for t in RunLoop.main()._timers
            if t.target is st and t.selector == 'MainControl' and t.isValid()]


def _past_the_level_change():
    RunLoop.main().pump(now=runloop.clock() + S1E.LEVEL_CHANGE_SECONDS + 0.5)


def test_pausing_while_the_level_changes_holds_it():
    """DIVERGENCE: the original's ChangeLevel: fires under the panel and starts the
    walk there, and continue adds a second walk timer. Here the pause holds it, and
    continue gives it its wait again."""
    _app, st = _new_stage()
    try:
        st._level_transition()
        gain = st.monsterHPGain
        assert st.StopPlayAction_() is True
        _past_the_level_change()
        assert st.monsterHPGain == gain, 'the level changed under the pause panel'
        assert not _walk_timers(st), 'the walk started under the pause panel'
        assert st.continueAction_() is True
        assert not _walk_timers(st), 'continue walked before the level changed'
        _past_the_level_change()
        assert st.monsterHPGain == gain * 1.5, 'the level never changed after continue'
        assert st.levelChanging is False
        assert len(_walk_timers(st)) == 1, 'more than one walk timer'
    finally:
        st.teardown()


def test_restarting_while_the_level_changes_walks_at_one_speed():
    _app, st = _new_stage()
    try:
        st._level_transition()
        st.StopPlayAction_()
        assert st.gameReplayAction_() is True
        _past_the_level_change()
        assert st.LVUP == 1 and st.monsterHPGain == 1.0, 'the old level change landed'
        assert st.levelChanging is False
        assert len(_walk_timers(st)) == 1, 'restart left two walk timers'
    finally:
        st.teardown()

def test_restart_is_free_and_resets_the_run():
    app, st = _new_stage()
    try:
        st.gamePlayer.killMonsterCount = 9
        st.gamePlayer.HeadShotCount = 4
        st.gamePlayer.playerYplot = 500
        st.gamePlayer.HP = 1
        st.StopPlayAction_()
        assert st.gameReplayAction_() is True
        assert not hasattr(app, 'Coin'), 'a coin was counted'
        assert st.gamePlayer.HP == 3
        assert st.gamePlayer.playerYplot == 680 and st.gamePlayer.playerXplot == 20
        assert st.gamePlayer.killMonsterCount == 0
        assert st.gamePlayer.HeadShotCount == 0
        assert st.LVUP == 1 and st.monsterHPGain == 1.0
        assert st.MonsterBuffer == []
        assert st.gameState == 0 and st.running is True
    finally:
        st.teardown()


def test_restart_always_works_however_many_times():
    app, st = _new_stage()
    try:
        for n in range(6):
            st.StopPlayAction_()
            assert st.gameReplayAction_() is True, 'restart %d was refused' % n
            assert st.gameState == 0
    finally:
        st.teardown()


def test_the_main_menu_button_ends_the_run():
    _app, st = _new_stage()
    try:
        st.StopPlayAction_()
        assert st.GameEndAction_() is True
        assert st.running is False
        assert st.MonsterBuffer == []
        assert st.MotionSamplingTimer is None
    finally:
        st.teardown()


def test_gold_is_fifteen_a_kill_and_five_a_headshot():
    """0x3c616's shape, kills and headshots only - every per-kind tally the method reads
    first is discarded - with its 12 and 2 raised to the save's GOLD_PER_KILL and
    GOLD_PER_HEADSHOT, 15 and 5 by default (2026-10-05)."""
    _app, st = _new_stage()
    try:
        p = st.gamePlayer
        p.killMonsterCount, p.HeadShotCount = 10, 3
        p.killMonster9count = 100          # dead weight in the original too
        assert st.ObtainedGold() == 15 * 10 + 5 * 3
        st._fill_result_labels()
        assert st.GoldLabel == '165'
    finally:
        st.teardown()


def test_an_edited_gold_rate_changes_what_a_game_pays():
    app, st = _new_stage()
    d = UserDefaults.standardUserDefaults()
    kill, head = d.objectForKey_('GOLD_PER_KILL'), d.objectForKey_('GOLD_PER_HEADSHOT')
    try:
        d.setObject_forKey_(100, 'GOLD_PER_KILL')
        d.setObject_forKey_(0, 'GOLD_PER_HEADSHOT')
        p = st.gamePlayer
        p.killMonsterCount, p.HeadShotCount = 4, 2
        before = app.haveGold
        st.missionFailTell_()
        assert app.haveGold == before + 400, (before, app.haveGold)
        assert d.intForKey_('GOLD') == app.haveGold
    finally:
        d.setObject_forKey_(kill, 'GOLD_PER_KILL')
        d.setObject_forKey_(head, 'GOLD_PER_HEADSHOT')
        st.teardown()


def test_a_death_shows_the_panel_eleven_seconds_later():
    """0x3bd2c stores 11.0, and missionFailTell: is what sets gameState 3."""
    _app, st = _new_stage()
    loop = RunLoop.main()
    try:
        st.playerDie_()
        assert st.gameState == 0, 'the panel went up immediately'
        assert st.missionCompletSounding is True
        q = [p for _d, _s, p in loop._performs
             if p.selector == 'missionFailTell_']
        assert q, 'missionFailTell: was not queued'
        assert abs((q[0].due - runloop.clock()) - 11.0) < 0.5, 'not an 11 s wait'
        st.missionFailTell_()
        assert st.gameState == 3
        assert st.bStop is True, 'the panel cannot take a button press'
        assert st.missionCompletSounding is False
    finally:
        st.teardown()


def _grabbed(st, approach=0.5):
    """A zombie that has just taken hold of the player, with ``approach`` seconds to shake
    free; returns it."""
    st.MonsterInit_(71)
    g = st.MonsterBuffer[0]
    g.shakeMonsterApproachTime = approach
    g.monsterRange = 10.0
    st.MonsterAttPlayer()
    assert st.isShake, 'the zombie did not grab'
    return g


def test_a_grab_waits_while_the_game_is_paused_and_lands_after_continue():
    """The grab's 0.1 s poll and its landing ran on under the panel, so a zombie that had
    grabbed you took a heart while the game was paused.  The pause holds the grab and
    continue gives back the time that was left."""
    _app, st = _new_stage()
    try:
        g = _grabbed(st)
        hp0 = st.gamePlayer.HP
        start = runloop.clock()
        assert st.StopPlayAction_() is True
        RunLoop.main().pump(now=start + 10.0)
        assert st.gamePlayer.HP == hp0, 'the grab took a heart under the pause'
        assert st.isShake and g in st.MonsterBuffer, 'the grab let go under the pause'
        assert st.continueAction_() is True
        RunLoop.main().pump()
        assert st.gamePlayer.HP == hp0, 'the grab landed at once instead of giving the time back'
        RunLoop.main().pump(now=runloop.clock() + 1.5)
        assert st.gamePlayer.HP == hp0 - 1 and not st.isShake, 'the grab never landed'
    finally:
        st.teardown()


def test_a_grab_can_still_be_shaken_off_after_continue():
    _app, st = _new_stage()
    try:
        g = _grabbed(st, approach=5.0)
        assert st.StopPlayAction_() is True
        assert st.continueAction_() is True
        st.shakeFlag = 0                    # the shakes the player needed, done
        RunLoop.main().pump(now=runloop.clock() + 0.5)
        assert not st.isShake and g not in st.MonsterBuffer, 'the shake did not free the player'
        assert st.gamePlayer.HP == 3
    finally:
        st.teardown()


def test_a_grab_does_not_carry_on_into_a_restarted_game():
    """Restarting from the panel left the grab's timers running, so the old grab landed on
    the new game."""
    _app, st = _new_stage()
    try:
        _grabbed(st)
        start = runloop.clock()
        assert st.StopPlayAction_() is True
        assert st.gameReplayAction_() is True
        assert not st.isShake
        st.MonsterInit_(1)                  # a zombie of the new game, first in the list
        fresh = st.MonsterBuffer[0]
        RunLoop.main().pump(now=start + 30.0)
        assert st.gamePlayer.HP == 3, 'the old grab took a heart in the new game'
        assert not st.isShake
        assert fresh in st.MonsterBuffer, 'the old grab landed on a zombie of the new game'
        # and pausing and continuing the new game does not bring it back
        assert st.StopPlayAction_() is True
        assert st.continueAction_() is True
        RunLoop.main().pump(now=runloop.clock() + 30.0)
        assert st.gamePlayer.HP == 3 and not st.isShake
    finally:
        st.teardown()


def _die_while_paused(st):
    """Take the player's last heart so the stage notices it, then pause in the 1.3 s before
    the death is carried out; returns the time the pause was made."""
    st.gamePlayer.HP = 0
    st.walkXFlag = False
    st.MainControl()
    assert st.DieFlag, 'the stage did not notice the death'
    assert st.StopPlayAction_() is True, 'the game could not be paused as the player died'
    assert st.gameState == 1
    return runloop.clock()


def test_pausing_just_before_you_die_and_restarting_does_not_end_the_new_game():
    """Pausing in the 1.3 s before the death was carried out left it queued, so it ran
    after a restart, played the end music and 11 s later put the game over panel over
    the new game."""
    _app, st = _new_stage()
    st.speech = _Recorder()
    try:
        start = _die_while_paused(st)
        assert st.gameReplayAction_() is True
        assert st.DieFlag is False
        RunLoop.main().pump(now=start + 30.0)
        assert st.gameState == 0, 'the old death put the panel over the new game'
        assert st.missionCompletSounding is False, 'the old death started the end music'
        assert 'Game over.' not in st.speech.said, st.speech.said
        assert st.gamePlayer.HP == 3
        # ...and the held death is gone for good: pausing and continuing the new game
        # must not bring it back
        assert st.StopPlayAction_() is True
        assert st.continueAction_() is True
        RunLoop.main().pump(now=start + 60.0)
        assert st.gameState == 0 and st.missionCompletSounding is False,             'the old death came back after a pause and continue'
    finally:
        st.teardown()


def test_pausing_just_before_you_die_and_continuing_still_ends_the_game():
    """The pause holds the death, and continuing lets it go on, so the game is not won by
    pausing at the last moment."""
    _app, st = _new_stage()
    st.speech = _Recorder()
    try:
        start = _die_while_paused(st)
        RunLoop.main().pump(now=start + 30.0)
        assert st.gameState == 1 and 'Game over.' not in st.speech.said,             'the death went ahead under the pause'
        assert st.continueAction_() is True
        RunLoop.main().pump(now=start + 30.0 + 1.3 + 11.0 + 1.0)
        assert st.gameState == 3, 'continuing did not carry the death out'
    finally:
        st.teardown()


def test_a_run_that_beats_the_stored_best_saves_it():
    """0x34c56 / 0x34cc0 - TOPSCORE and TOPSCOREWEEK."""
    _app, st = _new_stage()
    d = UserDefaults.standardUserDefaults()
    try:
        st.gamePlayer.killMonster9count = 4          # 4 * 300 = 1200
        st.gamePlayer.killMonsterCount = 4
        st.SuccessOrFailMission()
        assert st.score == 1200, st.score
        assert d.intForKey_('TOPSCORE') == 1200
        assert d.intForKey_('TOPSCOREWEEK') == 1200
        assert st.TopScoreLabel == '1200'
        assert st.ScoreLabel == '1200'
        assert st.GoldLabel == '60'                  # 15 * 4 kills, no headshots
    finally:
        st.teardown()


def test_finishing_the_mission_banks_the_gold():
    app, st = _new_stage()
    try:
        before = app.haveGold
        st.gamePlayer.killMonsterCount = 3
        st.MissionSuccessTell()
        assert st.gameState == 2
        assert app.haveGold == before + 45           # 15 * 3 kills
        assert UserDefaults.standardUserDefaults().intForKey_('GOLD') == app.haveGold
        assert app.stage == 11, 'STAGE was not opened up'
    finally:
        st.teardown()


class _Recorder:
    def __init__(self):
        self.said = []

    def speak(self, text, interrupt=True):
        self.said.append(text)
        return True

    def stop(self):
        pass


def test_the_panel_speaks_its_rows():
    """PORT ADDITION: each row is read with its number, whole."""
    _app, st = _new_stage()
    st.speech = _Recorder()
    try:
        st.gamePlayer.killMonsterCount = 105
        st.gamePlayer.HeadShotCount = 3
        st.StopPlayAction_()
        st.pause_select(1)
        assert st.speech.said[-1] == 'Paused'
        st.pause_select(2)
        assert st.speech.said[-1] == 'Number of killed zombies, 105'
        st.pause_select(5)
        assert st.speech.said[-1] == 'Obtained gold, 1,590'
        st.pause_activate()
        assert st.speech.said[-1] == 'Obtained gold, 1,590', 'the row was not reread'
        st.pause_select(6)
        assert st.speech.said[-1] == 'Continue, Button'
        st.gameState = 3
        st.missionFailTell_()
        assert 'Game over.' in st.speech.said
    finally:
        st.teardown()


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
