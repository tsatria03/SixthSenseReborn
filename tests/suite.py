"""Run every test in tests\\case\\ side by side, and write what passed and what failed to a file.

    python tests\\suite.py                  every test file, several at a time
    python tests\\suite.py gameplay input   only those files
    python tests\\suite.py -j 4             four at a time instead of the default
    python tests\\suite.py --serial         one at a time, the old way

Each file runs as its own process, exactly as `python tests\\case\\<name>.py` does by hand, so every file
still sets its own throwaway save folder, its own silence and the null audio and dummy video drivers for
itself through `_scratch_save`.  Nothing here loads the game, so the suite itself can neither speak nor
open a device, and this run is as silent and as far from the real save as a run by hand
(aidocks/project_safe_test_run.md).

The slowest files start first, from the times kept in tests\\results\\timings.json, because one long file
decides how long the whole run takes: gameplay.py alone is over a minute.  A file with no time on record
is treated as a slow one, so a new file is never left until the end.

A file that fails is run once more on its own, since a test that fails only while sixteen other processes
are running is a test that needs its own clock, not a broken one.  The report says which of the two it
was.  `--no-rerun` leaves it out.

The terminal gets one line per file.  Every test name and its result goes to
tests\\results\\results-<date>-<n>.txt, with the totals, the times, the commit it ran on, and the real
save's files before and after to show the run never touched them.  A file that passes contributes its test
lines only, since the game's own warnings and the tracebacks its error-path tests expect would bury them;
a file that fails has its whole output kept, at the end, where it is worth reading.  The exit code is 1 if
anything failed, so a build or a workflow can run this first.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date, datetime

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
CASE = os.path.join(HERE, 'case')
RESULTS = os.path.join(HERE, 'results')
TIMINGS = os.path.join(RESULTS, 'timings.json')

# What tests/case/_scratch_save.py sets for every test file.  Set here as well, so a file that somehow
# misses that import is still silent and still off the real save.  SIXTHSENSE_USER_DIR is left to the
# file itself, which gives each process a folder of its own.
QUIET = {
    'SIXTHSENSE_SILENT': '1',
    'ALSOFT_DRIVERS': 'null',
    'SDL_AUDIODRIVER': 'dummy',
    'SDL_VIDEODRIVER': 'dummy',
    'PYGAME_HIDE_SUPPORT_PROMPT': '1',  # not one of _scratch_save's; it keeps pygame's banner out
}

UNTIMED = 9999.0                        # an unknown file sorts first, never last
COUNT = re.compile(r'^(\d+)/(\d+) passed$')


def test_files():
    """Every test file in tests/case/, by name.  `_scratch_save.py` is a helper, not a test."""
    return sorted(n for n in os.listdir(CASE) if n.endswith('.py') and not n.startswith('_'))


def chosen(names):
    """Turn what was typed on the command line into file names, with or without the .py."""
    have = test_files()
    out, missing = [], []
    for name in names:
        want = name if name.endswith('.py') else name + '.py'
        want = os.path.basename(want)
        if want in have:
            out.append(want)
        else:
            missing.append(name)
    if missing:
        sys.exit('no such test file: %s\nthere is: %s' % (', '.join(missing),
                                                          ', '.join(n[:-3] for n in have)))
    return out


def timings():
    try:
        with open(TIMINGS, encoding='utf-8') as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return {}


def keep_timings(times):
    known = timings()
    known.update(times)
    os.makedirs(RESULTS, exist_ok=True)
    with open(TIMINGS, 'w', encoding='utf-8') as fh:
        json.dump(known, fh, indent=1, sort_keys=True)


def longest_first(names):
    known = timings()
    return sorted(names, key=lambda n: (-known.get(n, UNTIMED), n))


def parse(output):
    """Read the counts and the failures out of a test file's own runner output.

    Every file ends in the same runner, which prints `ok    <test>` for each one that passes,
    `FAIL  <test>: <message>` or `ERROR <test>: <repr>` for each one that does not, and `<n>/<n> passed`
    on the last line.  inventory.py also prints a bare `<test>:` line before each test, which is ignored.
    """
    passed = total = None
    bad = []
    for line in output.splitlines():
        line = line.rstrip()
        hit = COUNT.match(line)
        if hit:
            passed, total = int(hit.group(1)), int(hit.group(2))
        elif line.startswith('FAIL  ') or line.startswith('ERROR '):
            kind, rest = line.split(' ', 1)
            bad.append((kind, rest.strip()))
    return passed, total, bad


def results_only(output):
    """A file's test lines on their own, and how many lines of other output were left out.

    A file that passes still prints the game's own warnings and the tracebacks its error-path tests
    expect, which across 34 files buries the results.  The report keeps the whole output of a file that
    failed, and only the test lines of one that passed.
    """
    keep, dropped = [], 0
    for line in output.splitlines():
        line = line.rstrip()
        if not line:
            continue
        if line.startswith(('ok    ', 'FAIL  ', 'ERROR ')) or COUNT.match(line):
            keep.append(line)
        else:
            dropped += 1
    return keep, dropped


def run_file(name, timeout):
    """Run one test file as its own process and read its output back."""
    env = dict(os.environ)
    env.update(QUIET)
    started = time.time()
    try:
        done = subprocess.run([sys.executable, os.path.join('tests', 'case', name)],
                              cwd=ROOT, env=env, timeout=timeout,
                              stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        output = done.stdout.decode('utf-8', 'replace')
        code = done.returncode
        late = False
    except subprocess.TimeoutExpired as e:
        output = (e.output or b'').decode('utf-8', 'replace')
        code, late = -1, True
    passed, total, bad = parse(output)
    seconds = time.time() - started
    if late:
        bad.append(('TIMEOUT', 'the file was still running after %d s' % timeout))
    elif passed is None:
        bad.append(('ERROR', 'the file printed no count, so it stopped before its runner finished'))
    return {
        'name': name, 'seconds': seconds, 'code': code, 'output': output,
        'passed': passed or 0, 'total': total or 0, 'bad': bad, 'timeout': late,
    }


def line_for(run, done=None, of=None):
    """The one line a finished file gets in the terminal."""
    head = '%3d/%d ' % (done, of) if done else ''
    mark = 'ok   ' if not run['bad'] else 'FAIL '
    counts = '%d/%d' % (run['passed'], run['total']) if run['total'] else '-'
    tail = '' if not run['bad'] else '   %d failed' % len(run['bad'])
    return '%s%s %-20s %6.1fs %8s%s' % (head, mark, run['name'][:-3], run['seconds'], counts, tail)


def user_dir():
    """Where the real save lives, worked out without loading the game."""
    if sys.platform == 'win32':
        base = os.environ.get('APPDATA') or os.path.expanduser('~')
    elif sys.platform == 'darwin':
        base = os.path.expanduser('~/Library/Application Support')
    else:
        base = os.environ.get('XDG_DATA_HOME') or os.path.expanduser('~/.local/share')
    return os.path.join(base, 'SixthSenseReborn')


def save_snapshot(folder):
    """Each file under the real save with its size and its time, to compare after the run."""
    found = {}
    for here, _dirs, files in os.walk(folder):
        for name in files:
            path = os.path.join(here, name)
            try:
                stat = os.stat(path)
            except OSError:
                continue
            found[os.path.relpath(path, folder)] = (stat.st_size, stat.st_mtime)
    return found


def save_report(folder, before, after):
    if not os.path.isdir(folder):
        return 'there is no save at %s, so there was nothing to touch' % folder
    if before == after:
        return 'untouched, all %d files unchanged (%s)' % (len(before), folder)
    changed = sorted(set(before) ^ set(after)) + sorted(
        k for k in set(before) & set(after) if before[k] != after[k])
    return 'CHANGED, which should never happen: %s (%s)' % (', '.join(changed), folder)


def commit():
    try:
        out = subprocess.run(['git', 'rev-parse', '--short', 'HEAD'], cwd=ROOT,
                             stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
        head = out.stdout.decode().strip() or 'unknown'
        out = subprocess.run(['git', 'status', '--porcelain'], cwd=ROOT,
                             stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
        dirty = ', with uncommitted changes' if out.stdout.strip() else ''
        return head + dirty
    except OSError:
        return 'unknown, git did not run'


def results_file():
    """tests/results/results-<today>-<n>.txt, counting the runs already made today."""
    os.makedirs(RESULTS, exist_ok=True)
    today = date.today().isoformat()
    used = [int(m.group(1)) for m in
            (re.match(r'^results-%s-(\d+)\.txt$' % today, n) for n in os.listdir(RESULTS)) if m]
    return os.path.join(RESULTS, 'results-%s-%d.txt' % (today, max(used, default=0) + 1))


def write_report(path, runs, alone, wall, workers, save):
    passed = sum(r['passed'] for r in runs)
    total = sum(r['total'] for r in runs)
    failed = [r for r in runs if r['bad']]
    with open(path, 'w', encoding='utf-8', newline='\n') as fh:
        out = fh.write
        out('SixthSenseReborn test suite\n\n')
        out('run        %s\n' % datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        out('commit     %s\n' % commit())
        out('python     %s on %s\n' % (sys.version.split()[0], sys.platform))
        out('at once    %d file%s\n' % (workers, '' if workers == 1 else 's'))
        out('wall time  %.1f s, against %.1f s of running one after another\n'
            % (wall, sum(r['seconds'] for r in runs)))
        out('totals     %d of %d passed across %d files\n' % (passed, total, len(runs)))
        out('real save  %s\n' % save)

        out('\nFiles, slowest first:\n')
        for r in sorted(runs, key=lambda r: -r['seconds']):
            out('  %6.1fs  %-20s %8s%s\n' % (r['seconds'], r['name'][:-3],
                                             '%d/%d' % (r['passed'], r['total']) if r['total'] else '-',
                                             '   %d failed' % len(r['bad']) if r['bad'] else ''))

        out('\nFailures:\n')
        if not failed:
            out('  none\n')
        for r in failed:
            second = alone.get(r['name'])
            if second is None:
                note = 'not run again'
            elif second['bad']:
                note = 'failed on its own too, %d of them' % len(second['bad'])
            else:
                note = 'PASSED when run on its own, so it is the clock, not the code'
            out('  %s (%s):\n' % (r['name'][:-3], note))
            for kind, rest in r['bad']:
                out('    %-5s %s\n' % (kind, rest))
            if second is not None and second['bad'] and second['bad'] != r['bad']:
                out('    on its own:\n')
                for kind, rest in second['bad']:
                    out('    %-5s %s\n' % (kind, rest))

        out('\nEvery test, file by file:\n')
        for r in sorted(runs, key=lambda r: r['name']):
            lines, dropped = results_only(r['output'])
            out('\n=== %s, %.1f s, %d/%d ===\n' % (r['name'], r['seconds'], r['passed'], r['total']))
            for line in lines:
                out(line + '\n')
            if dropped:
                out("  (and %d line%s of the game's own warnings and the tracebacks its error-path tests\n"
                    '   expect, left out; run the file by hand to see them)\n'
                    % (dropped, '' if dropped == 1 else 's'))

        if not failed:
            return
        out('\nThe whole output of the files that failed, tracebacks and all:\n')
        for r in failed:
            out('\n=== %s, %.1f s ===\n' % (r['name'], r['seconds']))
            out(r['output'] if r['output'].endswith('\n') else r['output'] + '\n')
            second = alone.get(r['name'])
            if second is not None:
                out('\n=== %s again on its own, %.1f s, %d/%d ===\n'
                    % (second['name'], second['seconds'], second['passed'], second['total']))
                out(second['output'] if second['output'].endswith('\n') else second['output'] + '\n')


def main():
    ap = argparse.ArgumentParser(description='Run the tests in tests/case/ side by side.')
    ap.add_argument('files', nargs='*', help='only these test files, with or without the .py')
    ap.add_argument('-j', '--workers', type=int, default=0, help='how many files at a time')
    ap.add_argument('--serial', action='store_true', help='one file at a time, in name order')
    ap.add_argument('--no-rerun', action='store_true', help="don't run a failing file again on its own")
    ap.add_argument('--timeout', type=int, default=300, help='give up on a file after this many seconds')
    args = ap.parse_args()

    names = chosen(args.files) if args.files else test_files()
    if not names:
        sys.exit('no test files in %s' % CASE)
    workers = 1 if args.serial else (args.workers or min(8, os.cpu_count() or 4))
    workers = max(1, min(workers, len(names)))
    order = sorted(names) if args.serial else longest_first(names)

    folder = user_dir()
    before = save_snapshot(folder)

    print('%d test file%s, %d at a time, silent and on a throwaway save'
          % (len(order), '' if len(order) == 1 else 's', workers))
    runs, started = [], time.time()
    with ThreadPoolExecutor(max_workers=workers) as pool:
        waiting = [pool.submit(run_file, name, args.timeout) for name in order]
        for job in as_completed(waiting):      # whichever finishes first, so the lines come as they go
            runs.append(job.result())
            print(line_for(runs[-1], len(runs), len(order)))
    wall = time.time() - started

    alone = {}
    failed = [r for r in runs if r['bad']]
    if failed and not args.no_rerun:
        print('\n%d file%s failed, running each on its own to see if it was the clock'
              % (len(failed), '' if len(failed) == 1 else 's'))
        for r in failed:
            second = run_file(r['name'], args.timeout)
            alone[r['name']] = second
            print(line_for(second))

    after = save_snapshot(folder)
    report = results_file()
    write_report(report, runs, alone, wall, workers, save_report(folder, before, after))
    keep_timings({r['name']: round(r['seconds'], 1) for r in runs if not r['bad']})

    passed = sum(r['passed'] for r in runs)
    total = sum(r['total'] for r in runs)
    print('\n%d of %d passed across %d files, in %.1f s' % (passed, total, len(runs), wall))
    if before != after:
        print('the real save changed during the run, which should never happen; see the report')
    for r in failed:
        second = alone.get(r['name'])
        if second is not None and not second['bad']:
            print('%s failed only while the others ran, and passes on its own' % r['name'][:-3])
        else:
            names = [t.split(':')[0] for _k, t in r['bad']]
            more = '' if len(names) < 4 else ' and %d more' % (len(names) - 3)
            print('%s failed: %s%s' % (r['name'][:-3], ', '.join(names[:3]), more))
    print('the whole output is in %s' % os.path.relpath(report, ROOT))
    return 1 if failed else 0


if __name__ == '__main__':
    sys.exit(main())
