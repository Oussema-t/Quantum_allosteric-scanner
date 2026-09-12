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

## Appendix B — A second pipeline, on a second cohort

Sections 1-7 report the `bartosz` track: fpocket candidates, 108 structures for the coherence tests, 1022 proteins in 276 families for the ensemble sweep. A second pipeline was built independently on the `allosteric` track, with a different pocket detector and a different candidate filter, and reaches the same verdict. It is reported here as **replication, not as an enlarged n**: the two cohorts differ in detector (PASSer against fpocket) and in family convention (399 against 276), so their counts are not interchangeable and are never pooled. Every AUC below is computed per structure and averaged, as in the main text.

**The pipeline.** PASSer top-10 pockets, drop the pocket holding the active site, apply a distal seed filter (`MIN_HOP`, 1 to 4 graph hops from the active site), run the walk, apply a cryptic-opening veto [6] with pockets already holding an apo-deposited ligand protected, run the walk again on survivors, rank pockets by best residue. One operator-and-score pair (`gauss/sym` with the energy-uncertainty score) fixed in advance and applied to every protein. Cohort: 630 proteins in 399 families drawn from the same five public benchmarks [4-6]; 199 further proteins were removed by the veto before scoring.

**The walk against its classical peers, on identical residues.** Family-weighted AUC, one vote per family, Wilcoxon paired on families:

| MIN_HOP | families | seeded walk | closeness | proximity | p |
|---|---|---|---|---|---|
| 1 | 399 | 0.585 | 0.601 | 0.616 | 0.001 |
| 2 | 291 | 0.542 | 0.569 | 0.570 | 0.003 |
| 3 | 157 | 0.544 | 0.575 | 0.563 | 0.044 |
| 4 | 50 | 0.543 | 0.580 | 0.581 | 0.258 |

There is no distal-filter setting at which the walk beats closeness centrality. Per-protein means show the opposite ordering at every setting, and that reversal is pseudo-replication: two proteins supply 68% of the walk's strict hits. Paired McNemar on which families each method clears at P@5 >= 0.8 is non-significant throughout (p = 0.078, 0.238, 0.754, 1.000).

**Combining all 221 observables reproduces distance.** A logistic regression over the 13 x 17 per-residue score vectors, true leave-one-family-out so the fold's model never sees its own family, reaches family-weighted AUC **0.7216** on the 91 distal proteins — against 0.5405 for the best single cell selected on the same data. The floor on that subset is *reversed* distance, since the subset is defined as truth at least 3 hops away: **0.7219**. The difference is -0.0003 (Wilcoxon p = 0.90). On the full 630 the model and the fixed cell are indistinguishable (0.5847 against 0.5854, p = 0.985). This is section 2's phase-free conclusion measured with a trained model rather than a single cell.

**Two-source interference at scale.** The finite-delay phase-sensitive observable of section 2 was run on all 630 proteins at `MIN_HOP` 1 to 4 across the same eleven-delay grid, as a point statistic at each delay and as range statistics across delays, with configuration and sign chosen blind by leave-one-family-out. Both arms fail every pre-registered test at every setting and rank below closeness centrality throughout.

**Protein-identity floor on this cohort.** The section 5 floor re-measured here: a constant-per-protein score reaches pooled AUC **0.771** across 630 proteins — above every method either track has tested, and a wider margin than the 0.65 section 5 reports on the first cohort. Any AUC pooled across proteins must clear it; the per-structure metrics used throughout both tracks are immune by construction.

**Retractions on this track.** The same register operating on the second branch caught three more: an AUC read backwards in a distal proximity-floor claim, a classical-comparison arm that differed in operator as well as in coherence, and a blind positive filed as a to-do rather than reported. All three are corrected in the public history.

**Why the family counts differ between tracks.** The 399 labels are inherited from five source datasets under three conventions: CASBench group codes (227 entries), UniProt accessions, and free-text names (CryptoBench 308, ASBench 67, PocketMiner 21, CryptoSite 7). The four largest families are all CASBench. A single clustering rule is a Phase-2 prerequisite for any absolute family count; the paired comparisons above do not depend on it.



**Replication, the blind model, and the construction.** A second pipeline, built independently on a different detector and a different candidate filter, reaches the same verdict on a larger cohort: across 630 proteins in 399 families the seeded walk loses to closeness centrality at every distal-filter setting (Wilcoxon p = 0.001, 0.003, 0.044, 0.258). The cohorts are not pooled — they differ in detector and family convention — so this is replication, not an enlarged n.

The same conclusion survives combining the observables rather than choosing among them. A logistic regression over all 221 per-residue score vectors, true leave-one-family-out, reaches family-weighted AUC **0.7216** on the distal subset — against 0.5405 for the best single cell selected on the same data, and **0.7219** for the trivial reversed-distance floor. The difference from the floor is -0.0003 (Wilcoxon p = 0.90): optimally combined, the quantum observables reproduce distance and nothing further.

### B.0 — The thirteen operators and seventeen scores

