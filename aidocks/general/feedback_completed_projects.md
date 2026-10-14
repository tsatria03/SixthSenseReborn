---
name: feedback_completed_projects
description: "Every plan lives in aidocks/plans/, planned or complete; a finished one is marked finished in its note and listed under Completed projects in the index, but never moves. The dev's layout since 2026-10-14; before it, a finished project moved to aidocks/completed/."
metadata:
  type: feedback
---

**A completed plan stays where it is.** Since 2026-10-14 the dev keeps the notes in two folders: `aidocks/plans/` holds every plan, planned or complete, and `aidocks/general/` holds the rest (feedback, project and user notes, `MEMORY.md` and `GAME_STRUCTURE.md`). The dev: "Plans should now hold things that are planned, but also complete." When the dev says a project works (the same moment its note is marked finished, [[feedback_record_plans_first]]), its status line says finished and its line in `MEMORY.md` moves to the "Completed projects" section; the file itself does not move.

**Why:** a plan that never moves keeps the same path from the day it is written, so the comments, notes and docs that cite it never need repointing when it is finished. The dev sorted the folder this way on 2026-10-14.

**History:** from 2026-10-05 a finished project moved to `aidocks/completed/` and lost its `project_` prefix (`project_save_split_plan.md` became `completed/save_split_plan.md`), the dev's rule then, because the main folder had grown past fifty notes. Every plan from `completed/` is now in `plans/` under the same name, and finished plans that say they "moved to `completed/`" describe that time.

**How to apply:**
- A new plan is `aidocks/plans/<name>_plan.md`, with no `project_` prefix and `name:` matching the file.
- A `[[name]]` link resolves to `aidocks/general/<name>.md` or `aidocks/plans/<name>.md`, whichever holds it. Paths in code comments and docs cite `aidocks/plans/<name>.md` or `aidocks/general/<name>.md`; inside `MEMORY.md`, a plan's link is `../plans/<name>.md`.
- Only a project the dev confirmed is listed as completed. A plan that is "built, not yet confirmed" or "planned" stays in the index's other sections. Reference notes that describe how something works (the binary notes, the sound organization, the volume knobs, the test range, the tests layout) are not plans and stay in `general/`; ask the dev if one is unclear.
