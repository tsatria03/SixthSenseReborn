---
name: test_suite_plan
description: "FINISHED 2026-10-06, confirmed by the dev. tests/suite.py runs every file in tests/case/ as its own subprocess, several at once, longest file first, rerunning any failure alone; it writes tests/results/results-<date>-<n>.txt (gitignored) and exits 1 on a failure. Stage one is file-level parallelism only, about 320 s down to about 90 s."
metadata:
  node_type: memory
  type: project
---

**Status: finished 2026-10-06, confirmed by the dev**, who read a full run's report and said "alright it's all in working order". Everything below is in `tests/suite.py`, with `tests/results/` added to `.gitignore`. Five fast files ran 99 of 99 in 5.5 s against 9.5 s one after another, and a throwaway failing file proved the FAIL and ERROR lines, the rerun on its own, the failures section and the exit code 1. **The full run was made at the dev's asking: 637 of 637 across 34 files in 85.8 s, against 286.9 s one after another, with no failure, so no test in the suite is sensitive to running beside others** (recorded in [[project_safe_test_run]]). Waiting only on the dev's own word that it works.

**The discovery is tunmi13productions'** (the dev, 2026-10-07): they timed each file before designing anything, found that the cost was a few files waiting on the wall clock rather than the number of tests, and built the runner from that.

Asked for by the dev: "this test suite takes ages to run ... I propose we create a python script, maybe test_suite.py, under the tests folder. It runs through each test, reporting what succeeded and what failed in a results file."

## Why the suite is slow, measured first

Timed on the dev's machine (16 cores) before any design, so the plan answers the real cost:

- `gameplay.py` 83.2 s (59 tests)
- `input.py` 20.8 s (50)
- `window.py` 7.1 s (11), `monster_sound.py` 6.6 s (11), `focus.py` 2.2 s (4)
- `release.py` 0.7 s (52 tests), `paths.py` 0.7 s (24), `runloop.py` 0.1 s (8)

So the 320 s of the last full run is not the number of tests. `release.py` runs 52 tests in under a second. The cost is a few files waiting on the wall clock, `gameplay.py` above all, plus Python, pygame and OpenAL starting 34 times. `gameplay.py` was about 35 s in the first baselines and has grown to 83 s.

**What follows from that:** running files side by side wins about 3.5x and nothing more, because one file is 83 s on its own. That is the floor of stage one, and it is accepted.

## The plan

**`tests/suite.py`**, beside `case/` and `interact/`, not inside `tests/case/`, so `paths.py`'s `test_every_test_file_keeps_off_the_real_save` (which scans its own folder) does not see it. It imports no game code at all, so it cannot speak or open a device itself.

- **A subprocess per file, never an import.** This is required, not a convenience: each test file sets `SIXTHSENSE_USER_DIR`, `SIXTHSENSE_SILENT`, `ALSOFT_DRIVERS=null`, `SDL_AUDIODRIVER=dummy` and `SDL_VIDEODRIVER=dummy` at import through `_scratch_save`, and takes a throwaway save folder of its own. Importing the 34 files into one process would share one save folder and one OpenAL device, and `_scratch_save`'s `atexit` cleanup would run once at the end. As separate processes every safety guarantee of [[project_safe_test_run]] holds exactly as it does today, untouched.
- **Several at once**, `-j` workers, defaulting to a sensible share of the cores.
- **Longest file first.** The suite keeps the last run's per-file times in `tests/results/timings.json` and starts the slowest first, so `gameplay.py` begins at second zero rather than last. Without that, a short file scheduled last leaves `gameplay.py` running alone at the end. An unknown file is assumed slow, so a new file is not left for the end of its first run.
- **No test file has to change.** 33 of the 34 end in a byte-identical runner block printing `ok NAME`, `FAIL NAME: msg`, `ERROR NAME: repr` and `N/M passed`, exiting 1 on a failure. The suite parses that. `inventory.py` is the one exception: it prints an extra `NAME:` line before each test, which looks like leftover debugging; the parser tolerates it, and dropping that line is offered separately, not as part of this.
- **A failure is rerun once, by itself.** A test that fails only under parallel load is timing-sensitive, not broken, and telling the two apart is what makes a parallel run trustworthy at all. Any file with a failure is rerun alone afterwards and the report says "failed alone too" or "passed when run alone", which names the file as a flaky one to look at. `--no-rerun` switches it off.
- **The terminal stays short and quiet.** One line per file: name, time, counts. Then the failures. The tracebacks that `runloop`, `save` and `window` print on purpose from passing error-path tests are captured and kept out of the terminal, going to the results file only. Nothing reaches the screen reader, from the suite or from any child ([[user_screen_reader]]).
- **Flags:** `-j N`, file names to run only those, `--serial`, `--no-rerun`.
- **Exit code 1 on any failure**, so the release workflow can run it before it builds, which is an open developer task in [[project_dev_tasks]].

## The results file

`tests/results/results-<YYYY-MM-DD>-<n>.txt`, the number counting repeat runs the same day, ISO date so the files sort by date. **`tests/results/` is gitignored**, the dev's choice, so runs never show in `git status`.

It holds the full captured output of every file, every test name with its result, the per-file times, the totals, the wall time, the git commit, the worker count, and the real save's timestamp read before and after the run with a line saying it was untouched. That last part makes each run carry its own evidence, the way the runs recorded in [[project_safe_test_run]] do by hand.

## What the results file keeps, and what it leaves out

The first full run put all 34 files' raw output in the report, and the dev said: "yikes, it spit out the entire terminal window so you can see pygame and whatnot loading. goodness that's a lot". So, the same day:

- `PYGAME_HIDE_SUPPORT_PROMPT=1` goes to every child beside the guards from `_scratch_save`, which keeps pygame's two-line banner out of the report altogether.
- **A file that passes contributes its test lines only**, each `ok <test>` and the count, followed by one line saying how many lines of the game's own warnings and expected tracebacks were left out, so nothing disappears silently. The tests are what the report is for.
- **A file that fails has its whole output kept**, verbatim, in a section of its own at the end, with its rerun on its own below it, since there a traceback may be the answer.

## Left out, and why

- **Sharding a single file across workers.** The only way past the 90 s floor is to split `gameplay.py` and `input.py`, loading the file as a module and running a subset of its tests per process, which could reach about 30 s. It changes which tests share a process, so it is only safe if a sharded run reproduces the same counts. Held for a second stage, after stage one is confirmed. The dev chose stage one alone for now.
- **pytest.** The tests are plain scripts by the dev's design ([[project_tests_layout]]) and stay that way. The suite drives them as they are.
- **Making `gameplay.py` itself faster.** Its time is real waiting on the run loop's clock. Rewriting timing-sensitive tests is its own job, not this one.

## How to apply

- Run it as `python tests\suite.py`. It is the full suite, so it runs when the dev asks for a full run, not after every change; the only-the-matching-files rule still holds for ordinary work ([[feedback_dont_run_or_build]]), and naming files on the command line covers that case too.
- Record each full run in [[project_safe_test_run]] as before, with the commit, the counts and the time.
