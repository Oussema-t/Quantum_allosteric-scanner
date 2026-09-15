# TASK-0375 — `git` invoked as a subprocess of `python3` fails on this machine (xcrun arch mismatch)

- Status: Done
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

- **Narrowed, 2026-09-15, not fully closed**: confirmed this is a
  subprocess-creation-level architecture routing issue (`subprocess.run`
  children run under Rosetta/x86_64 even from a confirmed arm64-native,
  non-fat `python3`, with environment variables ruled out directly —
  `env={}` still reproduces it), NOT a CLT installation defect — two real
  incidents (2026-09-12, 2026-09-13) both show a CLT reinstall leaves this
  exact symptom unchanged. Still open: WHY `subprocess`'s process creation
  picks the x86_64 slice specifically on this machine. Plausible,
  unconfirmed: an inherited "responsible process" or `posix_spawn` binary
  preference from further up this session's own process ancestry (e.g.
  the VS Code extension host, if that itself runs under Rosetta) — no
  longer believed to be CLT-related at all, which the 2026-09-12/13
  entries above assumed. Not required to fix: `_git`'s `arch -arm64`
  retry works around it regardless of the mechanism.
- Whether the CLT reinstalls were doing *anything* useful for this
  specific failure, or only ever fixed the separate direct-shell-call
  symptom (the PreToolUse hook's own bootstrap) — per the above, now
  believed to be the latter, exclusively. A future recurrence should
  reach for `_git`-style hardening or `arch -arm64` directly, not another
  CLT reinstall, unless the direct-shell-call symptom is *also* present.

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
- [x] User repairs the CLT installation again -- `sudo rm -rf /Library/
      Developer/CommandLineTools` + `xcode-select --install`, same as
      2026-09-12.
- [x] Re-run the reproduction; confirm it succeeds on both interpreters --
      **only partially did.** See the 2026-09-15 correction below: the
      reinstall fixed *direct* shell git calls (this session's own Bash
      tool calls, previously fully blocked, came back), but a bare
      `python3 -c "subprocess.run(['git', ...])"` reproduction **still
      failed, identically, after the reinstall.** This is the real finding
      this pass -- see below, superseding this checklist item's original
      framing.
- [x] Re-run the full `.ai/tools/` suite; confirm 0 failures -- **172
      passed**, after the root-cause fix below (not from the CLT reinstall
      alone, which left this suite still failing).
- [x] Specifically re-check `move`/`resolve`'s own staging -- confirmed via
      the new `_git` primitive's own tests plus a live `commit-guard
      --expect-empty` call succeeding end to end.

## Correction, 2026-09-15 (Toolsmith) — the CLT reinstall was never the
## real fix for this specific failure; found and fixed the actual cause

**A second CLT reinstall (identical to 2026-09-12's) left the python-
subprocess git failure completely unchanged.** What it DID fix, newly
discovered this pass: this session's own Bash tool had gone from "every
call blocked" (the PreToolUse hook's own bootstrap, `$(git rev-parse
--show-toplevel)`, is itself a **direct** shell git call, and had started
failing too between 2026-09-13 and 2026-09-15 -- a new, more severe
symptom not seen before) back to working. So the reinstall fixed *direct*
shell git invocations (again); it never touched the python-subprocess
path, and the 2026-09-12/13 entries above were wrong to treat a CLT
reinstall as the fix for that path -- it visibly helped because it
unblocked the hook, which made it look like a fix for the whole thing.

**Root cause, found by actually testing the hypothesis rather than
guessing further:**

```
python3 -c "import subprocess; print(subprocess.run(['arch']).stdout)"
```
prints `i386` -- from inside a confirmed-arm64, non-fat `python3` binary
(`platform.machine()` also says `arm64`; `lipo -info` on the interpreter
itself confirms single-architecture arm64, not a Rosetta-translated
binary). The **same** `arch` command typed directly in a shell prints
`arm64`. Ruled out environment variables as the cause directly: `arch`
run via `subprocess.run(['arch'], env={})` (a completely empty
environment) still prints `i386`. So an arm64-native python process's
*subprocess children* are, on this machine, routed through Rosetta/the
x86_64 execution context regardless of environment or the parent's own
architecture -- a process-creation-level behavior (`posix_spawn`
architecture preference, plausibly inherited from further up this
session's own process ancestry, e.g. the VS Code extension host), not a
CLT installation defect at all. `git`'s x86_64 slice then needs `xcrun`,
whose x86_64 support was never present to begin with on an Apple-Silicon
CLT install -- **there was never anything to reinstall for this specific
symptom.**

**Confirmed the fix, not guessed:**
```
python3 -c "import subprocess; r=subprocess.run(['arch','-arm64','git','rev-parse','HEAD'], cwd='.', capture_output=True, text=True); print(r.returncode, r.stdout, r.stderr)"
```
succeeds (exit 0, real commit hash, empty stderr) from the exact same
python process where a plain `git rev-parse HEAD` fails. Forcing the
arm64 slice explicitly, from inside the subprocess call itself, works
around the routing regardless of its own root cause.

### The real fix: `_git`, a single retrying wrapper, all call sites routed through it

New `_git(args, check=False, capture_output=False, cwd=None, input=None)`
in `claim.py` (module-level, right after the path constants): runs
`["git"] + args`; if that fails with the `xcrun: error: unable to load
libxcrun` signature specifically, retries once with `["arch", "-arm64",
"git"] + args`. Safe to retry unconditionally on that one signature: a
failed git invocation had no real side effect (it errored before doing
anything), so retrying a normally non-idempotent command like `git mv`/
`git commit` is still safe -- confirmed by design, not just assumed.
Always captures internally (so the retry decision always has real stderr
to inspect, regardless of what the caller asked for) and writes captured
output through to the real stdout/stderr when the caller wanted it live
(`git commit -F`) rather than silently swallowing it.

**Every one of this file's ~16 `subprocess.run(["git", ...])` call sites
now goes through `_git`** -- `_stage_registry_row_only`'s surgical
COMMON.md staging, `_warn_if_duplicate_tracked`'s write-tree/ls-tree
check, `_perform_transition`'s `git mv`/`git add`/both tracked-checks,
`cmd_resolve`'s `git reset`, `_staged_paths` (the exact call that started
this whole task), `cmd_commit_guard`'s `git commit -F`, `_is_tracked`, and
`cmd_stage`/`cmd_add`'s `git add` calls -- not a partial fix. Also
refactored `_run_git_bool_check` (the 2026-09-12 hardening) to call `_git`
internally rather than a second raw `subprocess.run`, so the arch-retry
applies there too, ahead of its own execution-failure detection.

**`test_claim.py`'s own scratch-repo bootstrap and ~25 direct git
verification calls had the identical unpatched bug** (they call git via
their own raw `subprocess.run`, not through `claim.py`) -- this is why
the suite had 46 failures even after `claim.py` itself was fixed earlier
in this pass. Fixed the same way: a module-level `_git` helper in
`test_claim.py` that delegates to `claim.py`'s own `_git` (reused, not a
second copy of the same workaround), and every raw git call in the file
converted to go through it.

**Tested, not just fixed:**
- New `test_claim.py::TestGitArchFallback` (6 tests, mocked
  `subprocess.run`, same reasoning as `TestGitExecutionErrorDetection` --
  reproducing a real git-execution failure means breaking git itself):
  success-on-first-try doesn't retry (asserts exactly 1 subprocess call);
  the xcrun signature retries exactly once with the correct `arch -arm64
  git ...` argv; an unrelated git failure (e.g. "not a git repository")
  does NOT retry; `check=True` still raises after the retry also fails;
  `capture_output=False` replays captured output to the real
  stdout/stderr (`capsys`); `input=` passes through.
- Live, against the actually-broken machine (no mocking): `claim.py
  commit-guard --expect-empty` -- the exact command that crashed opening
  this correction -- now succeeds.
- Full `.ai/tools/` suite: **172 passed**, 0 failed. `test_claim.py`
  alone: 51 -> 57 (the 6 new `TestGitArchFallback` tests), zero of the
  previous 46 scratch-repo failures remain.

### Outcome, 2026-09-15 (supersedes the incomplete checklist above)

- [x] Root cause identified precisely (Rosetta/posix_spawn subprocess
      routing, not a CLT defect) and confirmed by testing the fix
      directly, not guessed.
- [x] `_git` arch-fallback landed in `claim.py`, all git subprocess call
      sites routed through it.
- [x] `test_claim.py`'s own independent copy of the same unpatched bug
      found and fixed the same way.
- [x] Full suite green: 172 passed, 0 failed.
- [ ] Still open, correctly not claimed as closed: WHY subprocess children
      of an arm64-native python get Rosetta-routed on this machine
      specifically remains unconfirmed (Open Questions, below, updated).
      Does not block this task -- the fix works regardless of the
      mechanism -- but a future CLT reinstall attempt for a *different*
      symptom should not be assumed to touch this one again.
