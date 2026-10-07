"""The ten tutorial beats, and the handoff into the real game.

A beat that sends in a zombie waits for Enter; ``_tutorial`` presses it for the test after a
short pause (``_AUTO``), so the whole run fits, unless it is given ``prompt=None``.
"""
from __future__ import annotations

import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import _scratch_save                                             # noqa: E402,F401  never the real save

from sixthsense.game import stage_1_e as S1E                     # noqa: E402
from sixthsense.game import stage_tutorial as T                  # noqa: E402
from sixthsense.game.app_delegate import AppDelegate             # noqa: E402
from sixthsense.game.stage_tutorial import BEAT_NAMES, Stage_Tutorial  # noqa: E402
from sixthsense.platform.defaults import UserDefaults            # noqa: E402
from sixthsense.platform.runloop import RunLoop                  # noqa: E402

LANE = {1: 180.0, 2: 123.0, 3: 90.0, 4: 57.0, 5: 0.0}
_REAL_BEATS = list(T.BEATS)
_REAL_LOADING_SECONDS = S1E.LOADING_SECONDS
_AUTO = [0.4]                  # seconds before Enter is pressed for a waiting beat; None: never

_real_beat = Stage_Tutorial.tutorial_beat


def _beat_then_enter(self, name, restart=False):
    _real_beat(self, name, restart)
    if _AUTO[0] and self.waiting:
        RunLoop.main().perform(self, 'tutorial_advance', None, _AUTO[0])


Stage_Tutorial.tutorial_beat = _beat_then_enter


def _tutorial(prompt=0.4, first_run=False):
    """A tutorial that goes on by itself ``prompt`` seconds after each wait, and TUTORIAL
    cleared as on a fresh install."""
    _AUTO[0] = prompt
    S1E.LOADING_SECONDS = 0.0
    d = UserDefaults.standardUserDefaults()
    d.setObject_forKey_('0', 'TUTORIAL')
    d.synchronize()
    app = AppDelegate.shared()
    if app.playback is None:
        app.didFinishLaunching()
    RunLoop.main().reset()
    st = Stage_Tutorial(first_run=first_run)
    st.viewDidLoad()
    RunLoop.main().pump()                      # fire the (zeroed) loading delay
    st.gamePlayer.useWepon = 6                 # MG80, 1600 cm - reaches a fresh spawn
    st.weaponSource[6].BulletCount = 50
    return st


def _restore():
    T.BEATS[:] = _REAL_BEATS
    S1E.LOADING_SECONDS = _REAL_LOADING_SECONDS


def _pump(loop, seconds, until=None):
    t0 = time.monotonic()
    while time.monotonic() - t0 < seconds:
        loop.pump()
        if until is not None and until():
            return True
        time.sleep(0.004)
    return False


def test_the_beats_are_the_original_ten():
    assert BEAT_NAMES == ['One', 'Two', 'Three', 'Four', 'Five', 'FiveHalf',
                          'Six', 'Seven', 'Eight', 'Nine']
    # the words said for each beat, which replaced the recordings 275..284 and 361
    # (2026-10-05); every beat has some
    prompts = {n: s for n, s, _sp in _REAL_BEATS}
    assert all(isinstance(t, str) and t for t in prompts.values()), prompts
    # what each beat sends in, from tutorialNSoundStop
    spawns = {n: sp for n, _s, sp in _REAL_BEATS}
    assert spawns == {'One': 1, 'Two': 2, 'Three': 3, 'Four': 4, 'Five': 5,
                      'FiveHalf': 63, 'Six': None, 'Seven': None, 'Eight': 73,
                      'Nine': None}


def test_the_tutorial_does_not_walk():
    """-[Stage_Tutorial MapInitInBundle] arms CheckTutorial, not MotionSamplingTimer."""
    st = _tutorial()
    try:
        assert st.isTutorial == 0
        assert st.MotionSamplingTimer is None, 'the tutorial started the walk timer'
        assert st.checkTutorialTimer is not None
        start = st.gamePlayer.playerYplot
        _pump(RunLoop.main(), 3.0)
        assert st.gamePlayer.playerYplot == start, 'the player walked during the tutorial'
    finally:
        st.teardown()
        _restore()


def test_replaying_the_tutorial_does_not_read_it_as_finished():
    """0x7cfd8: the original forces isTutorial to 0. Without it, a save with
    TUTORIAL already "1" (from a previous completion or skip) made a replay
    start the walk timer immediately, and made P run the ordinary in-game pause
    instead of tutorial_skip, since isTutorial is what StopPlayAction_ branches
    on."""
    _AUTO[0] = 0.4
    S1E.LOADING_SECONDS = 0.0
    d = UserDefaults.standardUserDefaults()
    d.setObject_forKey_('1', 'TUTORIAL')          # already finished once before
    d.synchronize()
    app = AppDelegate.shared()
    if app.playback is None:
        app.didFinishLaunching()
    RunLoop.main().reset()
    st = Stage_Tutorial()
    try:
        st.viewDidLoad()
        RunLoop.main().pump()                      # fire the (zeroed) loading delay
        assert st.isTutorial == 0, 'a replay must not read as already finished'
        assert st.MotionSamplingTimer is None, 'the walk timer started during a replay'
        assert st.checkTutorialTimer is not None

        for n in T.STOP_NEEDS:
            st.beat_done[n] = True
        st.StopPlayAction_()
        assert st.gameState == 0, 'P ran the ordinary pause, not tutorial_skip'
        assert st.checkTutorialTimer is None, 'P did not end the tutorial'
    finally:
        st.teardown()
        _restore()


