# Adversarial Panel Review — Quantum Allosteric Scanner

**Date:** 2026-07-25 · **Deadline:** 2026-09-15 (7 weeks) · **Reviewers:** Computational Biophysicist · Protein Dynamics · Structural Biology · Quantum Computing · Hamiltonian Engineering · Drug Discovery · Nature/Science Referee

**Basis:** full repository read (516 files), `RESULTS.md` (252 KB), `EXECUTION_PLAN.md` (145 KB), `COMPETENCE_MAP.md`, `physics.md`, `ceiling.md`, `ALGORITHM_REGISTER.md`, all 155 TASK files, `src/allostery/*`. Test suite executed: **897 passed, 16 failed, 13 skipped**. All 16 failures are missing optional dependencies (`ripser`, `optuna`), not logic failures. **One new adversarial experiment was run against the code** — see §2.3, it is the most consequential item in this review.

**Provenance note, added 2026-07-25 (Architect/Planner, additive, original text below unchanged):** this review's "TASK-0154 (two-boson HOM)" (§4, §7.2(a)) referred to a task filed the same day by `REVIEW-2026-07-23-register-hygiene-and-p12-gate.md`, which collided with an unrelated, already-Done TASK-0154 (a tooling gate) and has since been renumbered to **TASK-0157**. Same task, same scope, no content changed — see that task file's own provenance note.

---

## 0. One-paragraph verdict

This is the most methodologically disciplined negative-result program I have reviewed in this domain. The falsification apparatus is real, executed, and repeatedly turned on the team's own claims — four separate headline positives have been retracted by the team's own subsequent work, each time with the superseded numbers preserved rather than overwritten. That discipline is the submission's genuine asset. **But the program's one surviving flagship positive (`dcc_low`, cross-target replicated on CARDIAC_MYOSIN and PTP1B) rests on a permutation null that I have now demonstrated to be anti-conservative by a factor of 5–40× for exactly the kind of label it is applied to.** Correcting that is a two-day job and it must happen before anything is written. Separately, the shipped deliverable pipeline (`run_challenge.py`) has silently diverged from the corrected science and currently emits a "quantum connectivity matrix" that contains no quantum computation. With seven weeks left and no proposal draft in existence, the binding constraint is writing — but two of these defects are load-bearing on what can honestly be written.

---

## 1. Current scientific status

### 1.1 What is demonstrated and evidence-supported

**Negative results, well-evidenced and reproducible.** These are the program's real output and they are solid:

| Claim | Status | Strength of evidence |
|---|---|---|
| The whole program lives in a single-particle Hilbert space of dimension *N*; every scored observable is one `eigh()` | **Verified directly in code** (`time_averaged_ctqw_converged` = Σ_k \|v_k(j)\|²\|v_k(s)\|²) | Anchoring theorem. Correct. Bounds every advantage claim in the submission |
| Seeded-walk occupation is a proximity-to-seed detector, not a communication measure | Strong — ρ(score,−hop) 0.43–0.97 across operators; a disorder-free bare Laplacian reproduces it | Confound lives in the observable, not the operator. Correct and important |
| Coherence does not improve pocket discrimination | Very strong — 3 independent routes (HYP-P7 flat γ-sweep; TASK-0105 ENAQT transport↑ but AUC↓; TASK-0141 pre-registered NEGATIVE on 3 targets, p=0.649/0.211/1.000) | Publication-grade negative |
| No mandatory target's shipped result is a statistically decided win over its own proximity floor | Strong — every CI overlaps its floor after four successive gauge corrections | This is the headline and it is honest |
| ENAQT is not more NISQ-noise-robust than coherent CTQW | Real negative (TASK-0068), contradicts the team's own hoped-for story | Discharges the noise-resilience secondary objective with a mechanism |
| Chiral/broken-TRS circulation is proximity-orthogonal but does not clear the bar | Confirmed 7/7 targets for orthogonality; FAIL on pre-registered CI criterion | Good physics, honest reporting |
| Cryptic pockets are not persistent-H2 voids at Cα resolution | FAIL 3/3; CARDIAC_MYOSIN detects the *wrong* void (AUC 0.192, null percentile 0.0) | Clean, informative kill |
| Graph-openness premise (near-in-3D / far-on-graph) | 0/7 targets pass | Kills the HYP-P9/P12 loop family at the premise |
| Real pockets are far more spatially compact than random same-size subsets | Discovered incidentally (TASK-0143: 0–19 of 500 matched replicates at 20M attempts) | **Under-exploited — see §2.3. This is the most important thing the project has found and it was filed as a footnote** |

