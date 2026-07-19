# TASK-0132 GNM transfer-entropy classical baseline

## Context

- ID: TASK-0132
- Title: implement directional transfer entropy over GNM contact
  topology (no MD, no quantum) as a classical baseline that does the
  same job as [[TASK-0122]]'s slow-mode-filtered co-participation —
  published, and never in this project's competence map.
- Status: Done
- Owner: Implementer
- Claimed By: Implementer C (this thread)
- Claimed At: 2026-07-19
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

- [x] Verify both cited papers exist and describe the claimed method —
      do not implement against an unverified citation.
- [x] Implement GNM transfer entropy, reusing existing shared GNM
      primitives where applicable.
- [x] Score against all 3 mandatory targets' real labels, check against
      the proximity floor.
- [x] Report the result — comparison against `H_new`/CTQW's own numbers,
      whichever way it comes out.

## Dependency

- [[TASK-0094]] (Done) — the proximity floor this task's score is
  checked against.
- Independent of [[TASK-0122]] — parallel, not sequential, work.

## Open Questions

- Exact transfer-entropy formulation (which of possibly several variants
  in the cited literature) — this task's own first step to determine
  once the citations are verified, not pre-decided here.
  **Resolved 2026-07-19**: the linear-Gaussian transfer entropy /
  Granger-causality closed form (Barnett, Barrett & Seth, *PRL*
  103:238701, 2009), `T_{Y->X} = 0.5*ln(Sigma_X/Sigma_{X|Y})`, applied
  directly over the GNM's own time-lagged covariance function. Exact for
  GNM fluctuations (multivariate Gaussian by construction) — no
  histogram-based Shannon-entropy estimation needed, unlike the cited
  MD-trajectory papers' own approach. See `transfer_entropy.py`'s module
  docstring for the full derivation and citation trail.

## Done

**2026-07-19, Implementer C (this thread).**

**Citations verified, one corrected.** Both papers checked directly
against PubMed before implementing (not assumed from this task's own
one-line Context summary):
- Hacisuleyman & Erman, *Proteins* 85(6):1056-1064 (2017), PMID
  28241380 — confirmed real, matches the claimed method (transfer
  entropy over GNM/"dGNM" harmonic contact topology, directional
  causal-flow signal, no MD trajectory required).
- **This task's own Context citation was wrong.** PMID 35644497 ("Subsets
  of Slow Dynamic Modes Reveal Global Information Sources as Allosteric
  Sites," *J Mol Biol* 434(17), 2022) is real and matches the claimed
  method, but its authors are **Altintel, Acar, Erman, Haliloglu** — not
  "Kaynak & Bahar" as filed. Flagged here rather than silently rewritten
  in the Context section above (historical record of what was filed).
- Minor secondary correction: the shared GNM primitives this task cites
  (`_kirchhoff_eigh`/`_normalized_dcc`) live in `potentials.py`, not
  `analysis.py` as the Intent Contract states.

**Formulation.** See Open Questions above — the Barnett-Barrett-Seth
linear-Gaussian closed form applied to the GNM's own lagged covariance,
`C(tau) = U @ diag(exp(-w*tau)/w) @ U.T` (Kirchhoff eigendecomposition,
zero mode excluded), which reduces exactly to `potentials._normalized_dcc`'s
own static covariance at `tau=0` — confirmed by test, not assumed.

**A genuine subtlety worked out and empirically verified, not just
derived on paper**: for the pure (reversible, detailed-balance) GNM
Langevin process, the lagged cross-covariance `C_ij(tau)` is provably
*symmetric* for any `tau` (sum of symmetric rank-1 `u_k u_k^T` terms) —
unlike the MD-trajectory papers' empirically-estimated correlations,
which pick up genuine asymmetry from nonlinear/non-Markovian effects the
linear GNM does not have. Transfer entropy stays directional anyway,
because `T_{i->j}` and `T_{j->i}` use different self-prediction
baselines (each residue's own, generally different, marginal relaxation
properties) — confirmed with a dedicated test
(`test_asymmetric_despite_symmetric_cross_covariance`) before trusting
it on real data.

