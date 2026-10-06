"""releaser.py and compiler.py, where they can be checked without building, running git or reaching GitHub:
the version numbering, filing the changelog and putting it back, the release's names and notes, zipping a
build (a small stand-in one), and what the compiler puts inside the executable and beside it.

Nothing here builds, commits, tags or uploads, and the repository's own VERSION and changelog.txt are never
touched: every file a test writes is in a temporary folder.
"""
from __future__ import annotations

import os
import sys
import tempfile
import time

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
import _scratch_save                                             # noqa: E402,F401  never the real save

import compiler                                                      # noqa: E402
import releaser                                                      # noqa: E402
from sixthsense import paths                                         # noqa: E402

CHANGELOG = ('unrelease:\n'
             'The newest change.\n'
             'An older change.\n'
             '\n'
             '26.09.01-1:\n'
             'Something released long ago.\n')


# --- the version ------------------------------------------------------------------------------------

def test_the_first_release_of_a_day_is_number_one():
    assert releaser.next_version([], '26.09.23') == '26.09.23-1'
    assert releaser.next_version(['V26.09.22-4'], '26.09.23') == '26.09.23-1'


def test_a_later_release_the_same_day_counts_up_from_the_tags():
    tags = ['V26.09.23-1', 'V26.09.23-2', 'V26.09.22-7', 'not-a-release', '26.09.23-9', 'V26.09.23-x']
    assert releaser.next_version(tags, '26.09.23') == '26.09.23-3'
    # a gap does not get filled: one past the highest
    assert releaser.next_version(['V26.09.23-1', 'V26.09.23-5'], '26.09.23') == '26.09.23-6'


def test_the_date_is_two_digit_year_month_and_day():
    moment = time.mktime((2026, 9, 3, 12, 0, 0, 0, 0, -1))
    assert releaser.today_stamp(moment) == '26.09.03'


def test_the_tag_and_the_title():
    assert releaser.tag_for('26.09.21-3') == 'V26.09.21-3'
    assert releaser.title_for('26.09.21-3') == 'SixthSenseReborn V26.09.21-3'


# --- the changelog ----------------------------------------------------------------------------------

def test_filing_moves_the_unreleased_lines_under_the_version():
    new, changed, _notes = releaser.plan_changelog(CHANGELOG, '26.09.23-1')
    assert changed
    blocks = compiler._parse_changelog(new)
    assert blocks[0] == ['unrelease:', []]
    assert blocks[1] == ['26.09.23-1:', ['The newest change.', 'An older change.']]
    assert blocks[2] == ['26.09.01-1:', ['Something released long ago.']]


def test_filing_nothing_leaves_the_changelog_as_it_was():
    text = 'unrelease:\n\n26.09.01-1:\nSomething released long ago.\n'
    new, changed, _notes = releaser.plan_changelog(text, '26.09.23-1')
    assert not changed and new == text


def test_a_missing_unrelease_line_is_put_back():
    new, changed, _notes = releaser.plan_changelog('26.09.01-1:\nOld.\n', '26.09.23-1')
    assert changed and new.startswith('unrelease:\n')


def test_the_release_notes_are_that_versions_lines():
    new, _changed, _notes = releaser.plan_changelog(CHANGELOG, '26.09.23-1')
    assert releaser.release_notes(new, '26.09.23-1') == 'The newest change.\nAn older change.'
    assert releaser.release_notes(new, '26.09.30-1') == ''


def test_the_unreleased_lines_are_counted():
    assert compiler.unreleased_lines(CHANGELOG) == ['The newest change.', 'An older change.']
    assert compiler.unreleased_lines('unrelease:\n\n26.09.01-1:\nOld.\n') == []
    assert releaser.MAX_ENTRIES == 100


def test_the_shipped_changelog_opens_on_the_version():
    new, _changed, _notes = releaser.plan_changelog(CHANGELOG, '26.09.23-1')
    assert compiler.without_unrelease(new).startswith('26.09.23-1:\n')
    # unreleased lines are never dropped from a copy
    assert compiler.without_unrelease(CHANGELOG).startswith('unrelease:\n')


def _with_temp_files(test):
    """Run ``test`` with the releaser's VERSION and changelog pointed at a temporary folder, the tags and
    the Y/N answer faked, so nothing real is read or written."""
    saved = (releaser.VERSION_FILE, releaser.CHANGELOG, releaser.all_tags, releaser.ask,
             releaser.today_stamp)
    with tempfile.TemporaryDirectory() as folder:
        releaser.VERSION_FILE = os.path.join(folder, 'VERSION')
        releaser.CHANGELOG = os.path.join(folder, 'changelog.txt')
        releaser.all_tags = lambda: ['V26.09.23-1']
        releaser.ask = lambda question: True
        releaser.today_stamp = lambda now=None: '26.09.23'
        try:
            test(folder)
        finally:
            (releaser.VERSION_FILE, releaser.CHANGELOG, releaser.all_tags, releaser.ask,
             releaser.today_stamp) = saved