**Benchmark-integrity findings.** Still the most defensible and most under-reported content in the repository: BCR-ABL1's myristoyl pocket moves *less* than background (ratio 0.49) — it is pre-formed, not cryptic; 5TBY was a 20 Å cryo-EM IHM homology model with non-crystallographic B-factors and a cross-species mismatch against its own holo; KRAS Switch-II/active-site overlap is documented. A referee will value this more than any AUC in the document.

**Engineering.** 897 passing tests, structured epistemic tagging, invariance/seam protocols, supersession discipline with no silent overwrites, permutation nulls and block-bootstrap CIs wired into headline numbers. This is better than most published computational-biology work.

### 1.2 What remains speculative or unsupported

- **`dcc_low`'s cross-target positive.** Currently framed as "the most robustly-evidenced positive result in the project." §2.3 shows the supporting p-values are computed against an invalid null. **Treat as unsupported until re-tested.**
- **`prs_low` on CARDIAC_MYOSIN** (p=0.006, holo-diagnostic "near-information-ceiling"). Same null defect. Also single-target — explicitly failed to generalize to PTP1B/CASPASE7.
- **BCR-ABL1 `T(E=0)` on the bare Laplacian** (AUC 0.699, p=0.003, Bonferroni-surviving). This one uses whole-graph AUC with a scattered null, so it is less exposed than the stratified results — but it **failed to generalize** (PTP1B AUC 0.382, *opposite direction*). Single-target, on a target whose pocket is pre-formed. Most likely explanation: `T(E=0)` on a bare Laplacian is a graph-centrality measure, and BCR-ABL1's pre-formed pocket is centrally located. Not evidence of allosteric communication.
- **KRAS ceiling headroom** (p=0.045 uncorrected, 0.135 Bonferroni). One target, one statistic, does not survive correction.
- **"Ceiling exists in the operator family."** Killed for CARDIAC_MYOSIN by TASK-0131 (55th percentile of pure noise). Inconclusive for BCR-ABL1. Plausible only for KRAS.
- **Every quantum-advantage claim.** Correctly labeled forward-looking throughout. Nothing demonstrated.

### 1.3 The one-line status

> A rigorous, multiply-confirmed negative result, with a falsification apparatus strong enough to have killed four of the team's own positives — and one surviving positive whose statistical support does not withstand the audit in §2.3.

---

## 2. Strengths and weaknesses

### 2.1 Biggest strengths

1. **The apparatus kills its own results.** TASK-0118 → 0129 → 0130 → 0124 is four independent gauge/structure corrections, each of which removed a positive the team had been carrying. Very few groups do this. It is the submission's thesis.
2. **Gauge discipline.** Identifying seed cardinality, propagation clock, and structure choice as *gauges* — quantities that must be declared, not chosen — is genuinely good methodology, and each was found to flip signs.
3. **Pre-registration.** TASK-0141/0142/0143 were filed with acceptance criteria *before* execution, and reported against those criteria even when they failed. TASK-0141's classical-limit sanity gate failed as literally specified and was root-caused (Zeno suppression) rather than quietly reinterpreted.
4. **Closed-form elimination of a parameter.** Replacing finite-*t* CTQW with the exact infinite-time limit removed an entire class of unanswerable questions rather than answering them badly. That is the right instinct.
5. **Negative controls that construct genuine conflict.** The dumbbell construction (well-depth vs. coupling) is a real double-dissociation design, not a sanity check.

### 2.2 Biggest weaknesses

**W1 — The permutation null is invalid for spatially compact labels.** See §2.3. Affects TASK-0123, 0133, 0139, 0142, 0149, 0151, 0152. This is the single most consequential defect.

**W2 — The shipped pipeline and the reported science have diverged.** `scripts/run_challenge.py` still hardcodes `T_MAX = 15.0`, `N_STEPS = 500` (lines 100–101) and calls `time_averaged_ctqw`, not `time_averaged_ctqw_converged`. Every corrected headline number lives in standalone scripts that deliberately "do not touch live pipeline defaults." So the artifacts a judge would receive are generated under a convention the project's own TASK-0110 documents as 145,000×–3,950,000× too short, and which TASK-0146 showed *flips KRAS's floor-clearing verdict*. The competence map describes a pipeline that does not exist as shipped.

