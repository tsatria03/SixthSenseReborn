---
name: project_provenance
description: "lbk2907 is the original creator of the port, and the Initial commit is entirely their work and names them as author. They handed the repo to tsatria03 to publish on GitHub and work on together. How to credit them."
metadata:
  node_type: memory
  type: project
  originSessionId: 8a78e7c9-236d-421e-8e76-c11a2895c278
---

**lbk2907 is the original creator of this repository.** Their work covers:
- extracting the binary (`analysis/bin/sixsense_armv7`)
- the analysis tools in `tools/` and everything in `analysis/`
- the whole Python port (`SixthSense.py`, `sixthsense/`; the entry script is `SixthSenseReborn.py` here now)
- `docs/` (its three references are in `aidocks/` since 2026-09-23; since 2026-10-04 only `GAME_STRUCTURE.md` is in this repository, and `DIVERGENCES.md` and `PORTING_STATUS.md` are in SixthSenseOriginal) and `tests/`
- **the full `README.md`**. Their version was lost before the initial commit: the repo only ever held GitHub's two-line stub, and neither the history nor Git's unreachable objects had their text. The dev restored it by hand on 2026-09-22. It was committed with updates and a Credits section as `4491f93`, which was then rewritten and force-pushed as **`7cf3e78`**, at the dev's request, to add `Co-authored-by: lbk2907`. The local backup branch `backup/before-readme-coauthor` was deleted the same day, once the dev had checked the result on GitHub. `main` is again the only branch.

They handed the repository to the dev, tsatria03, to publish at `github.com/tsatria03/SixthSense-Windows`, so the two of them can work on it together and add more contributors later. Their own version was never on GitHub, and they gave permission to publish it. The dev said all this on 2026-09-21 and plans to add lbk2907 as a contributor on GitHub. That repository is now SixthSenseOriginal; Reborn is at `github.com/tsatria03/SixthSenseReborn` since 2026-10-04 ([[project_two_repos]]). Name both by username only ([[feedback_use_github_usernames]]).

**The commit titled "Initial commit" is entirely lbk2907's work, and names them as its author.**
- It was first published as `a7108d2` with the dev as author.
- On 2026-09-21, at the dev's request, it was rewritten and force-pushed as `cf36408`, keeping the same files, message and timestamps.
- Its author is now `lbk2907 <54381410+lbk2907@users.noreply.github.com>`, and its committer is `tsatria03`, who published it.
- The second commit, "Port Sixth Sense to Windows from its reverse-engineered iOS binary", states the same attribution in its description.
- The two local backup branches made during the rewrite (`backup/before-author-rewrite` and `backup/before-username-change`) were deleted on 2026-09-21 at the dev's request, once the dev was happy with the result on GitHub. `main` is the only branch.

**Other contributors:**
- **tunmi13productions** fixed the coin economy and the spoken-digit order in `a16564f` (2026-09-21), found partly through live testing. They also committed batch 2, the vocal fixes (`503085a`), and the zombie batch (2026-09-22) from their own machine, under their own git identity. Since then they have become one of the two primary authors (see below); their larger work includes the screen reader mode (2026-09-22) and removing voice over (2026-10-05), the Linux build and release (2026-09-28), controller support (2026-10-04), the release workflow (2026-10-05) and `tests/suite.py` (2026-10-06).
- **mzanm** added the macOS runtime and native app builds in pull request #1 (`425bbf9`, 2026-10-02).
- When a contributor's commit and our own work fix the same thing, keep the contributor's version and drop ours. That is the dev's standing preference, first applied to batch 1 on 2026-09-21.

**Why:** Credit and permission matter for this project, and the code itself doesn't say who wrote the initial import.

**How to apply:**
- **"The dev" is whoever is in the session, not always the same person.** tsatria03 and tunmi13productions both work on this repository, and the older notes say "the dev" for tsatria03 because they were written in tsatria03's sessions. **Never guess which one you are talking to from the notes.** `git config user.name` says it, and the session's own git identity is in the environment. On 2026-10-06 Claude credited today's decisions to tsatria03 in new code comments and a plan note; tunmi13productions corrected it ("no, I'm tunmi13productions") and the comments were fixed. When a note records a decision, name the person who made it, by GitHub username ([[feedback_use_github_usernames]]).
- Credit lbk2907 wherever credits are written: a README, a credits file, or release notes. **`README.md` has had a Credits section since 2026-09-22**, at the dev's request:
  - lbk2907 first, as the one who started the port
  - then **the two primary authors, in the order they joined: tsatria03, who owns and publishes the repository, then tunmi13productions** (the dev, 2026-10-06: "the primary authors are me (tunmi13productions) and tsatria03. he's the main repo owner")
  - then the other contributors in the order they joined: **mzanm**, who added the macOS runtime and the native app builds through pull request #1 (their commit is authored "Mazen"; credits name them by their GitHub username, [[feedback_use_github_usernames]])
  - each linked to their GitHub profile, with a line on what they did
  - Bitbee named last, as the original game's maker

  When someone new contributes, add them at the end of the contributors list. The changelog carries no credit lines ([[feedback_changelog]]).

- **The credits say who did the big things, not every fix** (the dev, 2026-10-06: "don't do small things like, deleted the row. big things. for instance, added controller support. removed voiceover completely"). Rewritten from the commit history on 2026-10-06, 351 commits in: themed bullets for each primary author, the small fixes dropped. Where one of them built a feature and the other reshaped it, both are named for their part: tsatria03 built weapon upgrades, tunmi13productions retuned them to a share of each weapon's own stats; tunmi13productions added the screen reader mode, then removed voice over altogether. `docks/readme.txt` carries the same credits for players, one plain line each.
- The dev is the author of their own commits, under whichever identity git is set to in that session (tsatria03 is `156674543+tsatria03@users.noreply.github.com`). Only add them as a co-author when they ask; see [[feedback_git_commits]].
- When lbk2907 contributes to a commit, credit them with `Co-authored-by: lbk2907 <54381410+lbk2907@users.noreply.github.com>`. 54381410 is their public GitHub account ID, and the noreply form links the credit to their profile without exposing an email.
- `LICENSE` (MIT) reads "Copyright (c) 2026 tsatria03, lbk2907, tunmi13productions and mzanm" since 2026-10-06, when the dev asked for everyone who wrote part of the game to be named; before that it read "tsatria03 and lbk2907", from 2026-09-21. It ships beside the game as `license.txt`. Change it again only if the dev asks, for example to add a new contributor.
- Rewriting published history needs the dev's explicit go-ahead each time. For how commits and pushes work in this repo, see [[feedback_git_commits]].
