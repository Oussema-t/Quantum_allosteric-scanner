# TASK-0375 — `git` invoked as a subprocess of `python3` fails on this machine (xcrun arch mismatch)

- Status: In Progress
- Owner: **Toolsmith** (finding + workaround); the actual fix needs the human user
- Priority: High — silently degrades every thread's commit-safety tooling
- Filed: 2026-09-12 by Toolsmith thread, corroborating an independent report
  from another implementer thread the same day
- Related: [[TASK-0367]] (where this was first found, mid-task), [[TASK-0028]]/
  [[TASK-0029]]/[[TASK-0356]] (`commit-guard`/`stage`, the tools this breaks)

## The finding

Any `git` subprocess call made from a `python3` process on this machine now
fails:

```
xcrun: error: unable to load libxcrun (dlopen(/Library/Developer/CommandLineTools/usr/lib/libxcrun.dylib, 0x0005):
tried: '/Library/Developer/CommandLineTools/usr/lib/libxcrun.dylib' (fat file, but missing compatible
architecture (have 'arm64,arm64e', need 'x86_64')), ...)
```

`xcode-select -p` reports `/Library/Developer/CommandLineTools` — the CLT
install itself is present, but its `libxcrun.dylib` is now arm64-only while
whatever exec path `/usr/bin/git` takes when spawned as a `python3` child
still requires an x86_64 slice. Reproduced with **both** the `pyenv`-shimmed
`python3` and `.venv/bin/python` (itself arm64 per `platform.machine()` —
this is not simply "the interpreter is x86_64", the exact mechanism is
unresolved, see Open Questions) — same error, same missing architecture.

**`git` invoked directly (not as a child of any `python3` process) is
unaffected** — confirmed repeatedly: a plain `git rev-parse HEAD`/`git init`
via a normal shell call succeeds every time, immediately before and after a
failing `python3 -c "subprocess.run(['git', ...])"` call against the exact
same repo.

## Two independent confirmations, same day

1. **This thread, mid-[[TASK-0367]]**: `claim.py stage`/`commit-guard` both
   raised `subprocess.CalledProcessError` from their internal
   `git diff --cached ...` calls. Reproduced identically on `test_claim.py`'s
   pre-existing, untouched `TestChainedTransitionNoDuplicate` class and on a
   bare `git rev-parse HEAD` in the real repo — ruling out anything
   TASK-0367 itself touched. Worked around by staging and committing that
   task's own changes with direct `git add`/`git commit` calls (verifying
   the staged diff by eye first), since `release` (pure JSON file I/O, no
   git subprocess) was unaffected.
2. **Another implementer thread, same day, independently**: identical
   symptom, identical root cause identified (`commit-guard`/`stage`'s
   internal `git diff --cached` subprocess call), identical workaround
   (manual stage/verify, direct commit), flagged specifically because it
   "will affect every other thread's SCQ sequence too until fixed."

Two independent threads hitting the exact same failure the same day is
itself signal: this is a live, ongoing hazard for anyone currently following
the documented `claim GIT-COMMIT -> stage -> commit-guard --commit -> release`
sequence, not a one-off fluke.

## Impact

- `claim.py stage`, `commit-guard` (both the read-only check and the
  TASK-0356 `--commit` atomic form), and anything else in `.ai/tools/` that
  shells out to `git` from Python is affected whenever invoked via a
  `python3` (pyenv or venv) interpreter on this machine specifically.
- `release`, `claim`, `move`, `resolve`, `sync` are **not** affected for
  their own claim-file bookkeeping (pure JSON/file I/O) but `move`/`resolve`
  DO shell out to `git mv`/`git add` internally for the actual file
  relocation — those calls are equally exposed; not yet confirmed broken
  live (this task's own `move` calls during filing happened to succeed, see
  Open Questions), so do not assume this is safe.
- `test_claim.py`'s entire scratch-repo test suite (~40+ tests, every class
  that calls `_make_scratch_repo`) cannot currently run to completion in
  this environment — every `git init` in a fresh scratch dir fails the same
  way.
- Every thread's `GIT-COMMIT` → `stage` → `commit-guard --commit` → `release`
  sequence is exposed to a silent step failure mid-sequence, on this
  machine, until fixed.

## Workaround in force (document, don't rely on silently)

