---
name: project_headshot_settings_plan
description: "Agreed 2026-10-05: two main menu toggles, speaking the headshot and a beep on a headshot (the dev's headshot_beep.wav, played at the zombie's position); saved in settings.json. Planned, not built."
metadata:
  node_type: memory
  type: project
---

**Agreed with tunmi13productions on 2026-10-05, not built yet.** It follows [[project_screen_reader_only_plan]], which made "Headshot!" a spoken line.

**What:**
- Two new rows in the main menu, after the vibration row, each a toggle in the vibration row's shape: "Spoken headshot, currently on." and "Headshot beep, currently on." (the dev chose these labels from three).
- **Spoken headshot** turns the screen reader's "Headshot!" on or off. It speaks normally, as it does now.
- **Headshot beep** plays the dev's `game/sounds/used/sfx/weapons/headshot_beep.wav` at the zombie's position, on every headshot hit, even when a tough zombie survives it (the dev's pick over playing it only when the headshot downs the zombie).
- **Defaults on a new save:** speech on, beep off. So today's behaviour does not change until the player turns the beep on.

**How:**
- Keys in settings.json beside VIBRATION: `HEADSHOTSPEECH` and `HEADSHOTBEEP`, '1' or '0', added to `defaults.SETTINGS_KEYS`.
- A new `SoundList.plist` entry, 374, `headshot_beep` (373 is the last one). Its trim comes from the same levelling the other sounds have (`platform/sound_trims.py`).
- The beep is played in `Stage_1_E.MonsterDamage` where "Headshot!" is said now, at `m.Pos`, z 40, and the weapons' volume group covers it because it lives in `sfx/weapons/`.
- Tests in `menu.py`, `gameplay.py` or `monster_sound.py`, `save.py` and `sound_trims.py`; the readme and changelog are updated.

**Status:** planned. Mark it finished only once the dev says it works, then move it to `aidocks/completed/` ([[feedback_completed_projects]]).
