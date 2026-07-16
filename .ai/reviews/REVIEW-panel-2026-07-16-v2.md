# Multidisciplinary Panel Review v2 — Quantum Allosteric Scanner (bartosz branch)

**Date:** 2026-07-16 (supersedes v1, 2026-07-16) · **Deadline:** Phase 1 ideation, 15 Sept 2026
**Panel:** Computational Biophysicist · Protein Dynamics · Structural Biology · Quantum Computing · Hamiltonian Engineering · Drug Discovery · *Nature/Science* referee

**What changed in v2.** This version reconciles v1 with a second adversarial review from another thread. Three of that review's findings are correct, load-bearing, and are now incorporated as primary conclusions (the potential-normalization bug; the observable-is-the-confound framing; the ceiling/floor seed-splice). Four of its claims overreach and are corrected here with executed evidence. All numbers tagged **[EXECUTED]** were re-run by this panel against the repo's own `src/allostery` code (synthetic constructions; no RCSB in this environment). Real-target numbers are **[REPO-REPORTED]**.

---

## 0. Verdict up front

The engineering and the falsification discipline remain the best this panel has seen in this domain. But two reviews now converge on the same structural conclusion, and it is more fundamental than "the operator is weak":

**The reported AUCs are not yet interpretable — as signal *or* as no-signal — because three physical units in the calculation are unfixed:**

1. **The seed** — one residue (a crash workaround) vs. the full active-site array. Worth ±0.3 AUC, and it moves the *floor* in lockstep with the score. [EXECUTED: single vs. array occupation Spearman only 0.61; [REPO-REPORTED] KRAS 0.78 scalar vs. 0.45 array]
2. **The clock** — `t_max = 15` is applied to every operator regardless of its energy scale, and at t=15 the walk has barely left the seed. [EXECUTED: bare disorder-free Laplacian still has most mass near the source at t=15]
3. **The potential's scale** — the five diagonal terms are not commensurate; the operator's "physics-informed" GNM/allostery terms contribute ~0.2% of the variance. [EXECUTED: V_R 88.8%, V_C 0.1%, V_M 0.1%]

Until these are fixed, "KRAS is a proximity detector" and "the ceiling is below the floor" are both **artifacts of the units**, not findings. **But so is the opposite claim** — the other thread's "you have a +0.042 positive you've argued yourself out of" splices two different runs and is equally unsupported. The honest state is **undetermined**, and four days of P0 work makes it determined.

One thing that is *not* undetermined, and is the deepest result here: **the confound lives in the observable, not the operator.** [EXECUTED] A bare, disorder-free normalized Laplacian, seeded at one residue, correlates with distance-from-seed at ρ = +0.83 at the operating point and never drops below ~0.5 at any time. **No Hamiltonian in the register can clear a proximity floor while the scored quantity is "occupation seeded at the active site."** The fix is a different observable, not a better operator.

---

## 1. Current scientific status

### 1.1 Demonstrated and reproduced (I re-ran these)

- **CTQW occupation ≈ distance-from-seed.** [EXECUTED] ρ(occupation, −hop) = +0.85; ρ(occupation, −Euclid) = +0.83 on a bare disorder-free Laplacian. Proximity confound confirmed, and confirmed to be a property of the observable.
- **GSR tracks the potential well, not active-site coupling.** [EXECUTED] Dumbbell double dissociation: C2 GSR 0.000 / CTQW 1.000; C3 GSR 1.000 / CTQW 0.000. Clean. BCR-ABL1's 0.7315 is correctly re-framed as a structural-prior signature.
- **The potential's variance budget is broken.** [EXECUTED] With default λ: V_R **88.8%**, V_T 8.5%, V_B 2.5%, **V_C 0.1%, V_M 0.1%**; ρ(V_R, −degree) = +0.81; disorder/bandwidth W/J ≈ 9.8. The two terms that carry the allostery rationale (GNM cross-correlation, slow-mode participation) are numerically inert.
- **ENAQT interior-γ optimum is real physics.** [EXECUTED] 5–33× transport ratio on a canonical disordered chain — but absolute transport at the optimum shrinks toward zero as disorder grows, which is why [REPO-REPORTED] it never improves AUC.
- **The phantom operators (H11/H12) are genuinely fixed.** [EXECUTED] No longer identical to H6 / the Laplacian.
- **`time_averaged_ctqw` is effectively decoherent.** [EXECUTED] Spearman 0.9998 to the true infinite-time limit at the operating t_max, though it is a *finite* average and retains ~2% residual coherence — the docs' "all phase averaged out by construction" is slightly overstated but practically harmless.

