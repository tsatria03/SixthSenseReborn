"""Where the game finds its files: ``paths.path_for_resource``.

The original bundle is flat; the port keeps its sounds in folders under
``game/sounds/used``, and those the game never plays under ``game/sounds/unused``, which
is searched last.  Each test builds a small bundle of its own in
a temporary folder, so these check the lookup itself rather than the shipped data - that
is ``data.py``'s job - and they never touch the save or play a sound.
"""
from __future__ import annotations

import os
import shutil
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import _scratch_save                                             # noqa: E402,F401  never the real save

from sixthsense import paths                                     # noqa: E402

# what paths._is_bundle looks for before it takes a folder for the bundle
MARKERS = ('SoundList.plist', 'g_CH1_E')


def _bundle(files):
    """A throwaway bundle holding the two marker files and ``files`` (paths inside the
    bundle, with '/' between folders), and the lookup pointed at it."""
    top = tempfile.mkdtemp()
    for rel in MARKERS + tuple(files):
        p = os.path.join(top, *rel.split('/'))
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, 'w', encoding='utf-8') as f:
            f.write(rel)
    paths.set_game(top)
    return top


def _done(top):
    paths.set_game(None)
    shutil.rmtree(top, ignore_errors=True)


def _found(top, name, ext=None):
    """Where the lookup found it, inside the bundle, with '/' between folders."""
    p = paths.path_for_resource(name, ext)
    return None if p is None else os.path.relpath(p, top).replace(os.sep, '/')


def test_a_sound_in_a_folder_is_found():
    rel = 'sounds/used/sfx/zombies/normal/normalcave1/zombie_1_coming_cave.wav'
    top = _bundle([rel])
    try:
        assert _found(top, 'zombie_1_coming_cave', 'wav') == rel
    finally:
        _done(top)


def test_the_unused_folder_is_searched_last():
    """What the game never plays is in sounds/unused; a name only there is still found."""
    rel = 'sounds/unused/speech/game/the rank.wav'
    top = _bundle([rel])
    try:
        assert _found(top, 'the rank', 'wav') == rel
    finally:
        _done(top)


def test_a_sound_in_the_used_folder_wins_over_the_unused_one():
    top = _bundle(['sounds/unused/sfx/misc/ui_select.wav', 'sounds/used/sfx/misc/ui_select.wav'])
    try:
        assert _found(top, 'ui_select', 'wav') == 'sounds/used/sfx/misc/ui_select.wav'
    finally:
        _done(top)


def test_case_does_not_matter():
    rel = 'sounds/used/speech/menus/main/Game Start Button.wav'
    top = _bundle([rel])
    try:
        assert _found(top, 'game start button', 'wav') == rel
        assert _found(top, 'GAME START BUTTON', 'WAV') == rel
    finally:
        _done(top)


def test_a_shared_sound_is_always_the_same_copy():
    """Where the original reuses one recording, each folder that uses it has a copy.
    The first in sorted order is taken, whichever order the folders were made in."""
    top = _bundle(['sounds/used/sfx/zombies/normal/normalcave7/zombie_3_7_hit_player.wav',
                   'sounds/used/sfx/zombies/normal/normalcave3/zombie_3_7_hit_player.wav'])
    try:
        want = 'sounds/used/sfx/zombies/normal/normalcave3/zombie_3_7_hit_player.wav'
        assert _found(top, 'zombie_3_7_hit_player', 'wav') == want
        assert _found(top, 'zombie_3_7_hit_player', 'wav') == want
    finally:
        _done(top)


def test_the_top_folder_comes_first():
    """pathForResource:ofType: only ever looked in the top folder, so a file there wins
    over one of the same name in the sounds folder."""
    top = _bundle(['ui_select.wav', 'sounds/used/sfx/misc/ui_select.wav'])
    try:
        assert _found(top, 'ui_select', 'wav') == 'ui_select.wav'
    finally:
        _done(top)


def test_the_plists_and_maps_are_in_the_top_folder():
    top = _bundle(['type1.plist', 'a_CH1_E.txt', 'sounds/used/sfx/misc/ui_select.wav'])
    try:
        assert _found(top, 'type1', 'plist') == 'type1.plist'
        assert _found(top, 'a_CH1_E', 'txt') == 'a_CH1_E.txt'
        assert _found(top, 'g_CH1_E') == 'g_CH1_E'
        assert _found(top, 'SoundList', 'plist') == 'SoundList.plist'
    finally:
        _done(top)


