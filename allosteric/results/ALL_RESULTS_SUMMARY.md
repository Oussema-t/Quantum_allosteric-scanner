# Every test run, both branches, and what each returned

Written 2026-09-09. Every number in the `allosteric` column was re-verified against its raw
artifact immediately before writing. Numbers in the `bartosz` column are transcribed from that
branch's Phase-1 submission v1 (`PHASE1_SUBMISSION_LATEX_v1_c5f0419`) and its task register —
**not independently re-run here.**

---

## 0. The two cohorts are NOT comparable — read this first

| | allosteric branch | bartosz branch |
|---|---|---|
| candidate pockets from | **PASSer top-10** | **fpocket** |
| veto | PocketMiner (apo-ligand protected) | PocketMiner ("cryptic-opening veto") |
| scored cohort | **630 proteins / 399 families** | 1022 proteins / **276 families** |
| coherence-test cohort | 630 (or 91 distal) | **108 structures / 76 clusters** |

Different pocket finder, different family clustering, different cohorts. "20 of 399 families" and
"5 of 276 families" are not the same measurement. **Fixing one cohort matters more than any
further experiment.**

---

## 1. The pipeline (allosteric branch)

Seeded-CTQW-pipeline: PASSer top-10 → drop active-site pocket → MIN_HOP filter → CTQW round 1 →
PocketMiner veto (apo-ligand protected) → CTQW round 2 → rank residues, then pockets by best residue.

| stage | proteins | families |
|---|---|---|
| worklist | 1022 | 688 |
| reached the CTQW | 829 | 529 |
| **scored end to end** | **630** | **399** |

Losses: 193 at pocket selection, 199 to the veto destroying the true pocket. A separate 46 were
lost to a PocketMiner preprocessing bug (selenomethionine + incomplete backbones), since fixed —
that recovered 33 proteins and moved the denominator 597 → 630.

### Headline counts, and what survives a null

| | P@5 ≥ 0.8 | null (label permutation) | real excess |
|---|---|---|---|
| best of 884 configurations | 137 families | **99.8** | **+37**, p<0.001 |
| one fixed cell (gauss/sym/neg_dE) | 20 families | **5.1** | **+15**, p<0.001 |

**73% of the sweep's headline is chance.** The fixed cell is only 25% chance. Neither raw count
should be reported; the excess over null is the defensible number.

---

## 2. Classical baselines — 13 measures, identical residues and labels, 630 proteins

| measure | seeded? | mean AUC | P@5≥0.8 prot/fam |
|---|---|---|---|
| **Seeded-CTQW-pipeline** | yes | **0.600** | **69 / 20** |
| closeness centrality | no | 0.576 | 48 / **29** |
| betweenness | no | 0.575 | — |
| proximity (closer) | yes | 0.574 | 44 / 16 |
| personalised PageRank | yes | 0.565 | 31 / 20 |
| commute time (v2 notebook) | yes | 0.549 | 47 / 22 |
| weighted communicability (v2) | yes | 0.543 | 54 / 23 |
| GNM cross-correlation (v2) | yes | 0.540 | 23 / 13 |
| degree | no | 0.533 | 48 / 12 |
| GNM perturbation response (v2) | yes | 0.531 | 49 / 17 |
| eigenvector centrality | no | 0.529 | 63 / 25 |
| **heat kernel e^{-Lt}** | yes | **0.512** | 23 / 17 |
| GNM low-mode | no | 0.430 | 8 / 5 |

**Result:** highest AUC of all 14, beats 10 of 13 at p<0.02, **ties closeness / betweenness /
proximity**. At FAMILY level it LOSES at P@5≥0.8 — closeness 29, eigenvector 25, communicability 23,
commute time 22, against the pipeline's 20.

---

## 3. The controls that changed conclusions

| test | what it showed |
|---|---|
| **proximity floor** | I read an AUC backwards. 0.227 on distal means the REVERSED predictor scores 0.773. Family level on distal: CTQW **0.507** vs reversed proximity **0.722**, CTQW wins **14/53**. The distal claim died here. |
| **CAS0002 dominance** | 28 of 91 distal structures are one protein. Removing it: CTQW 0.617 → **0.501**. |
| **unconstrained (no PASSer/veto)** | 303 candidates instead of 40, base rate 0.070 instead of 0.33. **P@5 collapses for every method** — closeness 48 proteins → **6**. The classical funnel does the localisation. |
| **site level (rank the pocket)** | CTQW best top-3 (**86%** vs 78-81%) and best mean rank (2.12); second on top-1 by 1 point (37% vs proximity 38% — noise). Random is ~26% with 3.9 pockets. |
| **fixed-cell LOFO on distal** | AUC **0.500** — exactly chance, even choosing best-of-221 blind. |

---

## 4. The quantum-specific tests

| test | result | status |
|---|---|---|
| amplitudes vs probabilities, matched operator (`binary/comb/p_avg` vs heat kernel) | +0.031 family level, cluster-perm p = 0.020 | **ON HOLD** — normalisation and dynamic range differ, not only phase |
| self-interference cross terms `I(r,t) = P_q − P_diag` | **FAILS** both pre-registered bars: worse than its own diagonal (p=0.0065) and worse than proximity | closed |
| **two-source phase interference** `2·Re⟨r|e^{−iHτ}|a⟩` | distal, config+sign chosen blind by LOFO: **+0.107 vs pipeline, p = 0.007**; survives dropping CAS0002 (0.624 vs 0.500); **no P@5 gain** (25/3 vs 29/4) | **OPEN** — τ objection unresolved |
| sign stability check | inverted in **53 of 53 folds**; 80% of proteins below 0.5 (mean 0.314) | not sign-fishing |
| QMI (entanglement) | AUC 0.538, **13th of 17 scores** | the most quantum score ranks near the bottom |
| centrality ablation vs JACS ρ≈0.95 | our ρ = **0.689**, not 0.95 — the seeding is the difference | done |

