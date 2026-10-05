---
name: project_screen_reader_only_plan
description: "Agreed 2026-10-05: drop the self-voiced mode so everything is spoken through Prism, tutorial and in-play announcements included, then remove the main menu's voice over row. Staged; not built yet."
metadata:
  node_type: memory
  type: project
---

**Agreed with the dev on 2026-10-05, not built yet.** Supersedes the earlier decision in [[project_screen_reader_mode]] that the tutorial and in-play announcements stay recordings. It carries out the todo items about speaking everything through Prism, the screen reader friendly tutorial and removing the voice over row ([[project_reborn]], [[project_prism_speech]]).

**Decisions:**
- **Wording:** Claude drafts the tutorial and announcement lines from the recordings' file names and the existing `KEY_HINTS`, rewritten for keys and controllers instead of touch gestures. The dev corrects them by ear. Don't treat a drafted line as confirmed.
- **Cleanup:** `EYEMODE` is ignored from the last stage on, saves are left alone, and recordings the game no longer plays move to `game/sounds/unused/`, never deleted.

**Stages, each tested and confirmed by the dev before the next:**
1. In-play announcements (zombies are coming, headshot, paused, game over, score, numbers) spoken through Prism instead of the recordings.
2. The tutorial's lines spoken through Prism. The recording-length delays (9.5 s, 6.5 s) in `tutorial_sound_stop` become speech-aware or fixed timing; the key and controller hints become the main line.
3. Screen reader mode becomes the only mode: `app.screen_reader` branches collapse, unused recordings move to `unused/`.
4. The voice over row leaves the main menu; update menu rows, hints, tests, `docks/readme.txt` and the changelog.

**Open for the dev to decide when reached:** whether speech interrupts or queues (suggested: interrupt for gameplay callouts, queue for tutorial lines).

**Status:** planned. Mark finished only once the dev says it works.
