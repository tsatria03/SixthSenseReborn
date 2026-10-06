"""The gold a game pays, GOLD_PER_KILL and GOLD_PER_HEADSHOT in save.json.

A PORT ADDITION (tsatria03, 2026-10-05; aidocks/completed/gold_rates_plan.md).  The
original's 12 a kill and 2 a headshot, raised to 15 and 5 and editable: written on every
start where missing, and put back to the default when unusable.

Each test runs on a new, empty save folder of its own.
"""
from __future__ import annotations

import json
import os
import shutil
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import _scratch_save                                             # noqa: E402,F401  never the real save

from sixthsense import paths                                     # noqa: E402
from sixthsense.game import gold_rates                           # noqa: E402
from sixthsense.platform.defaults import UserDefaults            # noqa: E402


class _NewSave:
    """A new, empty save folder, with the save read from it afresh."""

    def __enter__(self):
        self.old = os.environ.get(paths.USER_DIR_ENV)
        self.top = tempfile.mkdtemp()
        os.environ[paths.USER_DIR_ENV] = os.path.join(self.top, 'SixthSense')
        UserDefaults._instance = None
        self.d = UserDefaults.standardUserDefaults()
        return self

    def __exit__(self, *exc):
        if self.old is None:
            os.environ.pop(paths.USER_DIR_ENV, None)
        else:
            os.environ[paths.USER_DIR_ENV] = self.old
        UserDefaults._instance = None
        shutil.rmtree(self.top, ignore_errors=True)


def test_a_new_save_shows_its_gold():
    """GOLD was written only when it changed; a start now writes a missing one as '0',
    and keeps gold already there."""
    from sixthsense.game.app_delegate import AppDelegate
    with _NewSave() as s:
        app = AppDelegate.shared()
        app.didFinishLaunching()
        assert UserDefaults().flat()['GOLD'] == '0'      # read back from disk
        s.d.setObject_forKey_('750', 'GOLD')
        app.didFinishLaunching()
        assert s.d.objectForKey_('GOLD') == '750' and app.haveGold == 750


def test_the_defaults_are_fifteen_and_five():
    assert gold_rates.DEFAULTS == {'GOLD_PER_KILL': 15, 'GOLD_PER_HEADSHOT': 5}


def test_a_new_save_gets_both_rates_in_save_json():
    with _NewSave() as s:
        assert gold_rates.fill(s.d) is True
        s.d.synchronize()
        saved = UserDefaults().flat()                    # read back from disk
        assert saved['GOLD_PER_KILL'] == 15 and saved['GOLD_PER_HEADSHOT'] == 5, saved
        assert gold_rates.fill(s.d) is False, 'a second start wrote again'


def test_an_edited_rate_stays_and_is_used():
    with _NewSave() as s:
        gold_rates.fill(s.d)
        s.d.setObject_forKey_(40, 'GOLD_PER_KILL')
        s.d.setObject_forKey_(0, 'GOLD_PER_HEADSHOT')       # 0 is allowed
        assert gold_rates.fill(s.d) is False
        assert gold_rates.gold_for(10, 3, s.d) == 400


def test_an_unusable_rate_is_put_back():
    with _NewSave() as s:
        for kill, head in (('lots', -1), (2.5, True), (None, '7')):
            s.d.setObject_forKey_(kill, 'GOLD_PER_KILL')
            s.d.setObject_forKey_(head, 'GOLD_PER_HEADSHOT')
            assert gold_rates.gold_for(1, 1, s.d) == 20, (kill, head)   # read as defaults
            assert gold_rates.fill(s.d) is True
            assert s.d.objectForKey_('GOLD_PER_KILL') == 15, kill
            assert s.d.objectForKey_('GOLD_PER_HEADSHOT') == 5, head
        s.d.setObject_forKey_(30.0, 'GOLD_PER_KILL')        # whole, written as 30.0
        gold_rates.fill(s.d)
        got = s.d.objectForKey_('GOLD_PER_KILL')
        assert got == 30 and type(got) is int, got


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
