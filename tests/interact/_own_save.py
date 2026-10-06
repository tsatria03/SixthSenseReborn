"""The save every by-ear tool here plays on, so the player's own is never touched.

Not a tool itself.  ``own_save('level_chooser')`` points ``SIXTHSENSE_USER_DIR`` at
``<save folder>/level_chooser/SixthSenseReborn``, where ``<save folder>`` is the game's own
(``%APPDATA%\\SixthSenseReborn`` on Windows, ``~/.local/share/SixthSenseReborn`` on Linux,
``~/Library/Application Support/SixthSenseReborn`` on macOS), and copies the player's key
bindings and settings into it, but never the save.  Call it before anything reads the save.

Until 2026-10-06 each tool changed ``APPDATA`` instead, which the game reads on Windows
alone, so on Linux and macOS the tools would have played on the real save
(aidocks/project_evaluation_fixes_plan.md).  The Windows folders are the same as they
were, so a save a tool already has carries on.
"""
from __future__ import annotations

import os
import shutil

#: What a tool takes from the player's own folder each time it starts.
COPIED = ('keys.json', 'settings.json')


def own_save(name, copied=COPIED):
    """Send the save to the tool ``name``'s own folder, and return that folder."""
    from sixthsense import paths
    real = os.path.join(paths.save_base(), paths.SAVE_FOLDER)
    mine = os.path.join(real, name, paths.SAVE_FOLDER)
    os.makedirs(mine, exist_ok=True)
    for file in copied:
        yours = os.path.join(real, file)
        if os.path.exists(yours):
            shutil.copyfile(yours, os.path.join(mine, file))
    os.environ[paths.USER_DIR_ENV] = mine
    return mine