### 1.2 Real but mis-attributed (numbers real, claim wrong)

- **BCR-ABL1 GSR 0.7315** — real, floor-clearing, correctly narrowed to "structural prior." Added caution (both reviews): that narrowed claim still rests on **n = 1 target** and has never been benchmarked against fpocket/PocketMiner. It is an anecdote until ≥10 targets + an external baseline.
- **CARDIAC-MYOSIN 0.786 "floor-cleared"** — [REPO-REPORTED] the one surviving positive, and it rests on the worst structure in the set: apo **5TBY, a 20 Å cryo-EM IHM assembly / docked homology model** whose "B-factors" are not crystallographic and whose chain assignment is unverified against a 6-chain complex. The `LARGE_N_THRESHOLD` correction that promoted it from `INSUFFICIENT_RESOLUTION` to `NO_FAILURE_DETECTED` was itself correct, but it removed two wrong reasons for caution and left the right one load-bearing.

### 1.3 Speculative, unsupported, or refuted by the repo's own data

- **"KRAS is a proximity detector" / "the ceiling is below the floor."** Both are gauge-contaminated (§2.1) and cannot be asserted as written.
- **"You have a +0.042 positive you've argued yourself out of"** (other thread). Also unsupported — it splices an array-seeded ceiling (TASK-0046) with a floor from a different run (TASK-0093). The correct status of every floor/ceiling/actual comparison right now is **undetermined**.
- **"CTQW trapping mechanism" (REVIEW-13c/TASK-0106).** Partially a clock artifact (§2.2), but the localization itself is real and gauge-robust — see the correction below.
- **HYP-P8 (is the pocket even in apo?)** — still unmeasured.

---

## 2. The findings that change the picture (reconciled)

### 2.1 The seed is an unfixed gauge that moves the score *and* the floor — [EXECUTED + code-verified]

Two code paths seed the walk differently: `run_challenge.py:299` uses a **single** residue (`int(np.sort(active_site_idx)[0])`, a documented TASK-0090 crash workaround, *explicitly not a physics choice*); `ceiling_search_batched.py:117` uses the **full array**. [EXECUTED] Single vs. array seeding gives occupation Spearman only 0.61 and different AUC even on synthetic data; [REPO-REPORTED] the real KRAS swing is 0.78 (scalar) vs. 0.45 (array).

**The consequence for the headline is real:** `COMPETENCE_MAP.md` compares an **array-seeded ceiling (0.524)** to a **scalar-seeded floor (0.798)** and reports "ceiling below floor" as "the strongest evidence gathered." That comparison is invalid. **Agree with the other thread that this kills the negative claim.**

**But do not replace it with a positive claim yet.** The other thread's "ceiling 0.524 clears the array floor 0.482 by +0.042" splices TASK-0046 (ceiling) with TASK-0093 (floor) — two different runs, different cutoff/label context — which is the same cross-run splicing it (correctly) criticizes. Under a consistent array seed the shipped *actual* result is ~0.45, still **below** its ~0.48 floor. The defensible statement is: *"floor/ceiling/actual are currently incomparable across seed conventions; re-run under one convention before reporting any of them."*

**Why the seed matters mechanistically:** collapsing an 18-residue site to one point makes the occupation a purer distance-from-one-point map, inflating both the score and the proximity floor together. So the scalar seed manufactures the very confound it appears to reveal. **This is the single most important correctness fix, and no `INV-XXXX` record owns it.**

