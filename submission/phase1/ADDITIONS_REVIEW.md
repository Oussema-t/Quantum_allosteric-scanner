# Proposed additions to the Phase 1 Concept Proposal

**Team AuraQu, `allosteric` branch, 2026-09-12.** Nothing here is in the submission yet.
Each block is staged with `status: PENDING`; the merge tool writes a new file and never edits
the proposal in place. The base is `PHASE1_SUBMISSION_V4.md`, byte-identical to `bartosz@9f1d521`.

Consistency was checked mechanically against the 64 numeric claims already in the proposal.
Where a number differs from one already there, it is a second measurement on a second cohort
and says so in the same sentence.

| block | to | lines |
|---|---|---|
| ADD-1 | S5 | 2 |
| ADD-2 | S2 | 4 |
| ADD-3 | S2 | 3 |
| ADD-4 | App B | 1 page |
| ADD-5 | S7 | 2 |
| ADD-6 | S2 | 16 |
| ADD-7 | S1 / App B | 10 |


## ADD-1 — Protein-identity floor, second cohort

*To:* 5. Validation Plan. *Cost:* 2 lines. *Status:* PENDING.

*Inserted after:* "...re without this floor is not interpretable, and we have found no report of the check."

Re-measured on the second cohort described in Appendix B, the same constant-per-protein score reaches **AUC 0.771** across 630 proteins — above every method either track has tested, and a wider margin than the 0.65 above.

## ADD-2 — Independent replication of the central null

*To:* 2. Technical Approach. *Cost:* 4 lines. *Status:* PENDING.

*Inserted after:* "...because McNemar is a paired test over the same families."

A second pipeline, built independently on a different detector and a different candidate filter, reaches the same verdict on a larger cohort: across 630 proteins in 399 families, the seeded walk loses to closeness centrality at every distal filter setting (family-weighted AUC 0.585 / 0.542 / 0.544 / 0.543 against 0.601 / 0.569 / 0.575 / 0.580; Wilcoxon p = 0.001, 0.003, 0.044, 0.258). The two cohorts are not pooled — they differ in detector and in family convention — so this is replication, not an enlarged n. Appendix B reports it in full.

## ADD-3 — A blind model over all 221 observables reproduces distance

*To:* 2. Technical Approach. *Cost:* 3 lines. *Status:* PENDING.

*Inserted after:* "...What it adds is simply not coherence"

The same conclusion survives combining the observables rather than choosing among them. A logistic regression over all 221 per-residue score vectors, true leave-one-family-out, reaches family-weighted AUC **0.7216** on the distal subset — against 0.5405 for the best single cell selected on the same data, and **0.7219** for the trivial reversed-distance floor. The difference from the floor is -0.0003 (Wilcoxon p = 0.90): optimally combined, the quantum observables reproduce distance and nothing further.

## ADD-4 — Appendix B, the full second-cohort report

*To:* Appendix (new B, after references). *Cost:* ~1 page. *Status:* PENDING.

(The full appendix drafted earlier — pipeline description, the four-MIN_HOP table, the LOFO result,
the two-source interference run, the family-provenance audit, the notebook run, and our retractions.
Held until ADD-1..3 are settled, since it must not repeat whatever goes into the body.)

## ADD-5 — Our retractions in the §7 ledger

*To:* 7. Team Capability. *Cost:* 2 lines. *Status:* PENDING.

*Inserted after:* "...It found five of our own errors in seven days, including our headline result."

The same register operating on the second branch caught three more: an AUC read backwards in a distal proximity-floor claim, a classical-comparison arm that differed in operator as well as in coherence, and a blind positive filed as a to-do rather than reported. All three are corrected in the public history.

## ADD-6 — The thirteen operators and seventeen scores, named

*To:* 2. Technical Approach (Paradigm). *Cost:* ~16 lines. *Status:* PENDING.

*Inserted after:* "...-body objects and conformational ensembles rather than single-structure optimisation."

**What was swept.** Residues are nodes at their C-alpha coordinates, edges within a 10 A cutoff; the walk is `U(t) = exp(-iHt)` seeded at the active site, reported in the converged time-average `p_avg(s->a) = sum_k |v_k(s)|^2 |v_k(a)|^2` — a sum of squares, which is why the converged propagator is phase-free. Every operator is real symmetric, hence Hermitian.

