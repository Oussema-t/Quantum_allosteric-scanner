# TASK-0321 — The hypothesis register is write-mostly: a decision brief for Architect/Planner

- Status: Done
- Owner: **Architect/Planner** (source-of-truth control is that role's boundary, not the Reviewer's)
- Priority: High — it produced a wrong claim in a collaborator-facing document this week
- Filed: 2026-09-03 by Reviewer thread (id via `claim.py reserve-next`)
- Related: [[TASK-0320]], [[HYP-P9]], [[TASK-0310]], [[TASK-0307]], [[TASK-0319]]

## Why this is filed

Raised by the repo owner as *"I have a feeling we are under-using our hypotheses
mechanics — the moment any agent is writing such a brief, it should have our own
Library of Alexandria easily accessible, rather than pulling it from memory or
inferring."*

It is not a feeling. It is measurable, and the triggering incident is mine:
[[TASK-0320]]'s collaborator brief stated that complex hopping / a chiral walk
was an **open route**. [[HYP-P9]] had recorded it **FAIL on 2026-07-23**, and
`src/allostery/chiral.py` implements exactly that construction. I wrote the claim
by reasoning forward from [[TASK-0312]] instead of reading the hypothesis that
owns the question — in a file the same session had already opened and edited.
The repo owner caught it, not the register and not me.

**Do not read this as a request to fix my mistake.** One error is an anecdote.
The measurements below are the reason it is filed.

## Measurements, taken 2026-09-03

Scope: `.claude/hypotheses/*.md` (4 files: `physics`, `ceiling`,
`search_complexity`, `reference_register`) against all 339 task files and the 12
documents in `__WORK_IN_PROGRESS__/documentation/`.

### 1. Two-thirds of hypotheses have never been given a verdict

| | count |
|---|---|
| hypotheses defined | **21** |
| with a **dated Status** line | **7** |
| with no dated status at all | **14** |

The two most-referenced hypotheses in the whole register are among the unjudged:

| hypothesis | tasks citing it | dated status |
|---|---|---|
| **HYP-P1** | **16** | **none** |
| **HYP-P13** | **8** | **none** |
| HYP-P8 | 4 | none |
| HYP-P9 | 4 | 2026-09-03 |
| HYP-P14 | 5 | 2026-09-01 |

### 2. The register is almost never read back

| | count | share |
|---|---|---|
| task files total | 339 | |
| **citing any hypothesis** | **29** | **9%** |
| never citing one | 310 | 91% |
| outward-facing documents | 12 | |
| **citing any hypothesis** | **2** | `REFERENCES.md`, `CTQW_CONTRIBUTION_BRIEF.html` |

Neither of those two is the current submission draft.

### 3. Staleness is *not* the problem

Only **2 of 21** have evidence newer than their recorded status (`HYP-P12`,
`HYP-P14`), both by a single day. My first framing of this — "the register is
stale" — was wrong, and the measurement corrected it.

## Diagnosis: two distinct failure modes, needing different fixes

**A · Not consulted.** [[HYP-P9]] had a correct, current, unambiguous `FAIL`.
A brief still claimed the opposite. The 9% citation rate says this is systemic
rather than one careless thread. *Writing more or better hypotheses does not fix
this — nobody is reading the ones that exist.*

**B · Not maintained.** 14 of 21 carry no verdict, so for two-thirds of the
register even a diligent reader gets nothing back. A reader who consults
`HYP-P1` — the most-cited hypothesis here — learns only what someone once
proposed, not whether it survived.

These pull in opposite directions on effort: (A) argues for making the register
*load-bearing at the point of writing*; (B) argues for *back-filling verdicts*
before it is worth consulting. Sequencing them is an Architect decision.

## Options — sketched, not recommended

Deliberately not costed or ranked; that is the Architect's call.

1. **Citation obligation.** Any claim of the form "X is open / closed / untested"
   in an outward-facing document must cite a hypothesis id and its status date.
   Cheap to state, unenforced unless checked.
2. **A checker**, in the shape of `.ai/tools/doc_parity.py` ([[TASK-0319]]'s
   precedent): flag hypothesis ids whose newest citing task post-dates their last
   status line, and flag documents making open/closed claims with no id. Catches
   B mechanically; catches A only if writers already cite.
3. **Verdict back-fill sprint.** Give all 14 unjudged hypotheses a dated status
   (including `SUPERSEDED` / `NEVER TESTED` / `ABANDONED`, which are verdicts).
   Makes consultation worthwhile; does nothing to make it happen.