**Implementation.** New `src/allostery/transfer_entropy.py`:
`_gnm_lagged_covariance`, `gnm_relaxation_time` (lag `tau* = 1/gap`,
matching this project's own spectral-gap clock convention from
TASK-0109/0119/0130 — the cited papers don't prescribe a universal lag,
this is this task's own Implementer's-call choice, stated not hidden),
`pairwise_transfer_entropy` (per-pair Schur-complement residual
variance over the 3-variable joint Gaussian), `transfer_entropy_source_score`
(per-residue mean outgoing TE — the ranking used for scoring).

**Validation.** `tests/test_transfer_entropy.py`, 12 tests, all passing:
tau=0 matches `_normalized_dcc`; lagged covariance symmetric at any tau;
covariance decays monotonically with lag; TE matrix non-negative
(guaranteed by the closed form, not just empirically true); the
symmetric-cross-covariance/asymmetric-TE subtlety confirmed directly;
and the task's own required falsification gate — a custom synthetic
two-clique-plus-bridge network (not the existing dumbbell construction,
which carries an unrelated "well" potential feature this test doesn't
need) confirms a more tightly-coupled clique scores as a stronger net
information source, before trusting the method on real targets.

**Real-target result — reported whichever way it came out, per this
task's own Intent Contract.** New `scripts/transfer_entropy_baseline.py`
(reuses `run_challenge._load_apo_holo`, the standard floor/label/
diagnosis pipeline). All 3 mandatory targets, compared against
`COMPETENCE_MAP.md`'s current `H_new`/CTQW actual-AUC numbers
(TASK-0130's closed-form convention):

| Target | Floor | Transfer-entropy AUC | `H_new`/CTQW actual AUC | TE diagnosis |
|---|---|---|---|---|
| KRAS_G12C | 0.4818 | 0.4485 | 0.5901 | BEATS_CHANCE_NOT_FLOOR |
| BCR_ABL1 | 0.5817 | 0.3497 | 0.5266 | BEATS_CHANCE_NOT_FLOOR |
| CARDIAC_MYOSIN | 0.7921 | 0.5335 | 0.7272 | NO_SIGNAL_IN_APO |

**Mixed result — neither of this task's own two anticipated outcomes
holds cleanly.** Transfer entropy fails to clear the proximity floor on
any of the 3 targets (0/3), and scores lower than `H_new`/CTQW's own
current numbers on all 3, decisively so on 2 (KRAS_G12C, BCR_ABL1).
This is neither "a classical method already does the job" (it does not
beat `H_new`, nor clear the floor) nor "the task itself is uniformly
hard regardless of method" (this specific classical baseline underperforms
this project's own operator, which itself only clears its floor
decisively on 1/3 targets per TASK-0130/0131). Full comparison table and
narrative: `RESULTS.md`, "GNM transfer-entropy classical baseline"
section, open-questions index row 18. Cross-reference: TASK-0122's mode
co-participation (an independent classical-ish comparison) clears its
floor on 1/3 targets (BCR_ABL1) — transfer entropy clears 0/3, a
somewhat weaker classical baseline on this specific comparison.

**Runtime**: 0.7s/3.5s/16.9s (KRAS_G12C/BCR_ABL1/CARDIAC_MYOSIN,
N=169/451/950) — the naive `O(N^2)` Python-loop implementation is fast
enough at these sizes, no vectorization needed.

**Not done / explicitly out of scope** (per this task's own Intent
Contract): no change to the submission operator selection (Tier-2-gated,
[[TASK-0100]]); TASK-0122's own observable untouched, this is a fully
independent comparison point. Full regression suite re-run after this
change: 755 passed, 6 deselected, 2 xfailed — no regressions.
