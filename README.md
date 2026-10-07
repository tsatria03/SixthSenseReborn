# SixthSenseReborn

A Windows, Linux and macOS game in Python, grown from a port of **Sixth Sense**
(`kr.co.bitbee.sixsense` 1.2, Bitbee, 2013), an iPhone audio game for blind players: you walk
down a corridor in the dark and shoot what you hear coming. Here changes need not be
faithful to the original; the faithful port is
[SixthSenseOriginal](https://github.com/tsatria03/SixthSenseOriginal).

The port runs off the original app bundle's own data — the binary plists and the three
map layers, unconverted, and the original's recorded sounds, sorted into folders under
their own names — and drives OpenAL Soft with the same calls and the same values the
iOS build used. In SixthSenseOriginal nothing about the game's numbers was invented; this
repository changes what the dev chooses to.

**Wear headphones.** The game says so itself (`SoundList.plist` 234,
"you must use earphone") and none of it works on speakers.

## Download

To play without installing Python, download the newest release from the
[latest release page](https://github.com/tsatria03/SixthSenseReborn/releases/latest).
Each release has a zip for Windows, `SixthSenseReborn-Win-<version>.zip`. Extract it and run
`SixthSenseReborn.exe` in the `SixthSenseReborn-Windows` folder it contains. From 2026-09-28 a release
can also carry `SixthSenseReborn-Linux-<version>.tar.gz`: extract it with
`tar xzf SixthSenseReborn-Linux-<version>.tar.gz`, or your archive manager, and run
`SixthSenseReborn` in the `SixthSenseReborn-Linux` folder. The `docks` folder beside it
holds the player's readme, the changelog and the todo list.

A version is the date of the release and that day's number: `26.09.24-2` is the second
release of the 24th of September 2026. The changelog lists what each release changed,
and every release is on the [releases page](https://github.com/tsatria03/SixthSenseReborn/releases).
Your save is kept in `%APPDATA%\SixthSenseReborn`, not in the game's folder, so a new release
can go in a fresh folder and carries on from your progress. The first time it starts, it
copies a Sixth Sense save, from SixthSenseOriginal, if there is one, and never changes it.

---

## Requirements

To run it from source instead: 64-bit Python 3.12 or newer on Windows 10 or later,
64-bit Linux (WSL included), or macOS 11 or later, and two packages:

    pip install -r requirements.txt

| package | what needs it |
|---|---|
| `pygame` | the window, the keyboard and the frame loop (`SixthSenseReborn.py`, `ui/`). It must be `pygame`, not `pygame-ce`: the two cannot be installed side by side, and the port is written against `pygame` |
| `prismatoid` | Prism, which speaks the few lines no recording covers through any screen reader other than NVDA, or through a Windows voice when none is running (`platform/speech.py`). Without it the game still runs, but only NVDA speaks |

Everything else is the standard library — the audio is OpenAL Soft through `ctypes`,
and the WAVs, plists and map files are read with `wave` and `plistlib`. OpenAL Soft
(`vendor/openal/soft_oal.dll`, `vendor/openal/libopenal.so.1` for Linux, and
`vendor/openal/libopenal.1.dylib` for macOS) ships with the repository, so there is
nothing to install for it. On Linux, if the vendored library is
missing, the system's own `libopenal.so.1` is used (`libopenal1` on Debian and Ubuntu).
On Linux the save is in `~/.local/share/SixthSenseReborn` (or `$XDG_DATA_HOME/SixthSenseReborn`)
instead of `%APPDATA%\SixthSenseReborn`, and the NVDA client, being Windows-only, is skipped:
Prism speaks instead.

On macOS the save is in `~/Library/Application Support/SixthSenseReborn`, and Prism
speaks through VoiceOver, or a native voice when no screen reader is running.
The bundled OpenAL Soft is universal: source runs need Python and packages for
the Mac's own architecture, Apple Silicon or Intel.

`vendor/nvda/nvdaControllerClient64.dll` ships too. Since 2026-10-05 everything the game
says goes through your screen reader: the menus, the shop, the inventory, the settings,
the pause and result panel, the tutorial and the announcements during play. NVDA speaks
through its own client, any other screen reader through Prism, and with none running a
system voice does. The original's recorded speech is no longer played. The tutorial names
the keys for each lesson, or, with a game controller attached, the stick and button moves.

One more package is needed only to redo the reverse engineering, never to play:

    pip install capstone

| package | what needs it |
|---|---|
| `capstone` | the armv7 Thumb-2 disassembler (`tools/dz.py`, `tools/dc.py`, `tools/digest.py`) |

`tools/mb.py`, `tools/objc.py`, `tools/rows.py`, `tools/bands.py` and
`tools/pan_check.py` are standard library only — `pan_check.py` drives the same
vendored OpenAL Soft the game does.

## Running it

```bash
python SixthSenseReborn.py
```

That opens on the publisher's logo and its sound, then the splash and the warning, as
the original does, and then the menu. Enter skips the logo, and Escape skips straight
to the menu. The opening screen's third row tells the game's story, which the original
recorded but never played.
**Up** and **Down** walk the five rows - the title, Start Game, Tutorial, Store and
Settings - and **Enter** chooses; your screen reader reads each row. Games are free: the
original's coins, one spent a game and one back every thirty minutes, are gone.

The **Store** row opens the shop — the weapon list, a page per weapon with its numbers
read aloud and its upgrade button, and the inventory, where what you equip is what the
stage hands you, and where you can reorder the weapons. Gold comes out of your runs:
15 a kill and 5 a headshot, both editable in `store/shop.json` (the original paid 12 and
2). The **Settings** row holds skipping the opening screens, the spoken headshot and its
beep, vibration, shaking a pad to break free, and which controller to play with.

`--stage` and `--tutorial` skip the menu, `--no-intro` skips the opening for one run
(`SKIPINTRO` in `settings.json`, set on the Settings screen, does it for good). Other
options: `--no-window` (headless), `--game DIR` (another copy of the bundle), `-v`.

`--debug` is for trying things out: a zombie that reaches you just dies, nothing takes a heart and
you cannot die, and no kill, headshot, score or gold counts. A stage says "Debug mode"
as it starts. Tab reaches every weapon, bought or not, and no gun or grenade runs out.
Eight keys are added, which the F1 screen lists and rebinds: F2 next section of the
corridor, Shift+F2 next level (after 8, back to 1), F5 spawn a zombie in the lane you
last attacked, Shift+F5 choose what F5 spawns, F6 hold the zombies in place, F7 let
zombies hit you without taking a heart, F8 turn the sound trims off or on, F11 say where they are.

Until you have finished the tutorial once, Start Game takes you to the tutorial first, as the original does; pressing P at its end counts 3, 2, 1 and starts
the real game. Finished once, by either route, Start Game goes straight into the game.
`--skip-tutorial` writes the key the tutorial writes, if you would rather skip it.

The save lives in `%APPDATA%\SixthSenseReborn`, in short files in four folders, one thing
each (tsatria03's layout, 2026-10-06):

- `saves/save.json`: progress (`TUTORIAL`, `STAGE`, the score records), and any key not
  named below.
- `config/settings.json`: the volumes and the Settings screen's rows; `config/keys.json`:
  the key bindings.
- `store/shop.json`: the shop's rules, lowercase (`gold_per_kill`, `upgrade_start_price`
  ...).
- `store/inventory.json`: `gold`, `grenades`, and `owned`, `equipped` and `order` as lists
  of weapon names.
- `weapons/<name>.json`, one per weapon (`grenade`, `knife`, `colt`, `shotgun`, `m4a1`,
  `ak47`, `mg80`, `sword`): `ammo_capacity`, `range`, `damage`, `price`, `level` and
  `max_level`.

The game itself still asks for the original's key names (`GOLD`, `M4USE`,
`SHOTGUN_DAMAGE`); `sixthsense/platform/defaults.py` routes each to its file and translates
the name, so nothing else knows about the folders. Below, a key is named as the game names
it.

`settings.json` holds `MASTERVOLUME`, `MENUMUSICVOLUME`, `LEVELMUSICVOLUME`,
`AMBIENCEVOLUME`, `WEAPONVOLUME` and `PLAYERVOLUME`, whole percentages
from 0 to 100, where 100 is the original's mix, and `GAMEPLAYGAIN`, whole decibels from 0
to 6, where 0 is; they are read on the next start, and the menu music, the gain and the
two groups are also set by Page Up and Page Down. It also holds what the **Settings**
screen sets: `SKIPINTRO`, `VIBRATION`, `HEADSHOTSPEECH`, `HEADSHOTBEEP` and `SHAKE`, each '1' or '0',
and `CONTROLLER`, the name of the pad the game plays with, or '' for whichever is found
first. `CONTROLLER` is a **name, never an id**: unplug the pad on id 0 and the next one
plugged in takes that id, so an id means nothing between runs. A saved name that is not
attached is left alone and the game falls back to the first pad it finds, so plugging the
preferred pad back in picks it up again. Only that pad plays, buzzes and is read for a
shake; any other attached pad is ignored, which is also how a pad SDL has listed twice
stops being two controllers. The original kept all of these in one plist. An older save -
`save.json` and `settings.json` in the folder itself (before 2026-10-06), or a
`defaults.json` (before 2026-09-25) - is moved into the folders on the first start, each
old file kept with `.old` on its name, and a key found in a file it does not belong in is
moved to its own on every start. An empty file counts as new.

The weapon files hold each weapon's stats, which the game plays with and the shop and
inventory read out: `<W>_AMMO_CAPACITY` (the magazine), `<W>_RANGE` (centimetres, read
out in metres), `<W>_DAMAGE` and `<W>_PRICE` (what the shop charges), where `<W>` is
`GRENADE`, `KNIFE`, `COLT`, `SHOTGUN`, `M4`, `AK47`, `MG80` or `JAPAN`, so
`SHOTGUN_DAMAGE` is the shotgun's damage. An older save's keys without underscores
(`SHOTGUNDAMAGE`) are renamed on the first start, values kept. They start as the weapon
files' numbers and the shop's prices; there is no key where nothing could use one (the
grenade's count is `GRENADECOUNT`, the blades have no magazine, the knife and colt are
not sold). A value that is not a whole number of 0 or more is put back on the next start.
`GOLD_PER_KILL` (15) and `GOLD_PER_HEADSHOT` (5) are the gold a game pays when it ends,
per kill and per headshot hit, raised from the original's 12 and 2 and editable the same
way; the weapon test range keeps its own 12% of the score.
`WEAPON_ORDER` is the order the weapons come in, the eight slot numbers (0 grenade,
1 knife, 2 colt, 3 shotgun, 4 M4A1, 5 AK47, 6 MG80, 7 Japanese sword), each exactly once
or the whole list is put back. It starts as `[2, 3, 4, 5, 6, 7, 0, 1]`, the original's own
cycle turned round to begin at the colt, so an untouched save plays as the original did.
The inventory's Reorder weapons screen is the easy way to change it: Up and Down walk the
equipped weapons, Shift with either moves one, and on a pad the bumpers do. That order is
what Tab cycles through in a game and what a game starts you on.
Weapon upgrades: each weapon has `<W>_LEVEL` (0) and `<W>_MAX_LEVEL` (10; a level above
it counts only as the cap), and one
upgrade button on its pages raises the level, adding to its damage, ammo capacity and
range at once (not the grenade's or the blades' ammo). Five keys apply to every weapon:
`UPGRADE_START_PRICE` (100) and `UPGRADE_PRICE_GROWTH` (1.2), so level n costs
100 × 1.2^(n-1); and `UPGRADE_DAMAGE_SHARE`, `UPGRADE_AMMO_SHARE` and
`UPGRADE_RANGE_SHARE` (15 each), the percentage of the weapon's own stat a level adds,
so at 15 level 10 is two and a half times the weapon: a colt of 7 rounds, 30 damage and
10 metres holds 18, does 75 and reaches 25. The range is rounded to a whole metre, since
it is read out in metres. The price growth may be a fraction; everything else is a whole
number.

## Controls

The tutorial teaches the five lanes as **clock positions** — 9, 10:30, 12, 1:30, 3 —
and 6 o'clock for reload. The arrow keys are a clock face, so that is where they sit:

| clock | arrows | letter | |
|---|---|---|---|
| 9:00 | **←** | **A** | attack hard left (180°) |
| 10:30 | **← + ↑** | **Q** | attack half left (123°) |
| 12:00 | **↑** | **W** | attack straight ahead (90°) |
| 1:30 | **→ + ↑** | **E** | attack half right (57°) |
| 3:00 | **→** | **D** | attack hard right (0°) |
| 6:00 | **↓** | **S** or **R** | reload — the game's own 6 o'clock swipe |

Both sets are live at once, so either hand position works. The diagonals are real
chords: hold both keys together.

| | |
|---|---|
| **Tab** / **Shift+Tab** | next / previous weapon |
| **Space** | shake free when the animal zombie grabs you: one to five separate presses, a new number each grab, and holding Space down counts as one |
| **P** | pause — the original's stop button, which has no key of its own |
| **F1** | key bindings — see below |
| **Esc** | pause a stage, and resume it from the pause panel; back to the menu from the tutorial; quit from the menu |
| **Page Up** / **Page Down** | the menu music louder / quieter, in the menu, the shop and the inventory: 0 to 100% in steps of ten, saved as `MENUMUSICVOLUME`, and said aloud. The level music is left alone |
| **Page Up** / **Page Down** in play | the gameplay gain, 0 to 6 dB on OpenAL's listener: every sound effect louder together, the music and ambience held where they were. With **Shift** or **Alt**: the weapons or the player, 0 to 100% in tens. The entities (zombies, bosses, the monster, the woman) are always at full volume, and **Ctrl** with these keys does nothing. Saved in `settings.json` and said aloud |

When the pause or result panel is up, the keyboard belongs to it: **Up** and **Down**
walk its rows, **Enter** chooses. The same goes for the menu, the shop and the
inventory. **Home** and **End** also go to the first row and
the last, and **Left** and **Right** move to the previous row and the next, like
VoiceOver's flicks. You can pause as often as you like: continue and restart both let the next
pause through, as in the original.

Keyboard only — no mouse. The lane keys replace the swipe rather than simulating it:
`MovingShot:` quantises its angle into five bands and a reload sector anyway, so a key
hands the game the band directly.

### Rebinding

**F1** opens the key-binding screen, which reads itself aloud — through NVDA if it is
running, otherwise through any other screen reader by way of Prism (JAWS, ZoomText,
System Access, Narrator and more), or a Windows voice if none is running. It has to:
the game's own voice is 269 recorded WAVs and none of them can say "Left Arrow".

    Up / Down   move          Enter   rebind        A   add a second binding
    Delete      unbind        R R     reset all     Escape / F1   back

Binding captures a chord — hold the keys together and let go. **F1 and Escape are not
rebindable**, so there is always a way back in. Bindings live in
`%APPDATA%\SixthSenseReborn\config\keys.json`, stored by key name so a pygame update cannot
scramble them.

## How to play

Monsters do not walk on the map; they walk down one of **five lanes** toward you, and
each footstep brings them 40-ish cm closer and makes them louder. Listen for which lane
a monster is in and attack that lane before it reaches 25 cm.

Every monster **breathes**, and there is a gap in the breathing. A hit landed in that
gap is a headshot and does double damage. That is the whole skill of the game, and it is
what the loading screen tells you: *"You can shoot head when zombies stop breathing."*

Your own breathing tells you your health: three hearts is `player_breath_1`, two is
`player_breath_2`, one is `player_breath_3`.

---

## Layout

```
SixthSenseReborn.py            entry point
sixthsense/
  paths.py               where the bundle's data lives
  platform/
    openal.py            ctypes binding for OpenAL Soft
    music.py             the two AVAudioPlayer streams
    runloop.py           NSTimer and performSelector:afterDelay:
    defaults.py          NSUserDefaults, as short files in the save folder's folders
    keymap.py            PORT ADDITION: bindings, including chords
    speech.py            PORT ADDITION: the game's voice: NVDA, Prism or a system voice
    volume.py            PORT ADDITION: the volume knobs, in decibels
    sound_trims.py       PORT ADDITION: per-file trims that even out the recordings
    sound_position.py    PORT ADDITION: where a sound is placed, lanes nearer 12
    motion.py            PORT ADDITION: a pad's motion sensor, through SDL
    controller_names.py  PORT ADDITION: a pad's buttons in the words the game says
  game/
    app_delegate.py      global state + the sound dispatch
    oal_playback.py      oalPlayback
    make_maps.py         MakeMaps
    moving_accelerometer.py
    player_control.py    weapon_control.py    monster_control.py
    sound_list_control.py
    stage_1_e.py         Stage_1_E, including the pause and result panel
    stage_tutorial.py    Stage_Tutorial
    stage_1_test.py      Stage_1_TEST - the weapon test range behind Try
    main_controller.py   MainController - the menu
    intro.py             startIntroPage - the logo, the splash, the warning and the story
    blind_screen.py      the shape every menu screen shares
    store.py             the shop: front menu, weapon list, weapon page
    inventory.py         the eight slots, equipping them, and reordering
    settings_screen.py   PORT ADDITION: the Settings screen
    weapon_stats.py      PORT ADDITION: each weapon's numbers, from the save
    weapon_upgrades.py   PORT ADDITION: upgrade levels and their prices
    weapon_order.py      PORT ADDITION: the order the weapons come in
    gold_rates.py        PORT ADDITION: the gold a game pays
    debug.py             PORT ADDITION: the --debug keys
  ui/
    input.py             the keyboard, resolved through the keymap
    keybind_screen.py    the rebinding screen (F1)
    menu_input.py        Up/Down/Enter for the menu
    screen_input.py      ...and for the shop, the inventory and the settings
    focus.py             switching away from the window pauses a stage
    controller.py        PORT ADDITION: a game controller, through SDL
    vibration.py         PORT ADDITION: the controller's motors
    shake.py             PORT ADDITION: shaking a pad to break free
game/                    the original app bundle, its sounds sorted into folders (see below)
vendor/                  OpenAL Soft and NVDA's controller client, with their licenses
analysis/                the binary, and the disassembly this was written from
tools/                   the Mach-O / Objective-C / Thumb tooling that produced it
aidocks/                 GAME_STRUCTURE.md (how the original works), and
                         the notes for AI-assisted work (see CLAUDE.md)
docks/                   readme.txt, changelog.txt and todo list.txt, which ship in a docks folder
tests/case/              the tests, one plain script each
tests/interact/          tools to play by ear: the level and tutorial choosers, the
                         headshot tester and the controller tester
compiler.py              builds the game with PyInstaller
releaser.py              sets the version, files the changelog, builds, zips, tags and uploads a release
.github/workflows/       release.yml: builds and publishes a release when a V<version> tag is pushed
requirements.txt         the two packages it needs
```

`aidocks/GAME_STRUCTURE.md` is the useful one: it is the mechanism of the game as read out
of the binary, with addresses.

### `game/` — the original's data

`game/` holds the contents of `Payload/sixsense.app` as the IPA shipped them: the binary
plists, the three map layers, the nibs, the PNGs, `Info.plist`, `iTunesArtwork`, the
Facebook resource bundle, `_CodeSignature/` and the `sixsense` binary itself. The port
never writes to it — the save file lives in `%APPDATA%\SixthSenseReborn`.

The one thing that is not where the original kept it is the sounds. The original keeps
its 269 WAVs in one flat folder; here every sound the game uses sits in
`game/sounds/used/`, sorted into folders by what it is — zombies, weapons, menus, the
tutorial and so on — and each keeps its original file name, so `SoundList.plist` still
finds it. Each file was matched to the original by comparing its audio. They came back
through a compressed copy, so they carry faint codec noise, but they are 16-bit PCM,
like the originals; six are the original files themselves. `game/sounds/used/` holds
only what the game plays, 103 files, and it is all a build carries.
`game/sounds/unused/` holds 191 the game never plays, kept for reference: 145 recordings
of speech, which the screen reader replaced on 2026-10-05, and 46 sound effects for
things the port leaves out, such as the ranking, the coins and the zombies that never
spawn, with extra copies and the sounds that are not the original's own. A few entries
of `SoundList.plist` follow files renamed by ear, and the port adds four, 371 to 374:
the bosses' being-hurt sound, two controller sounds and the headshot beep.

The port reads from there, so the data it runs on is the original's data. `--game PATH`
(or `SIXTHSENSE_GAME`) points at another copy; an untouched original bundle, with its
WAVs all in one folder, works too.

`analysis/bin/sixsense_armv7` is the thin armv7 slice cut out of `game/sixsense`, which
is what `tools/` disassembles. The game never reads it; it is there so the analysis is
reproducible without the IPA.

## Tests

`tests/` has two folders and a runner:

- **`tests/case/`** holds the tests: 34 plain scripts, each checking one part of the
  game against the original and printing `ok` or `FAIL` for every check, then a total.
  Run any of them on its own; there is nothing to install beyond what the game needs.
- **`tests/suite.py`** runs them all, eight at a time and the slowest first, which takes
  about 85 seconds where running them one after another takes nearly 290. Each file is
  still its own process, with its own throwaway save and its own silence. Every test name
  and its result goes to `tests/results/results-<date>-<n>.txt`, and a file that fails is
  run once more on its own, so a test that only fails while the others run is told apart
  from a broken one. The exit code is 1 if anything failed.
- **`tests/interact/`** holds tools you play rather than tests: `level_chooser.py`
  and `tutorial_chooser.py`, which open the real game at any level or the tutorial at
  any lesson, `headshot_tester.py`, a game where every gun hit is a headshot, and
  `controller_tester.py`, for checking something by ear. See "Starting at any level",
  "Starting the tutorial at any lesson" and "Hearing a headshot" below.

The tests, one line each:

```bash
python tests/case/data.py           # the port's tables against game/
python tests/case/paths.py          # where the game finds its sounds, plists and maps
python tests/case/gameplay.py       # a headless playthrough (~35 s, opens the audio device)
python tests/case/input.py          # the keyboard mapping
python tests/case/tutorial.py       # the ten tutorial beats
python tests/case/menu.py           # the menu rows, and games being free
python tests/case/menu_music.py     # Page Up and Page Down on the menu music (audio device)
python tests/case/settings_menu.py  # the Settings screen, and what the attached pad can do
python tests/case/pause.py          # the pause and result panel
python tests/case/store.py          # the shop, buying, and the inventory
python tests/case/inventory.py      # equipping through the inventory's screens, step by step
python tests/case/weapon_stats.py   # each weapon's stats in the save, read by the pages and the stage
python tests/case/gold_rates.py     # the gold a game pays per kill and per headshot, from the save
python tests/case/weapon_upgrades.py  # upgrade levels, prices and what each level adds
python tests/case/weapon_order.py   # the order the weapons come in, and the reorder screen
python tests/case/weapon_range.py   # the weapon test range behind the shop's Try button
python tests/case/intro.py          # the logo, the splash, the warning, the story, skipping
python tests/case/speech.py         # which screen reader or voice speaks (stand-ins, silent)
python tests/case/volume.py         # the decibel knobs, and the binary's mix left alone
python tests/case/sound_trims.py    # the per-file trims that even out the recordings
python tests/case/sound_position.py # the lanes at 10:30 and 1:30 heard nearer 12
python tests/case/controller.py     # a game controller on the menus (fake pads)
python tests/case/controller_names.py # a pad's buttons in the game's words
python tests/case/vibration.py      # the controller's motors when something hits you (fake pads)
python tests/case/shake.py          # shaking a pad to break free (fake pads and sensor)
python tests/case/gameplay_volume.py # the gain and the group volumes in play (audio device)
python tests/case/monster_sound.py  # zombie sounds read back from OpenAL (audio device)
python tests/case/focus.py          # switching away from the window pauses a stage
python tests/case/window.py         # the window's close button and the screen loop
python tests/case/release.py        # the releaser's version, changelog and names (builds nothing)
python tests/case/save.py           # the save folders, the names translated, old layouts moved over, damaged files kept (temp folders only)
python tests/case/music_memory.py   # changing the music and ambience frees the old files (audio device)
python tests/case/audio_device.py   # a lost audio device is reopened (fake device, then OpenAL's null driver)
python tests/case/runloop.py        # timers and delayed calls: once each, in time order, on a fine clock
```

`case/data.py` checks the port against the original data rather than against itself: the
map shape and the action layer, every weapon's stats, every monster type's kind and
lane, that every sound number the monster tables use resolves to a WAV in
`game/sounds/used`, and that everything meant to be positional is mono (OpenAL will not
spatialise stereo, and the game relies on that).

**The tests never touch your save, and make no sound.** Each one imports
`tests/case/_scratch_save.py` first, which points `SIXTHSENSE_USER_DIR` at a throwaway
folder and deletes it afterwards, sets `SIXTHSENSE_SILENT` so nothing is ever sent to your
screen reader or a Windows voice, and sends the audio to OpenAL Soft's null driver with no
window, whatever your shell has set. `case/paths.py` fails if a test file leaves that out.
`_scratch_save.py` is not a test; `tests/suite.py` skips files starting with `_`, as should you
when running them all by hand.

## Building and releasing

Both scripts open a numbered menu when double-clicked, and wait for Enter at the end.
Building needs PyInstaller (`pip install pyinstaller==6.22.3`, the version the release
workflow pins); releasing also needs the GitHub
CLI, signed in with `gh auth login`.

`compiler.py` only builds. It never zips and never changes the repository. Everything
lands in `dist\SixthSenseReborn-Windows`, around `SixthSenseReborn.exe`. Run on Linux, WSL included, it
builds a Linux game instead, in `dist/SixthSenseReborn-Linux` around `SixthSenseReborn`, with OpenAL
Soft's Linux library and no NVDA client; PyInstaller only builds for the system it runs
on. `releaser.py` releases both, one system at a time (below).

On Windows and Linux, the build can be:

- **Folder build:** the game in a folder, with its sounds and data beside the
  executable in `game\`.
- **Single exe** (`--embed`): the sounds and the game's data inside one executable.
  It unpacks them at every launch, so it starts a few seconds slower.

Either way, the readme, the changelog and the todo list go in a `docks` folder beside
the executable, as in the repository, and `VERSION` and the license sit beside it too,
where a player can open them. The third-party licenses go inside the executable, in a
`licenses` folder. `docks/readme.txt` is the player's own readme: plain text, one sentence a line,
with none of this file's developer parts.

On macOS it builds `dist/SixthSenseReborn-macOS/SixthSenseReborn.app`, with
the data, dependencies and documents inside: copy the app on its own and open
it in Finder. The app targets the build Python's architecture, ARM64 or Intel.
`--console` keeps a console-folder build instead; otherwise
`--embed` and `--onefile` still build an app without self-extraction. For a distributable build that
keeps the macOS 11 minimum, use uv-managed Python for the target architecture:

    uv run --managed-python --python 3.13 --with-requirements requirements.txt --with pyinstaller python compiler.py --clean

`releaser.py` does the rest. Its full release goes through each step and asks Y or N
before each one:

1. **Check** that everything is committed and pushed, `gh` is signed in, and the
   changelog has between 5 and 100 changes under `unrelease:`. With 1 to 4 it asks
   whether to release anyway, and only a Y goes on; none at all, or more than 100, never
   make a release.
2. **Prepare:** `VERSION` becomes today's date and that day's release number, such as
   `26.09.23-1`, and the unreleased lines are filed under it in `docks/changelog.txt`.
3. **Build** with the compiler, as a folder or a single exe. A failed build puts
   `VERSION` and the changelog back.
4. **Zip** `dist\SixthSenseReborn-Windows` into `dist\SixthSenseReborn-Win-26.09.23-1.zip`, which
   extracts to a `SixthSenseReborn-Windows` folder. It only zips a build made for this version.
5. **Commit and push** `VERSION` and `docks/changelog.txt` as "Release 26.09.23-1".
6. **Tag** it `V26.09.23-1`, and push the tag.
7. **Upload** the zip to GitHub as the release "SixthSenseReborn V26.09.23-1", with that
   version's changelog lines as its notes. If the release is already there, the zip is
   added to it.

It never moves or replaces a tag, a release, or a file already on a release.

One release carries both builds: `SixthSenseReborn-Win-<version>.zip`, and
`SixthSenseReborn-Linux-<version>.tar.gz`, which extracts to a `SixthSenseReborn-Linux` folder; a
tar keeps the executable runnable and every Linux can open it. Since
PyInstaller only builds for the system it runs on, make the release on one system with
the full release, then on the other choose **Add this system's build to the release**:
it builds, zips and adds that zip to the same release, and files, commits and tags
nothing. On Linux, WSL included, install the GitHub CLI there too (`sudo apt install gh`)
and sign it in with `gh auth login`.

### Releasing through GitHub

Pushing a tag `V<version>` makes GitHub build and publish the release itself, with
`.github/workflows/release.yml`. On your side there is one choice in `releaser.py`,
**Prepare and tag**: it checks everything, sets `VERSION`, files the changelog, commits
and pushes "Release <version>", then tags it and pushes the tag. It builds, zips and
uploads nothing.

The tag starts one build per system on GitHub's own machines. Each first runs every test
in `tests/case`, and a failing test stops that build and so the release. Then Windows and Linux build as a
single executable (`compiler.py --embed`), and the Mac as its app, once for Apple Silicon
and once for Intel. Each build is packed by the releaser's own `package()`, so the names
and the folders inside are the ones above, with `SixthSenseReborn-macOS-arm64-<version>.tar.gz`
and `SixthSenseReborn-macOS-x86_64-<version>.tar.gz` added. When all four are built, the
release "SixthSenseReborn V<version>" is created with that version's changelog lines as
its notes. A build that fails publishes nothing: re-run the failed job under Actions
and the release follows. A tag whose `VERSION` is not the tag's builds nothing, and
nothing on a release is ever replaced. The Mac builds are not signed.

**Test it without publishing:** the releaser's **Test the workflow** starts the same workflow
by hand on the pushed branch (or run it from the Actions page). It builds all four archives
and checks the release step, but a test run has no tag, so nothing is published, no tag is
made and no release is touched. The archives are kept for a week, so the Mac ones can be
downloaded and tried. GitHub only offers a workflow to run once its file is on the default
branch.

The full release and the other menu steps still work, for building on your own machine.

### Starting at any level

`tests/interact/level_chooser.py` is not a test. It opens the real game at the level you choose,
so a bug on level 3 does not take three levels of play to reach. Opened on its own, it
asks for the level, the area (cave, forest or rain) and whether to start just before
the boss. It also takes them on the command line:

```bash
python tests/interact/level_chooser.py                    # asks
python tests/interact/level_chooser.py 2                  # level 2
python tests/interact/level_chooser.py 3 --mode forest    # level 3, in the forest
python tests/interact/level_chooser.py 2 --boss           # level 2, two steps before the siren
python tests/interact/level_chooser.py 1 --row 300        # level 1, from row 300 of the corridor
```

A level is what walking there would give you: monsters 1.5 times tougher and faster per
level, one more of them out at a time, and the area alternating between the cave and
the forest. It plays on its own save in `%APPDATA%\SixthSenseReborn\level_chooser`, so your
own save is never touched, and it copies your key bindings in each time it starts.

### Starting the tutorial at any lesson

`tests/interact/tutorial_chooser.py` is not a test either. It opens the real tutorial at the
lesson you choose, with the ending you choose, so neither needs a deleted save or a
replay of the lessons before it. Opened on its own, it asks two things:

- **The ending:** `start`, where P counts 3, 2, 1 into the real game as after a
  first Start, or `menu`, where P goes back to the main menu as from the Tutorial
  button.
- **The lesson,** 1 to 10: the five clock positions, the stronger zombie, reloading,
  changing weapon, shaking off the animal zombie, and ending the tutorial with P.

```bash
python tests/interact/tutorial_chooser.py                              # asks
python tests/interact/tutorial_chooser.py --lesson 9                   # the animal zombie
python tests/interact/tutorial_chooser.py --ending start --lesson 10   # P, then into the game
```

The lessons before the one you choose count as done, so the tutorial carries on from
there as it would have. It plays on its own save in
`%APPDATA%\SixthSenseReborn\tutorial_chooser`, so your own save is never touched.

### Hearing a headshot

`tests/interact/headshot_tester.py` is not a test either. It opens a real game where every
gun hit is a headshot, so you can hear what one does with the spoken headshot and the
headshot beep each on or off. Opened on its own, it asks for both; Enter keeps your own
setting. The knife, the sword and the grenade have no headshots, as in the game.

```bash
python tests/interact/headshot_tester.py                          # asks
python tests/interact/headshot_tester.py --speech on --beep on    # both
python tests/interact/headshot_tester.py --speech off --beep on   # the beep alone
```

It plays on its own save in `%APPDATA%\SixthSenseReborn\headshot_tester`, with copies of
your key bindings and settings, so your own save is never touched.

## Where this came from

The armv7 slice of `sixsense` ships **unencrypted** (`LC_ENCRYPTION_INFO
cryptid = 0`), so the whole thing could be read directly. The
tooling in `tools/` parses the Mach-O, walks the Objective-C metadata (67 classes,
~2900 methods, ivar offsets, selector and class references, the dyld bind table), and
disassembles Thumb-2 with selector, string, ivar and float-literal resolution. Its
output is in `analysis/disasm/`; every ported method carries the address it came from.

## The tutorial

Ten lessons, in the original's order. Five teach the lanes as clock positions — 9,
10:30, 12, 1:30, 3 — which is where the A/Q/W/E/D keys come from; one sends a stronger
zombie; one teaches 6 o'clock, which is the reload; the rest teach the weapon switch,
shaking off the animal zombie, and ending the tutorial, the original's three-finger tap,
which is **P** here. Each lesson plays its instruction and sends in the monster it is
about, and each only counts once the ones before it are done.

P ends the tutorial once the first eight lessons are done. Reached from Start Game on
your first go, it then counts 3, 2, 1 and the real game begins; from the Tutorial row,
it goes back to the main menu.

## Status

The opening, the menu, the tutorial, the stage, the monsters, the weapons, the
fighting, the pause and result panel, the shop and the inventory are ported, along with
the whole audio path, and so is the weapon test range behind the shop's Try button
(`Stage_1_TEST`). What is left is the ambient sound layer the shipped map does not use, and everything that needed the
publisher's server or the App Store.

## Credits

**[lbk2907](https://github.com/lbk2907)** started the port. They found that the iOS
binary ships unencrypted, extracted it, and wrote the tooling in `tools/` that reads it
and the disassembly in `analysis/`. Then they wrote the Python port itself from that
disassembly, method by method, along with its docs, its tests and the first version of
this README.

Contributors, in the order they joined:

- **[tsatria03](https://github.com/tsatria03)** publishes and maintains the repository,
  and carries the port on:
  - **Publishing:** put the port on GitHub, restored this README, and keeps the
    license, the credits, the changelog and the todo list, and gave players a readme
    of their own, in a `docks` folder beside the game.
  - **Sounds:** sorted every sound into folders under its original name, then set apart
    every sound the game never plays, and found the real "main menu button" recording.
  - **The original, checked again:** the publisher's logo at launch, the story on the
    opening screen's third row (tunmi13productions' idea), "paused" when pausing, the tutorial's reload lesson
    saying its instruction once, the weapon change sound at the original's volume,
    a grenade scoring every zombie it hurts, a zombie's blow heard in the middle of your head, the coin
    row's pauses, and the menu's missing clicks.
  - **Speech and keys:** speech through Prism for every screen reader and a Windows
    voice. Rebinding keys that works, a reset that asks first, and rolling from one
    attack key to the next.
  - **The mix:** the music and ambience as quiet as the original's, loud gunshots, the
    kill sound, the rain that keeps falling, silent exits, the menu music on decibel
    knobs, carrying on where it was, and no longer filling memory.
  - **Play:** weapons that keep their own ammo, the girl and the woman zombie walking
    straight in along their lanes, the woman's growl timed by her distance, and the
    turn keys removed.
  - **The menus and the panel:** the shop refusing weapons you have not bought, each
    screen saying its name, Home, End, Left and Right with voice over off, the score
    row reading your score, result rows that reread themselves, the coin store and
    purchase all weapons rows removed, a coin clock that starts again when a save has
    none, and unequipped starting weapons that stay unequipped.
  - **Debug mode:** its second set of keys, a tutorial it can finish, and F7 in the
    window's list of keys.
  - **Tools:** the build script with its single-exe build, the releaser, its
    five-to-a-hundred rule and the question to release fewer anyway, the level and tutorial choosers, the tests folder split into
    `case` and `interact`, tests that never touch your save or make a sound, and a run
    loop that keeps time in order.
- **[tunmi13productions](https://github.com/tunmi13productions)** has fixed and ported
  a great deal of the game:
  - the coin economy, and the order spoken numbers are read in
  - zombies that move in their lanes, the boss and the end of each level, the girl who
    heals you and the woman zombie
  - reloading and headshots as in the original, with shots that take time to land
  - pausing as often as you like, and pausing when the window loses focus
  - pausing that pauses the ambience and the music, and holds a level change until you
    continue
  - the screen reader mode for the menus and the result panel, and Escape as pause
  - debug mode
  - the weapon test range behind the shop's Try button
  - the tutorial's order, its ending with P, and its spoken key hints
  - shaking free in one to five presses
  - stopping recordings from talking over each other
  - removing the ranking, Game Center and restore purchases rows, and quitting from the
    window's close button on any screen
  - the voice over row saying what it does, the coin row and the earphone warning no
    longer talking over other rows, and "no coin" said alone
  - a damaged save kept aside, with the game carrying on from a backup
  - the sound following your audio device when headphones are unplugged or plugged in
  - saying aloud why the game could not start, or stopped
  - the bloopers folder

SixthSense itself is Bitbee's game, from 2013.

## Licence

The port's code is in `LICENSE`. Everything under `game/`, and the binary and
disassembly under `analysis/`, are Bitbee's and are not covered by it.

The third-party pieces keep their own licenses. OpenAL Soft's and NVDA's controller
client's sit beside their DLLs in `vendor/`, and a build puts them, along with
Prism's and pygame's, into a `licenses` folder inside the executable. Each can also be
read online:

- OpenAL Soft, LGPL 2: <https://github.com/kcat/openal-soft/blob/master/COPYING>
- the NVDA controller client, LGPL 2.1: <https://github.com/nvaccess/nvda/blob/master/extras/controllerClient/license.txt>
- Prism, MPL 2.0: <https://github.com/ethindp/prism>
- pygame, LGPL 2.1: <https://github.com/pygame/pygame/blob/main/docs/LGPL.txt>
