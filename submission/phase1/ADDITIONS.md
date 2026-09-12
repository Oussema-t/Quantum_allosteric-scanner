# Additions staging area

Nothing here reaches the PDF until its `status:` is `APPROVED`. The merge tool takes only
APPROVED blocks, inserts each at its `anchor:`, and writes a **new** file — the verbatim copy of
his V4 is never edited in place.

Block format:

    ### ADD-<n> — <short title>
    status: PENDING | APPROVED | REJECTED
    section: <which section of the proposal>
    anchor: <a literal phrase from V4; the block is inserted immediately after that paragraph>
    cost: <approximate lines>
    ---
    <the text to insert, in his register and markdown style>

Rules, from PROVENANCE.md:
- A number that differs from his is a **second measurement on a second cohort**, never a correction.
- Per-structure AUC, averaged. Never pooled across proteins.
- Any best-of-N number carries its search budget in the same sentence, or does not go in.
- Run `python3 submission/tools/check_addition.py submission/phase1/ADDITIONS.md` before merging.

---

## Candidates — awaiting your decision

### ADD-1 — Protein-identity floor, second cohort
status: REJECTED  # its 2 lines in section 5 pushed 3 sentences of section 7 past page 6; the 0.771 is already stated in Appendix B
section: 5. Validation Plan
anchor: A pooled figure without this floor is not interpretable, and we have found no report of the check.
cost: 2 lines
---
Re-measured on the second cohort described in Appendix B, the same constant-per-protein score reaches **AUC 0.771** across 630 proteins — above every method either track has tested, and a wider margin than the 0.65 above.

### ADD-2 — Independent replication of the central null
status: REJECTED  # moved into Appendix B to keep sections 6-7 inside the 6-page body
section: 2. Technical Approach
anchor: because McNemar is a paired test over the same families.
cost: 2 lines
---
A second pipeline, built independently on a different detector and a different candidate filter, reaches the same verdict on a larger cohort: across 630 proteins in 399 families the seeded walk loses to closeness centrality at every distal-filter setting (Wilcoxon p = 0.001, 0.003, 0.044, 0.258). The cohorts are not pooled — they differ in detector and family convention — so this is replication, not an enlarged n. Appendix B reports it in full.

### ADD-3 — A blind model over all 221 observables reproduces distance
status: REJECTED  # moved into Appendix B to keep sections 6-7 inside the 6-page body
section: 2. Technical Approach
anchor: What it adds is simply not coherence
cost: 3 lines
---
The same conclusion survives combining the observables rather than choosing among them. A logistic regression over all 221 per-residue score vectors, true leave-one-family-out, reaches family-weighted AUC **0.7216** on the distal subset — against 0.5405 for the best single cell selected on the same data, and **0.7219** for the trivial reversed-distance floor. The difference from the floor is -0.0003 (Wilcoxon p = 0.90): optimally combined, the quantum observables reproduce distance and nothing further.

### ADD-4 — Appendix B, the second-cohort report
status: APPROVED
section: Appendix B (after section 7, before the references)
anchor: uding our headline result. The full task history, including every retraction, is public at `github.com/Oussema-t/Quantum_allosteric-scanner` (branch `bartosz`).
cost: ~1 page
---

## Appendix B — The walk, the operators, and per-target connectivity

A second pipeline on the `allosteric` track (PASSer detection, 630 proteins in 399 families [4-6]), reported as **replication** of sections 1-7's `bartosz` track (fpocket), not pooled with it -- the two differ in detector and family convention. Every AUC is per structure, averaged.