def test_an_original_flat_bundle_still_works():
    """--game pointed at an untouched sixsense.app, with every WAV beside the plists."""
    top = _bundle(['zombie_1_coming_cave.wav', 'type1.plist'])
    try:
        assert _found(top, 'zombie_1_coming_cave', 'wav') == 'zombie_1_coming_cave.wav'
        assert _found(top, 'type1', 'plist') == 'type1.plist'
        assert paths.sounds() == top
    finally:
        _done(top)


def test_sounds_is_the_used_folder():
    top = _bundle(['sounds/used/sfx/misc/ui_select.wav'])
    try:
        assert paths.sounds() == os.path.join(top, 'sounds', 'used')
    finally:
        _done(top)


def test_a_missing_sound_is_none():
    top = _bundle(['sounds/used/sfx/misc/ui_select.wav'])
    try:
        assert _found(top, 'zombie_5_hit_player', 'wav') is None
        assert _found(top, 'ui_select', 'plist') is None, 'the extension was ignored'
    finally:
        _done(top)


def test_pointing_somewhere_else_forgets_the_old_sounds():
    first = _bundle(['sounds/used/sfx/misc/ui_select.wav'])
    try:
        assert _found(first, 'ui_select', 'wav') is not None
        second = _bundle([])
        try:
            assert _found(second, 'ui_select', 'wav') is None, \
                'a sound from the previous bundle was still found'
        finally:
            _done(second)
    finally:
        _done(first)


def test_the_save_goes_where_sixthsense_user_dir_points():
    """The tests' way off the real save; without it, the save is in
    %APPDATA%\\SixthSenseReborn."""
    old_dir, old_appdata = os.environ.get(paths.USER_DIR_ENV), os.environ.get('APPDATA')
    was = paths.WINDOWS
    top = tempfile.mkdtemp()
    try:
        mine = os.path.join(top, 'mine')
        os.environ[paths.USER_DIR_ENV] = mine
        assert paths.user_dir() == mine and os.path.isdir(mine)
        os.environ.pop(paths.USER_DIR_ENV)
        paths.WINDOWS = True
        os.environ['APPDATA'] = top
        assert paths.user_dir() == os.path.join(top, 'SixthSenseReborn')
    finally:
        paths.WINDOWS = was
        for key, old in ((paths.USER_DIR_ENV, old_dir), ('APPDATA', old_appdata)):
            if old is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = old
        shutil.rmtree(top, ignore_errors=True)


def test_on_linux_the_save_goes_in_the_users_data_folder():
    """2026-09-28: $XDG_DATA_HOME/SixthSenseReborn, which is ~/.local/share/SixthSenseReborn
    when unset."""
    keys = (paths.USER_DIR_ENV, 'XDG_DATA_HOME')
    old = {k: os.environ.get(k) for k in keys}
    was = paths.WINDOWS, paths.MACOS
    top = tempfile.mkdtemp()
    try:
        os.environ.pop(paths.USER_DIR_ENV, None)
        paths.WINDOWS = False
        paths.MACOS = False
        os.environ['XDG_DATA_HOME'] = top
        assert paths.user_dir() == os.path.join(top, 'SixthSenseReborn')
        os.environ.pop('XDG_DATA_HOME')
        assert paths.save_base() == os.path.join(os.path.expanduser('~'), '.local', 'share')
    finally:
        paths.WINDOWS, paths.MACOS = was
        for k, v in old.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
        shutil.rmtree(top, ignore_errors=True)


INTERACT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                        'interact')


def test_the_by_ear_tools_never_change_appdata():
    """2026-10-06: the tools in tests/interact kept off the save by changing APPDATA, which
    the game reads on Windows alone, so on Linux and macOS they played on the real save.
    Each one that starts the game now goes through _own_save, or sets
    SIXTHSENSE_USER_DIR itself as the controller tester does."""
    tools = [n for n in os.listdir(INTERACT) if n.endswith('.py') and not n.startswith('_')]
    assert tools, 'no tools found in %s' % INTERACT
    for name in tools:
        with open(os.path.join(INTERACT, name), encoding='utf-8') as fh:
            src = fh.read()
        for wrong in ("environ['APPDATA']", 'environ["APPDATA"]'):
            assert wrong not in src, '%s changes APPDATA' % name
        assert 'own_save(' in src or paths.USER_DIR_ENV in src, \
            '%s does not keep off the real save' % name


