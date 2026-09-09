# Two branches, side by side — my tests, his tests, agreements, disagreements

Written 2026-09-09, seven days before the Phase-1 deadline.
`allosteric` numbers re-verified against raw artifacts. `bartosz` numbers transcribed from that
branch's submission v1 and task register — not independently re-run here.

---

## PART 1 — MY TESTS (allosteric branch)

### 1.1 The pipeline
**Seeded-CTQW-pipeline:** PASSer top-10 → drop active-site pocket → MIN_HOP filter → CTQW round 1
→ PocketMiner veto (apo-ligand protected) → CTQW round 2 → rank residues.

| stage | proteins | families |
|---|---|---|
| worklist | 1022 | 688 |
| reached the CTQW | 829 | 529 |
| **scored end to end** | **630** | **399** |

Also fixed a PocketMiner preprocessing bug (selenomethionine, incomplete backbones) that had
silently dropped 46 proteins; recovered 33, moving the denominator 597 → 630.

### 1.2 Headline counts, null-corrected

| | observed | null | real excess |
|---|---|---|---|
| best of 884 configurations, P@5≥0.8 | 137 families | 99.8 | **+37**, p<0.001 |
| one fixed cell, P@5≥0.8 | 20 families | 5.1 | **+15**, p<0.001 |

**73% of the sweep's headline is chance; 25% of the fixed cell's is.**

### 1.3 Classical baselines — 13 measures, identical residues and labels

| measure | seeded | AUC | P@5≥0.8 prot/fam |
|---|---|---|---|
| **Seeded-CTQW-pipeline** | yes | **0.600** | 69 / 20 |
| closeness centrality | no | 0.576 | 48 / **29** |
| betweenness | no | 0.575 | — |
| proximity (closer) | yes | 0.574 | 44 / 16 |
| PageRank | yes | 0.565 | 31 / 20 |
| commute time | yes | 0.549 | 47 / 22 |
| weighted communicability | yes | 0.543 | 54 / 23 |
| GNM cross-correlation | yes | 0.540 | 23 / 13 |
| degree | no | 0.533 | 48 / 12 |
| GNM perturbation response | yes | 0.531 | 49 / 17 |
| eigenvector centrality | no | 0.529 | 63 / 25 |
| heat kernel e^{-Lt} | yes | 0.512 | 23 / 17 |
| GNM low-mode | no | 0.430 | 8 / 5 |

Highest AUC of 14; beats 10 of 13 at p<0.02; **ties closeness, betweenness, proximity**.
**Loses at family-level P@5** to closeness (29), eigenvector (25), communicability (23), commute (22).

### 1.4 Controls that changed conclusions

| test | result |
|---|---|
| proximity floor | **I read an AUC backwards.** 0.227 means the reversed predictor scores 0.773. Distal, family level: CTQW **0.507** vs reversed proximity **0.722**, we win **14/53**. |
| CAS0002 dominance | 28 of 91 distal structures are one protein. Without it CTQW 0.617 → **0.501**. |
| unconstrained (no PASSer/veto) | 303 candidates instead of 40, base rate 0.070 vs 0.33. **P@5 collapses for everything** — closeness 48 proteins → **6**. |
| site level (rank pockets) | CTQW best top-3 (**86%**) and mean rank (2.12); second on top-1 (37% vs proximity 38% — noise). |
| fixed-cell LOFO on distal | AUC **0.500** — chance, even choosing best-of-221 blind. |

### 1.5 Quantum-specific

| test | result | status |
|---|---|---|
| amplitudes vs probabilities, matched operator | +0.031, cluster-perm p = 0.020 | **on hold** — normalisation differs too |
| self-interference cross terms | fails both pre-registered bars | closed |
| **two-source phase interference** `2·Re⟨r\|e^{−iHτ}\|a⟩` | distal, config+sign blind LOFO: **+0.107, p = 0.007**; survives dropping CAS0002; **no P@5 gain** | **open** — τ unresolved |
| sign stability | inverted in **53/53 folds**, 80% of proteins below 0.5 | not sign-fishing |
| QMI (entanglement) | 0.538, **13th of 17 scores** | the most quantum score ranks near the bottom |
| centrality ablation vs JACS ρ≈0.95 | ours **0.689** | seeding is the difference |
| AI recommender | accuracy **0.107 vs 0.137 baseline**; loses to a fixed cell | negative result |

**What `neg_dE` is:** reproduces exactly (ρ = 1.0000) from the diagonals of H and H² — sees only
two-step neighbourhoods. A legitimate quantum quantity (energy uncertainty at a residue, setting
the local rate of evolution) but with **no phase, no interference, no long-range coupling**.

---

## PART 2 — HIS TESTS (bartosz branch)

| test | result |
|---|---|
| 1022-protein ensemble, 13 ops × 17 scores + veto | **no arm clears more than 5 of 276 families**; quantum vs classical **McNemar p = 1.0** |
| blind validity rule | 2 of 7 mandated/recommended pass; **49%** over 63 independent pairs |
| cryptic vs distal, 1233 proteins | 23% of allosteric sites and 7% of drug-contact pockets are distal; **cryptic datasets median hop = 0** |
| apo contamination audit | 3 of 7 targets ligand-held open; **40 of 40 ASBench** carry a ligand at the scored site |
| converged CTQW, distance-conditioned | 0.5921 → **0.5184, not significant** |
| chiral walk (Peierls phases) | **0.4960 — below chance** |
| ENAQT engineered dephasing | relaxes to the classical/proximity limit |
| spectral coherence / entanglement entropy | 0.5226 / 0.4903 |
| **coherent vs decoherent toggle** | **+0.0023, Wilcoxon p = 0.92, cluster-robust p = 0.83** — well-powered null |
| distance-proxy ordering | classical diffusion 0.953 → decoherent 0.735 → **coherent 0.692** |
| centrality ablation (105 structures / 74 proteins) | ρ median **0.41**; beats degree/eigenvector/GNM, ties betweenness/closeness |
| spatially matched pocket-block null | BH-FDR survivors **45/110 → 0/110** |
| convergence check on propagation time | **50 of 108 structures flip verdict sign** between T=15 and converged |
| hardware | **169–704 qubits**, 3.3M–124.9M two-qubit gates; coarse-graining to 10–15 qubits destroys the signal; every mandated target `FAULT_TOLERANT_ONLY` |
| mandated targets | KRAS 0.514, BCR-ABL1 0.541, myosin 0.548 — all `NO_SIGNAL_IN_APO` |