#: Five entries: the fewest a release may carry.
FIVE = ('unrelease:\n'
        'The newest change.\n'
        'Another change.\n'
        'A third change.\n'
        'A fourth change.\n'
        'An older change.\n'
        '\n'
        '26.09.01-1:\n'
        'Something released long ago.\n')


def test_preparing_sets_the_version_and_files_the_changelog_and_a_failed_build_puts_them_back():
    def test(folder):
        releaser.write_text(releaser.VERSION_FILE, '26.09.21-1\n')
        releaser.write_text(releaser.CHANGELOG, FIVE)
        saved = releaser.step_prepare()
        assert saved is not None and saved[0] == '26.09.23-2'
        assert open(releaser.VERSION_FILE, encoding='utf-8').read() == '26.09.23-2\n'
        filed = open(releaser.CHANGELOG, encoding='utf-8').read()
        assert '26.09.23-2:\nThe newest change.' in filed
        releaser.restore(saved)
        assert open(releaser.VERSION_FILE, encoding='utf-8').read() == '26.09.21-1\n'
        assert open(releaser.CHANGELOG, encoding='utf-8').read() == FIVE
    _with_temp_files(test)


def _checked(status, changelog, answer=False):
    """step_check with git, gh, the changelog and the Y/N answer faked: what it said, and
    its answer.  Each question asked is added to what it said, marked with "?? "."""
    said = []
    saved = (releaser.git, releaser.gh_path, releaser.gh, releaser.read_changelog, releaser.say,
             releaser.ask)
    replies = {'status': (True, status), 'fetch': (True, ''), 'rev-list': (True, '0\t0')}
    releaser.git = lambda *a: replies[a[0]]
    releaser.gh_path = lambda: 'gh'
    releaser.gh = lambda *a: (True, '')
    releaser.read_changelog = lambda: changelog
    releaser.say = lambda text='': said.append(text)
    releaser.ask = lambda question: said.append('?? ' + question) or answer
    try:
        return said, releaser.step_check()
    finally:
        (releaser.git, releaser.gh_path, releaser.gh, releaser.read_changelog,
         releaser.say, releaser.ask) = saved


def test_the_check_names_its_problems_not_the_waiting_changes():
    """The verdict came straight after "11 change(s) are waiting to be released" and said
    "the release cannot go ahead until those are fixed", as if the changes were the
    problem.  It now names each problem again, and the count says it is fine."""
    said, ready = _checked(' M releaser.py', FIVE)
    assert ready is False
    assert '  5 change(s) are waiting to be released, which is fine.' in said, said
    at = said.index('  the release cannot go ahead until this is fixed:')
    assert said[at + 1] == '    1. there are changes that are not committed. Commit them first:', said
    assert not any('those are fixed' in line for line in said)
    said, ready = _checked('', FIVE)
    assert ready is True and said[-1] == '  everything is ready.', said


FOUR = FIVE.replace('A fourth change.\n', '')


def test_fewer_than_five_entries_do_not_make_a_release():
    """tsatria03, 2026-09-24: a version needs at least five entries.  Four are refused
    when the question to release anyway is answered N, and nothing is filed or changed."""
    assert releaser.MIN_ENTRIES == 5

    def test(folder):
        releaser.ask = lambda question: False
        releaser.write_text(releaser.VERSION_FILE, '26.09.21-1\n')
        releaser.write_text(releaser.CHANGELOG, FOUR)
        assert releaser.step_prepare() is None
        assert open(releaser.VERSION_FILE, encoding='utf-8').read() == '26.09.21-1\n'
        assert open(releaser.CHANGELOG, encoding='utf-8').read() == FOUR
    _with_temp_files(test)
    said, ready = _checked('', FOUR, answer=False)
    assert ready is False
    assert '?? Release anyway with 4 change(s)?' in said, said
    at = said.index('  the release cannot go ahead until this is fixed:')
    assert said[at + 1] == ('    1. only 4 change(s) are under "unrelease:", and a release '
                            'needs at least 5.'), said
    # said once before the question, and named once more in the verdict, not twice before it
    assert said.count('  only 4 change(s) are under "unrelease:", and a release needs at least 5.') == 1


def test_fewer_than_five_can_be_released_anyway():
    """tsatria03, 2026-09-24: the force override.  Answering Y to releasing anyway lets
    the check pass and the prepare step file the four; a full release asks only once."""
    said, ready = _checked('', FOUR, answer=True)
    assert ready is True, said
    assert '  releasing anyway with 4 change(s).' in said, said
    assert said[-1] == '  everything is ready.', said

    def test(folder):
        releaser.write_text(releaser.VERSION_FILE, '26.09.21-1\n')
        releaser.write_text(releaser.CHANGELOG, FOUR)
        saved = releaser.step_prepare()
        assert saved is not None and saved[0] == '26.09.23-2'
        assert '26.09.23-2:\nThe newest change.' in open(releaser.CHANGELOG, encoding='utf-8').read()
        # forced, as a full release calls it after the check: no second question
        releaser.write_text(releaser.CHANGELOG, FOUR)
        asked = []
        releaser.ask = lambda question: asked.append(question) or True
        assert releaser.step_prepare(forced=True) is not None
        assert not any('anyway' in q for q in asked), asked
    _with_temp_files(test)