def test_the_first_prompt_waits_for_its_loading_delay():
    """0x7d6a2: beat One's words must wait LOADING_SECONDS after the stage loads.  Only
    "Now loading." comes before them (2026-10-05)."""
    _AUTO[0] = 0.4
    S1E.LOADING_SECONDS = 0.3
    d = UserDefaults.standardUserDefaults()
    d.setObject_forKey_('0', 'TUTORIAL')
    d.synchronize()
    app = AppDelegate.shared()
    if app.playback is None:
        app.didFinishLaunching()
    RunLoop.main().reset()
    said = []
    st = Stage_Tutorial()
    st._say = said.append
    try:
        st.viewDidLoad()
        assert said == [S1E.LOADING_TEXT], said
        del said[:]
        _pump(RunLoop.main(), 0.15)
        assert not said, 'beat One started before LOADING_SECONDS was up'
        _pump(RunLoop.main(), 0.3)
        assert said and said[0].startswith(T.BEATS[0][1]), 'beat One never started'
    finally:
        st.teardown()
        _restore()


def test_leaving_the_tutorial_stops_the_current_prompt():
    """teardown() must silence whatever beat is still being spoken, so it does not run
    on over the menu."""
    st = _tutorial(prompt=0.4)

    class _Speech:
        stopped = 0

        def speak(self, text, interrupt=True):
            return True

        def stop(self):
            _Speech.stopped += 1
    st.speech = _Speech()
    try:
        assert st.current_beat == 'One'
        st.teardown()
        assert _Speech.stopped, "beat One's words were not stopped"
    finally:
        _restore()


def test_a_beat_prompts_then_sends_its_monster():
    st = _tutorial(prompt=0.4)
    loop = RunLoop.main()
    try:
        assert st.current_beat == 'One'
        assert not st.MonsterBuffer, 'the monster arrived before the prompt finished'
        got = _pump(loop, 3.0, until=lambda: bool(st.MonsterBuffer))
        assert got, 'no monster after the prompt'
        m = st.MonsterBuffer[0]
        assert m.MovingType == 1, 'beat One should send a lane-1 monster, got %d' % m.MovingType
    finally:
        st.teardown()
        _restore()


def test_a_beat_says_its_words_then_the_keys():
    """PORT ADDITION: each beat says its words and then the player's own bindings, in one
    line, whatever voice over says."""
    from sixthsense.platform.keymap import KeyMap
    st = _tutorial(prompt=0.4)
    app = st.app
    km = KeyMap.shared()
    saved_bindings = dict(km.bindings)
    saved_pads = app.controllers
    said = []
    st._say = said.append
    try:
        app.controllers = None
        km.bindings = {a: list(b) for a, b in km.bindings.items()}
        km.bindings['lane1'] = [('a',), ('left',)]
        km.bindings['reload'] = [('s',), ('r',), ('down',)]
        km.bindings['lane2'] = [('q',), ('left', 'up')]
        assert st.key_hint('One') == "Press A or Left Arrow to shoot toward 9 o'clock."
        assert st.key_hint('Two') == 'Press Q or Left Arrow plus Up Arrow to shoot toward 10:30.'
        assert st.key_hint('Six') == 'Press S, R, or Down Arrow to reload.'
        assert st.key_hint('FiveHalf') is None
        km.bindings['pause'] = [('p',)]
        assert st.key_hint('Nine') == 'Press P to end the tutorial.'
        km.bindings['shake'] = [('left shift', 'space'), ('right shift', 'space')]
        assert st.key_hint('Eight') == 'Press Shift plus Space a few times to shake the zombie off.'
        km.bindings['shake'] = [('left shift', 'space')]
        assert st.key_hint('Eight') == 'Press Left Shift plus Space a few times to shake the zombie off.'
        km.bindings['lane1'] = []
        assert st.key_hint('One') is None, 'an unbound action should say nothing'
        km.bindings['lane1'] = [('a',), ('left',)]
        st.tutorial_beat('One')
        assert said == [_REAL_BEATS[0][1] + " Press A or Left Arrow to shoot toward 9 o'clock."
                        ' Press Enter to continue.'], said
        said.clear()
        st.tutorial_beat('FiveHalf')
        assert said == [_REAL_BEATS[5][1] + ' Press Enter to continue.'], said
        said.clear()
        _pump(RunLoop.main(), 3.0, until=lambda: bool(st.MonsterBuffer))
        assert len(said) == 0, 'the monster coming in said something more: %r' % said
    finally:
        km.bindings = saved_bindings
        app.controllers = saved_pads
        st.teardown()
        _restore()


class _Pad:
    def __init__(self, name):
        self.name = name


class _Pads:
    def __init__(self, *names):
        self.pads = [_Pad(n) for n in names]