Until fixed: stage with plain `git add -- <exact paths>`, verify with
`git diff --cached --name-status` **read by eye** (not `claim.py
commit-guard`), then `git commit -F <message file>` directly — all as plain
Bash/shell `git` invocations, never through a Python subprocess. `release
GIT-COMMIT` afterward is unaffected and should still be run normally.

## Recommended fix (human action required — not a task an agent thread can perform)

Reinstall/repair Xcode Command Line Tools:

```
sudo rm -rf /Library/Developer/CommandLineTools   # only if a plain reinstall doesn't take
xcode-select --install
```

or, if a full Xcode install manages the toolchain instead of the standalone
CLT package, verify `xcode-select -p`/`xcode-select -s` point at a complete,
non-arch-limited toolchain. This needs `sudo` and changes system state —
**out of any agent thread's authority to run unprompted**; flagging for the
user directly, not attempting it.

## Outcome

- [x] User repairs the CLT installation. `xcode-select --install` alone
      reported "already installed" and did NOT fix it (expected -- that
      command only installs when CLT is absent, it doesn't repair a broken
      one); `sudo rm -rf /Library/Developer/CommandLineTools` followed by
      `xcode-select --install` (GUI installer) did.
- [x] Re-run the reproduction below; confirm it succeeds. Confirmed, both
      interpreters: pyenv `python3` (`git rev-parse HEAD` -> exit 0, empty
      stderr) and `.venv/bin/python` (same).
- [x] Re-run `test_claim.py`'s full scratch-repo suite; confirm it's back to
      passing. `.ai/tools/` full suite: **161 passed**, 0 failed -- back to
      the pre-incident all-green state, not routed around.
- [x] Close this task once confirmed; no code change is this task's own
      deliverable, the finding + workaround + user handoff are.

## Reproduction (for whoever verifies the fix)

```
python3 -c "import subprocess; print(subprocess.run(['git','rev-parse','HEAD'], cwd='.', capture_output=True, text=True).stderr)"
```
Empty output = fixed. The `xcrun: error: unable to load libxcrun ...` text =
still broken.

## Open Questions

- Exact mechanism still unconfirmed: why does a `python3` PARENT process
  change which architecture slice of `/usr/bin/git` (and therefore `xcrun`)
  macOS execs, when `platform.machine()` reports `arm64` for that same
  `python3`? Plausible: Rosetta-related exec-preference state left over from
  something else running earlier in the session, not a property of the
  interpreter binary itself. Not required to fix (the CLT repair should
  resolve it regardless of mechanism) — recorded so a future recurrence
  isn't re-diagnosed from scratch.
- Whether this is specific to this one machine/session or would recur after
  a clean CLT reinstall (e.g. if something keeps re-triggering it) — nothing
  in either incident points at a repo-side cause, but not proven absent
  either.

## Done — 2026-09-12, Toolsmith

Fixed by the user, confirmed by this thread. `xcode-select --install` alone
was not sufficient (reported "already installed," left the broken lib in
place, exactly as this task's own Recommended Fix anticipated as a possible
outcome) -- `sudo rm -rf /Library/Developer/CommandLineTools` followed by
`xcode-select --install` (the GUI installer) resolved it.

Verified, not assumed: the exact reproduction command from this task's own
"Reproduction" section now returns exit 0 with empty stderr, checked against
BOTH interpreters this task named as affected (pyenv `python3` and
`.venv/bin/python`) -- the earlier finding never pinned the mechanism down
to one specific interpreter, so both needed checking, not just the one that
happened to be tested first. `claim.py commit-guard --expect-empty` (the
exact subcommand that raised `CalledProcessError` while filing this task)
now succeeds. Full `.ai/tools/` suite: **161 passed**, 0 failed -- the
scratch-repo suite this task's own Impact section said "cannot currently run
to completion" is confirmed back to fully passing, not routed around or
partially checked.

