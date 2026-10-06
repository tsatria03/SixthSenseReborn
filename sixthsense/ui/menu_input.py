"""The menu's keyboard, in place of touch exploration and the double tap.

``-[MainController selectTapPointSoundStart]`` reads whichever row your finger is over
and ``-[MainController tapCount]`` runs it on a double tap. A keyboard has no finger,
so Up and Down walk the same rows in the same order, reading each one with the same
WAV, and Enter is the double tap.
"""
from __future__ import annotations

import logging

log = logging.getLogger('menu.input')

#: PORT ADDITION (tsatria03, 2026-09-25): the menu music volume keys, and which way each
#: one steps it.  The menu, the shop and the inventory only; a stage has its own keyboard.
MENU_MUSIC_KEYS = {'page up': 1, 'page down': -1}

#: PORT ADDITION (2026-10-06): the pad's bumpers, as ui/controller.py sends them, and
#: which way each moves a weapon on the reorder screen: left up, right down.
MOVE_BUMPERS = {'f13': -1, 'f14': 1}


def move_weapon_key(name, event, pygame, screen):
    """PORT ADDITION (2026-10-06): moving a weapon on the reorder screen
    (game/weapon_order.py).  Shift with an arrow on the keyboard, and the two bumpers on a
    pad, which reach here as F13 and F14 (ui/controller.py).

    Only the reorder screen has ``move_weapon``, so everywhere else Shift and an arrow is
    just the arrow, and a bumper does nothing at all.  True when ``name`` was handled, so
    both keyboards (this one and screen_input.py) can call it first and go no further.
    """
    move = getattr(screen, 'move_weapon', None)
    if move is None:
        return name in MOVE_BUMPERS      # a bumper is still swallowed, so it does nothing
    if name in MOVE_BUMPERS:
        move(MOVE_BUMPERS[name])
        return True
    if name in ('up', 'down') and (event.mod & pygame.KMOD_SHIFT):
        move(-1 if name == 'up' else 1)
        return True
    return False


def menu_music_key(name, app, say):
    """Page Up or Page Down on a menu screen: step the menu music's volume.  With voice
    over off the screen reader says the new volume; with it on nothing is said, since no
    recording says a percentage, and the music changing is the answer.  Nothing happens
    where the menu music is not playing, such as the opening screen.  True when ``name``
    was one of the two keys."""
    if name not in MENU_MUSIC_KEYS:
        return False
    percent = app.change_menu_music_volume(MENU_MUSIC_KEYS[name])
    if percent is not None:
        say('Music volume %d%%' % percent)
    return True


class MenuInput:
    def __init__(self, menu):
        self.menu = menu
        self.quit = False
        self.open_bindings = False

    def handle(self, event, pygame):
        if event.type == pygame.QUIT:
            self.quit = True
            return
        if event.type != pygame.KEYDOWN:
            return
        name = pygame.key.name(event.key)
        if menu_music_key(name, self.menu.app, self.menu._say):
            return
        if move_weapon_key(name, event, pygame, self.menu):
            return
        if name == 'escape':
            self.quit = True
        elif name == 'f1':
            self.open_bindings = True
        elif name == 'up':
            self.menu.move(-1)
        elif name == 'down':
            self.menu.move(1)
        elif name in ('return', 'enter', 'space'):
            self.menu.activate()
        elif name in ('home', 'end'):
            # the first row or the last, as a screen reader's own lists go
            self.menu.jump(last=(name == 'end'))
        elif name in ('left', 'right'):
            # ...and Left and Right as VoiceOver's flicks: right is the next row
            self.menu.move(1 if name == 'right' else -1)
        else:
            # anything else just repeats where you are, as the original does when a
            # finger lands back on the same row
            self.menu.blindModeSelectedMenu()