def test_a_controller_gets_its_own_callouts():
    """tunmi13productions, 2026-10-05: with a pad attached the tutorial says the controller's way,
    stick first and the D-pad as the alternative."""
    st = _tutorial(prompt=0.4)
    app = st.app
    saved_pads = app.controllers
    said = []
    st._say = said.append
    try:
        app.controllers = _Pads('Xbox One Controller')
        want = {
            'One': "Push the left stick left to shoot toward 9 o'clock, or press D-pad left.",
            'Two': 'Push the left stick diagonally up and left to shoot toward 10:30, '
                   'or press D-pad left and up together.',
            'Three': "Push the left stick up to shoot toward 12 o'clock, or press D-pad up.",
            'Four': 'Push the left stick diagonally up and right to shoot toward 1:30, '
                    'or press D-pad right and up together.',
            'Five': "Push the left stick right to shoot toward 3 o'clock, or press D-pad right.",
            'Six': 'Pull the left stick down, press D-pad down, or press X, to reload.',
            'Seven': 'Press the right bumper to change to the next weapon.',
            'Eight': 'Press A a few times to shake the zombie off.',
            'Nine': 'Press B or Start to end the tutorial.',
        }
        for name, text in want.items():
            assert st.callout(name) == text, (name, st.callout(name))
        assert st.callout('FiveHalf') is None, 'FiveHalf teaches nothing new'
        said.clear()
        st.tutorial_beat('One')
        assert said == [_REAL_BEATS[0][1] + ' ' + want['One'] + ' Press A to continue.'], said
    finally:
        app.controllers = saved_pads
        st.teardown()
        _restore()


def test_every_movement_lesson_names_the_dpad():
    """The D-pad does everything the left stick does, reload included (ui/input.py's
    DPAD_LANES maps down to reload), so no lesson that teaches a direction may leave it
    out.  Six did until tunmi13productions noticed, 2026-10-06."""
    from sixthsense.game.stage_tutorial import CONTROLLER_HINTS
    for name in ('One', 'Two', 'Three', 'Four', 'Five', 'Six'):
        assert 'D-pad' in CONTROLLER_HINTS[name], name


def test_a_playstation_pad_hears_playstation_button_names():
    st = _tutorial(prompt=0.4)
    app = st.app
    saved = app.controllers
    try:
        app.controllers = _Pads('PS5 Controller')
        assert st.callout('Six') == ('Pull the left stick down, press D-pad down, '
                                     'or press Square, to reload.')
        assert st.callout('Seven') == 'Press R1 to change to the next weapon.'
        assert st.callout('Eight') == 'Press Cross a few times to shake the zombie off.'
        assert st.callout('Nine') == 'Press Circle or Options to end the tutorial.'
        assert st.callout('Two').endswith('D-pad left and up together.'), 'the D-pad has no names'
    finally:
        app.controllers = saved
        st.teardown()
        _restore()


def test_without_a_controller_the_keyboard_hints_stand_as_they_were():
    st = _tutorial(prompt=0.4)
    app = st.app
    saved_pads = app.controllers
    try:
        app.controllers = None
        assert app.controller_name() is None
        app.controllers = _Pads()
        assert app.controller_name() is None, 'a controller list with nothing in it'
        assert st.callout('One') == st.key_hint('One') and st.callout('One') is not None
        assert 'stick' not in st.callout('One')
    finally:
        app.controllers = saved_pads
        st.teardown()
        _restore()


def test_the_shake_is_only_offered_when_the_pad_can_sense_one():
    """tunmi13productions, 2026-10-05: lesson Eight offers shaking the controller only to a pad
    that can be shaken, a DualSense; an Xbox pad is told about A alone."""
    class _CanShake:
        def __init__(self, can):
            self.can = can

        def capable(self):
            return self.can
    st = _tutorial(prompt=0.4)
    app = st.app
    saved = (app.controllers, app.shake)
    try:
        app.controllers = _Pads('Xbox One Controller')
        app.shake = _CanShake(False)
        assert st.callout('Eight') == 'Press A a few times to shake the zombie off.'
        app.shake = None
        assert st.callout('Eight') == 'Press A a few times to shake the zombie off.'
        app.controllers = _Pads('PS5 Controller')
        app.shake = _CanShake(True)
        assert st.callout('Eight') == ('Press Cross a few times, or give the controller a shake, '
                                       'to shake the zombie off.')
        assert st.callout('One') == "Push the left stick left to shoot toward 9 o'clock, or press D-pad left."
        app.controllers = None
        assert 'shake the controller' not in (st.callout('Eight') or ''), 'no pad, no shaking offered'
    finally:
        app.controllers, app.shake = saved
        st.teardown()
        _restore()


def test_killing_in_the_taught_lane_finishes_the_beat():
    st = _tutorial(prompt=0.4)
    loop = RunLoop.main()
    try:
        _pump(loop, 3.0, until=lambda: bool(st.MonsterBuffer))
        m = st.MonsterBuffer[0]
        _pump(loop, 2.0, until=lambda: m.MovingPosAngle != 0)
        st.shotFlag = False
        st.MovingShot_(LANE[m.MovingType])
        _pump(loop, S1E.SHOT_TRAVEL + 0.5, until=lambda: st.beat_done['One'])
        assert st.beat_done['One'], 'the kill did not finish beat One'
        got = _pump(loop, 4.0, until=lambda: st.current_beat == 'Two')
        assert got, 'the tutorial did not move on to beat Two'
    finally:
        st.teardown()
        _restore()