def test_other_problems_are_not_hidden_behind_the_question():
    """With another problem in the way, the check does not ask to release anyway, since
    the release could not go ahead either way; the shortfall is named with the rest."""
    said, ready = _checked(' M releaser.py', FOUR, answer=True)
    assert ready is False
    assert not any(line.startswith('?? ') for line in said), said
    assert '    2. only 4 change(s) are under "unrelease:", and a release needs at least 5.' in said, said


def test_nothing_waiting_is_never_released_anyway():
    said, ready = _checked('', 'unrelease:\n\n26.09.01-1:\nOld.\n', answer=True)
    assert ready is False
    assert not any(line.startswith('?? ') for line in said), said


def test_preparing_with_nothing_waiting_does_nothing():
    def test(folder):
        text = 'unrelease:\n\n26.09.01-1:\nOld.\n'
        releaser.write_text(releaser.VERSION_FILE, '26.09.21-1\n')
        releaser.write_text(releaser.CHANGELOG, text)
        assert releaser.step_prepare() is None
        assert open(releaser.VERSION_FILE, encoding='utf-8').read() == '26.09.21-1\n'
        assert open(releaser.CHANGELOG, encoding='utf-8').read() == text
    _with_temp_files(test)


# --- the zip ----------------------------------------------------------------------------------------

def test_the_zip_is_named_for_the_version():
    assert releaser.zip_path('26.09.23-1') == os.path.join(
        ROOT, 'dist', releaser.zip_name('26.09.23-1'))
    assert releaser.find_zip('00.00.00-0') is None


def test_each_system_has_its_own_zip():
    """tunmi13productions, 2026-09-28: one release carries both builds, each in its own zip."""
    assert releaser.zip_name('26.09.28-1', compiler.SYSTEMS['win32']) == 'SixthSenseReborn-Win-26.09.28-1.zip'
    assert releaser.zip_name('26.09.28-1', compiler.SYSTEMS['linux']) == 'SixthSenseReborn-Linux-26.09.28-1.tar.gz'
    assert releaser.zip_name('26.09.28-1') == releaser.zip_name('26.09.28-1', compiler.SYSTEM)


class _Release:
    """Stands in for gh and the question, for adding a zip to a release already made."""

    def __init__(self, assets, answer=True, upload_ok=True):
        self.assets, self.answer, self.upload_ok = assets, answer, upload_ok
        self.uploaded = []
        self.saved = (releaser.release_assets, releaser.ask, releaser.gh)

    def __enter__(self):
        releaser.release_assets = lambda tag: None if self.assets is None else list(self.assets)
        releaser.ask = lambda question: self.answer

        def gh(*args, capture=True):
            assert args[:2] == ('release', 'upload') and '--clobber' not in args, args
            self.uploaded.append(os.path.basename(args[3]))
            return self.upload_ok, ''
        releaser.gh = gh
        return self

    def __exit__(self, *exc):
        releaser.release_assets, releaser.ask, releaser.gh = self.saved
        return False


def test_the_second_system_adds_its_zip_to_the_release_and_replaces_nothing():
    with tempfile.TemporaryDirectory() as folder:
        archive = os.path.join(folder, 'SixthSenseReborn-Linux-26.09.28-1.tar.gz')
        open(archive, 'wb').close()
        with _Release(['SixthSenseReborn-Win-26.09.28-1.zip']) as r:
            assert releaser.add_to_release('V26.09.28-1', archive) is True
        assert r.uploaded == ['SixthSenseReborn-Linux-26.09.28-1.tar.gz']
        with _Release(['SixthSenseReborn-Win-26.09.28-1.zip', 'SixthSenseReborn-Linux-26.09.28-1.tar.gz']) as r:
            assert releaser.add_to_release('V26.09.28-1', archive) is True
        assert r.uploaded == [], 'a zip already on the release was uploaded again'
        with _Release(['SixthSenseReborn-Win-26.09.28-1.zip'], answer=False) as r:
            assert releaser.add_to_release('V26.09.28-1', archive) is False
        assert r.uploaded == []
        with _Release(None) as r:
            assert releaser.add_to_release('V26.09.28-1', archive) is False
        assert r.uploaded == []


def _fake_build(folder, version):
    build = os.path.join(folder, 'SixthSenseReborn')
    os.makedirs(os.path.join(build, 'game'))
    for name, body in (('SixthSenseReborn.exe', 'exe'), ('VERSION', version + '\n'),
                       (os.path.join('docks', 'todo list.txt'), 'todo'),
                       (os.path.join('game', 'SoundList.plist'), 'x')):
        os.makedirs(os.path.dirname(os.path.join(build, name)), exist_ok=True)
        with open(os.path.join(build, name), 'w', encoding='utf-8') as fh:
            fh.write(body)
    return build