**W3 — The "connectivity matrix" deliverable contains no quantum computation.** Challenge §5 requires "an N×N matrix where entry (i,j) represents the calculated **quantum** connectivity strength between residue i and residue j." What is written to `connectivity_matrix.npz` is `edge_propensity_to_matrix(edge_propensity(H_new, active_idx))` — a **classical current-flow linear solve**, **seeded at the active site** (so not an all-pairs property), and **non-zero only on contact-graph edges** (so not a dense N×N connectivity). It fails the deliverable on three counts. The fix is nearly free: `time_averaged_ctqw_converged` already computes P_∞(i,j) = Σ_k \|v_k(i)\|²\|v_k(j)\|², which *is* a genuine, symmetric, dense, all-pairs, quantum-defined connectivity matrix from one eigendecomposition.

**W4 — Program-level multiple comparisons are unaccounted.** Individual tasks apply Bonferroni within their own family. Nobody has accounted across the program. Conservatively: 96-cell operator sweep + 24-cell lowmode grid + 22-cell generalization grid + 9 transport cells + 7-target chiral + 7-target closure + 3-target ENAQT×8γ + H2, spectral, entanglement, transfer-entropy, co-participation, percolation… **on the order of 200+ scored cells against ~7 answer keys.** At α = 0.05 that predicts ~10 spurious "significant" cells. The project currently reports 3–4 surviving positives. **The number of positives found is not clearly in excess of what the testing volume alone would produce.** This is uncomfortable but it is the honest reading, and stating it explicitly is stronger than having a referee compute it.

**W5 — The generalization set is being consumed.** TASK-0115 correctly identified repeated-exposure risk and TASK-0081/0127 mitigated it. But PTP1B/CASPASE7 have now been scored twice (TASK-0127, TASK-0151) and PTP1B is now cited as *confirmatory evidence* for `dcc_low`. A held-out set used to confirm a hypothesis is no longer held out. There are 7 unresolved ASD configs in `targets.yaml` — freeze 3 now and do not look at them until the final check.

**W6 — Block bootstrap blocks on the wrong axis.** `metrics.block_bootstrap_ci` blocks along residue *index* order (i.e., sequence), with `block_size=10`, to "preserve local spatial correlation." But the dependence structure that matters is **3D spatial**, and pockets are spatially compact while being sequence-scattered. The CIs therefore do not capture the actual correlation structure. This makes the negative conclusions *safer* (real CIs would be wider) but makes any positive less safe. Same root cause as W1.

**W7 — Only one published classical allosteric predictor has been benchmarked.** GNM transfer entropy (TASK-0132) is the sole external classical comparator. `ALGORITHM_REGISTER.md` rates PocketMiner, ProteinLens, and fpocket at 4 and none was run. The challenge scores "Comparison to classical analogs." A referee will ask why a program that ran ~40 quantum observables ran one classical baseline.

**W8 — Benchmark deviation on CARDIAC_MYOSIN.** The challenge Table 1 mandates 5TBY → 6C1H. The repo uses 8QYP → 8QYR. The scientific justification is excellent and verified. But it is a deviation from the specified benchmark and must be argued explicitly and prominently, not buried in a task file — otherwise it reads as target-shopping, which is precisely the accusation the rest of the methodology is designed to preempt.

### 2.3 NEW FINDING — the permutation null is anti-conservative by 5–40×

**This is the most important item in this review. It was not previously known to the project.**

Every null in the repository draws `rng.choice(N, size=pocket_size, replace=False)` — a **uniformly scattered** random subset. This is called a "random-patch null" in TASK-0133 and downstream, but it is not a patch; it is a scatter. Real pockets are **spatially contiguous**. TASK-0143 discovered this exact fact independently ("real pockets are far more spatially compact than typical random same-size subsets") and filed it as an interesting aside. Its implication for every *other* null in the program was never drawn.

**Why it matters.** The scored observables (`dcc_low`, `prs_low`, low-mode GNM covariance) are *smooth spatial fields*. A contiguous patch has correlated scores across its members; a scattered set does not. Under distance stratification the effect compounds: a compact patch concentrates its positives into one or two hop shells, so the well-powered shell contains many mutually-correlated positives, and the statistic reported is a **maximum over shells**.

**Measured on a protein-like globule (N=500, pocket=14, seed=8 residues) using the project's own `dcc_low`, `stratified_auc`, `hop_from_seed`, and `_well_powered_max`:**

