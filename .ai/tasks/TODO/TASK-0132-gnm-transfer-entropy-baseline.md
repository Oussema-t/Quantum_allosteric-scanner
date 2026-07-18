# TASK-0132 GNM transfer-entropy classical baseline

## Context

- ID: TASK-0132
- Title: implement directional transfer entropy over GNM contact
  topology (no MD, no quantum) as a classical baseline that does the
  same job as [[TASK-0122]]'s slow-mode-filtered co-participation —
  published, and never in this project's competence map.
- Status: TODO
- Owner: Implementer
- Claimed By: —
- Claimed At: —
- Source: `.ai/reviews/REVIEW-panel-2026-07-17.md` §4 P1-6, §6.3 action
  #5. Citations given, **not independently verified by this Architect/
  Planner thread** — confirm both exist and say what the review claims
  before implementing against them, as this task's own first step:
  - Hacisuleyman & Erman, PMID 28241380 — directional causal flow from
    contact topology alone.
  - Kaynak & Bahar, J Mol Biol 2022, PMID 35644497 — slow-mode-subset
    transfer entropy, reported to recover allosteric sites on a
    20-protein benchmark set.
- Priority: **P1.** Per the review: "the published classical method that
  does [slow-mode filtering] already. If you can't beat it, you don't
  have a result."

## Intent Contract

- Outcome: a working implementation of GNM-based transfer entropy
  (directional, causal-flow-style signal from contact topology alone —
  confirm the exact formulation against the verified source papers, not
  guessed from the review's one-line description), scored against all 3
  mandatory targets' real pocket labels, checked against the proximity
  floor ([[TASK-0094]]) the same as every other observable in this
  project's register.
- Why this matters beyond "one more baseline": two possible outcomes,
  both informative — (a) if this classical, published, seconds-on-a-
  laptop method beats or matches this project's own operator family,
  that's the honest, better-supported result to report, and directly
  strengthens the "coherence adds nothing" narrative already established
  (TASK-0099/0105/0068) by showing a *classical* method already does the
  job; (b) if it also lands at or near the floor on these same targets,
  that is a *stronger* negative result than anything currently in the
  repo — it would mean the task itself (not just this project's specific
  operator choices) is hard on these 3 targets, not just this pipeline.
- In Scope:
  - Verify the two cited papers exist and describe what the review
    claims — this task's own first step, not assumed.
  - Implement the transfer-entropy computation over GNM contact
    topology, reusing this project's existing GNM/Kirchhoff machinery
    (`analysis._kirchhoff_eigh`/`_normalized_dcc`, per TASK-0066's
    shared-primitive precedent) rather than re-deriving it from scratch.
  - Score against all 3 mandatory targets' real labels, checked against
    TASK-0094's proximity floor.
  - Report result whichever way it comes out — per this project's own
    "an honest NO is a publishable result" convention.
- Out Of Scope:
  - Reselecting the submission operator based on this result alone —
    Tier-2-gated per [[TASK-0100]], same as every other candidate.
  - The slow-mode-filtered co-participation observable itself —
    [[TASK-0122]]'s own scope; this task is an independent classical
    comparison point, not a dependency of it.
- Constraints And Invariants: report which specific transfer-entropy
  formulation was implemented (there are several in the literature) and
  why, given the review's citation is a one-line summary, not a full
  method spec.
- Planned Validation: real-target scoring against TASK-0094's floor, same
  discipline as every other observable in this register; a synthetic
  sanity check (e.g. the dumbbell construction, [[TASK-0103]]) if the
  method's own directionality claim needs a falsification gate before
  trusting it on real data.

## In Progress

None

## TODO

- [ ] Verify both cited papers exist and describe the claimed method —
      do not implement against an unverified citation.
- [ ] Implement GNM transfer entropy, reusing existing shared GNM
      primitives where applicable.
- [ ] Score against all 3 mandatory targets' real labels, check against
      the proximity floor.
- [ ] Report the result — comparison against `H_new`/CTQW's own numbers,
      whichever way it comes out.

## Dependency

- [[TASK-0094]] (Done) — the proximity floor this task's score is
  checked against.
- Independent of [[TASK-0122]] — parallel, not sequential, work.

## Open Questions

- Exact transfer-entropy formulation (which of possibly several variants
  in the cited literature) — this task's own first step to determine
  once the citations are verified, not pre-decided here.

## Done

(not yet)