def test_the_releaser_zips_the_build_under_one_folder():
    import zipfile
    saved = releaser.zip_path
    with tempfile.TemporaryDirectory() as folder:
        build = _fake_build(folder, '26.09.23-1')
        releaser.zip_path = lambda version: os.path.join(folder, 'SixthSenseReborn-Win-%s.zip' % version)
        try:
            archive = releaser.package(build, '26.09.23-1')
            with zipfile.ZipFile(archive) as zf:
                names = sorted(zf.namelist())
            leftover = os.path.exists(archive + '.part')
        finally:
            releaser.zip_path = saved
    # The archive extracts to the current system's build folder.
    assert names == [compiler.FOLDER + '/' + name for name in
                     ('SixthSenseReborn.exe', 'VERSION', 'docks/todo list.txt', 'game/SoundList.plist')]
    assert not leftover


def test_the_linux_build_is_a_tar_gz_that_extracts_to_a_linux_folder():
    """tunmi13productions, 2026-09-28: a gzipped tar, which every Linux opens, under one SixthSenseReborn-Linux
    folder, like the Windows zip."""
    import tarfile
    saved = (releaser.zip_path, compiler.FOLDER)
    with tempfile.TemporaryDirectory() as folder:
        build = _fake_build(folder, '26.09.28-1')
        releaser.zip_path = lambda version: os.path.join(folder, 'SixthSenseReborn-Linux-%s.tar.gz' % version)
        compiler.FOLDER = 'SixthSenseReborn-Linux'
        try:
            archive = releaser.package(build, '26.09.28-1')
            with tarfile.open(archive, 'r:gz') as tf:
                names = sorted(tf.getnames())
            leftover = os.path.exists(archive + '.part')
        finally:
            releaser.zip_path, compiler.FOLDER = saved
    assert names == ['SixthSenseReborn-Linux/SixthSenseReborn.exe', 'SixthSenseReborn-Linux/VERSION',
                     'SixthSenseReborn-Linux/docks/todo list.txt',
                     'SixthSenseReborn-Linux/game/SoundList.plist'], names
    assert not leftover


def test_the_releaser_will_not_zip_a_build_made_for_another_version():
    saved = (releaser.BUILD_DIR, releaser.ask, releaser.package)
    zipped = []
    with tempfile.TemporaryDirectory() as folder:
        releaser.BUILD_DIR = _fake_build(folder, '26.09.21-1')
        releaser.ask = lambda question: True
        releaser.package = lambda build, version: zipped.append(version)
        try:
            assert releaser.built_version() == '26.09.21-1'
            assert releaser.step_package('26.09.23-1') is False
            assert zipped == []
            assert releaser.step_package('26.09.21-1') is True
            assert zipped == ['26.09.21-1']
        finally:
            releaser.BUILD_DIR, releaser.ask, releaser.package = saved


def test_answering_no_skips_the_zip():
    saved = (releaser.BUILD_DIR, releaser.ask, releaser.package)
    zipped = []
    with tempfile.TemporaryDirectory() as folder:
        releaser.BUILD_DIR = _fake_build(folder, '26.09.23-1')
        releaser.ask = lambda question: False
        releaser.package = lambda build, version: zipped.append(version)
        try:
            assert releaser.step_package('26.09.23-1') is None
        finally:
            releaser.BUILD_DIR, releaser.ask, releaser.package = saved
    assert zipped == []


# --- the compiler -----------------------------------------------------------------------------------

class _Args:
    def __init__(self, **flags):
        for name in ('embed', 'onefile', 'no_game', 'console', 'clean', 'dry_run'):
            setattr(self, name, flags.get(name, False))


def test_the_compiler_no_longer_files_the_changelog_or_zips():
    for name in ('plan_changelog', 'prepare_release_files', 'first_version', 'package', 'PACK_STEPS'):
        assert not hasattr(compiler, name), name
    assert not any('--no-package' in flags for _text, flags in compiler.MENU)


def test_the_player_documents_ship_in_a_docks_folder():
    """The build lays docks\\ out as the repository does; VERSION and the license stay at the top."""
    with tempfile.TemporaryDirectory() as build:
        compiler.copy_side_files(build)
        compiler.strip_shipped_changelog(build)
        top = sorted(os.listdir(build))
        docks = sorted(os.listdir(os.path.join(build, 'docks')))
        shipped = open(os.path.join(build, 'docks', 'changelog.txt'), encoding='utf-8').read()
    assert top == ['VERSION', 'docks', 'license.txt'], top
    assert docks == ['changelog.txt', 'readme.txt', 'todo list.txt'], docks
    # an empty unrelease: heading is taken out of the copy in docks\, not left in it
    assert shipped == compiler.without_unrelease(shipped)


def test_the_player_documents_are_read_from_docks():
    for name in ('readme.txt', 'changelog.txt', 'todo list.txt'):
        assert os.path.isfile(os.path.join(ROOT, 'docks', name)), name
    assert releaser.CHANGELOG == os.path.join(ROOT, 'docks', 'changelog.txt')
    assert releaser.CHANGELOG_GIT == 'docks/changelog.txt'


def test_the_players_readme_has_no_markdown():
    """A screen reader reads every # * | and ` aloud, so the readme a player opens has none."""
    with open(os.path.join(ROOT, 'docks', 'readme.txt'), encoding='utf-8') as fh:
        text = fh.read()
    assert text.strip()
    for mark in ('#', '*', '|', '`'):
        assert mark not in text, mark