| Nominal α | Fraction of **pure-null compact** pockets the repo's scattered null calls significant | Inflation |
|---|---|---|
| 0.05 | 0.2420 | **4.8×** |
| 0.0167 (3-target Bonferroni) | 0.1320 | **7.9×** |
| 0.0083 (TASK-0151 transport α) | 0.1100 | **13.3×** |
| 0.0031 (TASK-0151 lowmode α) | 0.0740 | **23.9×** |
| 0.001 | 0.0420 | **42.0×** |

**Negative control (essential):** repeating the identical procedure with a spatially *uncorrelated* white-noise score gives inflation of **0.1× at α=0.05 and 0.0× at every tighter threshold** — i.e. no inflation at all, slightly conservative. The effect is therefore caused by the interaction of *spatial autocorrelation in the score field* with *compactness of the label*, exactly as predicted, and is not an artifact of the test construction.

**Mechanism, confirmed directly:** a compact patch places **67%** of its residues in a single hop shell; a scattered patch places **34%**. Doubling the count of mutually-correlated positives inside the shell that gets selected by the max is what drives the tail.

**Consequence for the flagship result.** `dcc_low` reports p<0.001 on CARDIAC_MYOSIN and p=0.001 on PTP1B. Under a correctly-specified compact null, **~4% of pure-null compact pockets reach that threshold.** Two independent targets both reaching it is roughly 0.04² ≈ 0.0016 if independent — still notable, but nothing like the joint p ≈ 10⁻⁶ the current framing implies. The result moves from *"the most robustly-evidenced positive in the project"* to *"suggestive, marginal, needs a correct null."* It is not dead. It is not established either.

**Reproduce:** `null_audit.py`, `null_audit2.py` (attached). Runtime ~15 min on one core.

**Fix:** replace `rng.choice(...)` with a spatially contiguous draw — pick a random seed residue, take its *k* nearest neighbours by Euclidean distance (`compact_patch()` in the attached script is 4 lines). Optionally match the real pocket's radius of gyration. Then re-run TASK-0149, 0151, 0142, 0133/0139/0152. This is a two-day job and it is the highest-value two days remaining in the program.

### 2.4 Hidden assumptions worth surfacing

- **Allostery as a directed channel from the active site.** Every observable seeds at the active site and asks where signal goes. Challenge ref [4] (Motlagh/Hilser 2014, *Nature*) argues allostery is **ensemble redistribution**, not signal transmission. The project has never tested the ensemble framing, and never tested the **reverse direction** (seed at the pocket, measure coupling into the active site) — which is the direction that actually matters therapeutically and which is what allosteric experiments measure. These are not symmetric under a non-normal operator or a multi-residue incoherent mixture.
- **The crystal structure is the relevant conformer.** Both apo and holo are energy minima; the transition path between them need not pass through either. Noted in `ALGORITHM_REGISTER.md` §G but never operationalized.
- **The pocket label is ground truth.** It is a 4.5 Å ligand-contact shell in the holo structure. TASK-0114 showed `classify_failure`'s diagnosis flips for 2/3 targets at the grid edges. The label is a proxy, and its uncertainty is not propagated into any CI.
- **H_new has physical meaning.** It does not, in any strict sense. There is no ħ, no energy scale, no temperature. Site energies come from B-factors and GNM mode participation via heuristic z-scored combination. "Quantum" here means "we exponentiate *i* times a symmetric matrix on a graph." The project knows this; the submission must own it in the first paragraph rather than let a referee find it.

### 2.5 Overfitting exposure

Honestly, this is **better controlled than in most such projects** — the ceiling is explicitly labeled as intentional overfitting, label leakage via Optuna was identified and corrected, TASK-0131's permutation null was built specifically to detect winner's-curse in the ceiling, and TASK-0138 applied it to H14 and killed that margin too. The residual exposure is: (i) the null defect in §2.3, (ii) program-level multiplicity (W4), (iii) generalization-set consumption (W5). None of these is a *tuning* problem — they are *selection* problems, which is the harder kind to see.

---

## 3. Scientific assessment

### 3.1 Biological validity — **weak-to-moderate**

The elastic-network premise is granted by the challenge itself, so it is legal. But three biological gaps stand out. First, the ensemble/entropic mechanism (challenge ref [4]) is entirely untested, and it is the mechanism most relevant to cryptic pockets — a cryptic pocket exists because the *ensemble* contains conformers where it is open, not because a signal travels there. Second, direction: allosteric coupling is measured pocket→active-site in experiment and never tested that way here. Third, benchmark heterogeneity: the three mandatory targets are mechanistically incommensurable — a cryptic pocket that forms on binding (KRAS), a pre-formed pocket (BCR-ABL1, ratio 0.49), and a mechanical/motor site in a large multi-domain protein (myosin). Averaging performance across them is meaningless; the per-target competence-map framing is exactly right and should be defended as a methodological contribution.

