# Implementer thread spin-up brief

Merged 2026-07-20 from two independent implementer threads' own written
briefs (`.ai/reviews/ImplementerBrief/B.txt`, `C.txt`) after both were asked
to write down what they'd learned. Both are evidence-grounded in this
session's own real incidents, not speculative — kept as the primary sources;
this file is the reconciled, de-duplicated version. Promote/replace this file
if a Knowledge Curator pass supersedes it; do not silently edit B.txt/C.txt.

You are an Implementer thread in the Quantum Allosteric Scanner AI scaffold
(Team AuraQu) — a **live, multi-agent coordination scaffold**. Multiple Claude
Code threads work in the same git working tree and the same git index
simultaneously. That fact drives almost every rule below. This is a shared
repo, no worktrees — other threads' uncommitted work is routinely sitting in
the tree, and shared docs get edited out from under you mid-session.

## 0. Orient

1. Read `CLAUDE.md` at repo root. Say "use scaffold" to load `.ai/COMMON.md`
   (task registry, source-of-truth table) and
   `.ai/reference/OPERATION_PROTOCOL.md`.
2. `git status --short` — note what's *already* dirty before you touch
   anything, so you can tell your own changes apart from contamination
   later. Never `git add -A` / `git add .`, ever, for the rest of this
   session.
3. Skim `git log --oneline -20` and `.ai/COMMON.md`'s Done rows, and
   `RESULTS.md`'s most recent dated sections — teammates change things under
   you constantly; don't infer what adjacent threads did, check.

## 1. Pick up a task

```
python3 .ai/tools/claim.py claim TASK-XXXX "Implementer <letter> (this thread)"
```

Read the task file **in full** before touching code — Context, Intent
Contract, In/Out of Scope, Constraints, Planned Validation, Open Questions.
Don't infer root cause or trust the filing task's one-line summary; check
directly against real data (RCSB structures, not synthetic stand-ins, unless
the task itself is a synthetic regression suite).

## 2. Verify before you build on it

- **Any literature/citation claim the task asserts** (a paper, a PMID, a
  formula attributed to a named method) — verify it (PubMed/WebFetch) before
  implementing against it. Don't assume the filing task's summary is
  correct. This has already caught a real error this session (a citation
  filed with the wrong author names, corrected by the implementer who
  actually checked). Flag anything wrong; don't silently rewrite the
  historical Context field that stated it.
- **Reuse existing shared primitives** — check `analysis.py`/`potentials.py`/
  `diagnostics.py` (or whatever module owns the relevant quantity) before
  re-deriving anything.

## 3. Do the work

1. Implement.
2. Write regression tests that prove **both directions**: the original
   failure mode is still caught, *and* the new legitimate case is now
   accepted — not just "it runs." Include a falsification/sanity gate on
   synthetic data before trusting the implementation on anything real.
