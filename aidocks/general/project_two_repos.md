---
name: project_two_repos
description: "Sixth Sense is two repositories: SixthSenseOriginal (the faithful port, frozen since 2026-10-05, not to be touched) and SixthSenseReborn (the old custom branch, where all work now happens and fidelity is not the goal)."
metadata:
  type: project
---

Since 2026-10-04 the game is two repositories, side by side in the dev's `games` folder:
- **SixthSenseOriginal** (`github.com/tsatria03/SixthSenseOriginal`, formerly SixthSense-Windows): the faithful port, `main` only. **Frozen since 2026-10-05.**
- **SixthSenseReborn** (`github.com/tsatria03/SixthSenseReborn`): the old `custom` branch, moved there with its full history on 2026-10-04 and deleted from SixthSenseOriginal. Fidelity is not the goal; its name for players is Sixth Sense Reborn.

**Why:** On 2026-10-04 the two were worked in tandem ("We are working on 2 repos in tandom"). On 2026-10-05 the dev fixed SixthSenseOriginal's last four port bugs (its `d51bc4c`) and then said: "Because I'm no longer touching the original repository, we can purely focus on this reborn one."

**How to apply:**
- Work only in SixthSenseReborn. Don't edit, commit to, or propose changes for SixthSenseOriginal, and don't plan a change as spanning both. It may still be read as a reference (its DIVERGENCES.md and notes record the binary evidence for the original's behaviour).
- The save folders (2026-10-04): SixthSenseOriginal keeps its save in `SixthSenseOriginal`; Reborn keeps its own in `SixthSenseReborn`, copying SixthSenseOriginal's save once, or an old `SixthSense` one.
- **Names (2026-10-04):** SixthSenseOriginal keeps the plain names (`SixthSense.py`, `SixthSense.exe`); Reborn's carry its own name (`SixthSenseReborn.py`, `SixthSenseReborn.exe`).
- The second evaluation's eight bugs: all are fixed in Reborn or no longer apply there, since tunmi13productions' screen-reader-only work and the purchase line fix (`4994824`, 2026-10-05). SixthSenseOriginal fixed four and keeps the original's own four.