Root-cause mechanism (Open Questions' first item) remains genuinely
unconfirmed -- out of this task's own scope to chase further now that the
fix is verified and the symptom is gone; recorded as-is for whoever
re-diagnoses a recurrence, not closed as resolved.

## Correction, 2026-09-13 (Toolsmith) — recurred; the "closed as resolved"
## framing above was wrong, not the fix itself

**Reopened, not superseding the 2026-09-12 Done section above** (kept
verbatim, per this project's no-silent-overwrite convention) -- the CLT
repair genuinely worked THAT day, this is a second, independent
recurrence, reported by another thread and reproduced directly by this one
before touching anything:

```
python3 -c "import subprocess; print(subprocess.run(['git','rev-parse','HEAD'],
cwd='.', capture_output=True, text=True).stderr)"
```
-> the identical `xcrun: error: unable to load libxcrun ... need x86_64`
text, unchanged from the original finding. `claim.py commit-guard
--expect-empty` fails with the identical traceback too.

**New finding this pass, not documented before**: the Open Questions'
"not yet confirmed broken live" caveat about `move`/`resolve`'s internal
`git mv` is now confirmed, and the failure mode is WORSE than `stage`/
`commit-guard`'s loud crash. `_perform_transition`'s `tracked` check
(`claim.py:1108`) is `subprocess.run(["git", "ls-files", ...]).returncode
== 0` -- no `check=True`, so when `git` itself fails to run at all (the
xcrun error), `tracked` silently evaluates to `False` and the code takes
the "untracked, plain filesystem move" branch instead of `git mv`.
Reproduced live moving this very task file back to `IN_PROGRESS`: `move`
reported success ("moved TASK-0375 -> IN_PROGRESS ... registry updated"),
but `git status` showed the rename as a plain untracked add + unstaged
delete -- **nothing staged at all**, no error, no warning. A thread
trusting `move`'s own success message here would ship a commit missing
the very file it just "moved." Workaround unchanged (stage everything by
hand, verify by eye), but now known to apply to `move`/`resolve` too, not
only `stage`/`commit-guard`.

Recurrence is itself the answer to the Open Questions' second item
("would this recur after a clean reinstall") -- yes, on this machine, at
least once. Root cause still unconfirmed; not pursued further here either,
same reasoning as 2026-09-12.

### Code hardening landed this pass (does not wait on the CLT reinstall)

The silent-staging-fallback bug above is a real code defect independent of
whether this specific xcrun incident ever recurs again -- ANY transient git
execution failure (disk full, permissions, a future toolchain break of a
different shape) would have hit the identical silent misread. Fixed at the
source: new `GitExecutionError` + `_run_git_bool_check(args,
expected_no_needle)` (`claim.py`) -- runs a git subcommand that answers a
yes/no question via exit code, but only trusts a nonzero exit as a real "no"
if stderr matches the expected negative-answer shape (e.g. "did not match
any file" for `git ls-files --error-unmatch`, "does not exist in" for `git
cat-file -e HEAD:...`); anything else raises instead of silently returning
`False`. Wired into all three call sites that had this pattern:
`_perform_transition`'s `tracked` and `final_tracked` (`move`/`resolve`),
and `_is_tracked` (`stage`'s TASK-0197 deletion check) -- each site's own
caller now catches `GitExecutionError` and prints a clear `error: ... git
itself did not run as expected ...` message instead of either crashing with
a raw traceback or (the actual bug) silently proceeding as if nothing was
wrong.

**Tested without needing the environment fixed**: 5 new mocked tests
(`test_claim.py::TestGitExecutionErrorDetection`) -- fabricate the exact
`CompletedProcess` shapes for "tracked," "legitimately not tracked," and
"xcrun broken," asserting the third raises `GitExecutionError` rather than
returning `False`. Deliberately not scratch-repo-based like every other
class in this file: reproducing a genuine git-execution failure would mean
breaking git itself, not something a test should do to its own environment.
Full `.ai/tools/` suite otherwise unaffected: `test_submission_build.py`/
`test_submission_build_latex.py`/`test_pytest_local.py` -- 57 passed;
`test_claim.py` itself -- the 46 pre-existing scratch-repo failures are
unchanged in count and cause (still the environment, not this change), the
5 new tests pass, nothing newly broken.

### Outcome, this occurrence (separate from the 2026-09-12 checklist above)

- [x] Code hardening (above) -- landed and tested independent of the
      environment state.
- [ ] User repairs the CLT installation again.
- [ ] Re-run the reproduction; confirm it succeeds on both interpreters.
- [ ] Re-run the full `.ai/tools/` suite; confirm 0 failures (should now
      also implicitly re-validate the hardening's real-git-success path,
      already covered by the mocked tests but worth seeing live too).
- [ ] Specifically re-check `move`/`resolve`'s own staging (not just that
      they don't crash) -- stage something via `move`, confirm with `git
      status` that it actually landed in the index, not just on disk. The
      2026-09-12 pass never checked this and should have; the hardening
      above should now make a future recurrence LOUD here instead of
      silent, but confirm the happy path still stages correctly too.