def test_a_by_ear_tools_save_is_its_own():
    """_own_save puts a tool's save in a folder of its own inside the game's, on every
    system, the same folder on Windows as before, and copies the key bindings and the
    settings, from config/ (or, where the player's save has not moved into the folders yet,
    from beside them), but never the save."""
    from unittest.mock import patch
    sys.path.insert(0, INTERACT)
    try:
        from _own_save import own_save
    finally:
        sys.path.remove(INTERACT)
    for layout in ('config', ''):
        with tempfile.TemporaryDirectory() as top:
            real = os.path.join(top, 'SixthSenseReborn')
            os.makedirs(os.path.join(real, 'config'))
            os.makedirs(os.path.join(real, 'saves'))
            for name in ('keys.json', 'settings.json'):
                with open(os.path.join(real, layout, name), 'w', encoding='utf-8') as fh:
                    fh.write(name)
            with open(os.path.join(real, 'saves', 'save.json'), 'w', encoding='utf-8') as fh:
                fh.write('{}')
            with patch.object(paths, 'save_base', return_value=top), patch.dict(os.environ):
                mine = own_save('level_chooser')
                assert mine == os.path.join(real, 'level_chooser', 'SixthSenseReborn'), mine
                assert os.environ[paths.USER_DIR_ENV] == mine
                assert paths.user_dir() == mine
                assert os.listdir(mine) == ['config'], 'the save came along: %s' % os.listdir(mine)
                assert sorted(os.listdir(os.path.join(mine, 'config'))) == \
                    ['keys.json', 'settings.json'], layout or 'flat'
        assert os.environ[paths.USER_DIR_ENV] == _scratch_save.FOLDER, \
            "the tests' own override was not put back"


def test_openal_is_the_systems_own_library():
    """Each platform loads its own bundled binary, not another system's library."""
    names = {'win32': 'soft_oal.dll', 'linux': 'libopenal.so.1', 'darwin': 'libopenal.1.dylib'}
    for platform, name in names.items():
        assert paths.openal_lib_name(platform) == name
    assert paths.OPENAL_LIB_NAME == paths.openal_lib_name(sys.platform)
    assert os.path.basename(paths.OPENAL_DLL) == paths.OPENAL_LIB_NAME
    for name in names.values():
        assert os.path.isfile(os.path.join(paths.VENDOR, 'openal', name)), name


def test_on_macos_the_save_goes_in_application_support():
    from unittest.mock import patch
    with tempfile.TemporaryDirectory() as top:
        with patch.object(paths, 'WINDOWS', False), patch.object(paths, 'MACOS', True), \
                patch('os.path.expanduser', return_value=top), \
                patch.dict(os.environ, {'XDG_DATA_HOME': os.path.join(top, 'xdg')}):
            assert paths.user_dir() == _scratch_save.FOLDER, 'save override was ignored'
            os.environ.pop(paths.USER_DIR_ENV)
            expected = os.path.join(top, 'Library', 'Application Support', 'SixthSenseReborn')
            assert paths.user_dir() == expected and os.path.isdir(expected)


def _old_save(top, files=('save.json', 'settings.json', 'keys.json'), folder='SixthSense'):
    """A Sixth Sense save folder under ``top``, each file holding its own name."""
    old = os.path.join(top, folder)
    os.makedirs(os.path.join(old, 'level_chooser'))
    for name in files + ('save.json.bak',):
        with open(os.path.join(old, name), 'w', encoding='utf-8') as fh:
            fh.write(name)
    return old


def _snapshot(folder):
    out = {}
    for dirpath, dirs, files in os.walk(folder):
        for name in files:
            p = os.path.join(dirpath, name)
            with open(p, encoding='utf-8') as fh:
                out[os.path.relpath(p, folder)] = (fh.read(), os.path.getmtime(p))
    return out