def test_a_folder_build_puts_nothing_of_the_games_inside():
    """Nothing of the game's own goes inside a folder build; only the third-party licenses
    do (tsatria03, 2026-09-25)."""
    cmd = compiler.command(_Args(console=True))
    assert '--onefile' not in cmd
    added = [cmd[i + 1] for i, part in enumerate(cmd) if part == '--add-data']
    assert added == [compiler.LICENSES_STAGE + os.pathsep + 'licenses'], added
    assert cmd[-1] == compiler.ENTRY


def test_the_third_party_licenses_go_inside_and_license_txt_stays_beside():
    """tsatria03, 2026-09-25: the licenses of OpenAL Soft, the NVDA client, Prism and pygame
    go inside the executable; the port's own license.txt stays beside it, and nothing is
    copied into a licenses folder beside it any more."""
    for flags in ({}, {'embed': True}, {'onefile': True}):
        cmd = compiler.command(_Args(**flags))
        added = [cmd[i + 1] for i, part in enumerate(cmd) if part == '--add-data']
        assert compiler.LICENSES_STAGE + os.pathsep + 'licenses' in added, (flags, added)
    assert not hasattr(compiler, 'copy_licenses')
    assert ('LICENSE', 'license.txt') in compiler.SIDE_FILES
    with tempfile.TemporaryDirectory() as folder:
        stage = os.path.join(folder, 'licenses')
        copied = compiler.stage_licenses(stage)
        found = [os.path.relpath(os.path.join(d, f), stage).replace(os.sep, '/')
                 for d, _s, fs in os.walk(stage) for f in fs]
    assert copied == len(found) and copied > 0, found
    assert 'openal-soft/license.txt' in found
    assert ('nvda-controller-client/license.txt' in found) == (compiler.system_key() == 'win32')


def test_embedding_puts_the_sounds_and_the_data_inside_one_executable():
    with tempfile.TemporaryDirectory() as bundle:
        os.makedirs(os.path.join(bundle, 'sounds', 'used', 'sfx'))
        os.makedirs(os.path.join(bundle, 'sounds', 'unused', 'sfx'))
        data = compiler.embedded_data(bundle)
        cmd = compiler.command(_Args(embed=True, console=True), data)
    assert '--onefile' in cmd
    assert cmd[cmd.index('--distpath') + 1] == compiler.output_dir()
    assert cmd[cmd.index('--name') + 1] == 'SixthSenseReborn'
    added = [cmd[i + 1] for i, part in enumerate(cmd) if part == '--add-data']
    assert compiler.EMBED_STAGE + os.pathsep + 'game' in added
    assert os.path.join(bundle, 'sounds', 'used') + os.pathsep + 'game/sounds/used' in added
    assert not any('unused' in a for a in added), 'sounds/unused went inside: %s' % added
    # the text a player reads is never among what goes inside; only the third-party
    # licenses are (since 2026-09-25), never the port's own license.txt
    assert not any('changelog' in a or 'todo' in a or 'license.txt' in a.lower() for a in added)
    assert compiler.LICENSES_STAGE + os.pathsep + 'licenses' in added


def test_a_build_carries_only_the_sounds_the_game_plays():
    """tsatria03, 2026-10-06: "When I compile the game, it should only build with
    sounds/used."  sounds/unused stays in the repository; the blooper was never to ship."""
    with tempfile.TemporaryDirectory() as bundle:
        for rel in ('sounds/used/sfx/misc/ui_select.wav',
                    'sounds/unused/speech/game/paused.wav',
                    'sounds/unused/sfx/misc/coin_sound.wav'):
            p = os.path.join(bundle, *rel.split('/'))
            os.makedirs(os.path.dirname(p), exist_ok=True)
            open(p, 'wb').close()
        assert compiler.sound_files(bundle) == [os.path.join('sounds', 'used', 'sfx', 'misc',
                                                             'ui_select.wav')]
    real = compiler.sound_files(paths.game())
    assert real and not any('unused' in name or 'blooper' in name for name in real), \
        [n for n in real if 'unused' in n or 'blooper' in n]


def test_a_flat_bundle_embeds_its_top_folder_alone():
    with tempfile.TemporaryDirectory() as bundle:
        assert compiler.embedded_data(bundle) == [(compiler.EMBED_STAGE, 'game')]


def test_every_build_lands_in_one_folder():
    """tsatria03, 2026-09-25: the folder is SixthSenseReborn-Windows, and the executable inside it
    is still SixthSenseReborn.exe."""
    assert compiler.output_dir(_Args()) == compiler.output_dir(_Args(embed=True)) \
        == os.path.join(ROOT, 'dist', compiler.FOLDER) == releaser.BUILD_DIR