### 2.2 The clock is unfixed and short — but the trapping is real, not an artifact — [EXECUTED, corrects the other thread]

`t_max = 15` is hardcoded and applied to every operator regardless of its energy scale. **Agree** that this is (a) not comparable across operators and (b) too short: [EXECUTED] at t=15 a disorder-free walk still concentrates most of its mass near the seed (PR ≈ 9 of 169 residues), so nothing has equilibrated. TASK-0108/0109/0110 (convergence checks) are still TODO and are a precondition for the physics, not hygiene.

**Disagree** with the stronger claim that "the CTQW trapping mechanism is mostly a time-units artifact that dissolves under gauge-fixing." [EXECUTED] After normalizing each operator by its hopping scale and re-running, H_new stays strongly localized (PR **1.3 → 3.8** across t=15→1500) while the bare Laplacian spreads (**14.7 → 83.7**) and H10 spreads (**23.5 → 48**). The localization is **gauge-robust and real** — it is Anderson localization driven by the 7–10× disorder/bandwidth ratio the other thread itself established in its §2.4, which is a gauge-invariant quantity. Its own two sections are in tension; the executed data sides with "real localization." The correct statement: *the operators are not compared at equal effective time (fix the clock), and independently, H_new genuinely localizes because its disorder swamps its bandwidth (fix the potential).*

**Secondary — the PR reporting is confused, but not in the way claimed.** [EXECUTED] `_transport_participation_ratio` = 1/(N·Σp²), high = *delocalized*, and both REVIEW-13c and TASK-0106 use it (not `metrics.ipr`, contrary to the other thread). The real defect is that TASK-0106's *prose* reads a **higher** PR/N (0.299) as evidence the walk "stays markedly closer to the seed" (localized) — which is backwards for this metric. Right smell, wrong mechanism. Fix the narrative direction; the two documents are not using reciprocal formulas.

### 2.3 The confound is in the observable, not the operator — [EXECUTED, strong agreement]

The most important general result across both reviews. [EXECUTED] A bare normalized Laplacian with **zero disorder and zero potential**, seeded at one residue:

| t_max | occ on source | PR (residues) | ρ(occ, −dist) |
|---|---|---|---|
| 1 | 0.95 | 1.1 | +0.97 |
| 15 (operating point) | 0.26 | 9.3 | **+0.83** |
| 150 | 0.06 | 62 | +0.77 |
| 2000 | 0.05 | 83 | +0.67 |

**"Occupation of a walk seeded at a point" is a monotonically-decreasing function of distance from that point — for any operator, at any time.** A proximity floor is therefore not a bar this observable can clear; it is a proof that this observable is the wrong one. The programme's fix is a **different observable** (co-participation, ENAQT transport) and a **different evaluation** (distance-matched decoys), not a better Hamiltonian.

### 2.4 The "physics-informed" potential is one term, and it is degree — but the *output* is not degree — [EXECUTED, agree with correction]

[EXECUTED, agree] The variance budget is broken by a normalization mismatch: V_R is a sum of three z-scores (σ ≈ 1.9); V_C and V_M are max-normalized to [−1, 0] (σ ≈ 0.06), ~30× smaller. So λ_C and λ_M are unreachable knobs, V_R = 88.8% of the potential, and V_R correlates with node degree at +0.81. This retro-explains three "findings" the repo treated as physics: `most_impactful_term = V_R`, the ground state sitting on low-diagonal residues, and the failure to beat degree centrality. **It is a real bug and a real, honest engineering narrative: "our 5-term potential was 88% one term until we renormalized." Fixable by z-scoring all five terms and setting σ(V) ≲ 0.2·J.**