def test_a_kill_finishes_the_beat_in_debug_mode_too():
    """--debug counts no kill, but the tutorial's lessons still see the zombie die,
    so beat One finishes and the tutorial can be played through."""
    app = AppDelegate.shared()
    st = _tutorial(prompt=0.4)
    loop = RunLoop.main()
    app.debug = True
    try:
        _pump(loop, 3.0, until=lambda: bool(st.MonsterBuffer))
        m = st.MonsterBuffer[0]
        _pump(loop, 2.0, until=lambda: m.MovingPosAngle != 0)
        st.shotFlag = False
        st.MovingShot_(LANE[m.MovingType])
        _pump(loop, S1E.SHOT_TRAVEL + 0.5, until=lambda: st.beat_done['One'])
        assert st.beat_done['One'], 'in debug mode the kill did not finish beat One'
        assert st.gamePlayer.killMonsterCount == 0, 'the kill counted in debug mode'
    finally:
        app.debug = False
        st.teardown()
        _restore()


def test_reload_finishes_beat_six():
    """0x84cfa..0x84d16: a reload only counts once One to FiveHalf are done, and then
    NextTutorial starts beat Seven at once (0x84d5a)."""
    st = _tutorial(prompt=0.4)
    try:
        st.GunReloadAction_()
        assert not st.beat_done['Six'], 'a reload during beat One finished beat Six'
        for n in T.REQUIRES['Six']:
            st.beat_done[n] = True
        st.GunReloadAction_()
        assert st.beat_done['Six']
        assert st.current_beat == 'Seven', st.current_beat
    finally:
        st.teardown()
        _restore()


def test_p_does_nothing_before_beat_eight_is_done():
    """0x83926..0x8393c: the stop button is ignored until beats One to Eight are
    done; it used to end the tutorial at any time and leave you stuck."""
    st = _tutorial(prompt=0.4)
    try:
        for n in BEAT_NAMES[:7]:               # One to Seven, Eight still to go
            st.beat_done[n] = True
        st.StopPlayAction_()
        assert not st.finished and not st.ending
        assert st.checkTutorialTimer is not None, 'CheckTutorial was stopped'
        assert st.gameState == 0, 'P paused the tutorial'
        assert UserDefaults.standardUserDefaults().intForKey_('TUTORIAL') == 0
    finally:
        st.teardown()
        _restore()


def test_leaving_the_window_never_ends_the_tutorial():
    """tsatria03, 2026-10-07: leaving the window pressed P, which ends the tutorial once
    lessons One to Eight are done, so switching away finished it.  The lessons ignore it
    now; P itself still ends them, and the real game after the countdown still pauses."""
    from sixthsense.ui.focus import interrupt_stop, stop_for_focus
    st = _tutorial(prompt=0.4)
    try:
        for n in T.STOP_NEEDS:
            st.beat_done[n] = True
        assert not interrupt_stop(st)
        assert not st.finished and not st.ending, 'leaving the window ended the tutorial'
        assert UserDefaults.standardUserDefaults().intForKey_('TUTORIAL') == 0
        st.real_game = True                     # past the countdown, a game like any
        st.isTutorial = 1
        assert stop_for_focus(st) and st.gameState == 1, 'the real game did not pause'
    finally:
        st.teardown()
        _restore()


def test_p_ends_the_tutorial_row_back_at_the_menu():
    """Beat Nine: P plays tutorial success, and 3.05 s later -[Stage_Tutorial
    tutorialEnd:] (0x83738) is GameEndAction:."""
    st = _tutorial(prompt=0.4)
    loop = RunLoop.main()
    said = []
    st._say = said.append
    try:
        calls = []
        real_beat = st.tutorial_beat
        st.tutorial_beat = lambda name, **k: (calls.append(name), real_beat(name, **k))[-1]
        for n in T.STOP_NEEDS:
            st.beat_done[n] = True
        st.StopPlayAction_()
        assert st.beat_done['Nine'] and st.finished
        assert st.checkTutorialTimer is None, 'CheckTutorial is still running'
        assert UserDefaults.standardUserDefaults().intForKey_('TUTORIAL') == 1
        assert T.TEXT_TUTORIAL_SUCCESS in said
        st.StopPlayAction_()                   # a second P while it ends
        assert st.gameState == 0, 'P paused the ending'
        assert st.running
        assert _pump(loop, 4.0, until=lambda: not st.running), 'never went back to the menu'
        assert not calls, 'a prompt restarted after the tutorial ended'
        assert T.TEXT_ZOMBIES_COMING not in said
        assert st.MotionSamplingTimer is None, 'the tutorial row started the game'
    finally:
        st.teardown()
        _restore()


