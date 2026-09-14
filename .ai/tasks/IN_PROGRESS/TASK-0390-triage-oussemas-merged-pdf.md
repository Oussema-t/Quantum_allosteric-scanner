# TASK-0390 — Triage Oussema's merged PDF: salvage Appendix B, do not ship the body

- Status: In Progress
- Owner: Implementer to apply; Team Lead to decide the page-budget items
- Priority: High — Appendix B contains our best independent corroboration, and the body it is attached to would undo a week of fixes
- Filed: 2026-09-13 by Reviewer thread
- Source: `PHASE1_SUBMISSION_MERGED.pdf`, provided by Oussema 2026-09-13
- Related: [[TASK-0367]], [[TASK-0385]], [[TASK-0387]], [[TASK-0388]]

## Verdict in one line

**Appendix B is genuinely valuable and partly better than what we have. The
sections 1–7 it is bolted onto are a stale snapshot that reverts at least six
fixes, including one we treated as a blocker.** Take the appendix, rebuild it
onto HEAD, discard the merged body.

---

## A. DO NOT SHIP THE MERGED BODY — verified regressions against HEAD

Each checked directly against `PHASE1_SUBMISSION_V4.md` at HEAD:

| # | merged PDF | HEAD | severity |
|---|---|---|---|
| A1 | **`SUBMISSION_BUILD_APPENDIX_START_7f3a9c` printed on page 7** | retired entirely for the LaTeX route by [[TASK-0367]] | **blocker** — this is item 32 of the 2026-09-11 review, back and now *visible*, not just in the text layer |
| A2 | Section 7's member table + repo line sit on **page 7** → body is 7 pages | body 6/6 | **blocker** — the exact violation [[TASK-0367]] fixed; Guidelines §5 permits assessment on the first 6 pages only, which cuts Team Capability (10%) |
| A3 | "the register needs **169–704 qubits**" | **170–704** | regression (2026-09-11 review item 9) |
| A4 | "**Two survive** our own screening … and coupled conformational search at that same 50–80-residue scale" | "**One survives** … Coupled conformational search, the other candidate, **we closed ourselves**" | regression — reintroduces review item F8, a contradiction against our own register |
| A5 | "Against a real IBM device calibration snapshot, every mandated target verdicts `FAULT_TOLERANT_ONLY`" | "**We built the circuit and transpiled it** against a real IBM device calibration snapshot…" | regression — Challenge §4.1 *mandates* building a circuit; HEAD satisfies it, the merged PDF drops the clause and fails it |
| A6 | noise-resilience sentence absent | "we **pre-registered a noise-robustness hypothesis** … and **falsified it**" | regression — §4.2 requirement, satisfied at HEAD, dropped here |
| A7 | reframe absent | "**The likeliest reason these nulls are nulls is the input, not the walk.**" | regression — survived four rounds of cutting precisely because it is the honest core of §2 |
| A8 | cardiac row has no footnote | footnote names Table 1's `5TBY → 6C1H` and both defects | regression — undoes [[TASK-0369]] item 4, closed 2026-09-13 |

**A1 and A2 alone are disqualifying.** Do not merge this body under time pressure
"to save the appendix" — rebuild the appendix onto HEAD instead.

### One thing the merged body gets *right* that HEAD does not