---

## PART 3 — WHERE WE AGREE

**Eight points.** Each measured independently, on different cohorts, reaching the same conclusion.

*(An earlier version of this file listed "same pipeline architecture" as a ninth agreement. That
was wrong and is corrected below: the pipeline SHAPE is shared — candidate detection → CTQW →
veto — but the candidate detector differs, PASSer vs fpocket, which changes which residues are
scored. It belongs in Part 4.4, not here.)*

| point | allosteric | bartosz |
|---|---|---|
| **the walk does not beat distance** | blind LOFO on distal, **raw** AUC **0.500** | **residualised** AUC (distance removed) **0.5184**, n.s. |

> **Read that row carefully — the two numbers are different quantities.** Mine is a raw AUC on the
> distal cohort with the cell chosen blind: the walk is at chance before any correction. His is a
> residualised AUC on 108 structures: once distance is regressed out, nothing remains. Both support
> the same conclusion by different routes, and his is the stronger statement. They are not
> interchangeable and should not be quoted as one number.
| **centrality ablation verdict** | beats degree/eigenvector/GNM, **ties closeness & betweenness** | same verdict, same wording |
| **JACS ρ≈0.95 does not replicate** | ours **0.689** | his **0.41** |
| **best-of-N is not a score** | sweep 137 families, **99.8 from chance** | retracted a headline after the same realisation |
| **classical stages do the localisation** | unconstrained: closeness 48 → **6 proteins** | "the classical stages carry the signal we can currently certify" |
| **Table 1 defects** | 6C1H no mavacamten; 4OBE wild-type | same two, reported to organisers |
| **family-level counting is mandatory** | CAS0002 = 28 of 91 distal | four selection procedures died of pseudo-replication |
| **no quantum advantage demonstrated** | not a quantum-advantage claim; classically simulated | no asymptotic speedup claimed |

---

## PART 4 — WHERE WE DISAGREE

### 4.1 The one substantive disagreement: does coherence contribute?

| | measurement | result |
|---|---|---|
| **his** | `coherent=True` vs `coherent=False` on the **converged** propagator | **+0.0023, p = 0.92** — null |
| **mine** | `2·Re⟨r\|e^{−iHτ}\|a⟩` at **finite delay** | **+0.107, p = 0.007** on distal |

**This may not be a real disagreement.** His propagator is *provably phase-free* — his own
TASK-0157 derived that time-averaging integrates the cross-term to zero. So zero is the expected
answer for his observable. Mine keeps the phase.

**His open objection, which is legitimate and unresolved:** the integration window is set by 1/gap,
and he has measured that **46% of structures flip verdict sign** with the clock. My result lives
inside that unstable band.
**My counter, measured:** the sign came out inverted in **53 of 53 folds**, and 80% of proteins fall
below 0.5 — so it is not per-fold sign-fishing. That does not answer the clock objection.
**Resolution agreed:** rerun at a principled per-protein τ with the sign pre-registered.

### 4.2 Framing, not measurement

| | his position | mine |
|---|---|---|
| what to conclude | *"single-particle coherent transport on a static contact graph is exhausted"* | the **phase-free** construction is exhausted; one finite-delay route is untested |
| Phase 2 deliverable | a certifying benchmark | the benchmark **plus** a named quantum route |
| reporting +0.114 | not as a result | agreed — name it as the Phase-2 route |

### 4.3 Not disagreements, just gaps

| | allosteric only | bartosz only |
|---|---|---|
| | unconstrained test | benchmark validity audit |
| | AI recommender negative | convergence check (46% sign flip) |
| | null-corrected family counts | hardware resource analysis |
| | two-source observable | spatially matched pocket-block null |
| | 13-baseline comparison at 630 scale | apo contamination audit |

### 4.4 The blocking issue — not a disagreement, a decision

| | allosteric | bartosz |
|---|---|---|
| candidate pockets | **PASSer top-10** | **fpocket** |
| families | **399** | **276** |
| coherence cohort | 630 (91 distal) | 108 structures / 76 clusters |

**"20 of 399" and "5 of 276" are not the same measurement.** Until one cohort is fixed, neither
branch can verify the other, and a reviewer who finds two numbers from one team discounts both.

---

## PART 5 — AGREED NEXT STEPS

1. **Fix one cohort.** PASSer or fpocket; 399 families or 276. Blocks everything else.
2. **Replicate the two-source result** at a principled per-protein τ (`min_adequate_t_max`), sign
   pre-registered from a physical argument, on the agreed cohort.
3. **+0.031 stays on hold** pending a spectrally-matched control.
4. **Do not report +0.114 as a result.** Name the finite-delay phase-sensitive observable as the
   concrete Phase-2 quantum route, with its ceiling stated honestly.
5. **One document.** Two submissions from one team is the largest remaining risk.