def test_the_once_a_second_check_never_replays_a_prompt():
    """tutorialNEnd (0x8cb60 .. 0x8dd78) only slides the hint finger; a prompt is replayed
    only by tutorialNRestart, when the beat's monster reaches you, and tutorialSixRestart
    is never sent.  The port replayed the reload lesson's prompt about every ten seconds,
    since Six has no monster to hold it back."""
    st = _tutorial(prompt=0.4)
    try:
        calls = []
        real_beat = st.tutorial_beat
        st.tutorial_beat = lambda name, **k: (calls.append(name), real_beat(name, **k))[-1]

        st.current_beat = 'Six'
        st.tutorial_sound_stop('Six')          # the prompt has finished playing
        for _ in range(30):                    # half a minute of CheckTutorial ticks
            st.tutorial_beat_end('Six')
            st.CheckTutorial()
        assert calls == [], 'the reload prompt was replayed %d times' % len(calls)
    finally:
        st.teardown()
        _restore()


def test_weapon_change_finishes_beat_seven():
    st = _tutorial(prompt=0.4)
    try:
        AppDelegate.shared().useWeapon = ['1'] * 8
        st.gunChangeAction_(1)
        assert not st.beat_done['Seven'], 'Tab during beat One finished beat Seven'
        for n in T.REQUIRES['Seven'] + ('FiveHalf',):
            st.beat_done[n] = True
        st.gunChangeAction_(1)
        assert st.beat_done['Seven']
        assert st.current_beat != 'Eight', 'beat Eight came before the 1.5 s wait'
        assert _pump(RunLoop.main(), 2.5, until=lambda: st.current_beat == 'Eight'), \
            'beat Eight never came'
        st.threeTapChangeWeapon_()
        assert not st.beat_done['Nine'], 'the previous weapon finished beat Nine'
    finally:
        st.teardown()
        _restore()


def test_shaking_free_finishes_beat_eight():
    st = _tutorial(prompt=0.4)
    loop = RunLoop.main()
    try:
        for n in T.REQUIRES['Eight']:
            st.beat_done[n] = True
        st.MonsterInit_(73)                    # what beat eight sends in
        m = st.MonsterBuffer[0]
        assert m.shakeMonsterFlag, 'type73 is not a grabber'
        m.monsterRange = 10.0
        st.MonsterAttPlayer()
        assert st.isShake
        for _ in range(10):
            st.shake_step()
        _pump(loop, 2.0, until=lambda: not st.isShake)
        assert st.beat_done['Eight'], 'shaking free did not finish beat Eight'
    finally:
        st.teardown()
        _restore()


def test_the_animal_zombie_grabs_you_by_itself():
    """CheckTutorial 0x8c754 calls MonsterAttPlayer while you are not held, so the
    grabber beat Eight sends in takes hold without anything calling it by hand."""
    st = _tutorial(prompt=0.4)
    try:
        for n in BEAT_NAMES[:8]:
            st.beat_done[n] = True
        st.tutorial_sound_stop('Eight')        # the prompt is over; type 73 comes in
        assert st.noAtt, 'the animal zombie can be shot'   # 0x8e1a8
        m = st.MonsterBuffer[0]
        m.monsterRange = 10.0
        st.CheckTutorial()
        assert st.isShake, 'CheckTutorial never let it grab'
        hp0 = st.gamePlayer.HP
        for _ in range(10):
            st.shake_step()
        _pump(RunLoop.main(), 2.0, until=lambda: not st.isShake)
        assert st.beat_done['Eight']
        assert st.gamePlayer.HP == hp0
    finally:
        st.teardown()
        _restore()


def test_a_zombie_that_reaches_you_restarts_its_beat():
    """0x3b3a2..0x3b41c: no heart lost, and the beat is prompted again."""
    st = _tutorial(prompt=0.4)
    try:
        calls = []
        real_beat = st.tutorial_beat
        st.tutorial_beat = lambda name, **k: (calls.append(name), real_beat(name, **k))[-1]
        st.MonsterInit_(2)                     # beat Two's zombie
        st.MonsterBuffer[0].monsterRange = 10.0
        hp0 = st.gamePlayer.HP
        st.MonsterAttPlayer()
        assert st.gamePlayer.HP == hp0, 'the tutorial took a heart'
        assert calls == ['Two'], calls
    finally:
        st.teardown()
        _restore()


def _kill_the_beats_monster(st, loop):
    """Wait for the beat's monster and shoot it until it dies."""
    assert _pump(loop, 5.0, until=lambda: bool(st.MonsterBuffer)), \
        'beat %s sent no monster' % st.current_beat
    m = st.MonsterBuffer[0]
    _pump(loop, 2.0, until=lambda: m.MovingPosAngle != 0)
    for _ in range(40):
        if m not in st.MonsterBuffer:
            return
        st.shotFlag = False
        st.MovingShot_(LANE[m.MovingType])
        _pump(loop, S1E.SHOT_TRAVEL + 0.2, until=lambda: m not in st.MonsterBuffer)
    raise AssertionError('the monster of beat %s never died' % st.current_beat)