*Drug Discovery Scientist:* the pharmacological framing is sound and the benchmark-integrity findings would be genuinely useful to a medicinal chemistry team. The top-5 hit list, however, is not actionable in its current form — no druggability, no cavity volume, no consideration of whether the site is synthetically addressable. `fpocket` is rated 4 in the register and was never installed.

### 3.2 Physical validity — **strong on rigor, weak on physical grounding**

The physics that is present is done correctly and self-critically. Correctly identified: `heat` on an indefinite H_new is imaginary-time ground-state projection, not diffusion (and the code *warns* at runtime — I saw the warning fire during the test run); only flux around cycles is gauge-invariant, so an arbitrary initial phase is a label-leaking knob; the converged CTQW is provably phase-free; Anderson localization is genuine at finite *t* and washes out at the converged limit; non-interacting fermions reduce to a determinant and are classically trivial.

The weakness is that H_new is not derived from any molecular Hamiltonian. This bounds the strongest possible claim to: *"a family of graph operators, one of which is unitary, applied to protein contact topology."* That is defensible if stated. It is indefensible if implied otherwise.

*Hamiltonian Engineering:* the variance-budget fix (TASK-0121, V_R 88.8% → 15.4%) was necessary and correctly diagnosed the earlier "V_R is most impactful" claim as a normalization artifact. But the diagonal potential remains five heuristic terms with five weights, and HYP-P2 (the off-diagonal pairwise term — the first addition unreachable by *any* diagonal-only operator) has still never been built. That is the one architectural gap the operator sweep cannot close by searching harder.

### 3.3 Statistical validity — **the weakest dimension**

Strong: block-bootstrap CIs, permutation nulls, pre-registration, distance stratification, well-powered-shell filtering (correct — a single-positive shell hitting AUC 1.000 is not a result), max-over-shells correctly folded into the null replicate loop, honest dual reporting of primary and maximally-conservative Bonferroni families.

Weak: the null itself is misspecified (§2.3); program-level multiplicity is unaccounted (W4); bootstrap blocking is on the wrong axis (W6); the held-out set is being consumed (W5); label uncertainty is not propagated.

*Nature/Science Referee:* the paper I would want is *"Why topology-only allosteric-site prediction fails, and how we proved it on ourselves."* With the null fixed, that paper is publishable in a methods venue. With the null unfixed and `dcc_low` presented as a positive, I would ask for the compact-null control in the first round and the paper would come back much weaker. **Fix it before you write, not after a referee asks.**

### 3.4 Computational validity — **strong**

897 tests pass; the 16 failures are missing optional deps only. Determinism was tested and confirmed to 14+ significant figures (TASK-0135), correctly refuting an earlier BLAS-nondeterminism hypothesis and tracing the real cause to a stale cached object. The Sherman-Morrison reduction in `transport.py` (O(N⁴) → O(N²) for all-candidate Landauer transmission, verified against brute force to 1e-10) is a genuine algorithmic contribution worth a line in the proposal.

The one real defect is W2 — the shipped pipeline is stale relative to the corrected science.

---

## 4. Next steps, in execution order

Seven weeks. No draft exists. Analysis capacity should be spent on things that change what can be *written*, and nothing else.

**Week 1 — Repair the load-bearing defects (do not skip; these change the claims)**

1. **Fix the null and re-run every affected result.** (2 days) Compact/contiguous draw, optionally radius-of-gyration-matched. Re-run TASK-0149, 0151, 0142, 0133/0139/0152. *Why first:* it determines whether the submission has a positive to report at all. Every downstream writing decision depends on the answer.
2. **Re-point `run_challenge.py` at the corrected convention.** (½ day) Swap `time_averaged_ctqw(T_MAX, N_STEPS)` → `time_averaged_ctqw_converged`, delete the two constants. *Why:* the artifacts a judge sees must match the science the document reports.
3. **Replace the connectivity-matrix deliverable.** (½ day) Emit dense P_∞(i,j) = Σ_k \|v_k(i)\|²\|v_k(j)\|² from the existing eigendecomposition. *Why:* it is a stated, scored deliverable that is currently non-compliant on three counts, and the fix is one function call.
4. **Compute and state the program-level multiple-comparison budget.** (½ day) Count every scored cell. Report it. *Why:* a referee will do this arithmetic. Doing it yourself converts a fatal criticism into a demonstration of rigor.