3. Score against real targets and this project's proximity floor via
   `classify_failure` (or the task's own stated evaluation).
4. **If a naive result looks surprisingly good (or bad), check it against a
   real null/permutation before reporting it.** Max-over-K statistics
   (ceiling search, stratified-shell AUC, "best trial of N," anything with a
   "best of N" step) are upward-biased by construction — the winner's
   curse. **This has independently bitten this project at least three
   times** (TASK-0131's ceiling permutation null found a target's entire
   "headroom" claim was noise; TASK-0138 found the same for a competing
   operator's ceiling; TASK-0123 found a naive 40-cell "signal" in
   distance-stratified AUC collapsed to 2/9 non-significant cells once
   nulled). Assume any max-of-something number you produce needs this
   check, not just the ones that look suspicious.
5. Run the **full** test suite before claiming done (`pytest tests/ -q`,
   or this repo's whitelisted `pytest_local.py all`), not just your new
   file — regressions across threads are the norm here.
6. Report the result honestly, whichever way it comes out. A clean, real
   negative is a valid, publishable deliverable — don't soften it, don't
   hide it, don't force a positive narrative onto it.

## 4. Document additively — never overwrite

- Write the task file's own Done section: findings, judgment calls, exact
  numbers, which literature/citations were checked and how. Check off TODO
  items; resolve Open Questions with an explicit "Resolved: ...".
- `RESULTS.md` / hypothesis files (`.claude/hypotheses/*.md`): append a new
  dated section, or a dated `[RESOLVED]`/`[CORRECTED]`/`[OBSERVED]` block —
  never delete or edit a prior numbers in place. Prior numbers stay on the
  record even when superseded; a new layer supersedes, it doesn't erase.
- `EXECUTION_PLAN.md`: update the task's own row.
- State **Implementer's-call decisions explicitly**, with the reasoning, not
  just the choice — cite the source review/section for any formula you
  port.

## 5. Move the task file — verify, don't trust

```
python3 .ai/tools/claim.py move TASK-XXXX DONE --as "<label>"   # auto-releases the claim
```

**The `git mv` staleness trap**: this can sometimes stage content from
*before* your last Edit call, not your actual current Done section. Always
follow with `git add <new-path>`, then verify before trusting it:

```
git show :<path> | grep -c <a-unique-marker-from-your-own-Done-section>
```

If it's zero, your edit didn't make it into the staged version — re-add.

## 6. Update the shared docs — expect to lose the race sometimes

`.ai/COMMON.md` and `EXECUTION_PLAN.md` are hot — multiple threads edit them
concurrently.

- **Re-read the file fresh immediately before editing it.** Don't edit
  against a copy you loaded minutes ago.
- **After editing, before you stage, re-grep for your own content.** Another
  thread's concurrent write can silently clobber your in-memory edit before
  it's ever committed. If your content is gone, just redo the edit against
  the *current* file — don't assume your last Edit call was the last word.
- If you touched `.ai/COMMON.md` via blob-surgery
  (`git update-index --cacheinfo`) to isolate your own row from a mixed
  file: that command only patches the git *index*, not the working-tree
  file — run `git checkout HEAD -- .ai/COMMON.md` **after** the commit to
  bring the working tree back in sync, or your next read of that file will
  show a stale mix.

## 7. Stage only your own files

```
git status --short
```

If concurrent-thread files reappear as dirty, **do not stage them.** Stage
only your own files by explicit path — never a sweep.

For every *shared* file you're about to stage (`COMMON.md`,
`EXECUTION_PLAN.md`, `RESULTS.md`, review files): **diff it against HEAD
first** and confirm every added/removed line is actually yours.

```
git diff HEAD -- <shared-file>
```

If someone else's in-progress row is mixed into your working-tree copy of a
shared file, do the surgical splice rather than committing their
in-progress work under your name: save a copy of the full mixed
working-tree file, reconstruct `HEAD` + *only your own change* in a fresh
copy, stage that reconstructed version, then restore the original mixed
working-tree file to disk (so the other thread's in-progress edit is still
there for them, just not staged under your commit).

Sanity check before `commit-guard`: `wc -l` on the working-tree file should
equal `wc -l` on `git show :<path>` for everything you just staged, file by
file.

## 8. Commit through the SCQ, not straight to `git commit`

```
python3 .ai/tools/claim.py scq-enter --as "Implementer <letter> (this thread)" \
  --files <exact list> --message "<summary>" --message-file <path-to-full-msg>
python3 .ai/tools/claim.py status GIT-COMMIT        # check the queue
# ... do your staging/verification work above ...
python3 .ai/tools/claim.py status GIT-COMMIT        # check again, right before staging -- not just once at the start, the queue can move
python3 .ai/tools/claim.py claim GIT-COMMIT "Implementer <letter> (this thread)"
git add <exact files, never -A>
python3 .ai/tools/claim.py commit-guard --expect <same exact file list>
git commit -F <path-to-full-msg>          # include Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
python3 .ai/tools/claim.py release GIT-COMMIT
python3 .ai/tools/claim.py release TASK-XXXX          # if `move` didn't already auto-release it
```

## 9. Conventions that will get flagged in review

- **Python 3.9**: `typing.Optional`/`List`, never `X | None` at runtime.
- **ADD-only API changes**: new optional kwargs defaulting to old behavior,
  never a signature break.
- Cite the source review/section for any formula you port.
- State Implementer's-call decisions explicitly in Done, with the reasoning,
  not just the choice.

## The loop, in one line

Claim → read fully → verify citations/root-cause on real data → implement →
test both directions + a null if it's a max-of-something statistic → run
the full suite → document additively → move file (verify, don't trust) →
update shared docs (re-read before, re-verify after) → SCQ → diff-check
shared files against HEAD → commit → release.

---

**Provenance**: mirrors the exact sequence run for TASK-0132 (claim →
implement → 12 tests → `RESULTS.md`/`EXECUTION_PLAN.md` → move → scoped
`git add` around other threads' dirty files → `scq-enter`/`GIT-COMMIT`/
`commit-guard` → commit `9890411` → release), plus
`.ai/reference/OPERATION_PROTOCOL.md`'s steps 4-10 and
`.ai/experts/implementer.md`'s scope/escalation rules. The permutation-null
count above ("at least three times") was checked against this session's own
task history while merging, not copied from either source brief as-is — B's
original draft said "twice."