### What `neg_dE` actually is
Our best score reproduces **exactly (ρ = 1.0000)** from the diagonals of H and H². It sees only
two-step neighbourhoods. It IS a legitimate quantum quantity — the energy uncertainty of a state
localised at that residue, which by time-energy uncertainty sets the local rate of evolution — but
it carries **no phase, no interference, no long-range coupling**, and the same formula on the
classical operator gives the same numbers.

### The AI recommender
Topology → k weighted configurations out of 884. **Negative result:** exact-winner accuracy
**0.107 against a 0.137 commonest-class baseline**, and it loses to a single fixed cell
(0.625 vs 0.630). Per-protein operator preference is not learnable from topology.

---

## 5. The bartosz branch (transcribed, not re-run here)

| test | result |
|---|---|
| 1022-protein ensemble, 13 ops × 17 scores + veto | **no arm clears more than 5 of 276 families**; quantum vs classical McNemar **p = 1.0** |
| blind validity rule | 2 of 7 mandated/recommended targets pass; **49% over 63 independent pairs** |
| cryptic vs distal, 1233 proteins | only 23% of allosteric sites and 7% of drug-contact pockets are distal; **cryptic datasets median hop = 0** |
| apo contamination audit | 3 of 7 targets ligand-held open; **40 of 40 ASBench** structures carry a ligand at the scored site |
| converged CTQW, distance-conditioned | 0.5921 → **0.5184, not significant** |
| chiral walk (Peierls phases) | **0.4960 — below chance** |
| ENAQT engineered dephasing | relaxes to the classical/proximity limit |
| spectral coherence / entanglement entropy | 0.5226 / 0.4903 |
| **coherent vs decoherent toggle** | **+0.0023 AUC, Wilcoxon p = 0.92, cluster-robust p = 0.83** — a well-powered null |
| distance-proxy ordering | classical diffusion 0.953 → decoherent 0.735 → coherent **0.692** — the walk is measurably LESS a distance proxy |
| centrality ablation (105 structures / 74 proteins) | ρ median **0.41** not 0.95; beats degree/eigenvector/GNM (p<0.05), ties betweenness/closeness |
| spatially matched pocket-block null | BH-FDR survivors **45/110 → 0/110** |
| convergence check on propagation time | **50 of 108 structures flip verdict sign** between T=15 and the converged limit |
| hardware | **169–704 qubits, 3.3M–124.9M two-qubit gates**; coarse-graining to 10–15 qubits destroys the signal (Jaccard 0.00–0.18); every mandated target `FAULT_TOLERANT_ONLY` |
| mandated targets | KRAS 0.514, BCR-ABL1 0.541, cardiac myosin 0.548 — all `NO_SIGNAL_IN_APO` |

---

## 6. Where the two branches agree, and where they don't

**Agree, independently measured:**
- The walk does not beat distance — but by two DIFFERENT measurements, not one. Ours is a **raw**
  AUC on distal with the cell chosen blind (**0.500**, chance before any correction). His is a
  **residualised** AUC on 108 structures (**0.5184**, nothing left once distance is regressed out).
  Same conclusion, different quantities; his is the stronger form. Do not quote them as one number.
- Both centrality ablations: beats the seed-blind baselines (degree, eigenvector, GNM), **ties the
  seed-aware ones** (betweenness, closeness).
- Both found the JACS ρ≈0.95 does NOT replicate (0.689 ours, 0.41 his).
- Both identified the two Table-1 defects (6C1H has no mavacamten; 4OBE is wild-type KRAS).

**One open disagreement, and it may not be a disagreement:**
- He finds coherence contributes **zero** (+0.0023, p=0.92) using the **converged, phase-free**
  propagator — where zero is the expected answer, as his own TASK-0157 derived.
- I find **+0.114** using a **finite-delay phase-keeping** observable.
- Different observables. His τ objection to my number is legitimate and unresolved: the integration
  window is set by 1/gap, and he has measured that 46% of structures flip sign with the clock.

**NOT an agreement, though an earlier version of this file implied it:** the pipeline SHAPE is
shared (candidate detection → CTQW → veto) but the candidate detector differs — **PASSer here,
fpocket there** — which changes which residues are scored. That is a cohort difference, in §0.

**Only on the allosteric branch:** the unconstrained test, the AI recommender negative, the
null-corrected family counts, the two-source observable.

**Only on the bartosz branch:** the benchmark validity audit, the convergence check, the hardware
resource analysis, the spatially matched null.

---

## 7. What is agreed as next

1. **Fix one cohort** — PASSer or fpocket, 399 families or 276. Nothing from either side is
   quotable until this is settled.
2. **Replicate the two-source result** at a principled per-protein τ
   (`min_adequate_t_max`), with the sign **pre-registered from a physical argument** rather than
   chosen. If +0.114 survives, it is real.
3. **+0.031 stays on hold** pending a spectrally-matched control.
4. **Do not put +0.114 in the submission as a result.** Name the finite-delay phase-sensitive
   observable as the concrete Phase-2 quantum route, with its honest ceiling stated.