**Week 2 — Close the two cheap scientific gaps that a referee will name**

5. **Reverse-direction coupling test.** (1–2 days) Seed at the annotated pocket, score coupling into the active site, on all 7 targets. Uses existing machinery unchanged. *Why:* it tests a genuinely different biological hypothesis (bidirectional coupling), it is the direction experiments actually measure, and it is a real asymmetry test for the incoherent-mixture seed. Either outcome is publishable.
6. **Run PocketMiner and ProteinLens as external classical baselines.** (2 days, mostly waiting on web servers) *Why:* "Comparison to classical analogs" is explicitly scored. If they hit where you miss, your operator is the bottleneck; if they also miss, you have independent corroboration that the apo topology does not encode the answer — which is your thesis. Both outcomes strengthen the submission.

**Weeks 3–6 — Write.** The proposal is the deliverable. Six pages. Draft by end of week 4, internal review week 5, revise week 6.

**Week 7 — Buffer.** Do not plan work here.

**Explicitly deprioritized** (file, do not build before the deadline):
- **TASK-0154 (two-boson HOM).** It is the only genuinely non-reducible multi-particle residual and the only route out of the single-particle regime, but nothing in the single-particle register has cleared the proximity floor, and there is no reason to expect the two-particle coincidence observable to be proximity-orthogonal. Describe it in the forward-proposal section as the principled next rung. Do not spend two weeks on it.
- **TASK-0147 (vibronic/structured bath).** The most quantum-biology-grounded remaining idea and the only mechanism that could produce *site-selective* rather than distance-monotone enhancement. Highest implementation cost. Same treatment: propose, do not build.
- **Hodge-L1 half of TASK-0142.** Correctly gated; both gates are FAIL. Leave closed.

---

## 5. Validation strategy

### 5.1 Must-run before any claim is written

| # | Experiment | Falsifies / establishes | Cost |
|---|---|---|---|
| V1 | **Compact-null re-test** of `dcc_low`/`prs_low` on CARDIAC_MYOSIN + PTP1B | Whether the flagship positive survives a correctly-specified null | 2 d |
| V2 | **Program-level multiplicity budget** — enumerate every scored cell, report expected false-positive count | Whether the observed positive count exceeds chance expectation | ½ d |
| V3 | **Frozen held-out set** — resolve 3 unused ASD configs, run once, never again | Whether anything replicates on truly unseen labels | 1 d |
| V4 | **Spatial block bootstrap** — block on 3D neighbourhoods, not sequence index | Whether the CIs are correctly sized | 1 d |

### 5.2 High-value falsification tests

| # | Experiment | Why it discriminates |
|---|---|---|
| V5 | **Reverse-direction coupling** (pocket→active site) | Tests communication vs. ensemble framing; asymmetry is diagnostic |
| V6 | **Label-perturbation robustness** — jitter the pocket definition (4.0–5.5 Å) and propagate into the CI, don't just report verdict flips | Converts TASK-0114's sensitivity finding into an honest error bar |
| V7 | **Sequence-shuffled structure control** — same topology, permuted B-factors/residue identities | Isolates how much of any score comes from topology alone vs. the potential terms |
| V8 | **External classical baselines** (PocketMiner, ProteinLens, fpocket) | The one comparison the challenge explicitly scores and you have not made |
| V9 | **Ensemble/entropy observable** — per-residue conformational entropy contribution from GNM mode participation, no MD, challenge-legal | Tests the ref-[4] mechanism the whole program has ignored |

### 5.3 The falsification statement to pre-register now

> *"If a spatially-matched compact null removes `dcc_low`'s significance on both CARDIAC_MYOSIN and PTP1B, we report the program as a complete negative result across every observable tested, and the submission's contribution is the falsification apparatus and the per-target competence map, not a predictor."*

Write that sentence down before running V1. It is the difference between a result and a search.

---

## 6. Executive summary

### Five most important findings