**The construction.** Residues are nodes at their C-alpha coordinates, edges within a 10 A cutoff. The challenge-specified operator is `H_new = L_sym + diag(0.08 V_B + 0.16 V_T + 0.08 V_R + 0.04 V_C + 0.04 V_M)`, the symmetric normalised Laplacian of the exponential contact graph plus a diagonal site potential, each term z-scored and signed so penalties raise it and rewards lower it: `V_B` B-factor disorder, `V_T` chain termini and exposure, `V_R` rigidity, `V_C` GNM covariance with the core, `V_M` slow-mode participation. Real symmetric, hence Hermitian, at every setting we swept. The walk is `U(t) = exp(-iHt)` seeded at the active site, reported in the converged time-average `p_avg(s->a) = sum_k |v_k(s)|^2 |v_k(a)|^2` — a sum of squares, which is the one-line reason the converged propagator is phase-free.

Four edge weightings — binary (`d < 10 A`), exponential `exp(-0.3 d)`, Gaussian `exp(-d^2/72)` and harmonic `1/(d + 0.5)^2` — under three normalisations: the adjacency `W`, the combinatorial Laplacian `L = D - W`, and the symmetric normalised `L_sym = I - D^{-1/2} W D^{-1/2}`. Twelve operators, `binary/adj` through `harm/sym`, plus `H_new` gives thirteen. The seventeen scores fall in five families: **occupation** (`p_avg`, `p_peak`, and their ratio `R`); **proximity-corrected** (`residLOG`, `residRAW`, each optionally focused by walker spread, and `pavg_over_dX`); **resolvent** (`green_zero_0.01`, `green_zero_0.05`, `green_lmax_0.05`, i.e. `|<a|(E + i eta - H)^{-1}|s>|^2`, a commute-time analogue); **dispersion** (`neg_dD_mean`, `neg_ED_final`, `QMI`); and **energy-uncertainty** (`neg_dE` and two combinations). Thirteen times seventeen is the 221 cells per protein.

One qualification belongs with that list rather than buried in it. `neg_dE`, the strongest single score, is time-independent by construction and equals `sqrt(sum_j W_ij^2)` to machine precision — a classical local statistic under a quantum name. It ranks well and it cannot carry interference, which is one measured reason the coherent and decoherent arms agree.

### B.1 — Per-target re-runs: the selection stage decides the target

The two targets below were re-run end to end through the notebook pipeline, which seeds from detector-ranked candidate pockets rather than from PASSer. These are **not** the section 1 hit lists — those come from the `bartosz` walk on `H_new` and are the submitted predictions. These are a second measurement, and the AUCs are not comparable to them.

**KRAS G12C (`4LDJ`).** We verified the structure before using it: residue 12 is CYS, the only heteroatoms are GDP and Mg, and six apo G12C depositions exist in the PDB — Table 1's `4OBE` is wild-type at residue 12 and the organisers' suggested `8S8C` is drug-bound, so neither can serve. The result is then decided before the walk runs. Candidate pockets are cut to a top-K before seeding: under a narrower setting (detector ranking, top-5 by druggability) the true sotorasib pocket ranks **sixth** and is discarded, so P@5 is zero by construction whatever the operator does. Under the druggability-and-allostery consensus at top-10 it is seeded, leaving 38 distal seeds of which 6 are drug-pocket residues. Same structure, same walk, same scoring — the selection stage alone moved the target from unanswerable to answerable. On that seed set the best of 14 operators x 17 scores reaches AUC **0.828** (`H_new` with the resolvent score at the band top) and the worst **0.161** (`H7_harm`, proximity-corrected residual); the median cell is 0.500. Under the single cell fixed before scoring the target returns an honest negative (AUC 0.479, label-permutation p = 0.57).

This is the funnel ablation of section 6 seen on one target: the classical selection stage, not the transport subroutine, determines whether the answer is reachable at all. A method reported only at its best cell, on a seed set chosen after the fact, would have reported 0.809 here.

**BCR-ABL1 (`1OPL`).** The same pipeline and the same settings on the myristoyl target. Here the true asciminib pocket **is** seeded, and 18 of 43 distal seeds are drug-pocket residues — a base rate of 0.419, which is the finding rather than a convenience: 1OPL carries myristate in that pocket, as section 1 records, so the cavity is already open and this is not cryptic-pocket prediction. Best of the same cells: AUC **0.796** with P@5 1.0 (`H6_exp`, proximity-corrected residual with the focus term); worst **0.227** (`H5_gauss` scored by the coherence ratio `p_peak / p_avg`); median 0.491. The pre-registered single cell gives AUC **0.411**, label-permutation p = 0.84 — below chance and indistinguishable from it.

Read together the two targets make one point, and it is not about which operator wins. On KRAS the selection stage decided the answer was unreachable; on BCR-ABL1 it delivered a pocket myristate had already opened. In neither case did the transport subroutine determine the outcome. On both, half of the 238 cells sit at chance (median 0.500 and 0.491) and the spread from best to worst — 0.67 and 0.57 AUC — is larger than any margin between methods reported in section 2. The best cell is the tail of a distribution centred on nothing, which is why the pre-registered cell lands at 0.479 and 0.411. Nor is the winning score the occupation measure the method is usually described by: it is the resolvent on one target and the proximity-corrected residual on the other, while the explicitly coherence-sensitive ratio is the worst cell on both.

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

