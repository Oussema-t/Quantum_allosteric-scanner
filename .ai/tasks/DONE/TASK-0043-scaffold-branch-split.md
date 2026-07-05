# TASK-0043 Split `bartosz` into a `scaffold` branch (PR-ready) and hold back product code

## Context

- ID: TASK-0043
- Title: Create a `scaffold` branch off `main` containing every `bartosz`
  commit except the one that touches `backend/`, so the 145-file
  coordination/documentation pile can move to `main` as its own reviewable
  unit, separate from the one commit that actually changes deployed
  behavior
- Status: Done
- Owner: Architect/Planner
- Claimed By: Architect/Planner (this thread)
- Claimed At: 2026-07-05 20:27
- Source: user request, 2026-07-05 session — "Let us make a chunk for the
  Scaffold now. Also, a separate branch for Scaffold updates probably
  would be meaningful." Follows directly from the branch-merge planning
  discussion earlier this session (chunking `bartosz`'s 185-file diff by
  blast radius before merging to `main`).
- Scope: git history surgery only — no content changes beyond what was
  strictly necessary to keep `.ai/COMMON.md` and task-file locations
  internally consistent after excluding one commit.

## Intent Contract

- Outcome: a `scaffold` branch, based on `main`, containing all 40
  non-product-code commits from `bartosz` in their original order and
  authorship, verified to touch zero files under `backend/`/`frontend/`,
  with `.ai/COMMON.md`'s registry pointing only at paths that actually
  exist in that branch's tree. `bartosz` itself is untouched (no rewrite,
  no force-push) — this is additive history construction, not a rewrite.
- In Scope:
  - identify every `bartosz` commit touching `backend/`/`frontend/`
  - cherry-pick every other commit, in order, onto a new `scaffold` branch
    based on `main`
  - resolve any resulting conflicts caused by excluding the product-code
    commit(s), keeping the *documentation* of completed work accurate even
    though the *code* isn't present on this branch
  - verify: zero `backend/`/`frontend/` diff vs. `main`; every registry row
    points at an existing path
- Out Of Scope:
  - pushing `scaffold` to `origin` or opening the PR to `main` — this
    sandbox has no git network credentials (`git fetch`/`push` over HTTPS
    fails with no username, `gh` CLI isn't installed here) and no
    authority to merge into `main` unasked; the user does this part
  - the product-code chunk (`backend/geometry.py` Kabsch dedup) — stays on
    `bartosz`, handled as its own separate, smaller chunk later
  - the research-tree (`__WORK_IN_PROGRESS__`) port into `backend/` — that
    is TASK-0018's job, explicitly deferred per this session's plan
- Constraints And Invariants:
  - did not check out any other branch in the shared working directory —
    other threads may be actively working in this same working tree right
    now (confirmed multiple concurrent threads' commits landing during
    this very session). Used `git worktree add` for an isolated working
    directory instead, so nothing here could yank files out from under a
    concurrent thread mid-edit.
  - did not rewrite, rebase, or force-push `bartosz` — cherry-pick is
    additive; the original branch and its 41-commit history are untouched.
- Planned Validation:
  1. `git log --oneline main..scaffold | wc -l` — expect 40 (one less than
     `bartosz`'s 41).
  2. `git diff main...scaffold --stat -- backend/ frontend/` — expect
     empty output.
  3. every `| TASK-XXXX | ... | path |` row in `scaffold`'s
     `.ai/COMMON.md` resolves to a path that exists in that branch's tree
     (scripted check, not eyeballed).

## In Progress

None

## TODO

- [x] Identify which `bartosz` commits touch `backend/`/`frontend/`.
      **Result: exactly one** — `c5cd13f` ("Dedupe backend Kabsch into
      backend/geometry.py (TASK-0030)"). Verified by checking every one of
      the 41 commits' file lists against `-- backend/ frontend/`, not
      assumed from commit messages.
- [x] Create `scaffold` branch off `main` in an isolated `git worktree`
      (not the shared working directory).
- [x] Cherry-pick the 40 remaining commits in original order.
      **Result:** one conflict, at commit `42bfa1d`, in `.ai/COMMON.md`'s
      TASK-0030 registry row — because `c5cd13f` (the excluded commit)
      *also* bundled moving TASK-0030's task file to `DONE/` and updating
      its registry row in the same commit as the code change. Everything
      else applied clean.
- [x] Resolve the conflict without reintroducing product code: pulled
      `c5cd13f`'s final version of the task file
      (`git show c5cd13f:.ai/tasks/DONE/TASK-0030-...md`), confirmed by
      diff that the only differences from the pre-code TODO version were
      status/checklist/Done-section text (no code, no paths outside
      `.ai/`), moved the file to `DONE/` on the `scaffold` branch with
      that content, and resolved the registry row to `Done`/`DONE/` path
      with a one-line note that the code itself lives on a separate
      product-code chunk. This keeps the task documentation truthful
      (TASK-0030 *is* done) without smuggling backend code onto the
      scaffold branch.
- [x] Run all three Planned Validation checks — all passed (40 commits;
      empty backend/frontend diff; zero dangling registry paths).

## Dependency

- None blocking. Produces the "Chunk 1" input for the `bartosz` → `main`
  merge plan discussed earlier this session.
- The excluded commit (`c5cd13f`, TASK-0030) becomes its own follow-up
  chunk — smaller, higher-scrutiny, since it's the one that actually
  changes deployed backend behavior. Not filed as a separate task here;
  it's already fully documented in `TASK-0030`'s own Done section on both
  branches.

## Open Questions

- **Going-forward branch convention:** the user asked for "a separate
  branch for Scaffold updates" as an ongoing pattern, not just this one
  split. Recommend: future scaffold-only work (task filing, `.ai/`/
  `.github/`/`.claude/` edits with no `backend/`/`frontend/` touch) is
  authored directly on `scaffold` (or branched from it) going forward,
  while product-code work stays on feature branches off `main`. Left open
  for explicit user sign-off rather than declared unilaterally — this is
  a durable workflow-policy decision, not a one-off git operation.
- **Push/PR step is blocked on the user's own credentials** — this
  sandbox genuinely cannot authenticate to `origin` (`git fetch`/`push`
  fail with "could not read Username"; no `gh` binary present). The
  `scaffold` branch exists only in a local worktree
  (`/tmp/.../scratchpad/scaffold-worktree`) until the user pushes it
  themselves or supplies credentials.

## Done

- Created `scaffold` branch off `main` (a68ea70) in an isolated worktree.
- Cherry-picked all 40 non-product-code `bartosz` commits onto it, in
  original order and authorship, with one conflict resolved as described
  above (TASK-0030's Done-documentation kept, its code excluded).
- Verified: `git log --oneline main..scaffold` = 40 commits;
  `git diff main...scaffold -- backend/ frontend/` = empty;
  every `.ai/COMMON.md` registry path on `scaffold` resolves to a real
  file in that branch's tree.
- `bartosz` untouched — no rewrite, no force-push, still carries all 41
  original commits including the excluded `c5cd13f`.
- **Not done (needs the user):** `git push -u origin scaffold` and
  opening the PR to `main` — no network credentials available in this
  environment.