1. **The program is a well-evidenced negative result** with an unusually strong falsification apparatus — four self-inflicted retractions of the team's own positives, each documented without overwriting the superseded numbers.
2. **The single-particle anchor is correct and verified in code.** Every scored observable is one `eigh()` on an N×N matrix. This bounds every possible advantage claim, and the project is right to say so first.
3. **The proximity confound is structural to the observable, not the operator** — no Hamiltonian escapes a seed-proximity correlation baked into the measurement. Correctly diagnosed and repeatedly confirmed.
4. **The flagship positive rests on an invalid null.** Newly demonstrated here: the scattered permutation null used across seven tasks is anti-conservative by 4.8× at α=0.05 and 42× at α=0.001 for compact labels on smooth score fields, with a clean white-noise negative control showing zero inflation. `dcc_low`'s cross-target replication is materially weaker than reported.
5. **The shipped pipeline has silently diverged from the corrected science**, and its "quantum connectivity matrix" deliverable contains no quantum computation and is not all-pairs.

### Five biggest risks

1. **Submitting `dcc_low` as a positive without the compact-null re-test.** If a referee runs the control, the submission's one positive collapses and the credibility of the surrounding rigor collapses with it.
2. **Program-level multiplicity.** ~200+ scored cells against ~7 answer keys predicts ~10 spurious positives at α=0.05. The project reports 3–4. State this yourself.
3. **Deliverable non-compliance.** The N×N quantum connectivity matrix is a *stated, scored* requirement and is currently not met. Cheap to fix, expensive to be caught on.
4. **Writing time.** Seven weeks, no draft, and a documented pattern of generating new analysis instead of writing. The September 15 deadline is the binding constraint and the repository shows 155 tasks and zero proposal pages.
5. **Benchmark deviation on CARDIAC_MYOSIN (8QYP/8QYR vs. mandated 5TBY/6C1H).** Scientifically justified and verified, but unless argued prominently and up-front it reads as target-shopping.

### Five highest-priority actions

1. **Fix the null; re-run TASK-0149/0151/0142/0133/0139/0152.** (2 days, week 1) — decides whether a positive exists.
2. **Re-point `run_challenge.py` to the converged closed form; emit a genuine dense P_∞(i,j) connectivity matrix.** (1 day, week 1) — deliverable compliance and pipeline/science coherence.
3. **Compute and publish the program-level multiple-comparison budget.** (½ day, week 1) — turns the strongest available criticism into evidence of rigor.
4. **Run the reverse-direction test and two external classical baselines.** (3–4 days, week 2) — closes the two gaps a referee will name first.
5. **Start writing on 2026-08-08 regardless of analysis state.** Freeze scope. Ship six pages.

---

## 7. What of the "quantum explains allostery" hypothesis remains verifiable?

The challenge's lead hypothesis: *"Quantum computers offer a unique advantage in simulating non-local correlations and interference effects, which are analogous to how biological signals propagate through a complex protein network."*

### 7.1 What has been tested and closed

| Route | Verdict | Evidence |
|---|---|---|
| Coherent CTQW beats classical diffusion for discrimination | **DEAD** | Flat γ-sweeps; converged limit provably phase-free |
| ENAQT / dephasing-assisted transport improves discrimination | **DEAD** | TASK-0105 (transport ↑, AUC ↓), TASK-0141 pre-registered NEGATIVE, 3 targets |
| ENAQT is more NISQ-noise-robust | **DEAD** | TASK-0068: coherent ties or beats at every depth/error point |
| Chiral / broken-time-reversal circulation | **FAIL on bar** (orthogonality confirmed 7/7) | TASK-0140 |
| Persistent H2 / topological voids | **DEAD** | TASK-0142: 3/3 FAIL, one detects the wrong void |
| Graph-openness premise (gates the loop family) | **DEAD** | TASK-0143: 0/7 |
| Entanglement entropy across a spatial cut | **DEAD** | TASK-0148: clean complete negative |
| Frequency-domain spectral coherence | **DEAD** | TASK-0146: ρ(score,−hop) = +0.68…+0.72, confounded |
| Landauer transmission vs. classical R_eff | **1 target, did not generalize** | TASK-0145/0151 |
| Grover, QML kernels, HHL | **Ruled out on complexity grounds** | Readout bottleneck; near-continuum condition number |
| Non-interacting multi-fermion walks | **Provably classically trivial** | Reduces to a determinant |

That is a genuinely comprehensive falsification campaign. **Roughly a dozen distinct routes tested; none survives.**

### 7.2 What genuinely remains unverified

