# TASK-0354 — Decision assertions at build time, not a passive decision index

- Status: TODO
- Owner: **Toolsmith**
- Priority: Low — tooling, not submission work; no deadline pressure
- Filed: 2026-09-09 by Toolsmith thread, as [[TASK-0352]] Part A's own scoping decision
- Related: [[TASK-0352]] (Part A, gated on this), [[TASK-0322]], [[TASK-0321]]

## Why Part A was not built as specified

[[TASK-0352]] Part A asked for "a generated index, one line per recorded
decision: what was decided, when, and where the reason lives." Investigated,
not built, for a reason [[TASK-0352]] itself surfaces but doesn't quite
follow through on: **an incomplete decision index risks the exact "confident
negative" failure [[TASK-0352]]'s own "why this is an index and not a search
tool" section warns about.**

The precedent it names ([[TASK-0322]]'s hypothesis index,
`.claude/hypotheses/INDEX.md`) works because hypotheses are already
**structurally tagged** — every `HYP-Pxx`/`HYP-Sxx` id lives in a canonical
register with a claim/status/citation field, and the index is *generated*
from that structure by `hyp_register_check.py --build-index`. "Decisions and
their reasons," by contrast, are not structurally tagged anywhere in this
repo — they're prose, scattered across config comments
(`config/targets.yaml`), organiser-clarification docs, DONE task Done
sections, and `.claude/hypotheses/*`. Building a real index would mean
either:

1. Retroactively tagging every decision across the whole repo — large,
   judgement-heavy, and not exhaustively verifiable as complete (the person
   doing the tagging is exactly the kind of single unreviewed pass this
   scaffold's own conventions distrust), or
2. Indexing only what's already easy to find mechanically — which
   reproduces the same **incomplete, confidently-presented index** problem
   [[TASK-0352]] itself argues a search tool has, just one layer removed.

Either way, a *passive* artifact that requires someone to remember to
consult it is also directly contradicted by [[TASK-0322]]'s own filed
citation-rate measurement: **9%**. Building a more complete list does not
fix a 9% consultation rate.

## What to build instead — the Reviewer's own reframing, taken seriously

[[TASK-0352]]'s "Hold released" addendum names the actual working precedent
already in this repo: `submission_build.py`/`submission_build_latex.py`
assert compliance (page count, font floor, clipping) **at the moment of
building**, not as a document someone has to go read. That pattern already
caught real defects within seconds of existing (a tofu-rendered glyph, an
uncited reference) that three careful human readings of the same PDF missed.

**Outcome for this task**: pick 1-2 of the four concrete incidents
[[TASK-0352]] Part A named, and turn each into a standing assertion that
fires automatically at the point something could get it wrong again — not
an index entry someone has to think to check. Candidates, in likely order of
tractability:

1. **`config/targets.yaml`'s genotype/apo-vs-holo comments.** The reason a
   wrong target (`8S8C`, wrong KRAS genotype) got proposed twice is not that
   the correct answer was hard to find — it was already an inline comment in
   the file being read. A pre-flight assertion (fires wherever target
   selection reads this file, or as a standalone check runnable before
   proposing a structure substitution) that fails loudly if a proposed PDB
   id contradicts the file's own recorded genotype/apo verdict would catch
   this at the moment of proposal, not on review.
2. Audit whether [[TASK-0130]] (the chiral-walk interference-test precedent,
   cited by four tasks per [[TASK-0352]]'s own table) has a natural
   "did you check this" hook — e.g. a lint rule or docstring pointer in
   whatever module a new interference-test variant would be added to.
3. The fourth incident ("consistent with the JACS ρ≈0.95") was genuinely
   unmeasured, not misfiled — no assertion applies; leaving it as a plain,
   named open question is correct and requires no tooling.

## Constraints And Invariants

- Same as [[TASK-0352]]: read-only where it's a check, no auto-repair.
- **Record the pointer, never restate the reason** — an assertion should
  fail with a pointer to `targets.yaml`'s own comment (or wherever the
  reasoning lives), not a restated summary of it that can drift from the
  source.
- Ships with a test proving the assertion fires on the seeded original
  mistake (propose the wrong genotype/PDB id, the check must fail) —
  [[TASK-0319]]'s standing rule, same as [[TASK-0352]] Part B.
- Do not build a general "decision index" alongside this without first
  checking whether the assertion-based approach alone already closes the
  gap the index was meant to close — per this task's own argument, prefer
  fewer, load-bearing checks over a more complete but still-passive list.

## Not required before this can be picked up

No timing hold — [[TASK-0352]]'s own hold was already released before this
was filed, and this task carries no new one.