[EXECUTED, correction] The other thread's corollary — "H_new and the degree baseline are ~81% rank-identical by construction" — is true of the *diagonal* but **false of the output**. The actual CTQW occupation on H_new correlates with degree at only ρ = **+0.20**. The reported AUC is driven by **proximity** (§2.3), not by degree. These are two distinct confounds: degree contaminates the diagonal (real, fixable by renormalization), proximity contaminates the occupation (real, fixable only by changing the observable). Do not merge them — the dominant driver of the headline AUC is proximity, and renormalizing the potential will *not* by itself fix that.

### 2.5 `mode_coparticipation` was never built — and it only helps on a *clean* operator — [EXECUTED, agree with correction]

[EXECUTED, agree] REVIEW-13b §6 proposed it; grep confirms it exists nowhere. It is seed-dependent and not distance-monotone by construction — the right shape for an allosteric-channel detector.

[EXECUTED, correction] Its distance-confound depends entirely on which operator's modes it uses. On a **clean** normalized Laplacian, CP is the least-confounded observable in the register (|ρ| with distance ≈ **0.18**, vs. 0.28 for shipped CTQW in the same geometry). But on the **current disordered H_new**, CP inherits the localization and is *worse* than CTQW (|ρ| ≈ **0.50**). So CP is not a standalone fix — it is coupled to the potential renormalization (§2.4): build CP *and* fix the potential, or it buys nothing. And low distance-correlation is *necessary but not sufficient* to find a pocket; whether CP actually enriches for true pocket residues is untested and must be gated through the dumbbell matrix and real labels before it is claimed.

---

## 3. Strengths and weaknesses (net of both reviews)

### Strengths (the actual competitive edge)
1. **The falsification apparatus is the product** — proximity floor, dumbbell double-dissociation, permutation null, GAUGE/KNOB/SIGNAL protocol, "what else would produce this exact number?" This generalizes past the challenge and is the Innovation claim, not `H_new`.
2. **The 6C1H correction** — you proved the challenge's own Table 1 validation structure contains no mavacamten, against RCSB, with entities enumerated. Currently buried in a YAML comment; it should be a headline.
3. **Honest negatives reported as negatives** — ENAQT transport↑/AUC↓, coherent ≥ ENAQT under gate noise, 3133 Trotter steps, c-Myc as a principled ENM failure. Each is worth more to a Feasibility reviewer than a fitted AUC.
4. **Engineering** — 562 tests, unforgeable provenance, the indefinite-operator guard that fires live.

### Weaknesses (ordered by threat)
1. **Three unfixed gauges drive every headline** (seed ±0.3, clock, potential scale) — none registered as invariants; all discovered as by-products; none owned by a task.
2. **The observable is distance-confounded by construction** (§2.3) — no operator fixes it.
3. **The potential's GNM/allostery terms are numerically inert** (§2.4) — a normalization bug mistaken for a physics result.
4. **The one positive rests on the worst structure in the set** (5TBY, 20 Å docked homology model).
5. **No confidence intervals anywhere** — every reversal (0.779/0.798, 0.525/0.565, ceiling/floor) is a bare point estimate on 16–21 positives; a block bootstrap will likely collapse them into one interval.
6. **The scored deliverable is failing** — top-5 hit list misses the pocket even where AUC looks fine (BCR-ABL1 GSR: AUC 0.73, 0/5).
7. **The quantum content is a rigorous null** — negligible coherence, coherent ≥ ENAQT under noise. A virtue only if framed deliberately.
8. **Delivery gap** — the jury-facing app has no quantum layer 8 weeks out; the artifact/viz tasks (0083–0086) are all TODO, and the challenge scores 3D connectivity visualization explicitly.
9. **Reviewer-side overfitting** — ~15 review cycles over the same 3 answer keys; `frozen_context` gates the code, nothing gates the reviewers. The ASD generalization targets are the right mitigation and should become the reported result, not the appendix.

