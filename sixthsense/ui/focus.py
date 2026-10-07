"""Losing the window's focus is pressing P.

The original does this when the app goes to the background: ``applicationDidEnterBackground:``
posts ``InterruptON`` (0x4d90), and the stage and the tutorial answer it with
``interruptStop``, which calls ``StopPlayAction:`` (0x2c6ce, 0x84962) - the stop button,
the same call P makes here.  So everything P does, this does: the pause panel in a stage,
every time, and in the tutorial whatever P does there.
Nothing else observes the notification, so the menus ignore it.  In the original, coming
back does not resume anything; the panel waits for Continue, as it does after P.

**PORT DIVERGENCE (tsatria03, 2026-10-07): coming back resumes a game that losing focus
paused.**  Only that pause: one the player made with P before leaving stays, since then the
stop refused (``bStop`` was already set) and the game was not running when focus went
(``stop_for_focus``).  Resuming is Continue (``resume_after_focus``), with the "Paused"
voice still waiting from the pause cancelled, so it is never said over a running game.

What ``InterruptOff`` does on the way back, rebuilding the audio device
(``-[Stage_1_E audioRestart]`` 0x2c5bc), is ``AL.check_device`` here, which the frame
loop runs once a second and as soon as the window has focus again.
"""
from __future__ import annotations

import logging

log = logging.getLogger('focus')


def focus_lost(event, pygame):
    return event.type == getattr(pygame, 'WINDOWFOCUSLOST', None)


def focus_gained(event, pygame):
    return event.type == getattr(pygame, 'WINDOWFOCUSGAINED', None)


def stop_for_focus(screen):
    """The stop, as losing focus makes it; True only when it paused a game that was
    running, which is the one pause coming back should undo."""
    running = getattr(screen, 'gameState', None) == 0
    interrupt_stop(screen)
    return running and getattr(screen, 'gameState', None) == 1


def resume_after_focus(screen):
    """Continue a game that losing focus paused, as the panel's Continue does, without
    the "Paused" voice the pause left waiting (0x34710; nothing in the original cancels
    it).  True when it resumed."""
    if getattr(screen, 'gameState', None) != 1:
        return False                # it has moved on: a death, a restart, the menu
    from ..platform.runloop import RunLoop
    RunLoop.main().cancelPerform(screen, 'spaekMenu')
    log.info('window has focus again: continue')
    return bool(screen.continueAction_(None))


def interrupt_stop(screen):
    """``-[Stage_1_E interruptStop]`` / ``-[Stage_Tutorial interruptStop]``: the stop
    button, for whichever stage is up.  Returns True if the screen has one."""
    stop = getattr(screen, 'StopPlayAction_', None)
    if stop is None:
        return False
    log.info('window lost focus: stop, as P')
    stop(None)
    return True