**Thirteen operators** = four edge weightings x three normalisations, plus the challenge-specified `H_new`. The weightings are binary (`d < 10 A`), exponential `exp(-0.3 d)`, Gaussian `exp(-d^2/72)` and harmonic `1/(d + 0.5)^2`; each is used under three normalisations — the adjacency `W` itself, the combinatorial Laplacian `L = D - W`, and the symmetric normalised `L_sym = I - D^{-1/2} W D^{-1/2}` — giving twelve, written `binary/adj` through `harm/sym`.

`H_new` is the thirteenth: `L_sym` of the exponential graph plus a diagonal site potential `0.08 V_B + 0.16 V_T + 0.08 V_R + 0.04 V_C + 0.04 V_M`, each term z-scored and signed so penalties raise the potential and rewards lower it — `V_B` B-factor disorder, `V_T` chain termini and solvent exposure, `V_R` rigidity (degree, clustering, inverse GNM fluctuation), `V_C` GNM covariance with the core, `V_M` participation in the ten slowest GNM modes. Weights pre-registered in the notebook, not fitted here.

**Seventeen scores**, in five families:

| family | scores | what it ranks a residue by |
|---|---|---|
| occupation | `p_avg`, `p_peak`, `R` | converged transfer, its maximum over the time grid, and their ratio |
| proximity-corrected | `residLOG`, `residRAW`, `residLOG_dX`, `residRAW_dX`, `pavg_over_dX` | transfer with distance and degree regressed out, raw or log, optionally focused by walker spread |
| resolvent | `green_zero_0.01`, `green_zero_0.05`, `green_lmax_0.05` | `|<a|(E + i eta - H)^{-1}|s>|^2` at the band edge and band top — a commute-time / communicability analogue |
| dispersion | `neg_dD_mean`, `neg_ED_final`, `QMI` | spread of the walker's distance distribution, its final energy dispersion, and a mutual-information proxy |
| energy-uncertainty | `neg_dE`, `residLOG_dE`, `pavg_over_dE` | the seed state's spectral variance `sqrt(<E^2> - <E>^2)`, alone or combining with the above |

Thirteen times seventeen is the 221 cells per protein quoted above. One qualification belongs with this table rather than buried: `neg_dE`, the strongest single score, is time-independent by construction, and equals `sqrt(sum_j W_ij^2)` to machine precision — a classical local statistic wearing a quantum name. It ranks well and it cannot carry interference, which is one measured reason the coherent and decoherent arms agree.

## ADD-7 — KRAS G12C on 4LDJ: the seeding stage decides the target

*To:* 1. Problem Framing (beside the hit-list table) or Appendix B. *Cost:* ~10 lines. *Status:* PENDING.

**The stage that decided KRAS was not the walk.** Re-running the mandated target end to end on `4LDJ` — the genuine G12C apo structure (residue 12 = CYS; GDP and Mg only; we verified that six apo G12C depositions exist and that Table 1's `4OBE` is wild-type at residue 12 while the organisers' suggested `8S8C` is drug-bound) — the result is decided before the quantum walk runs.

Candidate pockets come from fpocket and are cut to a top-K before seeding. Under the narrower setting (fpocket ranking, top-5 by druggability) the true sotorasib pocket ranks **#6** and is discarded: 1 drug residue survives among 36 seeds, and P@5 is zero by construction — the pipeline cannot answer correctly whatever the operator does. Widening to a druggability-and-allostery consensus at top-10 seeds it: **8 drug residues among 44**, base rate 0.182. Same structure, same walk, same scoring; the selection stage alone moved the target from unanswerable to answerable.

Scored on that seed set, the best of 14 operators x 17 scores reaches AUC **0.809** (`H_new` with the resolvent score at the band top, P@5 0.6) and the worst reaches **0.184** (`H11_aniso`, proximity-corrected residual) — a spread of 0.63 AUC across cells that differ only in operator and score. Read correctly the worst is not a failure but a reversal: 1 - 0.184 = 0.816, within noise of the best. Under the pre-registered single cell fixed before scoring, the target returns an honest negative (label-permutation null, p > 0.05).

Consequence, and it is the same one section 6 reaches from the funnel ablation: on this target the classical selection stage, not the transport subroutine, determines whether the answer is reachable at all. A method reported only at its best cell, on a seed set chosen after the fact, would have reported 0.809 here.