### Hidden assumptions (each load-bearing, each false or untested)
- `t` is comparable across operators — **false** (§2.2). · `t_max=15` is long enough — **false** (§2.3). · The active site is a point — **false, ±0.3 AUC** (§2.1). · A coherent equal-amplitude superposition over 18 residues is the right initial state — **never argued**; an incoherent mixture is the defensible object. · The five V terms are commensurate — **false, 88/9/3/0.1/0.1** (§2.4). · B-factors are comparable across a 1.8 Å crystal and a 20 Å docked model — **false**. · AUC over all residues is the right metric — **distance-confounded, and already shown to diverge from the top-5 deliverable**. · The pocket is in the apo topology — **untested (HYP-P8)**.

---

## 4. Scientific assessment (net)

**Biological — moderate, with one structurally-unfit target and one unasked question.** KRAS is a poor discriminator because the Switch-II pocket is built *from* the catalytic Switch-II region — active and allosteric sites overlap, so no method scores cleanly on it. BCR-ABL1 (~32 Å, distinct lobes) is the only clean demonstrator, and it is the one at chance. 5TBY at 20 Å cannot support a Cα contact graph. And the learnability question (HYP-P8) is prior to all of it: a cryptic pocket that opens on binding is, by definition, largely absent from apo topology, and KRAS is the textbook case. **If HYP-P8 holds for KRAS, "the apo graph does not encode this pocket" is a publishable, challenge-relevant finding that reframes the whole submission — and it is one afternoon of Kabsch + RMSD.**

**Physical — the operator is unsound as parameterized, and every defect is a renormalization, not a redesign.** Indefinite (guarded), disorder 7–10× the bandwidth (guaranteed localization), potential 88% one degree-correlated term, two inert GNM terms, a clock 100× too short and not cross-operator-comparable. None of this is fatal to *the idea* of a CTQW on a residue contact graph; all of it is fatal to *this parameterization*. The GSR spectral-filter analysis and the identification of ENAQT as the only surviving coupling-tracking line are correct.

**Statistical — the weakest dimension.** No CIs; point estimates on 16–21 positives; three headline reversals on margins of 0.019–0.047; severe multiple-comparisons exposure (96-cell sweep × 60-trial ceiling × ~15 review cycles × 3 answer keys) with no correction; AUC is not the deliverable's metric. Fix order: CIs → distance-stratified evaluation → held-out targets.

**Computational — high and honestly bounded.** The dense-eigh O(N³) wall, the coarse-graining that failed and was kept on record, the NISQ 3133-step/188k-gate measurement, and the correct XY-model encoding are all exemplary.

---

## 5. Next steps — strictly prioritized

**Sequencing principle:** you cannot interpret any number until the units are fixed. P0 is not cleanup; it is the phase in which your existing results become interpretable. Every P0 item is ≤1 day and each changes the sign or meaning of a shipped claim.

### P0 — this week
1. **Fix the seed gauge.** Fix TASK-0090's multi-index crash properly (don't route physics around a bug); declare **one** convention — the panel recommends an *incoherent mixture over the active-site residues* (a coherent 18-residue superposition asserts phase coherence with no biophysical basis); register it as an invariant; re-run floor/ceiling/actual under it; and **retract "ceiling below floor" — but report the result as `undetermined→recomputed`, not as a new positive.** *(1 day; reverses the central claim.)*
2. **Fix the clock.** Set `t*` per operator from its spectral gap (`t ≈ 1/Δλ`, the graph mixing time), or normalize `H` by its hopping norm before propagation; re-run the operator comparison. Expect the H10-vs-H_new *ranking* to shift, but expect H_new's localization to survive — report both. *(1 day; corrects REVIEW-13c/TASK-0106's framing.)*
3. **Run the learnability gate (HYP-P8).** Kabsch-superpose holo→apo; per-residue apo→holo RMSD at pocket vs. background; Tama–Sanejouand cumulative overlap of Δr on the apo ANM modes; classify each target learnable/cryptic-structural. *(1 day, no quantum; your own docs say it must precede the ceiling you already ran; it can convert KRAS from a failure into a finding.)*
4. **Wire `block_bootstrap_ci` into every headline AUC.** *(½ day; the function exists.)* Expect several reversals to become "indistinguishable," which is *more* defensible.