Its structures table says **"All three deviations trace to that clarification"**.
That is the **correct count** — `4LDJ`, `8QYP`, `8QYR` — and it is exactly what
[[TASK-0387]] item 2 identifies as the right number against HEAD's "Two rows
above are deviations, one a retention" and doc 03's "Four". **Adopt his wording
when fixing 0387 item 2.** Its BCR-ABL1 row prose ("Substituting it would have
removed the evidence") is also sharper than ours and is a free swap.

It still carries "we followed it in each case" ([[TASK-0387]] item 1), so the
table is a starting point, not a drop-in.

---

## B. INCLUDE — net-new, defensible, and it strengthens our weakest flank

Ranked. Our headline problem is that a reviewer reads "nothing beats chance" as a
failed project; every item here converts that into a *measured* result on an
independent pipeline.

**B1. The pre-registered `H_new` cell is an honest near-negative on all four
targets** — KRAS 0.479 p=0.57, BCR 0.411 p=0.84, myosin 0.601 p=0.12, HIV-1 RT
0.665 p=0.060. **Highest-value item in the whole appendix.** It is the honest
counterpart to the best-of-221 table sitting directly above it, and it is a
second, independent pipeline reaching our own §1 conclusion. Ship it adjacent to
any selection-ceiling number, never apart from it.

**B2. Selection ceilings versus the single fixed cell.** Best-of-221 per protein
reaches P@5≥0.8 on 200/115, 147/77, 82/49, 47/20 (proteins/families) at MIN_HOP
1/2/3/4; the single fixed cell that survives removing the per-protein choice is
**69/20**. His own line — *"the gap between them is the multiplicity this
proposal corrects for"* — is our §1 argument, quantified on a different cohort
with a different detector. Our body currently makes this point with 137 families
vs a 99.8 null; this is the same finding measured independently.

**B3. The protein-identity floor reproduces on his cohort at pooled AUC 0.771,
"above every method tested."** Our §5 reports **0.65** on our cohort and says *"we
have found no report of the check."* An independent reproduction at a *higher*
value, on a different pipeline, materially strengthens what is arguably our best
methodological contribution. **This is the single most quotable corroboration in
the appendix.**

**B4. `neg_dE`, the strongest single score in the sweep, equals
`sqrt(Σ_j W_ij²)` to machine precision — a classical local statistic, so it
cannot carry interference.** A proof-style result, not a measurement: the best
score in a 221-cell quantum sweep is provably classical. Directly supports §2's
"the phase-free construction is exhausted." Cheap to state, hard to argue with.

**B5. Blind leave-one-family-out regression over all 221 scores reaches 0.7216 on
the 91 distal proteins against a reversed-distance floor of 0.7219.** The walk
does not beat distance, blind, on his cohort either. Independent replication of
our central negative.

---

## C. MOVE — valuable, but not worth 6-page-body space

Destination is `SUBMISSION_PACKAGE/Solution_Outputs.pdf` (not page-limited) or
the repo, per [[TASK-0384]]'s logic that output 1's methodology must reach a
scorer:

| item | where | why not the body |
|---|---|---|
| B.1 construction detail — `H_new` formula, 13 operators × 17 scores = 221, NET_CUTOFF 10 Å / SITE_CUTOFF 4.5 Å, the average-mixing matrix identity | `Solution_Outputs.pdf` §3 | §2 already states the construction; this is the methodological report's job |
| B.2 full best/worst table incl. HIV-1 RT | `Solution_Outputs.pdf` | four rows × two cells is a lot of page for one argument; B1/B2 above carry it |
| B.4 the Ridge configuration recommender — 9 features → 884 configurations → top-k softmax, LOFO over 630/399, 0.724 at k=6 over 43 families | `Solution_Outputs.pdf` | §6 already describes the **two random forests**; the recommender is a *different* model and currently reads as contradicting §6 rather than extending it. **Reconcile explicitly**: his own text says the two forests are "the diagnostic; the deliverable is the single recommender" — that sentence has to appear, or the two documents disagree |
| Page-9 connectivity heat-maps | with output 1 | good figure, belongs with the matrix deliverable |

---

## D. EXCLUDE, or fix before any use

**D1. "Reported as *replication* of sections 1–7's bartosz track" — the word is
wrong and it is a claim we cannot support.** Different detector (PASSer vs
fpocket), different cohort (630/399 vs 108–162/76–129), different seeding,
different candidate funnel. It is **corroboration** on B3/B5 and a
**contradiction** on coherence. Use "independent second pipeline", never
"replication".

**D2. The coherence contradiction is disclosed nowhere in the merged PDF — and
his own branch README flags it unprompted.** `seeded_classical/README.md` says:
*"This CONTRADICTS the conclusion drawn on the bartosz branch… must be reconciled
before submission."* On his cohort, coherent CTQW beats its exact classical twin
at **p = 2.3e-12** (we independently recomputed from his raw shards: 0.5999 vs
0.5124, Wilcoxon p = 2.25e-12, matching his number). Our §2 reports a
well-powered coherence **null**.

**This is the biggest content risk in the merged document.** Shipping an appendix
badged "replication" while omitting the one place the two tracks disagree — on
the central question of the whole proposal — is exactly the failure mode §1
accuses the field of. Either disclose it in one sentence, or do not attach his
track to ours at all. Reviewer's recommendation: **disclose it.** A submission
that names its own internal contradiction is worth more than one that hides it,
and this document has already spent six pages earning that posture.

**D3. HIV-1 RT best cell, AUC 0.963 / P@5 0.8.** Correctly captioned as
best-of-221 selection, but it is a near-perfect number in a document whose
headline is "nothing beats chance". **It will be quoted out of context.** Ship
only inside the same visual block as B1's near-negative, or not at all.

**D4. Page-9 caption: "Cardiac myosin's top-5 depends on a fpocket seeding that
does not reproduce headless."** A reproducibility defect disclosed in a figure
caption, in a submission whose thesis is reproducibility. **Fix it or state it in
the limitations section** — burying it in a caption is the worst of the three
options and invites the reviewer to ask what else is caption-only.

**D5. "Appendix B" with no Appendix A**, while our own appendix is
`Appendix — References`. The Team Profile's "Appendix B" citation was removed in
`5562517` as pointing at nothing. Renumber coherently before any of this lands.

**D6. ASCII typography throughout the appendix** — `->`, `A` for Å, `|v_k(s)|^2`,
`p_avg(s->a)`, `x` for ×. The body uses proper math. One document, two
conventions, and the glyph map in `submission_build_latex.py` already handles Å,
τ, ⟨, ⟩. Cheap fix, visible to a scorer on the first flip.

---

## Recommended order

1. Reply to Oussema: the appendix is wanted, the body must be HEAD — ask him to
   rebase rather than merge. **Ask him directly about D2**, since the
   reconciliation is his own branch's open question.
2. Lift **B1–B5** into HEAD (B3 and B4 are near-free; B1/B2 need the page trade
   already contested by [[TASK-0385]]).
3. Move **C** into `Solution_Outputs.md`.
4. Fix **D1, D3, D4, D5, D6** before anything from the appendix ships.
5. Adopt his "All three deviations" wording into [[TASK-0387]] item 2.

## Done when

Appendix content is on HEAD or explicitly declined item by item; nothing from the
merged body is merged; the rebuilt PDF reports body 6/6 PASS and **zero**
`SUBMISSION_BUILD` occurrences.