def test_the_whole_tutorial_plays_in_order():
    """Played through as a player would, with the reload and weapon keys pressed
    early: the beats come One to Nine, each once its action is done, and nothing
    pressed early finishes a later lesson."""
    st = _tutorial(prompt=0.4)
    loop = RunLoop.main()
    app = AppDelegate.shared()
    saved_weapons = list(app.useWeapon)
    order = ['One']
    real_beat = st.tutorial_beat
    st.tutorial_beat = lambda name: (order.append(name), real_beat(name))[-1]
    try:
        app.useWeapon = ['1'] * 8
        for name in ('One', 'Two', 'Three', 'Four', 'Five', 'FiveHalf'):
            assert _pump(loop, 3.0, until=lambda: st.current_beat == name), \
                'expected beat %s, at %s' % (name, st.current_beat)
            st.shotFlag = False
            st.ReloadGesture()                 # pressed early
            st.reloadGun_()
            st.gamePlayer.useWepon = 6
            st.doubleTapChangeWeapon_()        # pressed early
            st.gamePlayer.useWepon = 6
            st.weaponSource[6].BulletCount = 50
            assert not st.beat_done['Six'], 'an early reload finished beat Six'
            assert not st.beat_done['Seven'], 'an early Tab finished beat Seven'
            _kill_the_beats_monster(st, loop)
            assert st.beat_done[name], 'the kill did not finish beat %s' % name
        assert _pump(loop, 1.0, until=lambda: st.current_beat == 'Six')
        st.doubleTapChangeWeapon_()            # Tab before the reload
        st.gamePlayer.useWepon = 6
        assert not st.beat_done['Seven'], 'Tab during beat Six finished beat Seven'
        st.shotFlag = False
        st.ReloadGesture()
        assert st.beat_done['Six'] and st.current_beat == 'Seven'
        st.reloadGun_()
        st.doubleTapChangeWeapon_()
        assert st.beat_done['Seven']
        assert _pump(loop, 2.5, until=lambda: st.current_beat == 'Eight')
        assert _pump(loop, 3.0, until=lambda: bool(st.MonsterBuffer)), 'no animal zombie'
        st.MonsterBuffer[0].monsterRange = 10.0
        st.MonsterAttPlayer()
        assert st.isShake, 'the animal zombie did not grab'
        for _ in range(st.shakesNeeded):
            st.shake_step()
        assert _pump(loop, 3.0, until=lambda: st.current_beat == 'Nine'), \
            'beat Nine never came, at %s' % st.current_beat
        st.StopPlayAction_()
        assert st.finished
        seen = [n for i, n in enumerate(order) if i == 0 or order[i - 1] != n]
        assert seen == BEAT_NAMES, seen
    finally:
        app.useWeapon = saved_weapons
        st.teardown()
        _restore()


def test_the_first_run_counts_down_into_the_real_game():
    """-[Stage_1_E tutorialEnd:] 0x33bec reads 3, 2, 1, then tutorialEndGameStart:
    (0x33d40) 6.0 s later says zombies are coming and starts the walk."""
    st = _tutorial(prompt=0.4, first_run=True)
    loop = RunLoop.main()
    said = []
    st._say = said.append
    T.ENDING_DELAY, T.COUNTDOWN_SECONDS = 0.2, 0.3
    try:
        for n in T.STOP_NEEDS:
            st.beat_done[n] = True
        st.StopPlayAction_()
        assert st.MotionSamplingTimer is None, 'the game started before the countdown'
        assert _pump(loop, 2.0, until=lambda: st.MotionSamplingTimer is not None), \
            'the walk never started'
        assert said[-2:] == [T.TEXT_COUNTDOWN, T.TEXT_ZOMBIES_COMING], said
        assert st.running, 'the first run went back to the menu'
        assert st.isTutorial == 1, 'isTutorial was not set'          # 0x83786
        assert st.noAtt is False                                     # 0x83774
        assert st.shotFlag is False                                  # 0x83782
        assert not st.ending
        assert UserDefaults.standardUserDefaults().intForKey_('TUTORIAL') == 1
        st.StopPlayAction_()
        assert st.gameState == 1, 'P no longer pauses the real game'
    finally:
        T.ENDING_DELAY, T.COUNTDOWN_SECONDS = 3.05, 4.0
        st.teardown()
        _restore()


def test_a_waiting_beat_goes_on_with_enter_and_not_before():
    """PORT ADDITION (tunmi13productions, 2026-10-05): a beat that sends in a zombie says its
    words and waits for Enter instead of a timer; Enter cuts the speech and sends it."""
    st = _tutorial(prompt=None)
    said = []
    st._say = said.append
    stopped = []
    st.speech = type('S', (), {'speak': lambda *a, **k: True, 'stop': lambda self: stopped.append(1)})()
    try:
        assert st.waiting == 'One'
        _pump(RunLoop.main(), 1.0)
        assert not st.MonsterBuffer, 'the zombie came in without Enter'
        assert st.tutorial_advance() is True
        assert st.waiting is None and stopped, 'Enter did not cut the speech'
        assert len(st.MonsterBuffer) == 1 and st.MonsterBuffer[0].MovingType == 1
        assert st.tutorial_advance() is False, 'a second Enter sent another'
        assert len(st.MonsterBuffer) == 1
    finally:
        st.teardown()
        _restore()


