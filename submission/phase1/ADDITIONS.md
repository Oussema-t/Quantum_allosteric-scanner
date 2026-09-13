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

## Appendix B — The walk, the operators, per-target connectivity, and the AI stage

A second pipeline on the `allosteric` track (PASSer detection, 630 proteins in 399 families [4-6]), reported as **replication** of sections 1-7's `bartosz` track (fpocket), not pooled with it. Every AUC is per structure, averaged.

**B.1 The construction.** Residues are C-alpha nodes, edges within a **10 A** C-alpha contact cutoff (`NET_CUTOFF`; drug-pocket truth uses a separate 4.5 A heavy-atom `SITE_CUTOFF`); the walk is `U(t)=exp(-iHt)` seeded at the active site, read as the converged average `p_avg(s->a)=sum_k |v_k(s)|^2 |v_k(a)|^2` -- a sum of squares, hence phase-free. The **connectivity matrix** `C_ij` (first required deliverable) is that average-mixing matrix, `(V o V)(V o V)^T`: symmetric, row-stochastic, operator-only. Thirteen operators (four weightings x three normalisations, plus `H_new = L_sym + diag(0.08 V_B + 0.16 V_T + 0.08 V_R + 0.04 V_C + 0.04 V_M)`) x seventeen scores give the 221 cells. `neg_dE`, the strongest single score, is time-independent and equals `sqrt(sum_j W_ij^2)` to machine precision -- a classical local statistic, so it cannot carry interference.

**B.2 Per-target connectivity.** Best and worst cell per target -- the three mandated (KRAS, BCR-ABL1, cardiac myosin) plus one additional allosteric target (HIV-1 RT, the NNRTI pocket) -- each selected across all 221 cells (13 Hamiltonians x 17 scores) by P@5, all seeded identically (consensus of fpocket druggability and PASSer allostery, top-10, MIN_HOP 2). Connectivity matrices and top-5 x active-site sub-blocks are in `results/connectivity/`. Per-target detail is in this repository under `submission/phase1/supplementary/` (github.com/Oussema-t/Quantum_allosteric-scanner): for each of the four targets, a connectivity sheet (best/worst matrices, their difference, top-5 x active-site) and a walk-trace sheet (P(active,t) and p_avg to the active site).

| target (apo) | cell | operator / score | AUC | P@5 |
|---|---|---|---|---|
| KRAS G12C (`4LDJ`) [14] | best | `H_new` / resolvent | 0.809 | 0.6 |
| KRAS G12C (`4LDJ`) [14] | worst | `H11_aniso` / residual RAW | 0.184 | 0.0 |
| BCR-ABL1 (`1OPL`) [1-3] | best | `H6_exp` / residual+focus | 0.796 | **1.0** |
| BCR-ABL1 (`1OPL`) [1-3] | worst | `H5_gauss` / ratio p_peak/p_avg | 0.227 | 0.0 |
| Cardiac myosin (`8QYP`->`8QYR`) [15] | best | `H1_adj` / dX dip depth | 0.733 | 0.4 |
| Cardiac myosin (`8QYP`->`8QYR`) [15] | worst | `H12_anmS` / -E[D] final | 0.233 | 0.0 |
| HIV-1 RT (`1DLO`->`3V81`, NNRTI) | best | `H14_anmP` / p_peak | 0.963 | 0.8 |
| HIV-1 RT (`1DLO`->`3V81`, NNRTI) | worst | `H14_anmP` / Green E=lmax | 0.196 | 0.0 |