**B.1 The construction.** Residues are C-alpha nodes, edges within 10 A; the walk is `U(t)=exp(-iHt)` seeded at the active site, read as the converged average `p_avg(s->a)=sum_k |v_k(s)|^2 |v_k(a)|^2` -- a sum of squares, hence phase-free. The **connectivity matrix** `C_ij` (the first required deliverable) is that average-mixing matrix, `(V o V)(V o V)^T`; it is symmetric, row-stochastic, and depends on the operator only. Thirteen operators (four weightings x three normalisations, plus `H_new = L_sym + diag(0.08 V_B + 0.16 V_T + 0.08 V_R + 0.04 V_C + 0.04 V_M)`) x seventeen scores (occupation, proximity-corrected, resolvent, dispersion, energy-uncertainty) give the 221 cells. `neg_dE`, the strongest single score, is time-independent and equals `sqrt(sum_j W_ij^2)` to machine precision -- a classical local statistic, so it cannot carry interference.

**B.2 Per-target connectivity (mandated targets).** Each target's 221 cells, best and worst by P@5 (the hit-list criterion; AUC saturates when distal positives are few). Connectivity matrices, top-5 x active-site sub-blocks and figures are in `results/connectivity/`.

*Table B.2a -- KRAS G12C, apo `4LDJ` [14] (true G12C; Table 1's `4OBE` is wild-type at residue 12), MIN_HOP 1.*

| cell | operator | score | AUC | P@5 |
|---|---|---|---|---|
| best | `H_new` | resolvent (band top) | 0.809 | 0.6 |
| worst | `H11_aniso` | residual RAW | 0.184 | 0.0 |
| pre-registered | `H_new` | residual | 0.479 | p=0.57 |

*Table B.2b -- BCR-ABL1, apo `1OPL` [1-3] (myristate pre-bound, so the site is already open), MIN_HOP 2.*

| cell | operator | score | AUC | P@5 |
|---|---|---|---|---|
| best | `H6_exp` | residual + focus | 0.796 | **1.0** |
| worst | `H5_gauss` | ratio p_peak/p_avg | 0.227 | 0.0 |
| pre-registered | `H_new` | residual | 0.411 | p=0.84 |

*Table B.2c -- Cardiac myosin, apo `8QYP` -> `8QYR` [15] (drug XB2), true pocket seeded at top-10, MIN_HOP 2.*

| cell | operator | score | AUC | P@5 |
|---|---|---|---|---|
| best | `H3_normL` | dX dip depth | 0.685 | 0.4 |
| worst | `H8_gnm` | -dD mean | 0.068 | 0.0 |
| pre-registered | `H_new` | residual | 0.601 | p=0.12 |

Across all three the outcome turns on the selection stage, not the walk: BCR-ABL1's 5/5 is a pocket myristate already opened; KRAS and cardiac myosin reach the pocket only once it is seeded, and their pre-registered single cells are honest negatives. Half the 221 cells sit at chance.

**B.3 The seeded-CTQW pipeline across 630 proteins.** PASSer top-10 -> drop the active-site pocket -> distal `MIN_HOP` filter -> CTQW -> PocketMiner veto [6] (apo-ligand protected) -> CTQW -> rank pockets. One fixed operator+score.

*Table B.3 -- Family-weighted AUC (one vote per family), seeded walk vs classical baselines on identical residues; Wilcoxon paired [4-6, 9, 13].*

| MIN_HOP | families | seeded walk | closeness | proximity | p |
|---|---|---|---|---|---|
| 1 | 399 | 0.585 | 0.601 | 0.616 | 0.001 |
| 2 | 291 | 0.542 | 0.569 | 0.570 | 0.003 |
| 3 | 157 | 0.544 | 0.575 | 0.563 | 0.044 |
| 4 | 50 | 0.543 | 0.580 | 0.581 | 0.258 |

The walk never beats closeness centrality; the per-protein ordering reverses this and is pseudo-replication (two proteins supply 68% of strict hits), non-significant under paired McNemar (p=0.08-1.0). A blind leave-one-family-out regression over all 221 scores reaches 0.7216 on the 91 distal proteins against a reversed-distance floor of 0.7219 (p=0.90) -- distance reproduced, nothing beyond. Two-source interference, run on all 630 at `MIN_HOP` 1-4 blind, fails every pre-registered test. The protein-identity floor here is pooled AUC 0.771 [10-12], above every method either track has tested -- any pooled AUC must clear it. The 399 family labels are inherited from five datasets under three conventions; a single clustering rule is a Phase-2 prerequisite, but the paired comparisons do not depend on it. Three results on this track were retracted and corrected in the public history: an inverted distal proximity-floor AUC, a classical twin differing in operator as well as coherence, and a blind positive filed as a to-do.


### ADD-5 — Our retractions in the §7 ledger
status: REJECTED  # moved into Appendix B; in section 7 it pushed 3 sentences past page 6
section: 7. Team Capability
anchor: It found five of our own errors in seven days, including our headline result.
cost: 2 lines
---
The same register operating on the second branch caught three more: an AUC read backwards in a distal proximity-floor claim, a classical-comparison arm that differed in operator as well as in coherence, and a blind positive filed as a to-do rather than reported. All three are corrected in the public history.

### ADD-6 — The operator and the walk, in one paragraph
status: REJECTED  # moved into Appendix B to keep sections 6-7 inside the 6-page body
section: 2. Technical Approach (Paradigm)
anchor: That measured boundary, not a preference, is what sends the remaining quantum candidates toward many-body objects and conformational ensembles rather than single-structure optimisation.
cost: 4 lines
---
**The construction.** Residues are nodes at their C-alpha coordinates, edges within a 10 A cutoff. The challenge-specified operator is `H_new = L_sym + diag(0.08 V_B + 0.16 V_T + 0.08 V_R + 0.04 V_C + 0.04 V_M)`, the symmetric normalised Laplacian of the exponential contact graph plus a diagonal site potential, each term z-scored and signed so penalties raise it and rewards lower it: `V_B` B-factor disorder, `V_T` chain termini and exposure, `V_R` rigidity, `V_C` GNM covariance with the core, `V_M` slow-mode participation. Real symmetric, hence Hermitian, at every setting we swept. The walk is `U(t) = exp(-iHt)` seeded at the active site, reported in the converged time-average `p_avg(s->a) = sum_k |v_k(s)|^2 |v_k(a)|^2` — a sum of squares, which is the one-line reason the converged propagator is phase-free. Appendix B lists the thirteen operators and seventeen scores the 221 cells are built from.

### ADD-7 — KRAS G12C on 4LDJ (SUPERSEDED: folded into ADD-4 Appendix B)
status: REJECTED
section: 1. Problem Framing (beside the hit-list table) or Appendix B
anchor: __END__
cost: ~10 lines
---
**The stage that decided KRAS was not the walk.** Re-running the mandated target end to end on `4LDJ` — the genuine G12C apo structure (residue 12 = CYS; GDP and Mg only; we verified that six apo G12C depositions exist and that Table 1's `4OBE` is wild-type at residue 12 while the organisers' suggested `8S8C` is drug-bound) — the result is decided before the quantum walk runs.

Candidate pockets come from fpocket and are cut to a top-K before seeding. Under the narrower setting (fpocket ranking, top-5 by druggability) the true sotorasib pocket ranks **#6** and is discarded: 1 drug residue survives among 36 seeds, and P@5 is zero by construction — the pipeline cannot answer correctly whatever the operator does. Widening to a druggability-and-allostery consensus at top-10 seeds it: **8 drug residues among 44**, base rate 0.182. Same structure, same walk, same scoring; the selection stage alone moved the target from unanswerable to answerable.

Scored on that seed set, the best of 14 operators x 17 scores reaches AUC **0.809** (`H_new` with the resolvent score at the band top, P@5 0.6) and the worst reaches **0.184** (`H11_aniso`, proximity-corrected residual) — a spread of 0.63 AUC across cells that differ only in operator and score. Read correctly the worst is not a failure but a reversal: 1 - 0.184 = 0.816, within noise of the best. Under the pre-registered single cell fixed before scoring, the target returns an honest negative (label-permutation null, p > 0.05).

Consequence, and it is the same one section 6 reaches from the funnel ablation: on this target the classical selection stage, not the transport subroutine, determines whether the answer is reachable at all. A method reported only at its best cell, on a seed set chosen after the fact, would have reported 0.809 here.