### P1 — weeks 2–4 (repair the physics, then re-measure)
5. **Renormalize the potential** — z-score all five terms; set σ(V) ≲ 0.2·J (weak, transport-preserving disorder); re-derive λ; **report the variance budget in the submission.** Then the ablation means something for the first time.
6. **Build `mode_coparticipation`** and gate it through the dumbbell matrix — but pair it with (5), since [EXECUTED] CP on the un-renormalized H_new is *worse* than CTQW. On a clean operator it is the least-confounded observable you have.
7. **Adopt distance-stratified evaluation** — score pocket residues against distance-matched non-pocket decoys (same hop-shell), not against all residues. This is the standard way to evaluate under a known confound and the only way an occupation-based signal *inside* a shell can become visible.
8. **Re-anchor or retire CARDIAC-MYOSIN** — find a real apo β-cardiac motor-domain crystal, or report it as data-limited. Do not build the only positive on a 20 Å docked homology model.

### P2 — weeks 4–6
9. **H13 (or its N×N projection) through the ceiling search** — your own docs call this required. 10. **Extend the ASD generalization set (2–4 unseen targets) and make it the reported headline.** 11. **Verify the c-Myc resnums against 1NKP numbering** — `keep_nucleic: true` means the hit list may be reporting DNA nucleotides; a referee will spot "residue 943" instantly. 12. **SE(3) invariance regression.**

### Delivery — in parallel from week 1
13. **TASK-0083 (artifact contract) → TASK-0085 (3D connectivity viz).** The challenge scores interpretability; the contract's `GO/NO/UNSTABLE + knob-spread` shape already accommodates "this AUC is geometry, not signal."

---

## 6. Validation strategy — how to falsify what remains

| Hypothesis | Falsification test | Kill criterion | Cost |
|---|---|---|---|
| Apo graph encodes the pocket | Learnability gate: apo→holo pocket-vs-background RMSD + Tama–Sanejouand overlap | Pocket RMSD ≫ background & low overlap → **unlearnable from apo; report as the finding** | 1 d |
| CTQW occupation measures communication | **Effectively falsified** (§2.3); formal test: distance-matched-decoy AUC on all targets | Stratified AUC ≈ 0.5 in every shell → **observable dead; switch to co-participation/ENAQT** | 2 d |
| H_new's potential adds signal | Renormalized ablation, both gauges fixed, λ swept 0→default | AUC decreases with λ → **potential is a transport-destroying confound; ship L_norm/weak-λ** | 2 d |
| ENAQT helps discrimination | **Already measured:** transport↑, AUC↓ in 3/3 optima | Settled — report as a clean quantum-specific negative | done |
| GSR is a cryptic-pocket prior | ≥10 ASD targets vs. fpocket **and** PocketMiner | Doesn't beat fpocket → retire; beats it → **this is your positive result** | 1 wk |
| Seed cardinality is a gauge | Sweep source = {1, k-subset, full, incoherent mixture} × 3 targets | AUC spread > 0.1 → **it is a SIGNAL, not a gauge; the pipeline has no defined initial condition** (current evidence: ≈0.3 → already failed) | 1 d |
| `mode_coparticipation` finds pockets | Dumbbell matrix + distance-matched-decoy AUC on renormalized operator | Fails the dumbbell or the decoy AUC → not the fix either | 1 d |

**Controls that must exist before any claim is final:** distance-matched decoys · bootstrap CIs on every margin · label-permutation null (extend to real targets) · the dumbbell matrix for every new operator · seed and t_max invariance · SE(3) invariance · held-out targets never seen by a review cycle.

---

## 7. Executive summary