def test_each_system_builds_its_own_folder_with_its_own_libraries():
    """tunmi13productions, 2026-09-28: the same compiler builds on Linux, into SixthSenseReborn-Linux, around an
    executable with no .exe, with OpenAL Soft's Linux library and no NVDA client."""
    assert compiler.system_key('win32') == 'win32'
    assert compiler.system_key('linux') == compiler.system_key('linux2') == 'linux'
    assert compiler.system_key('darwin') == 'darwin'
    win, linux = compiler.SYSTEMS['win32'], compiler.SYSTEMS['linux']
    assert (win['folder'], win['exe']) == ('Windows', 'SixthSenseReborn.exe')
    assert (linux['folder'], linux['exe']) == ('Linux', 'SixthSenseReborn')
    assert [src for src, _ in linux['binaries']] == ['vendor/openal/libopenal.so.1']
    assert not any('nvda' in src for src, _ in linux['binaries'])
    assert not any(folder == 'nvda-controller-client' for folder, _ in linux['licenses'])
    for system in (win, linux, compiler.SYSTEMS['darwin']):
        for src, _ in system['binaries']:
            assert os.path.isfile(os.path.join(ROOT, src)), src
        for _folder, files in system['licenses']:
            for src in files:
                assert os.path.isfile(os.path.join(ROOT, src)), src
    assert compiler.SYSTEM is compiler.SYSTEMS[compiler.system_key()]
    assert compiler.FOLDER == 'SixthSenseReborn-' + compiler.SYSTEM['folder']


def test_macos_builds_a_copyable_native_app():
    from unittest.mock import patch
    with patch.object(compiler, 'system_key', return_value='darwin'):
        for arch in ('arm64', 'x86_64'):
            with patch.object(compiler.platform, 'machine', return_value=arch):
                for flags in ({}, {'console': True}, {'embed': True}, {'onefile': True}):
                    cmd = compiler.command(_Args(**flags))
                    assert cmd[cmd.index('--target-arch') + 1] == arch
                    assert ('--windowed' in cmd) == (not flags.get('console', False))
                    if not flags.get('console', False):
                        assert '--onefile' not in cmd
                        assert compiler.APP_DOCS_STAGE + os.pathsep + '.' in cmd
    for system in ('win32', 'linux'):
        with patch.object(compiler, 'system_key', return_value=system):
            assert '--target-arch' not in compiler.command(_Args())
            assert '--windowed' in compiler.command(_Args())


def test_a_folder_build_is_moved_to_the_windows_folder():
    """PyInstaller names a folder build after the executable, dist\\SixthSenseReborn; the compiler
    moves it to dist\\SixthSenseReborn-Windows, and clears both before the next build."""
    saved = compiler.HERE
    with tempfile.TemporaryDirectory() as here:
        compiler.HERE = here
        try:
            built = compiler.pyinstaller_dir()
            dest = compiler.output_dir()
            assert built == os.path.join(here, 'dist', 'SixthSenseReborn')
            os.makedirs(os.path.join(built, '_internal'))
            open(os.path.join(built, 'SixthSenseReborn.exe'), 'w').close()
            compiler.move_folder_build(dest)
            assert not os.path.exists(built)
            assert os.path.isfile(os.path.join(dest, 'SixthSenseReborn.exe'))
            assert os.path.isdir(os.path.join(dest, '_internal'))
            os.makedirs(built)
            compiler.clear_output(dest)
            assert not os.path.exists(built) and not os.path.exists(dest)
        finally:
            compiler.HERE = saved


def test_the_stage_holds_only_what_the_game_reads():
    with tempfile.TemporaryDirectory() as bundle:
        for name in ('SoundList.plist', 'type1.plist', 'g_CH1_E', 'a_CH1_E.txt', 's_CH1_E.txt',
                     'sixsense', 'Icon.png', 'stage1ground', 'PkgInfo'):
            open(os.path.join(bundle, name), 'w').close()
        saved = compiler.EMBED_STAGE
        compiler.EMBED_STAGE = os.path.join(bundle, 'stage')
        try:
            names = compiler.stage_embedded(bundle)
            staged = sorted(os.listdir(compiler.EMBED_STAGE))
        finally:
            compiler.EMBED_STAGE = saved
    assert names == staged == sorted(['SoundList.plist', 'type1.plist', 'g_CH1_E', 'a_CH1_E.txt',
                                      's_CH1_E.txt'])


# --- the workflow (tunmi13productions, 2026-10-05) --------------------------------------------------------

def test_a_release_tag_gives_its_version():
    assert releaser.version_from_tag('V26.10.05-1') == '26.10.05-1'
    assert releaser.version_from_tag('V26.10.05-12') == '26.10.05-12'
    for bad in ('26.10.05-1', 'V26.10.05', 'v26.10.05-1', 'V26.10.05-x', 'V26.10.5-1', 'main', '', None):
        assert releaser.version_from_tag(bad) is None, bad


def test_a_release_carries_the_four_archives():
    assert releaser.release_archive_names('26.10.05-1') == [
        'SixthSenseReborn-Win-26.10.05-1.zip', 'SixthSenseReborn-Linux-26.10.05-1.tar.gz',
        'SixthSenseReborn-macOS-arm64-26.10.05-1.tar.gz', 'SixthSenseReborn-macOS-x86_64-26.10.05-1.tar.gz']
    wanted = releaser.release_archive_names('26.10.05-1')
    for key in ('win32', 'linux'):                      # what each system names its own is among them
        assert releaser.zip_name('26.10.05-1', compiler.SYSTEMS[key]) in wanted
    assert releaser.zip_name('26.10.05-1', compiler.SYSTEMS['darwin']) in wanted \
        or compiler.platform.machine() not in ('arm64', 'x86_64')