def test_the_first_start_copies_sixth_senses_save_once():
    """The dev, 2026-10-04: Reborn's own save folder takes a copy of Sixth Sense's save the
    first time it is made, and never touches Sixth Sense's folder."""
    with tempfile.TemporaryDirectory() as top:
        old = _old_save(top)
        before = _snapshot(old)
        new = os.path.join(top, 'SixthSenseReborn')
        assert paths.adopt_old_save(new, old)
        assert sorted(os.listdir(new)) == ['keys.json', 'save.json', 'settings.json'], \
            'the backup or the choosers came along: %s' % os.listdir(new)
        for name in os.listdir(new):
            with open(os.path.join(new, name), encoding='utf-8') as fh:
                assert fh.read() == name
        assert _snapshot(old) == before, "Sixth Sense's save was changed"
        # a later start leaves Reborn's save as it is
        with open(os.path.join(new, 'save.json'), 'w', encoding='utf-8') as fh:
            fh.write('played in Reborn')
        assert not paths.adopt_old_save(new, old)
        with open(os.path.join(new, 'save.json'), encoding='utf-8') as fh:
            assert fh.read() == 'played in Reborn'


def test_a_save_from_before_the_split_is_copied_too():
    """A defaults.json comes along, for defaults.py to move over as it does any old save."""
    with tempfile.TemporaryDirectory() as top:
        old = _old_save(top, files=('defaults.json',))
        new = os.path.join(top, 'SixthSenseReborn')
        assert paths.adopt_old_save(new, old)
        assert os.listdir(new) == ['defaults.json']


def test_with_no_sixth_sense_save_reborn_starts_fresh():
    with tempfile.TemporaryDirectory() as top:
        new = os.path.join(top, 'SixthSenseReborn')
        assert not paths.adopt_old_save(new, os.path.join(top, 'SixthSense'))
        assert not os.path.exists(new), 'adopt_old_save made the folder with nothing to copy'


def test_user_dir_copies_the_old_save_but_never_under_the_tests_override():
    """The real lookup copies from the folder beside it; the tests' throwaway save never
    takes a copy of anything."""
    from unittest.mock import patch
    with tempfile.TemporaryDirectory() as top:
        _old_save(top)
        with patch.object(paths, 'WINDOWS', True), patch.dict(os.environ, {'APPDATA': top}):
            assert paths.user_dir() == _scratch_save.FOLDER
            assert not os.path.exists(os.path.join(_scratch_save.FOLDER, 'keys.json'))
            os.environ.pop(paths.USER_DIR_ENV)
            new = paths.user_dir()
            assert new == os.path.join(top, 'SixthSenseReborn')
            assert os.path.isfile(os.path.join(new, 'save.json'))


def test_sixthsenseoriginals_folder_comes_before_the_old_one():
    """SixthSenseOriginal renamed its save folder on 2026-10-04; where both are there, the
    renamed one is the newer save."""
    from unittest.mock import patch
    with tempfile.TemporaryDirectory() as top:
        _old_save(top, files=('keys.json',))
        _old_save(top, files=('save.json',), folder='SixthSenseOriginal')
        with patch.object(paths, 'WINDOWS', True), patch.dict(os.environ, {'APPDATA': top}):
            os.environ.pop(paths.USER_DIR_ENV)
            assert os.listdir(paths.user_dir()) == ['save.json']


def test_a_file_that_cannot_be_copied_is_left_out():
    """The game starts with what could be copied rather than not at all."""
    from unittest.mock import patch
    real = shutil.copyfile

    def flaky(src, dst):
        if os.path.basename(src) == 'keys.json':
            raise PermissionError('locked')
        return real(src, dst)
    with tempfile.TemporaryDirectory() as top:
        old = _old_save(top)
        new = os.path.join(top, 'SixthSenseReborn')
        with patch.object(shutil, 'copyfile', flaky):
            assert paths.adopt_old_save(new, old)
        assert sorted(os.listdir(new)) == ['save.json', 'settings.json']
        assert not paths.adopt_old_save(new, old), 'it tried again'


def test_every_test_file_keeps_off_the_real_save():
    """Each test file imports _scratch_save before the game, so none can write the real save,
    whichever shell runs it."""
    here = os.path.dirname(os.path.abspath(__file__))
    forgot = []
    for name in sorted(os.listdir(here)):
        if name.endswith('.py') and not name.startswith('_'):
            with open(os.path.join(here, name), encoding='utf-8') as fh:
                if '\nimport _scratch_save' not in fh.read():
                    forgot.append(name)
    assert not forgot, 'these do not import _scratch_save: %s' % ', '.join(forgot)
    assert os.environ.get(paths.USER_DIR_ENV) == _scratch_save.FOLDER
    # ...and silent: no speech, no sound, no window for a screen reader to announce
    for key, value in _scratch_save.QUIET.items():
        assert os.environ.get(key) == value, key


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
