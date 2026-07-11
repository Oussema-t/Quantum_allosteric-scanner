# Q-0001 `GIT-COMMIT` lock (TASK-0028) does not actually prevent concurrent staging

## Context

- ID: Q-0001 (toolsmith addressee folder)
- Status: Answered
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

Both, not either/or — and TASK-0042 already exists to do the strengthening,
so this isn't a new design decision, it's confirmation that its filing
threshold has now been crossed for real.

1. **Narrow the documented contract now** (done as part of answering this:
   `.ai/reference/CAPABILITIES.md`'s `repo.commit.lock` row and
   `.ai/COMMON.md`'s Current Rules bullet both said "serialize"/"claim it
   before" without ever stating plainly that nothing stops a
   non-honoring thread. Both rewritten to say so explicitly, and to name
   `commit-guard` as the actual backstop rather than implying the lock
   and the guard are equally load-bearing.
2. **Strengthen enforcement — via TASK-0042, not a new mechanism.**
   TASK-0042 ("Hook-enforce the `GIT-COMMIT` gate via a Claude Code
   `PreToolUse` hook") was filed exactly for this: "advisory first,
   harden only after a real failure" (this scaffold's standing
   precedent, TASK-0017→TASK-0024, TASK-0025's own deferral). It was
   filed after this session's *first* round of `.ai/COMMON.md` collisions
   and one misattributed commit; this incident is a *second*,
   independent crossing of that same threshold, this time hitting the
   lock itself rather than just the shared file. Recommend prioritizing
   TASK-0042 now rather than treating it as background backlog — I'll
   claim it if no one else has by the time I next pick up Toolsmith work.
3. **`commit-guard` did its job.** Worth stating plainly since it's easy
   to read this incident as "the tooling failed": the two-layer design
   (advisory lock + guard check) is working as built — the lock was
   never meant to be sufficient alone, `commit-guard --expect` catching
   the contamination immediately once run correctly is exactly what
   TASK-0028 designed it to do. The gap is procedural (run it every time,
   not just when something feels off) and now partly closed by the
   TASK-0042 hook proposal, not a design flaw in `commit-guard` itself.
4. **The separate "shared working-tree file" finding is real and
   distinct** — even a fully-enforced `GIT-COMMIT` gate on `git
   commit`/`git push` (TASK-0042's scope) would not stop a concurrent
   `claim.py move`/`sync` call from mutating `.ai/COMMON.md`'s *working
   tree content* out from under a thread mid-assembling its `--expect`
   list, since those calls write directly to disk, not through git's
   index at all. This is a different failure surface than the staging
   race above. It's not a gap in TASK-0042 — that task's own Out Of
   Scope already limits it to the `git add`/`commit`/`push` family, not
   arbitrary tool-driven file writes. It's additional real-world
   evidence for TASK-0024.001 (whole-file resource locks, generalizing
   `GIT-COMMIT` beyond the git index to arbitrary shared files like
   `COMMON.md` itself) — logged there directly rather than re-litigated
   here.

## Action

- [TASK-0042](../../../../tasks/TODO/TASK-0042-hook-enforced-commit-gate.md)
  (TODO, unclaimed) — the actual enforcement fix. Recommend prioritizing;
  not claimed as part of answering this question, left for whichever
  Toolsmith thread picks it up next (including possibly this one, later).
- [TASK-0024.001](../../../../tasks/TODO/TASK-0024.001-whole-file-resource-locks.md)
  (TODO, unclaimed) — received this incident's second finding (shared
  working-tree file mutation) as contributed evidence in its Open
  Questions section.
- Documentation narrowing (`repo.commit.lock`/`repo.commit.guard` rows in
  `CAPABILITIES.md`, the `GIT-COMMIT` bullet in `COMMON.md`'s Current
  Rules) — done directly as part of this answer, no separate task needed.

Moved `need-action/` → `answered/` (this thread, 2026-07-11): re-verified
both completed sub-items directly rather than trusting the write-up —
`CAPABILITIES.md`'s `repo.commit.lock`/`repo.commit.guard` rows and
`COMMON.md`'s `GIT-COMMIT` bullet both carry the narrowed, non-guaranteeing
language; `TASK-0024.001`'s Open Questions section carries the contributed
evidence dated 2026-07-11. Follow-through now fully owned by
[TASK-0042](../../../../tasks/TODO/TASK-0042-hook-enforced-commit-gate.md)
and [TASK-0024.001](../../../../tasks/TODO/TASK-0024.001-whole-file-resource-locks.md)
per the questions README's folder-is-state rule — neither claimed by this
move, both still TODO/unclaimed.
