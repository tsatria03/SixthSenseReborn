---
name: feedback_completed_projects
description: "A project note moves to aidocks/completed/ and loses its project_ prefix once the dev confirms the project works; links and paths are updated and the index lists it under Completed projects."
metadata:
  type: feedback
---

**A completed project leaves the main folder.** Once the dev says a project works (the same moment its note is marked finished, [[feedback_record_plans_first]]), its note moves to `aidocks/completed/`, loses the `project_` prefix (`project_save_split_plan.md` became `completed/save_split_plan.md`), and its `name:` line becomes the new stem. The dev asked for this on 2026-10-05, for organization, and had the existing finished notes moved the same day.

**Why:** the main folder had grown to over fifty notes, and most of the project notes were finished records that crowded out the ones still being worked on.

**How to apply:**
- Move it with `git mv`, so its history follows.
- A link `[[project_x]]` becomes `[[x]]`, and `aidocks/project_x.md` becomes `aidocks/completed/x.md`, in every note, in `CLAUDE.md`, and in code comments that cite the plan. Search the whole repository, `sixthsense/game/` included, and check nothing still says `project_x`.
- In `MEMORY.md`, move its line to the "Completed projects" section and point it at `completed/<name>.md`.
- A `[[name]]` link resolves to `aidocks/<name>.md`, or to `aidocks/completed/<name>.md` when there is no such file.
- Only a project the dev confirmed moves. A note that is "built, not yet confirmed" or "planned" stays. Reference notes that describe how something works (the binary notes, the sound organization, the volume knobs, the test range, the tests layout) are not projects and stay, even when the code behind them is done; ask the dev if one is unclear.
