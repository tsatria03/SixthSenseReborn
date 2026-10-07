---
name: feedback_git_commits
description: "One commit per fix. Commit only when the dev asks. 'Commit' means commit only; 'commit/push' means both (2026-10-07); the dev tests batches before pushing. Force pushes and history rewrites still need an explicit go-ahead. Use git commit -F with a message file, and never hide git's errors."
metadata:
  node_type: memory
  type: feedback
  originSessionId: 8a78e7c9-236d-421e-8e76-c11a2895c278
---

**"Commit" means commit only; "commit/push" means commit and push** (the dev, 2026-10-07: "When I say the word commit, that means you only commit the file, and or files. When I say commit/push, that means you can do both at once when possible. Most of the time I want to test my things before pushing a large batch, so I offen prefer you to commit things, rather than push them one after another"). So commits pile up locally by default, and a push waits for the dev to say "push" or "commit/push". When asking, ask whether to commit, and mention the local commits waiting rather than offering to push each one.

**Commit only when the dev asks.** Until 2026-10-07 the rule was to push straight after every commit the dev asked for (2026-09-21); that is replaced by the paragraph above.

**Unless the dev says to hold the pushes.** On 2026-09-24 they asked for commits without pushing ("no pushing yet. We still have a lot more commits to work on"); while that holds, commit when asked and push only when they say so.

**Fetching is fine without asking; bringing commits in is not** (the dev, 2026-09-24, refining a stricter rule from the same day: "You are allowed to fetch without asking, but never pull/merge/rebase commits unless I give you the goahead"). `git fetch` only updates what is known about GitHub and changes no branch, so run it freely, for example before a commit, to see what others such as tunmi13productions have pushed. **Never pull, merge, rebase, cherry-pick or reset onto incoming commits without the dev's go-ahead**, each time. When the branch is behind, report the incoming commits (who, what) and wait.

**Fetch after every few commits** (the dev, 2026-10-06: "Just to be safe, you should do a git fetch after every few commits or so"), above all while holding a batch of unpushed commits, so anything tunmi13productions pushes is reported before more local work piles up on top. Report incoming commits and wait, as below.

**Rewriting published history still needs an explicit go-ahead every time.** That covers force pushes, amending or rebasing pushed commits, and changing authors. When it is approved, push with `--force-with-lease=main:<expected hash>`, and keep a local backup branch until the dev is happy.

**Why:** The dev approves what goes into a commit, and after that, pushing is routine for them. History rewrites can lose work, so they stay a deliberate choice.

**How to apply:**
- Write the message to a file in the scratchpad and run `git commit -F <file>`. Windows PowerShell 5.1 breaks double quotes inside arguments passed to programs, so `-m` messages that contain quotes fail. Never send git's error output to `$null`; a failed commit must be visible.
- **Mark the work finished before committing it** (the dev, 2026-09-24: "always mark things as finished first before commiting"). When the dev asks to commit work that completes a task, move its line to finished (the todo list, [[project_dev_tasks]] or the plan note) first, so the finished line goes in the same commit as the work, not in a later one.
- **One commit per fix or change** (the dev, 2026-09-23: "for everything we fix, make them separate commits to keep things tidy"). Each commit carries its own todo, changelog, docs and memory lines. When two fixes share a file such as `changelog.txt`, stage each fix's lines on their own (build the index blob with `git hash-object -w` and `git update-index --cacheinfo`, since `git add -p` is interactive), and never `git add -A` while the index already holds the other fix.
- Stage files by name when the commit should hold exactly what the dev approved, or `git add -A` when they ask to commit everything; check `git status` first either way.
- Format: a short summary line, a blank line, then a plain-text description wrapped at about 72 characters. End with the trailers: `Co-authored-by: lbk2907 <54381410+lbk2907@users.noreply.github.com>` only when lbk2907 contributed, then the Claude attribution line.
- The dev is always the author. When they ask to be named as a co-author too, as they did on 2026-09-21 for the sound reorganization commit, add `Co-authored-by: tsatria03 <156674543+tsatria03@users.noreply.github.com>`; GitHub shows them once either way. Don't add it unasked.
- Never commit throwaway working folders, such as `game/sounds2/` (the flat originals kept only for matching). Binary files stay in git history forever even after deletion, so leave them out with `':(exclude)path'` and say so.
- Names are GitHub usernames only ([[feedback_use_github_usernames]]). The author is tsatria03 through this repo's local git config.
- After pushing, confirm with `git ls-remote origin refs/heads/main` and report the new commit to the dev.
- Committing isn't building or running; [[feedback_dont_run_or_build]] still applies to those.