*Table B.2 -- best and worst of 221 cells per target, chosen by P@5. `4LDJ` is true G12C (`4OBE` is wild-type at residue 12); `1OPL` has myristate pre-bound; cardiac myosin's and HIV-1 RT's pockets are reached only once seeded by the consensus (their true pocket ranks outside fpocket's top-10 on druggability alone but 3rd on PASSer allostery). Best and worst share the protein, seeding and scoring, so the AUC spread (0.63/0.57/0.50/0.77) is the operator-and-score choice alone -- on HIV-1 RT the same operator (`H14_anmP`) is both best and worst depending on the score. The pre-registered `H_new` cell is an honest near-negative on all four (KRAS 0.479 p=0.57, BCR 0.411 p=0.84, myosin 0.601 p=0.12, HIV-1 RT 0.665 p=0.060).*

**B.3 Seeded-CTQW vs classical baselines, 630 proteins.** Pipeline: PASSer top-10 -> drop the active-site pocket -> distal `MIN_HOP` filter -> CTQW -> PocketMiner veto [6] (apo-ligand protected) -> CTQW **ranks the surviving residues** (P@5 is residue-level; pockets are then ordered by their best residue), one fixed operator+score. Hit-list counts on identical residues (MIN_HOP=1; P@5 with AUC>=0.6):

On identical residues (MIN_HOP=1, P@5 with AUC>=0.6) the seeded-CTQW-pipeline clears **69 proteins / 20 families** at P@5>=0.8 and 101 / 45 at P@5>=0.6 (AUC 0.600) -- more per-protein than any of the thirteen classical baselines, but fewer families than closeness centrality (48 / **29**), which has no active site. Family-weighted AUC confirms the walk never beats closeness (0.585/0.542/0.544/0.543 vs 0.601/0.569/0.575/0.580 at MIN_HOP 1-4, Wilcoxon p=0.001-0.26, non-significant under paired McNemar); a blind leave-one-family-out regression over all 221 scores reaches 0.7216 on the 91 distal proteins against a reversed-distance floor of 0.7219. The protein-identity floor here is pooled AUC 0.771 [10-12], above every method tested.

**Best-of-221 per MIN_HOP (selection, not blind performance).** Picking the best Hamiltonian and score for each protein -- 221 cells per target -- the seeded-CTQW reaches P@5>=0.8 on 200/115, 147/77, 82/49, 47/20 (proteins/families) at MIN_HOP 1/2/3/4, and P@5>=0.6 on 340/215, 238/144, 131/80, 58/28. These are selection ceilings; the single fixed cell in Table B.3 (69/20 at P@5>=0.8) is what survives once the per-protein choice is removed, and the gap between them is the multiplicity this proposal corrects for.

![Connectivity `C_ij` for the four scoreable targets -- the first required deliverable. **Top two rows:** the full N x N average-mixing matrix `C_ij = sum_k |v_k(i)|^2 |v_k(j)|^2` for each target's **best** and **worst** operator (Table B.2), symmetric, row-stochastic, operator-only; strips on both axes mark the **active site** (blue) and the **allosteric drug pocket** (red -- holo drug contacts at 4.5 A; purple = both). Best and worst share protein, seeding and scoring, so their contrast is the operator choice alone. **Bottom row:** the top-5 predicted x active-site sub-block (rows = predicted residues, **red label = in the drug pocket**; KRAS 3/5, BCR-ABL1 5/5, cardiac myosin 2/5, HIV-1 RT 4/5). KRAS's sites overlap (switch-II, 4 shared); the other three are distal. Cardiac's best-operator label is a near-tie that varies run-to-run (15-residue pocket in 704), but the consensus seeding reproducibly recovers the mavacamten pocket (P@5 0.4). Reproducible from the committed matrices; c-Myc/Max is connectivity-only, in `results/connectivity/`.](connectivity_sites.png)

**B.4 The AI stage: one configuration recommender.** A single model sets the quantum stage from topology alone, so the pipeline can be applied to a new apo protein without a sweep. **Architecture:** 9 topology features -> StandardScaler -> Ridge multi-output -> the predicted AUC of all **884 configurations** (221 Hamiltonian x score cells x 4 MIN_HOP) -> rank -> **top-k with softmax weights**. **Input:** 9 graph features (residues, edges, mean/variance/CV of degree, clustering coefficient, diameter, algebraic connectivity, spectral radius). **Output:** the caller picks **k** -- how many (MIN_HOP, Hamiltonian, score) configurations to run -- and may restrict MIN_HOP; the model returns those k with weights summing to one. **Training:** leave-one-family-out over 630 proteins in 399 families, each scored by a model that never saw its family.

What this one model can and cannot learn was measured by the two random-forest diagnostics of section 6 (a MIN_HOP classifier and an operator-score regressor on the same features): topology predicts **MIN_HOP** (near vs distal, AUC 0.793; running at the predicted MIN_HOP beats always-hop-1, 0.924 vs 0.901) but **not the operator and score** (0.625 vs 0.630 for one fixed cell). Those two are the diagnostic; the deliverable is the single recommender above. So the recommender is honest about its limits -- it narrows MIN_HOP well, and reports the operator/score shortlist as selection rather than a confident pick; at k=6 the shortlist's best cell averages AUC 0.724 over 43 families. `results/ml_model/recommender.py`.

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