class _Publishing:
    """Stands in for gh while the workflow's release job runs: what it was asked, and what is on GitHub."""

    def __init__(self, assets=None, exists=False, ok=True):
        self.assets, self.exists, self.ok = assets or [], exists, ok
        self.calls = []
        self.saved = (releaser.gh, releaser.release_assets)

    def __enter__(self):
        def gh(*args, capture=True):
            self.calls.append(args)
            if args[:2] == ('release', 'view'):
                return self.exists, ''
            assert '--clobber' not in args, args
            return self.ok, ''
        releaser.gh = gh
        releaser.release_assets = lambda tag: list(self.assets)
        return self

    def __exit__(self, *exc):
        releaser.gh, releaser.release_assets = self.saved
        return False

    def made(self, verb):
        return [c for c in self.calls if c[:2] == ('release', verb)]


def _archives(folder, version, names=None):
    names = releaser.release_archive_names(version) if names is None else names
    for name in names:
        os.makedirs(os.path.join(folder, 'archive-x'), exist_ok=True)
        open(os.path.join(folder, 'archive-x', name), 'wb').close()


def test_the_workflow_publishes_nothing_while_an_archive_is_missing():
    with tempfile.TemporaryDirectory() as folder:
        names = releaser.release_archive_names('26.10.05-1')
        _archives(folder, '26.10.05-1', names[:3])
        with _Publishing() as g:
            assert releaser.ci_release('V26.10.05-1', folder) == 1
        assert g.calls == [], 'it reached GitHub with a release that was not whole'


def test_the_workflow_creates_the_release_with_all_four_archives_and_the_notes():
    def test(_folder):
        with open(releaser.CHANGELOG, 'w', encoding='utf-8', newline='\n') as fh:
            fh.write(releaser.plan_changelog(FIVE, '26.10.05-1')[0])
        with tempfile.TemporaryDirectory() as folder:
            _archives(folder, '26.10.05-1')
            with _Publishing() as g:
                assert releaser.ci_release('V26.10.05-1', folder) == 0
        (create,) = g.made('create')
        assert [os.path.basename(a) for a in create[3:7]] == releaser.release_archive_names('26.10.05-1'), create
        assert '--verify-tag' in create and '--clobber' not in create
        assert create[create.index('--title') + 1] == 'SixthSenseReborn V26.10.05-1'
        assert g.made('upload') == []
    _with_temp_files(test)


def test_the_workflow_only_adds_what_a_release_already_made_lacks():
    with tempfile.TemporaryDirectory() as folder:
        _archives(folder, '26.10.05-1')
        names = releaser.release_archive_names('26.10.05-1')
        with _Publishing(assets=names[:2], exists=True) as g:
            assert releaser.ci_release('V26.10.05-1', folder) == 0
        assert g.made('create') == []
        assert [os.path.basename(c[3]) for c in g.made('upload')] == names[2:]
        with _Publishing(assets=names, exists=True) as g:
            assert releaser.ci_release('V26.10.05-1', folder) == 0
        assert g.made('upload') == [], 'an archive already on the release was uploaded again'


def test_a_failed_upload_is_a_failed_workflow():
    with tempfile.TemporaryDirectory() as folder:
        _archives(folder, '26.10.05-1')
        with _Publishing(ok=False):
            assert releaser.ci_release('V26.10.05-1', folder) == 1


def test_the_workflow_refuses_a_version_that_is_not_the_tag():
    def test(_folder):
        built = []
        saved = (compiler.main, releaser.read_version)
        compiler.main = lambda flags: built.append(flags) or 0
        releaser.read_version = lambda: '26.10.04-1'
        try:
            assert releaser.ci_build('V26.10.05-1') == 1
            assert releaser.ci_build('main') == 1
        finally:
            compiler.main, releaser.read_version = saved
        assert built == [], 'it built something the tag does not name'
    _with_temp_files(test)


def test_the_workflow_builds_a_single_exe_but_the_mac_builds_its_app():
    def test(_folder):
        got = []
        saved = (compiler.main, releaser.package, releaser.BUILD_DIR, releaser.read_version)
        with tempfile.TemporaryDirectory() as folder:
            compiler.main = lambda flags: got.append(flags) or 0
            releaser.package = lambda build, version: os.path.join(folder, 'x')
            releaser.BUILD_DIR = folder
            releaser.read_version = lambda: '26.10.05-1'
            try:
                assert releaser.ci_build('V26.10.05-1') == 0
            finally:
                compiler.main, releaser.package, releaser.BUILD_DIR, releaser.read_version = saved
        assert got == [[] if compiler.system_key() == 'darwin' else ['--embed']], got
    _with_temp_files(test)