**(a) Interacting multi-particle interference — the only real escape from dimension *N*.**
Two identical bosons with on-site interaction (TASK-0154, Bose–Hubbard *k*=2) live in a symmetrized space of dimension N(N+1)/2 ≈ 450k at N=950. The two-particle coincidence observable does *not* factorize into single-particle quantities when interactions are present — this is the one place where the Hilbert-space dimension argument genuinely breaks. **Still classically simulable at these sizes**, so it is a *modeling* claim, not an advantage claim, until N grows or k grows. Honest framing: *"the first rung of a ladder whose asymptotic behaviour is quantum, tested at the classically-verifiable bottom rung."* Prior: low — nothing suggests the coincidence observable is proximity-orthogonal, and proximity is what has killed everything else.

**(b) Structured-bath / vibronic resonance (TASK-0147).**
The single most interesting untested idea in the repository, and the one the panel has under-rated. All dephasing tested so far has been Markovian and **unstructured** — a single rate γ applied uniformly. Unstructured dephasing can only de-trap the walker *toward* classical diffusion, which is the proximity confound; this is why HYP-P11's prediction was correct and why every γ-sweep had to fail. A **structured** bath is qualitatively different: specific ANM modes resonantly coupled to specific site-energy gaps can enhance transport to a *particular* site rather than uniformly. That is the only mechanism proposed anywhere in this program that could plausibly produce a *site-selective*, non-distance-monotone score. The ANM modes are already computed. **This is the honest answer to "what would you do with more time" and belongs in the forward-proposal section as the named next experiment.**

**(c) QSVT / QSP spectral filtering.**
Rated 3 and never built — but note the coincidence: the project's *only* candidate positives (`dcc_low`, `prs_low`) both come from **restricting to the low-mode subspace**, and QSVT is precisely the quantum-native primitive for applying a spectral filter f(H). That is a coherent narrative: *"the allosteric signal, to the extent it exists, lives in the soft-mode band; QSVT is the quantum algorithm that isolates a spectral band with provably optimal query complexity."* It remains dequantizable at N ~ 700 with a readout bottleneck, so it is a proposal claim — but it is a *well-motivated* proposal claim tied to your own empirical finding, which is much stronger than a generic advantage assertion.

**(d) Quantum Betti / Hodge-Laplacian estimation (LGZ).**
The H2 half is now empirically dead as a *biological* signal at Cα resolution. The complexity-theoretic framing (regime-dependent BQP, partially dequantized by Tang and Gyurik–Cade–Dunjko; Jones polynomial at roots of unity is BQP-complete) survives as a *forward proposal only*, and should be labeled as such. Do not let it carry weight it cannot bear.

### 7.3 What remains unverified about *allostery*, independent of quantum

These are, in the panel's judgement, higher-expected-value than any remaining quantum route:

1. **The ensemble/entropic mechanism** (challenge ref [4], Motlagh & Hilser 2014). Completely untested. Per-residue conformational-entropy contribution is computable from GNM mode participation with no MD and is challenge-legal. If cryptic pockets are ensemble-entropic rather than signal-propagative, that *explains* the entire negative result mechanistically — and turns a null into a mechanism.
2. **Directionality.** Pocket→active-site coupling has never been computed. Cheap, uses existing machinery, tests a different hypothesis.
3. **Two-state ANM (challenge ref [15], rated 5 in your own register) and NMFF (rated 5).** The register's own build order begins with these and neither was ever built. A referee who reads your algorithm register will notice that the two methods you rated highest and the challenge itself cites are the two you did not implement.
4. **The pairwise off-diagonal term (HYP-P2).** The one operator extension unreachable by any combination of diagonal terms. Still unbuilt after ~40 observables were tested within the diagonal-only family.
5. **Whether allosteric-site prediction from apo topology alone is well-posed.** Your own evidence increasingly says no. If the compact-null re-test (V1) also comes back negative, that is your result — state it as a *positive scientific finding about the problem*, with the competence map and the falsification apparatus as the contribution. **A program that proves its own problem is ill-posed, and does so by trying forty ways to solve it and building the instruments that killed each one, is a legitimate and interesting scientific contribution.** That framing is available to you and it is strong. It becomes unavailable the moment you overstate a marginal positive.

---

## Appendix — reproduction

- `null_audit.py` — scattered vs. compact null on `dcc_low` and `prs_low`, protein-like globule, project's own machinery.
- `null_audit2.py` — tail-resolution version (2000 scattered / 500 compact replicates) with the white-noise negative control.

Both import directly from `__WORK_IN_PROGRESS__/src`. Adjust the `SRC` path if run elsewhere. Runtime ≈ 15 min single-core.
