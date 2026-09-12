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

- [ ] User (or a thread with explicit authorization) repairs the CLT
      installation.
- [ ] Re-run the reproduction below; confirm it succeeds.
- [ ] Re-run `test_claim.py`'s full scratch-repo suite; confirm it's back to
      passing (it was, earlier this same session, before this broke —
      not a pre-existing failure to route around).
- [ ] Close this task once confirmed; no code change is this task's own
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