4. **Fold the register into the operation protocol** — a mandatory read step
   before any brief or task that claims a route is open. Addresses A directly and
   is the only option that does; also the most intrusive.
5. **Do nothing structural**, and treat [[HYP-P9]]'s new explicit
   *"do not re-propose complex hopping as an open route"* line as the pattern:
   write the warning into the hypothesis where the next agent will hit it. Cheapest;
   relies on someone having been burned first, every time.

## Open questions for the Architect

- Is the hypothesis register meant to be **authoritative** (a claim contradicting
  it is a defect) or **advisory** (a lab notebook)? Behaviour differs sharply,
  and the answer is currently implicit.
- Should a hypothesis with no verdict be **citable at all** in an outward-facing
  document, or does citing it imply a status it does not have?
- Where does the boundary sit between `.claude/hypotheses/` and `.ai/memory/`?
  Both hold durable claims; only one is consulted at 9%.
- Is 21 hypotheses across 4 files the right granularity, or is the split by file
  itself part of why they go unread?

## Constraints

- **Do not close this by rewriting the hypotheses.** The content is largely
  sound; [[HYP-P9]] was *correct* and still failed to prevent the error.
- Any checker must ship with a test that proves it **fails** on a seeded
  violation — [[TASK-0319]]'s standing finding.
- Measurements above are reproducible; the queries are recorded in this task's
  own filing thread and can be re-run before acting.

## Note

The sharpest version of the problem: this register has unusually good discipline
about *recording* what it learns and unusually poor discipline about *reading it
back*. [[TASK-0307]] found the same shape in the submission documents — 13 Done
tasks categorically absent from both shipped drafts. That is twice now that
knowledge was captured correctly and then not consulted where it mattered. The
common factor is not the artefact; it is that nothing in the workflow forces a
read.

## Done

**2026-09-03, Architect/Planner.** Discussed directly with the repo owner
rather than decided unilaterally. Answers to the four open questions, and the
decision they drive:

- **Authoritative vs advisory** — split by verdict, not by blanket policy. A
  claim contradicting a *dated* verdict is a defect (what actually happened
  in [[TASK-0320]]). A hypothesis with no verdict can't be held to a standard
  the register itself hasn't reached — advisory until it has one.
- **Citable with no verdict?** — yes, but must say so explicitly
  ("no verdict recorded"), not cite bare. Reuses this project's own existing
  three-way discipline for external citations
  (`.ai/reference/PAPER_CITATION_PROTOCOL.md`'s direct-claim / re-test /
  inherited-unverified split) rather than inventing a new convention.
- **`.claude/hypotheses/` vs `.ai/memory/` boundary** — checked directly:
  not actually confused. `.ai/memory/shared/` (decisions/glossary/patterns/
  pitfalls) is process and pattern knowledge; hypotheses are specifically
  scientific physics conjectures. The 9% citation figure is not a boundary
  problem.
- **21-across-4-files granularity** — not the discoverability problem either;
  none of the 4 files has a status table at its own top. Fixed by
  [[TASK-0322]]'s index, not by reorganizing files.

**A genuine third failure mode surfaced in discussion, upstream of both A and
B named above**: some of the 14 unjudged hypotheses may not be untested at
all — a Done task may have already tested and decided the underlying claim
and simply never written that verdict back to the hypothesis it was deciding.
Same shape as this task's own citation of [[TASK-0307]], recurring in a
second artifact. This is a **linking gap**, cheaper to close than fresh
research, and it must be checked before any backfill is commissioned blind.

**Split into three children, sequenced rather than run blind:**

| | Pathway | Task | Depends on |
|---|---|---|---|
| A | Not consulted — mechanical gate (index + checker, extends beyond stale-citation detection to flag bare uncited open/closed claims, the class that would have caught the real incident) | [[TASK-0322]] | [[TASK-0319]]'s precedent only — independent, starts now |
| C | The write-back gap surfaced above — audit Done tasks for already-tested-but-unlinked verdicts before commissioning fresh work | [[TASK-0323]] | [[TASK-0321]] (this task's own 14-item list) — independent of A, starts now |
| B | Verdict backfill | [[TASK-0324]] | **[[TASK-0323]]**, hard-blocked — scoped to whatever that task reports as genuinely never tested, not the full 14 blind |

Not closed by rewriting any hypothesis (this task's own Constraint, honored).
No hypothesis content changed here — only the mechanics of how the register
gets read, written back to, and enforced.