def test_beats_without_a_zombie_do_not_wait():
    """Six, Seven and Nine only speak: no continue prompt, nothing to press."""
    st = _tutorial(prompt=None)
    said = []
    st._say = said.append
    try:
        for name in ('Six', 'Seven', 'Nine'):
            said.clear()
            st.tutorial_beat(name)
            assert st.waiting is None, name
            assert 'continue' not in said[0], said
        assert st.tutorial_repeat() is False
    finally:
        st.teardown()
        _restore()


def test_any_other_key_repeats_a_waiting_beat_and_enter_goes_on():
    """Through the keyboard handler: Enter goes on, any other key says it again, Escape
    still leaves the tutorial, and a lone modifier does not repeat."""
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
            self.mod = 0

    st = _tutorial(prompt=None)
    said = []
    st._say = said.append
    keys = Input(st)
    try:
        keys.handle(_Key('h'), _Pygame)
        assert said == [st.line], said
        keys.handle(_Key('left shift'), _Pygame)
        assert len(said) == 1, 'a modifier repeated it'
        assert st.waiting == 'One'
        keys.handle(_Key('return'), _Pygame)
        assert st.waiting is None and len(st.MonsterBuffer) == 1
        said.clear()
        keys.handle(_Key('h'), _Pygame)
        assert not said, 'it repeated with nothing waiting'
        st.tutorial_beat('Two')
        said.clear()
        keys.handle(_Key('escape'), _Pygame)
        assert not said and st.waiting == 'Two', 'Escape did not behave as Escape'
        assert keys.quit, 'Escape did not leave the tutorial'
    finally:
        st.teardown()
        _restore()


def test_a_pad_goes_on_with_a_and_repeats_with_y():
    from sixthsense.ui.input import Input

    class _Pygame:
        CONTROLLERBUTTONDOWN = 10
        CONTROLLERBUTTONUP = 11
        CONTROLLERAXISMOTION = 12
        CONTROLLERDEVICEREMOVED = 13
        CONTROLLER_BUTTON_A, CONTROLLER_BUTTON_Y = 0, 3
        CONTROLLER_BUTTON_DPAD_UP, CONTROLLER_BUTTON_DPAD_DOWN = 11, 12
        CONTROLLER_BUTTON_DPAD_LEFT, CONTROLLER_BUTTON_DPAD_RIGHT = 13, 14
        CONTROLLER_BUTTON_X, CONTROLLER_BUTTON_B, CONTROLLER_BUTTON_START = 2, 1, 6
        CONTROLLER_BUTTON_RIGHTSHOULDER, CONTROLLER_BUTTON_LEFTSHOULDER = 10, 9
        CONTROLLER_AXIS_LEFTX, CONTROLLER_AXIS_LEFTY = 0, 1

    class _Ev:
        type = _Pygame.CONTROLLERBUTTONDOWN

        def __init__(self, button):
            self.button = button

    st = _tutorial(prompt=None)
    said = []
    st._say = said.append
    keys = Input(st)
    try:
        keys.controller(_Ev(_Pygame.CONTROLLER_BUTTON_Y), _Pygame, [])
        assert said == [st.line], said
        assert st.waiting == 'One'
        keys.controller(_Ev(_Pygame.CONTROLLER_BUTTON_A), _Pygame, [])
        assert st.waiting is None and len(st.MonsterBuffer) == 1
    finally:
        st.teardown()
        _restore()


def test_the_prompt_says_how_to_hear_it_again_only_the_first_time():
    st = _tutorial(prompt=None)
    app = st.app
    saved = app.controllers
    try:
        app.controllers = None
        st.told_repeat = False
        # and it says that the repeat key keeps working, since it is named only
        # here (tunmi13productions, 2026-10-06)
        assert st.continue_prompt() == ('Press Enter to continue, or any other key '
                                        'to hear this again. ' + T.REPEAT_ALWAYS)
        assert st.continue_prompt() == 'Press Enter to continue.'
        app.controllers = _Pads('PS5 Controller')
        st.told_repeat = False
        assert st.continue_prompt() == ('Press Cross to continue, or Triangle to '
                                        'hear this again. ' + T.REPEAT_ALWAYS)
        app.controllers = _Pads('Xbox One Controller')
        assert st.continue_prompt() == 'Press A to continue.'
        assert T.REPEAT_ALWAYS not in st.continue_prompt(), 'it was said twice'
    finally:
        app.controllers = saved
        st.teardown()
        _restore()


def test_the_animal_zombie_on_you_is_not_waited_for_or_sent_twice():
    """When the grab lands beat Eight is said again for the shake, but A is the shake
    button and the zombie is already on you, so it neither waits nor sends a second."""
    st = _tutorial(prompt=None)
    said = []
    st._say = said.append
    try:
        st.tutorial_beat('Eight')
        assert st.waiting == 'Eight'
        st.tutorial_advance()
        n = len(st.MonsterBuffer)
        assert n == 1
        st.tutorial_restart('Eight')
        assert st.waiting is None, 'the grab waited for a key that shakes'
        assert 'continue' not in said[-1], said[-1]
        assert len(st.MonsterBuffer) == n, 'a second animal zombie came in'
    finally:
        st.teardown()
        _restore()


