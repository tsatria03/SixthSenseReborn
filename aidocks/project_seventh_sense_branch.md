---
name: project_seventh_sense_branch
description: "The seventh-sense branch is a deliberate branch of the faithful port where changes need not match the original; how to work on it and which rules change."
metadata:
  type: project
---

**`seventh-sense` is a branch of the port where we make our own changes, not faithful to the original.** It was started on 2026-10-04 from `main` at `6d964dc`. The name is a step beyond Sixth Sense, chosen over "Sixth Sense Plus". `main` stays the faithful port.

**Why:** The dev wants room to redesign, add and change things the original never did, without each change counting as a divergence from a binary that is meant to be matched.

**How to apply on this branch:**
- Fidelity to the binary is no longer the goal. Do what the dev asks, even when the original did otherwise.
- When the dev proposes a change, or asks how something should work, compare briefly: say what the original did (from the binary, with the address when it matters), then the likely better solution or the difference. Then follow the dev's choice. Do not argue for the original, and do not refuse a change for not matching it.
- The original is a reference, not a rule. Keep consulting `analysis/` when it helps, and keep [[project_binary_analysis_notes]] in mind when reading it.
- **Removed on 2026-10-04 because they existed to keep the port faithful:** `DIVERGENCES.md`, `PORTING_STATUS.md`, `project_evaluation_2026_09.md` and `feedback_side_by_side.md`. They are still on `main`. Record this branch's changes in the changelog (when a player notices them) and in the plan note for the feature ([[feedback_record_plans_first]]). `GAME_STRUCTURE.md` and [[project_binary_analysis_notes]] stay as references for how the original works.
- Tests that pin original behavior may be changed with the code, in the same change.
- **Direction (2026-10-04):** drop the recordings eventually, speak all game speech through Prism, and make the tutorial screen reader friendly. These are on the todo list, not started.
- Everything else carries over: Python only ([[project_python_only]]), the dev runs and builds ([[feedback_dont_run_or_build]]), safe silent tests ([[project_safe_test_run]]), NVDA-friendly output ([[user_screen_reader]]), changelog and todo list formats, and the commit and push rules ([[feedback_git_commits]]).
- Changes made on `main` can be merged into this branch, but only the dev decides what goes back the other way; this branch's changes are not meant for `main`.
- **Renamed on 2026-10-04:** everything outside `game/` and `analysis/` says Seventh Sense: `SeventhSense.py`, the `seventhsense/` package, the `SEVENTHSENSE_*` environment variables, the save folder (`%APPDATA%\SeventhSense`, so Sixth Sense saves are not shared), the build names and the docs. Kept as they were: `game/`, `analysis/` and `tools/sixsense` (the original's data and binary), the bundle id `kr.co.bitbee.sixsense`, the in-game recordings and their text (the intro still says Sixth Sense), the GitHub repo URLs, released changelog entries, and the word "Sixth Sense" wherever it means the original game.
- Credit and provenance are unchanged ([[project_provenance]]). The game is still a derivative of the 2013 original, so keep the title clearly separate from it when releasing anything under the Seventh Sense name.
