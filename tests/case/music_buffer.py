"""Changing the music or the ambience really lets go of the file it leaves behind.

``music.py``'s ``_drop_buffer`` has to free its file in the order OpenAL insists on: stop
the source, take the buffer off it, then delete the buffer.  ``alDeleteBuffers`` refuses a
buffer that is still attached and answers AL_INVALID_OPERATION, so a delete that comes
first frees nothing and leaves the whole file in memory for as long as the game runs.
These are the largest sounds in the game, 2 to 3 MB each, and a level change swaps two of
them, so it added up: on 2026-09-23, with the freeing switched off, 200 swaps grew the
process by over a gigabyte.

``music_memory.py`` catches that by watching the process's memory, which takes a ``psapi``
call and so only runs on Windows.  This asks OpenAL instead, through ``alIsBuffer``:
a buffer that was really deleted is no longer a buffer, and one the delete refused still
is.  That is the same regression caught at its cause rather than its symptom, and it runs
on every system the release builds for.

Buffer names may be handed out again once they are freed, so none of this compares one id
with another; it only ever asks which of the ids it has seen are still alive.

It opens the audio device, so run it with OpenAL's null driver, and it writes the save
through ``didFinishLaunching``: see the safe way to run the tests.
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import _scratch_save                                             # noqa: E402,F401  never the real save

from sixthsense.game.app_delegate import AppDelegate             # noqa: E402

#: the music files a level change swaps between, as Stage_1_E asks for them
MUSIC = ['bgm_forest', 'bgm_cave']
AMBIENCE = ['bgm_cave_amb', 'bgm_forest_amb']
SWAPS = 20


def _playback():
    app = AppDelegate.shared()
    if app.playback is None:
        app.didFinishLaunching()
    return app.playback


def _loaded(pb, buffer):
    """Whether OpenAL still holds that buffer, which is what a failed delete leaves."""
    return bool(pb.al.alIsBuffer(buffer))


def test_dropping_the_music_frees_its_file():
    pb = _playback()
    try:
        pb.startBGPlayer_type_soundGain_Loop_(MUSIC[0], 'wav', 0.02, True)
        buffer = pb.bgPlayer.buffer
        assert buffer and _loaded(pb, buffer), 'the music never loaded, so there is nothing to free'
        pb.bgPlayer._drop_buffer()
        assert not _loaded(pb, buffer), \
            'OpenAL still holds the music file: the delete was refused, so it was never freed'
        assert pb.bgPlayer.buffer == 0 and pb.bgPlayer.path is None, 'the player still claims a file'
    finally:
        pb.backgroundSoundStop()


def test_dropping_the_ambience_frees_its_file():
    pb = _playback()
    try:
        pb.startAMBPlayer_type_soundGain_Loop_(AMBIENCE[0], 'wav', 0.2, True)
        buffer = pb.ambPlayer.buffer
        assert buffer and _loaded(pb, buffer), 'the ambience never loaded, so there is nothing to free'
        pb.ambPlayer._drop_buffer()
        assert not _loaded(pb, buffer), \
            'OpenAL still holds the ambience file: the delete was refused, so it was never freed'
        assert pb.ambPlayer.buffer == 0 and pb.ambPlayer.path is None, 'the player still claims a file'
    finally:
        pb.AMBSoundStop()


def test_many_swaps_leave_only_the_file_that_is_playing():
    """Twenty level changes' worth of music, with only the music player touched, so every
    buffer seen here is one it asked for."""
    pb = _playback()
    try:
        seen = set()
        for i in range(SWAPS):
            pb.startBGPlayer_type_soundGain_Loop_(MUSIC[i % len(MUSIC)], 'wav', 0.02, True)
            seen.add(pb.bgPlayer.buffer)
        alive = sorted(b for b in seen if _loaded(pb, b))
        assert alive == [pb.bgPlayer.buffer], \
            '%d of the %d music files are still loaded after %d swaps, not just the one playing' \
            % (len(alive), len(seen), SWAPS)
    finally:
        pb.backgroundSoundStop()


def test_asking_again_for_the_file_already_playing_reloads_nothing():
    """PORT ADDITION: the same file leaves the buffer where it is, so the menu music does
    not jump back to its first bar every time a menu is built."""
    pb = _playback()
    try:
        pb.startBGPlayer_type_soundGain_Loop_(MUSIC[0], 'wav', 0.02, True)
        buffer, path = pb.bgPlayer.buffer, pb.bgPlayer.path
        pb.startBGPlayer_type_soundGain_Loop_(MUSIC[0], 'wav', 0.02, True)
        assert pb.bgPlayer.buffer == buffer and pb.bgPlayer.path == path, \
            'the file that was already playing was loaded a second time'
        assert _loaded(pb, buffer), 'the file that was already playing was freed'
    finally:
        pb.backgroundSoundStop()


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