def test_nothing_else_works_while_a_lesson_waits():
    """The player must not shoot, reload or change weapon past a lesson that is waiting:
    every key but Enter, Escape and F1 only says it again, and a pad's buttons other than
    A, Y, B and Start do nothing."""
    from sixthsense.ui.input import Input

    class _Pygame:
        KEYDOWN, KEYUP, QUIT = 1, 2, 3
        CONTROLLERBUTTONDOWN, CONTROLLERBUTTONUP = 10, 11
        CONTROLLERAXISMOTION, CONTROLLERDEVICEREMOVED = 12, 13
        CONTROLLER_BUTTON_A, CONTROLLER_BUTTON_Y, CONTROLLER_BUTTON_X = 0, 3, 2
        CONTROLLER_BUTTON_B, CONTROLLER_BUTTON_START = 1, 6
        CONTROLLER_BUTTON_DPAD_UP, CONTROLLER_BUTTON_DPAD_DOWN = 11, 12
        CONTROLLER_BUTTON_DPAD_LEFT, CONTROLLER_BUTTON_DPAD_RIGHT = 13, 14
        CONTROLLER_BUTTON_RIGHTSHOULDER, CONTROLLER_BUTTON_LEFTSHOULDER = 10, 9
        CONTROLLER_AXIS_LEFTX, CONTROLLER_AXIS_LEFTY = 0, 1

        class key:
            @staticmethod
            def name(k):
                return k

    class _Key:
        type = _Pygame.KEYDOWN

        def __init__(self, name):
            self.key = name
            self.mod = 0

    class _Pad:
        def __init__(self, button=None, kind=_Pygame.CONTROLLERBUTTONDOWN, axis=None, value=0.0):
            self.type, self.button, self.axis, self.value = kind, button, axis, value

    st = _tutorial(prompt=None)
    st._say = lambda text: None
    keys = Input(st)
    done = []
    keys.perform = done.append
    keys.attack_lane = lambda lane: done.append(lane)
    try:
        assert st.waiting == 'One'
        for name in ('a', 'left', 'tab', 'r', 's', 'space', 'up', 'down', 'right'):
            keys.handle(_Key(name), _Pygame)
        assert not done, 'a key did something while the lesson waited: %r' % done
        for b in (_Pygame.CONTROLLER_BUTTON_X, _Pygame.CONTROLLER_BUTTON_DPAD_LEFT,
                  _Pygame.CONTROLLER_BUTTON_RIGHTSHOULDER):
            keys.controller(_Pad(b), _Pygame, [])
            keys.controller(_Pad(b, _Pygame.CONTROLLERBUTTONUP), _Pygame, [])
        keys.controller(_Pad(None, _Pygame.CONTROLLERAXISMOTION, 0, -1.0), _Pygame, [])
        assert not done and not st.MonsterBuffer, 'a pad did something: %r' % done
        keys.controller(_Pad(_Pygame.CONTROLLER_BUTTON_B), _Pygame, [])
        assert keys.quit, 'B did not leave'
        keys.quit = False
        keys.controller(_Pad(_Pygame.CONTROLLER_BUTTON_START), _Pygame, [])
        assert keys.quit, 'Start did not leave'
        st.tutorial_advance()
        keys.handle(_Key('r'), _Pygame)
        assert done, 'keys stayed blocked once the lesson was over'
    finally:
        st.teardown()
        _restore()


def test_the_first_game_after_the_tutorial_pauses_and_restarts_as_the_game():
    """The first run's real game is played by the tutorial's own stage object.  Escape there
    must pause, not leave for the menu as it does in the tutorial, and restarting from the
    panel must start the game again, walking, not the tutorial's first lesson."""
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
            self.mod = 0

    st = _tutorial(prompt=0.4, first_run=True)
    loop = RunLoop.main()
    st._say = lambda text: None
    T.ENDING_DELAY, T.COUNTDOWN_SECONDS = 0.2, 0.3
    try:
        for n in T.STOP_NEEDS:
            st.beat_done[n] = True
        st.StopPlayAction_()
        assert _pump(loop, 2.0, until=lambda: st.MotionSamplingTimer is not None),             'the walk never started'
        keys = Input(st)
        keys.handle(_Key('escape'), _Pygame)
        assert not keys.quit, 'Escape left the first game for the menu'
        assert st.gameState == 1, 'Escape did not pause the first game'
        keys.handle(_Key('escape'), _Pygame)
        assert st.gameState == 0, 'Escape did not resume'

        st.StopPlayAction_()
        assert st.gameState == 1
        calls = []
        st.tutorial_beat = lambda name, **k: calls.append(name)
        assert st.gameReplayAction_() is True
        assert not calls, 'the restart began the tutorial again: %r' % calls
        assert st.waiting is None
        assert st.isTutorial == 1, 'the restart read as the tutorial'
        assert st.MotionSamplingTimer is not None and st.MotionSamplingTimer.isValid(),             'the restarted game does not walk'
        st.StopPlayAction_()
        assert st.gameState == 1, 'P does nothing in the restarted game'
    finally:
        T.ENDING_DELAY, T.COUNTDOWN_SECONDS = 3.05, 4.0
        st.teardown()
        _restore()


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