### Five most important findings
1. **Every headline is currently gauge-contaminated — the negative *and* the "hidden positive."** "KRAS is a proximity detector" and "ceiling < floor" are seed/clock artifacts; the other thread's "+0.042 positive" splices two runs. True state: **undetermined until re-run under one seed and one clock.** [EXECUTED + code-verified]
2. **The confound is in the observable, not the operator.** A disorder-free Laplacian seeded at a point gives ρ(occ, −dist) = +0.83 and never below ~0.5 at any time. No Hamiltonian escapes it; the fix is a different observable. [EXECUTED]
3. **The "physics-informed" potential is 88% one degree-correlated term; its GNM/allostery terms are 0.2% of the variance** — a normalization bug, not a modeling choice, and fixable by renormalization. But it contaminates the *diagonal*, not the *output* (occupation↔degree ρ = 0.20) — proximity, not degree, drives the AUC. [EXECUTED]
4. **The trapping is real, not a units artifact** — gauge-fixed, H_new stays localized (PR 1.3–3.8) while a clean Laplacian spreads to 83; driven by its 7–10× disorder/bandwidth. Correcting the other thread here. [EXECUTED]
5. **The falsification apparatus and the 6C1H correction are the genuinely defensible contributions**, and both are under-sold — the negative-control template generalizes past this challenge, and proving the challenge's own validation structure is wrong is a citable result sitting in a YAML comment.

### Five biggest risks
1. **Shipping "ceiling below floor"** — a referee greps two files and finds the seed splice in ten minutes; it is more damaging than the original 0.779 because the document is framed as the honest correction.
2. **The one positive rests on a 20 Å docked homology model** (5TBY), flagged UNRESOLVED in your own config.
3. **No CIs** — the three reversals may be one interval; several corrections may have been noise-chasing.
4. **Delivery gap** — no quantum layer in the jury app 8 weeks out; interpretability/viz is explicitly scored.
5. **Symmetric over-correction** — the discipline that killed the false positive is now at risk of manufacturing a false negative; the answer to both is the same four P0 fixes, not more nihilism *or* more optimism.

### Five highest-priority actions
1. **Fix the seed gauge**, re-run floor/ceiling/actual under one convention, and correct `COMPETENCE_MAP.md` to `undetermined→recomputed`. *(1 d)*
2. **Fix the clock** (`t* ≈ 1/Δλ`) and re-run the operator comparison. *(1 d)*
3. **Run the learnability gate (HYP-P8).** *(1 d — the highest information-per-hour experiment available.)*
4. **Wire bootstrap CIs into every headline AUC.** *(½ d)*
5. **Renormalize the potential and build `mode_coparticipation` together** (neither works alone), gate through the dumbbell matrix, then re-run the ceiling. *(3–4 d)*

---

## 8. Strategic note

Phase 1 (15 Sept) is a ~6-page **ideation** proposal, weighted Relevance/Impact 25% · Innovation 25% · Feasibility 20% · Validation 15% · Hybrid 5% · Team 10%. Your executed evidence base already dominates the 35% (Feasibility + Validation) that most teams will fabricate — no competitor will have a proximity floor, a negative-control matrix, a measured 3133-step NISQ depth, or a proof that the challenge's own Table 1 is wrong.

The 50% at risk is Relevance + Innovation, where "our method is a proximity detector with no headroom" scores 2/5. The honest reframe both reviews support:

> *We built the falsification apparatus this problem requires and used it to kill our own first three results. In doing so we found that the field's default observable — walk occupation seeded at the active site — is a distance detector by construction, on any Hamiltonian. We propose the two observables that can escape it (mode co-participation; dephasing-assisted transport, for which we measured a real interior-γ optimum of 1.24–1.7× on real protein topologies), the evaluation that can score them (distance-matched decoys; per-target floor/ceiling/headroom with error bars), and the learnability gate that says in advance which targets are winnable at all. Here is the competence map.*

That is a 5/5 Innovation + Validation claim and it is **true** — provided co-participation and ENAQT are framed as the *hypotheses your Validation Plan will test*, not as results you already have. It needs the four P0 items and error bars. It does not need `H_new` to work.

**Do the four P0 items first. You will then know — rather than argue about — whether there is a signal.**