def test_prepare_and_tag_builds_zips_and_uploads_nothing():
    assert releaser.MENU[0][1] is releaser.prepare_and_tag
    src = open(os.path.join(ROOT, 'releaser.py'), encoding='utf-8').read()
    body = src[src.index('def prepare_and_tag'):src.index('def step_add_build')]
    for step in ('step_build', 'step_package', 'step_upload', 'compiler.main'):
        assert step not in body, step
    for step in ('step_check', 'step_prepare', 'step_commit', 'step_tag'):
        assert step in body, step
    assert any(text.startswith('Full release') for text, _action in releaser.MENU), 'the full release stays'


def test_the_workflow_file_names_the_same_calls():
    text = open(os.path.join(ROOT, '.github', 'workflows', 'release.yml'), encoding='utf-8').read()
    assert "tags: ['V*']" in text
    assert 'releaser.py --ci-build' in text and 'releaser.py --ci-release' in text
    assert 'needs: build' in text and 'contents: write' in text
    assert 'workflow_dispatch:' in text and "if: github.ref_type == 'tag'" in text and '--dry-run' in text
    for system in ('windows-latest', 'ubuntu-latest', 'macos-15', 'macos-15-intel'):
        assert system in text, system
    assert releaser.cli(['--ci-build']) is None and releaser.cli([]) is None, 'a bare flag opens the menu'


def test_a_test_run_checks_the_release_and_touches_nothing_on_github():
    def test(_folder):
        with open(releaser.CHANGELOG, 'w', encoding='utf-8', newline='\n') as fh:
            fh.write(releaser.plan_changelog(FIVE, '26.10.05-1')[0])
        with tempfile.TemporaryDirectory() as archives:
            _archives(archives, '26.10.05-1')
            with _Publishing() as g:
                assert releaser.ci_release('V26.10.05-1', archives, dry_run=True) == 0
            assert g.calls == [], 'a test run reached GitHub'
            _archives(archives, '26.10.05-2', releaser.release_archive_names('26.10.05-2')[:3])
            with _Publishing() as g:
                assert releaser.ci_release('V26.10.05-2', archives, dry_run=True) == 1, \
                    'a test run passed with an archive missing'
    _with_temp_files(test)


def test_a_run_that_was_not_started_by_a_tag_never_publishes():
    saved = os.getcwd()
    calls = []
    real = releaser.ci_release
    releaser.ci_release = lambda *a: calls.append(a) or 0
    try:
        on_a_branch = {'GITHUB_ACTIONS': 'true', 'GITHUB_REF_TYPE': 'branch'}
        assert releaser.cli(['--ci-release', 'V26.10.05-1', 'archives'], on_a_branch) == 1
        assert calls == []
        assert releaser.cli(['--ci-release', 'V26.10.05-1', 'archives', '--dry-run'], on_a_branch) == 0
        assert calls == [('V26.10.05-1', 'archives', True)]
        calls.clear()
        on_a_tag = {'GITHUB_ACTIONS': 'true', 'GITHUB_REF_TYPE': 'tag'}
        assert releaser.cli(['--ci-release', 'V26.10.05-1', 'archives'], on_a_tag) == 0
        assert calls == [('V26.10.05-1', 'archives', False)]
        assert releaser.cli(['--ci-release', 'V26.10.05-1', 'archives', '--other'], on_a_tag) is None
    finally:
        releaser.ci_release = real
        os.chdir(saved)


class _Git:
    """Stands in for git, gh and the question while the test run is started."""

    def __init__(self, ahead='0', upstream=True, answer=True, run_ok=True, branch='main'):
        self.ahead, self.upstream, self.answer, self.run_ok, self.branch = ahead, upstream, answer, run_ok, branch
        self.started = []
        self.saved = (releaser.git, releaser.gh, releaser.gh_path, releaser.ask)

    def __enter__(self):
        def git(*args, capture=True):
            if args[:2] == ('rev-parse', '--abbrev-ref'):
                return True, self.branch
            if args[:1] == ('rev-list',):
                return self.upstream, self.ahead
            return True, ''

        def gh(*args, capture=True):
            self.started.append(args)
            return self.run_ok, 'denied' if not self.run_ok else ''
        releaser.git, releaser.gh = git, gh
        releaser.gh_path = lambda: 'gh'
        releaser.ask = lambda question: self.answer
        return self

    def __exit__(self, *exc):
        releaser.git, releaser.gh, releaser.gh_path, releaser.ask = self.saved
        return False


def test_the_test_run_starts_the_workflow_on_the_pushed_branch():
    with _Git() as g:
        assert releaser.step_test_workflow() is True
    assert g.started == [('workflow', 'run', 'release.yml', '--ref', 'main')]
    with _Git(ahead='2') as g:
        assert releaser.step_test_workflow() is False, 'it tested what GitHub does not have'
    with _Git(upstream=False) as g:
        assert releaser.step_test_workflow() is False
    with _Git(answer=False) as g:
        assert releaser.step_test_workflow() is False
    with _Git(branch='HEAD') as g:
        assert releaser.step_test_workflow() is False
    with _Git(run_ok=False) as g:
        assert releaser.step_test_workflow() is False
    assert g.started and not any('release' == a[0] and a[1] == 'create' for a in g.started)


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
