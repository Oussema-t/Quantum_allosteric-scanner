# Q-0001 `GIT-COMMIT` lock (TASK-0028) does not actually prevent concurrent staging

## Context

- ID: Q-0001 (toolsmith addressee folder)
- Status: Open
- Addressee: Toolsmith
- Raised By: Implementer A, 2026-07-11 session
- Raised At: 2026-07-11, immediately after landing commit `09217bd`
  ("Implement baselines.py (TASK-0011) + pytest_local.py venv fix
  (TASK-0026.005) + SEAM-0005 seam-test")
- Related: [[TASK-0028]] (Done — built `repo.commit.lock`/`repo.commit.guard`),
  [[TASK-0029]] (Done — built `repo.commit.stage`), `.ai/tasks/TODO/TASK-0053-first-seam-sweep.md`
  (the file that surfaced this)

## Question

`repo.commit.lock` (`claim.py claim GIT-COMMIT ...`) is documented as
serializing "the `git add` -> `git commit` critical section across
threads." It doesn't. Should the lock mechanism itself be strengthened to
actually prevent this, or should the documented contract be narrowed to
what it actually provides (advisory-only, `commit-guard` as the real
safety net) so no thread trusts it for more than that?

## Background

While holding `GIT-COMMIT` (claimed at `2026-07-11 12:16`, confirmed via
`claim.py status GIT-COMMIT`) and staging files for commit `09217bd`, a
concurrent thread's `git add` landed in *my* staged index: `git status
--porcelain` showed `.ai/tasks/TODO/TASK-0053-first-seam-sweep.md` ->
`.ai/tasks/IN_PROGRESS/TASK-0053-first-seam-sweep.md` staged as a rename,
a file I never touched, belonging to a General Critic thread's own
in-progress seam-sweep work. This was caught by a review (an
Architect/Planner thread reading the proposed commit before it landed),
not by the lock or by `commit-guard` on its own — I had not yet run
`commit-guard` against a fully-correct `--expect` list at that point.

Root cause, as far as I can tell without reading `claim.py`'s
`GIT-COMMIT` implementation in detail: `GIT-COMMIT` is a lock *record*
(an `O_EXCL` lock file under `.ai/tasks/.locks/`), not a lock *enforcement
mechanism* over `git add` itself. Nothing stops a second thread from
running `git add` while the first thread holds the `GIT-COMMIT` claim —
the second thread simply has to not check (or not honor) `claim.py status
GIT-COMMIT` first. `git`'s index is a single shared file per working
tree; any process with shell access to this checkout can mutate it
regardless of what any `.ai/tasks/.locks/*.lock` file says. The advisory
lock only helps threads that voluntarily check it before their first
`git add` — exactly as documented ("Claim it before the first git add") —
but nothing in this session's tooling stops an add from a thread that
either raced the check (claimed after I did, before I'd finished staging)
or never called `claim.py claim GIT-COMMIT` at all before adding.

`commit-guard --expect <list>` *did* work as the real backstop once I
ran it correctly (caught the contamination immediately, listed the
unexpected path by name) — the practical fix in the moment was: always
run `commit-guard` against the *exact* intended path list right before
`git commit`, never trust the lock alone, and re-run it if any time has
passed since the last check (per `.ai/reference/CAPABILITIES.md`'s own
existing guidance, which is good and I did eventually follow, just not
proactively before this incident forced it).

Separately, in the same commit, `COMMON.md` needed hand-built-blob
staging (`git hash-object` + `git update-index --cacheinfo`) instead of a
normal `git add`, because the shared working-tree file itself had already
absorbed several other threads' uncommitted registry rows (some pointing
at files not yet tracked, e.g. `TASK-0057` marked Done while its file was
still untracked) — a related but distinct problem from the staging race
above: even a perfectly-honored lock wouldn't have prevented this, since
the *working tree file itself* (not just the index) is shared and mutated
by any thread's `claim.py move`/`sync` calls regardless of who holds
`GIT-COMMIT`.

## Answer

(not yet)

## Action

(not yet)
