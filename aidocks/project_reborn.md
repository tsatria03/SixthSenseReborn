---
name: project_reborn
description: "SixthSenseReborn is where changes need not match the original; how to work on it and which rules change. It was SixthSenseOriginal's custom branch until 2026-10-04."
metadata:
  type: project
---

**SixthSenseReborn is where we make our own changes to the game, not faithful to the original.** The faithful port is the separate repository SixthSenseOriginal ([[project_two_repos]]).

**History:** it began on 2026-10-04 as the `custom` branch of SixthSenseOriginal (then SixthSense-Windows), started from its `main` at `6d964dc`. tunmi13productions first named that branch `seventh-sense` and renamed the game Seventh Sense; tsatria03 renamed the branch `custom` and the game back to Sixth Sense the same day. Later that day the branch moved here with its full history (pushed as this repository's `main`, 237 commits, no tags) and was deleted from SixthSenseOriginal. The game then took its own name, Sixth Sense Reborn ([[reborn_identity_plan]]).

**Why:** The dev wants room to redesign, add and change things the original never did, without each change counting as a divergence from a binary that is meant to be matched.

**How to apply:**
- Fidelity to the binary is not the goal. Do what the dev asks, even when the original did otherwise.
- When the dev proposes a change, or asks how something should work, compare briefly: say what the original did (from the binary, with the address when it matters), then the likely better solution or the difference. Then follow the dev's choice. Do not argue for the original, and do not refuse a change for not matching it.
- The original is a reference, not a rule. Keep consulting `analysis/` when it helps, and keep [[project_binary_analysis_notes]] in mind when reading it.
- **Not carried over, because they existed to keep the port faithful:** `DIVERGENCES.md`, `PORTING_STATUS.md`, `project_evaluation_2026_09.md` and `feedback_side_by_side.md`. They are in SixthSenseOriginal. Record this repository's changes in the changelog (when a player notices them) and in the plan note for the feature ([[feedback_record_plans_first]]). `GAME_STRUCTURE.md` and [[project_binary_analysis_notes]] stay as references for how the original works. Older notes here that mention those files describe SixthSenseOriginal.
- Tests that pin original behavior may be changed with the code, in the same change.
- **Direction (2026-10-04):** drop the recordings eventually, speak all game speech through Prism, and make the tutorial screen reader friendly. These are on the todo list, not started. **Dropping the recordings means the game stops playing them, never deleting them (the dev, 2026-10-04):** once Prism speaks what a recording said and the game no longer plays it, its file moves from `game/sounds/used/` to `game/sounds/unused/`, like every other sound the game does not play. Until then the recordings stay in `used/`, since the game still plays them.
- Everything else carries over: Python only ([[project_python_only]]), the dev runs and builds ([[feedback_dont_run_or_build]]), safe silent tests ([[project_safe_test_run]]), NVDA-friendly output ([[user_screen_reader]]), changelog and todo list formats, and the commit and push rules ([[feedback_git_commits]]).
- Fixes made in SixthSenseOriginal can be brought here when the dev asks; this repository's changes are not meant for SixthSenseOriginal.
- **Names:** players see Sixth Sense Reborn; `SixthSenseReborn.py`, `SixthSenseReborn.exe`, and the `SixthSenseReborn` save folder. The `sixthsense` package and the `SIXTHSENSE_*` variables keep their names.
- Credit and provenance are unchanged ([[project_provenance]]). The game is still a derivative of the 2013 original.
