---
name: project_custom_branch
description: "The custom branch is a deliberate branch of the faithful port where changes need not match the original; how to work on it and which rules change."
metadata:
  type: project
---

**`custom` is a branch of the port where we make our own changes, not faithful to the original.** It was started on 2026-10-04 from `main` at `6d964dc`. `main` stays the faithful port.

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
- **The name (2026-10-04):** tunmi13productions started the branch as `seventh-sense` and renamed the game Seventh Sense (`SeventhSense.py`, a `seventhsense/` package, `SEVENTHSENSE_*` variables, a `SeventhSense` save folder and build names). The same day tsatria03 renamed the branch `custom` on GitHub (the old name redirects) and the game back to Sixth Sense, as on `main`: `SixthSense.py`, `sixthsense/`, `SIXTHSENSE_*`, the builds `SixthSense-Windows`, `SixthSense-Linux` and `SixthSense-macOS`, and the save in `%APPDATA%\SixthSense`. **That save folder is the same one `main` uses**, so playing either branch's build reads and writes the same save.
- Credit and provenance are unchanged ([[project_provenance]]). The game is still a derivative of the 2013 original.
