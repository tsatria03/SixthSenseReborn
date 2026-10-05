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

**Stage 1 built 2026-10-05, awaiting the dev's ear:** the panel (rows, "Paused.", "Game over.", "Mission success."), Home/End/Left/Right on it and the headshot call ("Headshot!", `HEADSHOT_TEXT`) speak in both modes. The dev dropped "Now loading" entirely, so its recording (46) no longer plays in the stage, the tutorial or the test range. `zombies are coming` (328) was never played by the stage. The panel's TTSNumber readers (`ReadScore` and the rest) are now unused by the panel; stage 3 removes them. Tests updated: pause, weapon_range, monster_sound, gameplay, tutorial.

**Stage 2 built 2026-10-05, awaiting the dev's ear:** `stage_tutorial.BEATS` now holds Claude's drafted words (column 2) instead of recording numbers; `tutorial_beat` says words plus the key or controller hint as one line, and the monster comes in after a fixed 6.0 s (4.5 s for Eight) instead of 9.5/6.5. Ending: `TEXT_TUTORIAL_SUCCESS`, `TEXT_COUNTDOWN` ('3, 2, 1.', wait cut from 6.0 to 4.0 s) and `TEXT_ZOMBIES_COMING`. Key hints no longer depend on voice over. The words and the delays are drafts for the dev to correct.

**Stage 2b, agreed 2026-10-05 (tunmi13productions): the tutorial waits for Enter instead of a timer.** The fixed delays were guesses at how long the speech takes, so they go. The beats that send in a zombie (One to Five, FiveHalf, Eight) say their words, the key or controller line, then "Press Enter to continue." (a pad: its A button's name). Enter cuts the speech and sends the zombie at once. Any other key repeats the line while it waits; on a controller only Y repeats (the pad's A is Enter's stand-in already, `ui/controller.py`). Six, Seven and Nine have no zombie and no timer, so they only speak. When a zombie reaches you the beat's words are said again and it waits again, except Eight after the grab landed: the animal zombie is already on you and A is also the shake button, so that repeat says the shake line, does not wait and sends no second zombie. `BEATS` loses its delay column. Code: `Stage_Tutorial.waiting`, `tutorial_advance`, `tutorial_repeat`; keys in `Input.handle`, pad buttons in `Input.controller`.

**Status:** planned. Mark finished only once the dev says it works.
