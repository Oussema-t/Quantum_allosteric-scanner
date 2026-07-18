# **bartosz Adversarial Panel Review — Quantum Allosteric Scanner (** **<mark>)</mark>** 

**Repo:** Oussema-t/Quantum_allosteric-scanner @ b926516 (branch bartosz ) **Date:** 17 July 2026 · **Prior:** REVIEW-panel-2026-07-16-v2.md (in-repo), AuraQu_scientific_review_2026-07-15.md **Panel:** Computational Biophysics · Protein Dynamics · Structural Biology · Quantum Computing · Hamiltonian Engineering · Drug Discovery · Nature/Science reviewer **Read:** COMPETENCE_MAP.md , RESULTS.md , EXECUTION_PLAN.md , HOLO_DIRECTION_MODULE.md , ALGORITHM_REGISTER.md , SYSTEMS_allosteric_corrected_v2.md , .ai/reviews/* , 

src/allostery/{propagators,ceiling,potentials,hamiltonians,metrics,baselines,superpose}.py **Method:** read-only inspection **plus** original numerics run this session against real PDB structures ( probe4.py , attached; all output pasted verbatim, acceptance criteria pre-registered in the module docstring before running). 

## **0. Headline** 

**The team executed four of my five July-15 P0 items in two days, with retraction discipline I have rarely seen in a funded lab, let alone a hackathon team.** The seed gauge is fixed. The learnability gate is run. The potential is renormalised. The clock was measured — and the measurement is far better than my estimate was. 

**And the project has re-committed the exact error it just fixed, one level up.** The seed bug was two code paths, two conventions, one document comparing across them. The clock "fix" is the same thing: min_adequate_t_max ships two convergence criteria; TASK-0119/0129 propagate with time_averaged_ctqw while setting t* from the **ground_state_relaxation** criterion. I measured the gap on a real protein: **65,189×** . The current competence map — the project's central negative result, freshly recomputed and cross-validated across two code paths — is computed at a t_max its own check_convergence rejects by four to five orders of magnitude. Two code paths agreeing does not catch a shared convention error. That was the whole lesson of the seed bug. 

**And the one positive claim in the whole document does not survive a permutation null.** "Every ceiling clears its own floor (+0.122 / +0.090 / +0.064)" is the only nonnegative statement in COMPETENCE_MAP.md . The ceiling is a **maximum over 60 blind draws taken with the answer key in hand** — upward-biased by construction. I ran the identical protocol on random pockets: the null ceiling-minus-floor is **+0.044 to +0.072 (median), sd ≈ 0.05, max +0.15** . All three reported margins sit inside that. None reaches p < 0.05. 

**The escape from all of it is already written in your own docstring and nobody has implemented it.** propagators.py:375 states the infinite-time limit as Σ_k |v_k(j)|² |v_k(source)|² . I measured it: **10.7 ms vs 4.1 s, agreement 9.5e-05, Spearman 1.0000** . Six tasks (0108/0109/0110/0117/0119/0129) exist to manage a parameter that has an exact closed form. Delete the clock; don't choose one. 

## **1. Current scientific status** 

### **1.1 Demonstrated and evidence-backed** 

|**Claim**|**Evidence**|**Verdict**|
|---|---|---|
|Seed convention swings AUC by 0.326|TASK-0118, INV-0006, real re-run on 3 targets|**Solid.**Confirms my Finding 1;<br>magnitude larger than I estimated|
|"KRAS ceiling below floor" was a gauge<br>artefact|TASK-0118 — retracted, old numbers preserved|**Solid, and correctly retracted**|
|Shipped<br>t_max=15 is 145,000×–<br>3,950,000× short of convergence|TASK-0110: closed form + 200-trial Optuna agreeing<br>to 1.3–2.5%|**Solid, and far better than my "~100×"**<br>**estimate — see §6.5**|
|True convergence is computationally<br>infeasible by integration|TASK-0110: real call did not return in 2+ h|**Solid**|
|V_R carried 88.8% of the potential's<br>variance;<br>lam_C/<br>lam_M unreachable|TASK-0121|**Solid.**Confirms my Finding 4 (88%)<br>to the decimal|
|most_impactful_term = V_R was a<br>normalisation artefact|TASK-0121 ablation: flips to<br>V_B on both targets,<br>V_R becomes least impactful on KRAS|**Solid, and an excellent retro-**<br>**explanation**|
|All 3 targets are<br>LEARNABLE from apo|TASK-0120: CO(20) = 0.638 / 0.794 / 0.584; RMSD<br>ratios 2.27 / 0.49 / 1.32|**Solid — and it refutes my own**<br>**prediction (§6.5)**|
|Coherence contributes nothing<br>measurable|TASK-0099:<br>auc_range 0.0132 (KRAS), 0.0050<br>(BCR_ABL1)→<br>COHERENCE_NOT_SIGNIFICANT|**Solid**|
|ENAQT enhances transport but degrades<br>discrimination|TASK-0105: 1.24–1.70× on 3/6 cells, AUC degrades<br>in every observed case|**Solid — independently reproduced**<br>**this session, §3.2**|
|Coherent ≥ ENAQT under NISQ noise|TASK-0068, 10-qubit, 2 timescales|**Solid negative**|
|3,133 Trotter steps = 2–3 orders beyond<br>NISQ|TASK-0068, empirical|**Solid**|



|BCR_ABL1's GSR 0.7315 is a structural<br>~~prior, not coupling~~<br>**Claim**|TASK-0103/0104 dumbbell double dissociation<br>**Evidence**|**Solid; the best-designed control in**<br>**~~the repo~~**<br>**Verdict**|
|---|---|---|
|6C1H contains no mavacamten|RCSB-verified; 8QYR substituted|**Solid, and still under-sold**|
|Zero of five targets' shipped results clear<br>their floor|TASK-0129 + TASK-0081|**Solid**|



### **1.2 Claimed but not supported** 

|**Claim**|**Why it fails**|
|---|---|
|**"Real headroom exists in**<br>**H_new** **'s physical-scalar space for**<br>**all three targets"**(the ceiling clears the floor by<br>+0.122/+0.090/+0.064)|Fails a permutation null of the identical protocol. §2.1.**This is the only**<br>**positive claim in the document.**|
|The TASK-0129 competence map is computed under a<br>"fully corrected convention"|It is corrected for the seed and**mis**-corrected for the clock:<br>t* from the GSR<br>criterion, applied to CTQW propagation. Off by 65,189× on my<br>measurement. §2.2|
|t*= 127 / 123 / 198 are meaningful per-operator clocks|The gap they derive from is numerically unstable (the repo's own BCR_ABL1<br>flag: 0.0374 vs 0.1933, 5.2× from BLAS reduction order). §2.3|
|The ceiling search covers<br>H_new 's physical-scalar space|It samples λ∈[0,2]⁵— 12–25× outside the σ(V) ≤ 0.2·J budget TASK-0121<br>proved is required, i.e. mostly inside the localised phase TASK-0121 exists<br>to escape. §2.4|
|BCR_ABL1's short-<br>t_max optimum (0.5829) is "unexploited<br>headroom, a new finding"|It reproduces that target's proximity floor (0.5817) to**+0.0012**. It is the floor,<br>computed the long way. §2.5|



### **1.3 Still speculative** 

- HOLO_DIRECTION_MODULE.md is a **spec, not a result** — Step 2 (its own gate) is unrun. Same status HYP-P8 had on 15 July. Everything about the NISQ demo beyond TASK-0068's negative. 

- c-Myc: consensus residue 943, 3/4 operators. The resnum-plausibility question I raised on 15 July (1NKP numbering: Myc ≈ 353–437, Max ≈ 22–102; 943 falls in neither) **is still not addressed anywhere I could find.** 

## **2. The five findings that are new to this review** 

All measured this session on real structures. Code: probe4.py . Pre-registered acceptance criteria in its docstring. 

### **2.1 The ceiling's "+0.122" is what pure noise produces — and a stated methodology rule made this invisible** 

ceiling.py draws **60 blind random parameter sets** over 8 dimensions ( _PARAM_RANGES ), scores each against the true pocket, and reports the **maximum** . A maximum over K draws is upward-biased by construction; that is the winner's curse. 

I replicated the protocol exactly — same _PARAM_RANGES , same 60 draws, same floor stack ( degree / euclid_from_seed / hop_from_seed , max of three) — on 3MHT (N=327), with **randomly drawn pockets** (no signal, by construction): 

|n_pos  rep   floor  ceiling   margin|draw sd|
|---|---|
|16    0  0.6029   0.6409  +0.0380|0.0318|
|16    1  0.5886   0.6461  +0.0575|0.0362|
|16    2  0.6045   0.6545  +0.0500|0.0284|
|16  ALL  null ceiling-minus-floor|over 12 random pockets:|
|median +0.0440, mean +0.0|472 +/- 0.0582, max +0.1529|
|21    0  0.5688   0.6572  +0.0884|0.0395|
|21    1  0.5847   0.6404  +0.0556|0.0247|
|21    2  0.5009   0.6321  +0.1312|0.0357|
|21  ALL  null ceiling-minus-floor|over 12 random pockets:|
|median +0.0715, mean +0.0|688 +/- 0.0506, max +0.1315|
|REPORTED (COMPETENCE_MAP, TASK-0129):|KRAS +0.122, BCR_ABL1 +0.090, CARDIAC_MYOSIN +0.064|
|n_pos=16: P(null >= KRAS +0.122)=0.08|P(>= BCR_ABL1 +0.090)=0.25   P(>= CARDIAC +0.064)=0.33|
|n_pos=21: P(null >= KRAS +0.122)=0.25|P(>= BCR_ABL1 +0.090)=0.33   P(>= CARDIAC +0.064)=0.50|



**CARDIAC_MYOSIN's +0.064 sits at the null's median.** BCR_ABL1's +0.090 is at roughly the 70th percentile. Only KRAS's +0.122 is even marginal, and it does not reach p < 0.05 under either pocket size. 

**The root cause is a rule the project wrote down and then trusted.** REVIEW-2026-07-15b-ceiling-search-methodology.md states: 

"N=60 blind random search is weak evidence for a null result, **though it would be perfectly adequate evidence for a positive finding (a single lucky trial clearing the floor is real regardless of how the rest of the space looks)** ." 

For a **maximum** statistic that is exactly backwards. The word doing the work is lucky. A lucky trial is luck. With 60 draws and an observed per-draw AUC sd of 0.025– 0.040, the max exceeds the mean by ≈ 2.3σ ≈ **+0.06 to +0.09 by construction, with no signal present at all.** 

And here is the mechanism by which this got past a very careful team: **TASK-0118's retraction was correct, and it silently moved the load-bearing claim across the boundary of that rule.** Before the fix, the claim was negative ("ceiling below floor") — the regime where the review demanded rigour, and got it (TASK-0116 filed). After the fix, the claim became positive ("ceiling clears floor") — the regime where the same review says no null is needed. Nobody re-examined it, because the rule said not to. TASK-0116's open text still frames the worry as "a denser search could find a materially higher ceiling" — the one direction that isn't the problem. 

**Required control, ~4 hours:** run ceiling_search_batched.py unchanged against permuted pocket labels, ≥ 200 replicates per target. Report ceiling−floor as a percentile of that null. This is the single highest-value experiment available and it is not in the task list. 

Caveat, stated because it matters: my V-term surrogates are reconstructions, not your potentials.py . If your real per-draw spread exceeds my 0.025–0.040, the null is **wider** and my result is conservative. Twelve replicates gives p-value resolution of only ~0.083 — enough to place all three margins inside the null's bulk, not enough to put a tight p on any one. That is what the 200-replicate run is for. 

### **2.2 The clock fix used the wrong criterion — the competence map is still ~65,000× off** 

propagators.min_adequate_t_max ships two branches (lines ~507–568): 

if kind == "ground_state_relaxation": 

gap = float(w[1] - w[0])                       # ground-state gap return -np.log(tol) / gap elif kind == "time_averaged_ctqw": min_gap = <minimum over ALL eigenvalue pairs>  # AAKV return 2.0 / (min_gap * tol) 

COMPETENCE_MAP.md : "All three columns are CTQW-propagated… floor, ceiling, and actual all use time_averaged_ctqw ." And: "TASK-0119 fixed the clock ( t* = - ln(tol)/gap per operator)." 

**That is the ground_state_relaxation formula applied to time_averaged_ctqw propagation.** EXECUTION_PLAN.md (~line 510) says so outright: "TASK-0119 deliberately avoided this specific criterion, using ground_state_relaxation 's simpler 2-eigenvalue-gap one instead." 

Measured, same H, same tol, this session: 

C1  the two prescriptions in min_adequate_t_max, same H, same tol=1e-2 

ground_state_relaxation branch: -ln(tol)/(w1-w0) =       99.391   [gap=0.04633] 

time_averaged_ctqw branch:      2/(min_gap*tol)  =  6479178.750   [min_gap=3.087e-05] RATIO = 65,189x 

AAKV bound at TASK-0129's t*: 2/(min_gap*t_gsr) = 651.9  (needs <= 0.01) -> off by 65,189x 

This independently reproduces TASK-0110's 145,000×–3,950,000× on a protein TASK-0110 never touched, from an independent implementation. 

The two criteria measure different physics. The GSR gap governs when **imaginary-time** relaxation is dominated by the ground state. The AAKV min-gap governs when **real-time oscillatory cross-terms** have averaged out. Substituting the first for the second because the second "blows up" does not make convergence happen — it stops you measuring how far from it you are. **And the second blows up because the physics blows up:** protein contact networks are fractal with spectral dimension d_s ≈ 1.6–2.5 (I measured this on 3MHT/1UBI; cf. Reuveni, Granek & Klafter, PNAS 107:13696), which means N(λ) ~ λ^(d_s/2) — a **dense low-frequency spectrum** , hence tiny min-gaps, **on every protein** . BCR_ABL1's near-continuum is not a quirk. It is the generic case, and it is predictable a priori. 

**The consequence:** TASK-0129's table — the project's current headline, described as the "fully corrected convention," cross-validated to 4 decimals across two code paths — is computed at a t_max that fails the propagator's own check_convergence by ~4–5 orders of magnitude. The two code paths agree because they share the wrong convention. That is precisely the seed bug's shape, recommitted six days later. 

### **2.3 The right move is to delete the clock — measured, and it is 400× faster and exact** 

propagators.py:374-375 already says it: 

"…oscillatory cross terms to approach the decoherent/infinite-time limit sum_k |v_k(j)|^2 |v_k(source)|^2 " 

**It is documented and never implemented.** grep finds it only in docstrings. Measured: 

C2  closed form vs brute-force time average (single-source, N=327) closed form  sum_k |v_k(j)|^2|v_k(s)|^2 :     10.7 ms time average t_max=5e4, n_steps=20000   :      4.1 s max |closed_form - time_avg| = 9.491e-05   (t_max=5e4 is still 130x short of the AAKV bound) spearman(closed, time_avg) = 1.0000 

Pre-registered bar was agreement < 1e-3 and runtime < 1 s at N > 300. Both cleared by wide margins, and **the ranking — which is all AUC consumes — is identical to four decimals.** 

This is Godsil's average mixing matrix. It is exact at t → ∞, gauge-free, phase-free, and O(N³) **once** . There is no t_max , no n_steps , no Nyquist check, no Optuna scan, no 2-hour timeout, no clock convention for a document to mix. Six tasks exist to manage a parameter with a closed-form answer. 

One correctness note the panel insists on: the index-wise formula is exact only for a **non-degenerate** spectrum. The rigorous object groups by eigenvalue — M� = Σ_r E_r ∘ E_r over spectral idempotents. Your spectra are near-degenerate, not degenerate, so the index formula is numerically right; but given §2.2's BLAS instability, assert a minimum gap or group eigenvalues within tolerance. Do not inherit a new silent bug while fixing an old one. 

### **2.4 The ceiling search violates TASK-0121's own disorder bound by 12–25×** 

TASK-0121 (landed 2026-07-18) proves a target-independent guarantee: all five V terms z-scored (std 1 each), so by Minkowski σ(Σλᵢ Vᵢ) ≤ Σ|λᵢ| ; with J ≤ 2 for the symmetric normalised Laplacian, Σ|λᵢ| = 0.4 gives σ(V) ≤ 0.2·J . Hence the new defaults lam_B=0.08, lam_T=0.16, lam_R=0.08, lam_C=0.04, lam_M=0.04 . 

ceiling.py::_PARAM_RANGES , unchanged: 

"lam_B": (0.0, 2.0), "lam_T": (0.0, 2.0), "lam_R": (0.0, 2.0), 

"lam_C": (0.0, 2.0), "lam_M": (0.0, 2.0), 

E[Σλᵢ] = 5.0 against a budget of 0.4 — **12.5× typical, 25× at the corner.** With every term now std 1, that puts σ(V)/J in the 1–5 range across most of the 60 draws: deep in the Anderson-localised phase, which is the exact regime TASK-0121 exists to escape. The renormalisation fixed the defaults and left the search space untouched, one day apart. 

So the ceiling is a max over 60 draws taken mostly from the localised regime, with no null. Both defects push the same way: **the ceiling number is not measuring the operator family's capacity.** 

### **2.5 BCR_ABL1's "unexplained tension" resolves — and the resolution deletes the finding** 

COMPETENCE_MAP.md flags this as open and unexplained: 

- "propagating BCR_ABL1's H_new operator toward its true decoherent limit does not improve discrimination — it may actively hurt it… reported as an open, unexplained tension for a future task to resolve." 

Floor (max of degree / euclid / hop): **0.5817** 

TASK-0110's AUC-optimal short time, t_max=2.39 : **0.5829** Convergence-motivated t* : **0.5305** 

- **0.5829 − 0.5817 = +0.0012.** The short-time CTQW optimum reproduces that target's proximity floor to three decimal places. 

It is not a tension. At short t the CTQW occupation **is** proximity. Measured this session on 3MHT at your production settings: ρ(occupation, −distance) = **+0.979** , participation ratio = **2.4 residues out of 327** . The walker has not left the seed. So an Optuna search over t_max maximising AUC will always be driven toward t → 0 , because that is where the floor's own signal lives. **TASK-0110's scan rediscovered the floor and labelled it headroom.** 

And "propagating longer hurts" is the confound leaving. Longer time → less proximity → AUC falls to the true value, which is chance. The short-time AUC was never signal. This strengthens your negative result: it explains, mechanistically, why every short-time number in this project's history hugged its floor. 

## **3. Scientific assessment** 

### **3.1 Biological validity — the benchmark is broken, and you have the receipts** 

Read TASK-0120's own numbers as a structural biologist would: 

|**Target**|**Pocket/background**<br>**RMSD**|**What it means**|
|---|---|---|
|KRAS_G12C|2.27|Cryptic opening —**but**Switch-II is built from the catalytic region, so active and allosteric<br>labels geometrically overlap|
|BCR_ABL1|**0.49**|The pocket moves**less**than background.**Pre-formed, not cryptic.**|
|CARDIAC_MYOSIN|1.32|On a 20 Å cryo-EM docked homology model with 3.16 Å background RMSD and 709/950<br>coverage|



BCR_ABL1's ratio of 0.49 is reported as "consistent with a structural prior" — correct, and the implication is bigger than stated. **If the myristoyl pocket is already open in 1OPL, finding it is a pocket-detection problem, not an allostery problem.** That is fpocket's job, and it explains ground_state_relaxation 's 0.7315 completely: it finds a well because there is a well. 

So the challenge's three mandatory targets are: **one where the pocket overlaps the active site, one where the pocket isn't cryptic, and one where the structure is unusable.** Not one of them is a clean distal-cryptic test. Combined with 6C1H containing no mavacamten, you have a second, independent, RCSB-verifiable finding about the benchmark itself. This is worth a page of the six, and it is currently worth a YAML comment. 

SYSTEMS_allosteric_corrected_v2.md deserves specific credit: catching that v1.2's lit_pocket lists were fabricated ( MYC_MAX [40,44,48,52,56] — an arbitrary i,i+4 pattern), contaminated with active-site residues, or construct-offset hazards, and replacing all of them with [] plus a derivation procedure, is exactly the discipline that separates this project from its competition. 

### **3.2 Physical validity — the quantum layer is now provably inert** 

Three independent Done tasks: 

**TASK-0099** : auc_range = 0.0132 (KRAS), 0.0050 (BCR_ABL1) → COHERENCE_NOT_SIGNIFICANT . Randomising coherence away changes nothing. **TASK-0105** : ENAQT gives 1.24–1.70× transport on 3/6 cells and **degrades** discrimination in every observed case. **TASK-0068** : coherent ties or beats ENAQT at every NISQ depth/error point. 

I reproduced TASK-0105's direction independently this session (Haken–Strobl on 3MHT, trace conserved to 1e-6): ρ(occ, −dist) climbs **0.980 → 0.985** monotonically in γ while PR collapses **2.2 → 1.1** . The mechanism is not mysterious: **ENAQT drives the walk toward classical diffusion, and classical diffusion is the maximally distanceconfounded transport there is.** It buys transport. It cannot buy discrimination. Ever. 

**Now add the theorem.** §2.3 establishes that the correct observable is the t → ∞ limit, and that limit is Σ_k |v_k(j)|²|v_k(src)|² — **real, symmetric, phase-free, four lines of numpy.** If the right answer is the infinite-time limit, and the infinite-time limit contains no phases, then **the CTQW's quantumness is provably irrelevant to this task.** That is not a hedge; it follows from your own docstring plus your own convergence analysis. 

This is a result, not a failure — and the challenge statement explicitly asks for it ("Comparison to classical analogs, where relevant, should be analyzed"). Nobody else will bring a proof. 

### **3.3 Statistical validity — one open task is doing all the damage** 

**TASK-0112 (CIs) is the only P0 from 15 July still open, and §2.1 is what it costs.** Every number in COMPETENCE_MAP.md is a bare point estimate on 7–21 positive residues. The margins being adjudicated are ±0.001 to ±0.12. block_bootstrap_ci exists in metrics.py and is called only from select.py 's LOPO path. 

Concretely: CARDIAC_MYOSIN's headline reversal — from NO_FAILURE_DETECTED (+75.1% headroom) to BEATS_CHANCE_NOT_FLOOR (−1.4%) — turns on **actual 0.7912 vs floor 0.7921, a margin of 0.0009** . That is being read as a decided result. On ~20 positives the AUC standard error is ~0.06. **The margin is 1.5% of one standard error.** The document calls it "essentially a tie, not a win," which is right in spirit and still 70× more precision than the data supports. 

classify_failure 's |AUC − 0.5| < 0.05 chance tolerance is also a hard-coded threshold standing in for a CI. It fires on KRAS (0.5442) and produces NO_SIGNAL_IN_APO — the right verdict, by the wrong instrument. 

### **3.4 Computational validity** 

Good: TASK-0128's ANM rigid-body fix (7 and 10 near-zero modes traced to a real under-constrained-substructure artefact, not papered over); TASK-0110's honest n_steps_capped exclusion; the RNG fast-forward in ceiling_search_batched.py ; two-code-path cross-checks. 

Bad: the BCR_ABL1 gap reproducibility flag — **5.2× disagreement (0.0374 vs 0.1933) on byte-identical inputs, from BLAS reduction order** — is flagged, correctly diagnosed as near-continuum fragility, and then used anyway as the basis for the headline clock. A quantity that moves 5× under thread scheduling cannot set a physical timescale. §2.3 removes the need for it entirely. 

## **4. Next steps, in execution order** 

**P0-1 · Implement the closed-form limit. Half a day.** 

def average_mixing(H, source): 

w, v = np.linalg.eigh(H) 

# assert non-degeneracy or group eigenvalues within tol (§2.3) return ((v**2) * (v[source, :]**2).mean(0)).sum(1) 

Recompute floor / ceiling / actual for all five targets. **This closes TASK-0108, 0109, 0110, 0117, 0119, 0129 and Q-0003 at once** , and makes every future number gauge-free by construction. Nothing else on this list is trustworthy until it lands. 

**P0-2 · Permutation null for the ceiling. Four hours.** ceiling_search_batched.py unchanged, permuted labels, ≥ 200 replicates/target. Report every ceiling−floor margin as a null percentile. This decides whether the competence map's only positive claim survives. **Fix REVIEW-2026-07-15b 's rule while you're there** — it is the reason nobody looked. 

**P0-3 · Wire block_bootstrap_ci into every headline AUC. Half a day.** TASK-0112. The function exists. Then re-read §3.3's −0.0009. 

**P0-4 · Fix ceiling.py::_PARAM_RANGES to respect σ(V) ≤ 0.2·J. One hour.** Sample λ on a simplex with Σ|λ| ≤ 0.4, or Sobol over the constrained set. Re-run the ceiling. This is TASK-0121's own bound applied to the one place that ignores it. 

**P1-5 · Slow-mode filtering — the experiment your own learnability gate demands. One day.** TASK-0120 measured that the apo→holo direction lives **58–79%** inside the lowest-20 ANM mode subspace (CO = 0.638 / 0.794 / 0.584). The CTQW observable integrates over **all** N modes (169–950). You are averaging a ~20-dimensional signal against 150–930 dimensions of proximity noise. 

The fix is P0-1's function with one index: 

CP_low(j) = Σ_{k ≤ n_low} |v_k(j)|² · mean_{i ∈ src} |v_k(i)|² 

Measured this session on 3MHT (N=327): 

|**retained modes k**|**ρ(CP, −dist)**|**ρ(CP@7Å,**<br>**CP@8Å)**|**PR (residues)**|
|---|---|---|---|
|3|+0.186|**+0.940**|264|



|5<br>10<br>**~~retained modes k~~**|**−0.061**<br>+0.126<br>**~~ρ(CP, −dist)~~**|+0.889<br>+0.836<br>**ρ(CP@7Å,**<br>**CP@8Å)**|285<br>243<br>**~~PR (residues)~~**|
|---|---|---|---|
|all 327|+0.560|+0.542|300|
|**CTQW occupation, production**<br>**settings**|**+0.979**|+0.988|**2.4**|



Noise floor: |ρ(random, −dist)| = 0.044 ± 0.036. **At k=5 the observable is statistically free of distance dependence — and it becomes nearly twice as reproducible under a contact-cutoff perturbation, not noisier.** That is the signature of real structure, exactly as Zheng/Brooks/Thirumalai (PNAS 103:7664) predict for soft modes. 

Note n_low is already a build_H_new argument and already in the ceiling search. You have been sweeping it as a potential ingredient. It should be an observable filter. 

**P1-6 · Run GNM-transfer-entropy as the classical baseline. One to two days.** Hacisuleyman & Erman (PMID 28241380) give directional causal flow from contact topology alone, no MD, seconds on a laptop. Kaynak/Bahar (J Mol Biol 2022, PMID 35644497) do slow-mode-subset TE and recover allosteric sites on a 20-protein set — i.e. **P1-5, classically, published.** This baseline appears nowhere in the competence map. If your method cannot beat it, there is no result; if GNM-TE also lands at its floor, your negative becomes a much stronger claim about the task. 

**P1-7 · Resolve c-Myc's resnums.** Reported top hits 943/246/925/243/226 against 1NKP (Myc ≈ 353–437, Max ≈ 22–102, keep_nucleic: true ). Raised 15 July, still open. Do not ship a hit list you cannot map to a residue. 

**P2-8 · Decide CARDIAC_MYOSIN (TASK-0124).** Now academic for headroom; still live for whether 5TBY appears at all. 

**Not now:** HOLO_DIRECTION_MODULE . §5.3. 

## **5. Validation strategy** 

### **5.1 The three experiments that can falsify the current headline** 

1. **Permutation null on the ceiling** (P0-2). Falsifies "real headroom exists in H_new 's space." 

2. **Closed-form recompute** (P0-1). Falsifies every number computed at any t_max , in either direction — including possibly restoring a positive. 

3. **Slow-mode filtered CP vs holo ground truth** (P1-5). Falsifies "the observable is the problem." If filtered CP also lands at its floor on your real targets with real active sites, then the apo topology genuinely does not encode the pocket **by any spectral observable** , and CO = 0.638 is spanning-without-locating. That is a stronger and more interesting negative than anything currently in the repo — and it needs P0-2's null to be believed. 

### **5.2 The control the learnability gate still needs** 

superpose.learnability_verdict requires pocket RMSD ≥ 1.5× background **AND** CO < 0.5. Both thresholds are unsourced, and the conjunction is doing real work: BCR_ABL1 passes as LEARNABLE by failing the RMSD condition (0.49) — i.e. because the pocket does not move. That is technically correct and scientifically misleading; "learnable because it's already there" and "learnable because the apo dynamics encode a hidden channel" are different claims. 

**Control:** compute CO(20) for a **random 16-residue patch** on each target. If a random patch also scores 0.58–0.79, then CO measures how much of any displacement the soft modes span, not how much of the pocket's displacement. Half a day, and it decides whether TASK-0120's headline means what it says. 

### **5.3 HOLO_DIRECTION_MODULE — good spec, wrong moment** 

The document is well-built: Step 0's freeze-before-looking, the explicit leakage firewall, "claim the assembly, not the ingredients," and the honesty about HHL/QSVT being pointless at N ~ hundreds. Three problems: 

1. **Step 4 inherits the broken observable.** "Run the existing CTQW/ENAQT on each admissible graph; the active-site→pocket signal now flows on the deformed connectivity." At production settings the observable is ρ = +0.979 with distance and PR = 2.4. Deforming the graph by a few Å will not decorrelate it. The module fixes the **graph** ; the defect is in the **observable** . 

2. **Its scoring metric divides by noise.** "Headroom recovered = (method − floor)/(ceiling − floor)" — §2.1 says that denominator is statistically indistinguishable from zero. You can already watch it detonate: +51.3%, −57.0%, −1.4% from margins of 0.12, 0.09, 0.06. A ratio with a noise denominator is not a metric. 

3. **Its ENAQT rationale contradicts two Done negatives.** "Calibrated dephasing reopens blocked paths" vs TASK-0105 (degrades discrimination) and TASK-0068 (coherent ≥ ENAQT under noise). And γ calibration from B-factors is meaningless on 5TBY. 

**Verdict:** shelve until P0-1 and P1-5 land. If filtered CP works, the module becomes a natural Phase-2 extension. If it doesn't, the module cannot save it. 

### **5.4 Documentation drift, now measurable** 

ALGORITHM_REGISTER.md : "it tells you per target whether the holo direction is even reachable from apo ( **KRAS Switch-II likely fails** )." HOLO_DIRECTION_MODULE.md : "KRAS Switch-II is the expected NO case." **TASK-0120 measured CO(20) = 0.638 — it does not fail.** Both documents encode a prediction the project has already refuted. (It was my prediction; see §6.5.) Two days is fast drift for a repo this disciplined — it is the cost of documents that cite each other's expectations rather than each other's measurements. 

## **6. Executive summary** 

### **6.1 The five most important findings** 

1. **The clock fix used the wrong criterion; the competence map is still ~65,000× off.** min_adequate_t_max ships two branches; TASK-0119/0129 propagate with time_averaged_ctqw and set t* from ground_state_relaxation . Measured: 99.4 vs 6,479,179 on a real protein; the AAKV bound at TASK-0129's t* is 651.9 against a required 0.01. Two code paths agreeing to 4 decimals does not catch a shared convention error — **that was the seed bug's entire lesson, recommitted six days later.** 

2. **The one positive claim in the document fails a permutation null.** Null ceiling−floor = +0.044 to +0.072 median, sd ≈ 0.05, max +0.15, under the identical 60draw protocol on random pockets. Reported: +0.122 / +0.090 / +0.064. p ≈ 0.08–0.50. CARDIAC's margin is at the null's median. 

3. **The escape is in your own docstring and unimplemented.** Σ_k |v_k(j)|²|v_k(src)|² : 10.7 ms vs 4.1 s, agreement 9.5e-05, **Spearman 1.0000** . Six tasks manage a parameter with a closed-form answer. Delete the clock. 

4. **The learnability gate is the project's best result and its implication is undrawn.** CO(20) = 0.638/0.794/0.584 — the answer lives in ~20 modes; the observable integrates over 169–950. Filtering to k=5 drops the distance confound to the noise floor (+0.560 → −0.061) and doubles reproducibility (0.542 → 0.940). **The clock problem, the observable problem, and the learnability finding collapse into one function.** 

5. **The quantum layer is provably inert — and that is publishable.** TASK-0099 (coherence NS) + TASK-0105 (ENAQT degrades discrimination) + TASK-0068 (coherent ≥ ENAQT under noise) + the t→∞ limit being phase-free. The challenge explicitly asks for the classical comparison. Nobody else will bring a proof. 

### **6.2 The five biggest risks** 

1. **Shipping the competence map as "fully corrected."** It is seed-corrected and clock-mis-corrected. A reviewer who opens min_adequate_t_max and reads its two branches finds this in ten minutes — the same exposure the seed bug carried on 15 July. 

2. **Shipping "+0.122 headroom" as a finding.** It is the max of 60 draws with the answer key, no null, drawn mostly from outside your own disorder bound. This is the most attackable sentence in the repo. 

3. **Zero CIs (TASK-0112) while adjudicating a −0.0009 margin.** Every headline reversal to date has come from a gauge, not from evidence. Without CIs you cannot tell which of the next ones are real. 

4. **Correction fatigue → nihilism.** Three consecutive gauge artefacts (seed, clock v1, clock v2) have each erased an apparent positive. The pattern is now "anything positive is an artefact." But TASK-0120 says the signal **is** in the apo structure, in the soft modes. The risk is no longer over-claiming. It is concluding "impossible" from three measurement bugs and never looking where your own gate points. 

5. **Eight weeks, no quantum layer in the app** (TASK-0083–0086 still TODO) — and the challenge scores 3D connectivity visualisation explicitly. Note the tension with the Phase-1 reality: this is a **6-page ideation proposal** , not a PoC. Do not let engineering eat the writing time. 

### **6.3 The five highest-priority actions** 

|**#**|**Action**|**Cost**|**Why now**|
|---|---|---|---|
|1|Implement<br>average_mixing closed form; recompute<br>all five targets|0.5<br>d|Closes six tasks; makes everything downstream gauge-free.**Nothing**<br>**else is trustworthy until this lands.**|
|2|Permutation null for the ceiling (≥200 reps/target); fix<br>REVIEW-2026-07-15b 's rule|4 h|Decides the only positive claim you have|
|3|Wire<br>block_bootstrap_ci into every headline AUC|0.5<br>d|The last open P0 from 15 July; §3.3 is what it costs|
|4|Slow-mode filtered CP on real targets vs holo ground<br>truth|1 d|The experiment your own learnability gate demands; the only route<br>back to a defensible positive|
|5|GNM-transfer-entropy baseline (Hacisuleyman &<br>Erman; Kaynak/Bahar)|1–2<br>d|The published classical method that does #4 already. If you can't<br>beat it, you don't have a result|



**Total ≈ 4 days.** Everything else — HOLO_DIRECTION, the NISQ demo, the app's quantum layer — should wait behind them. 

### **6.4 The submission narrative these findings support** 

We built the falsification apparatus this field lacks — proximity floors, supervised ceilings, negative-control double dissociations, gauge registers — and used it to kill four of our own positive results, three of which were measurement artefacts we introduced ourselves. We then proved the observable was wrong by construction: CTQW occupation from a source is 97% Euclidean distance at any tractable propagation time, its participation ratio is 2.4 residues out of 327, and its exact infinite-time limit is a phase-free classical spectral quantity — so coherence cannot be doing work here, and our own coherence-sensitivity, ENAQT, and NISQ-noise measurements independently confirm it isn't. Meanwhile our learnability gate shows the answer is in the apo structure, 58–79% inside the lowest-20 mode subspace. We propose the observable that looks there. And we found that the challenge's own validation set does not test what it claims: 6C1H contains no mavacamten, BCR-ABL1's myristoyl pocket is pre-formed rather than cryptic, and KRAS's Switch-II pocket is built from the catalytic region it is supposed to be distal from. 

Against the rubric: Feasibility (20%) and Validation Plan (15%) are already best-in-field. Technical Approach & Innovation (25%) is a 5 **if** framed as "we tested the quantum framing and falsified it with a mechanism," not "our method underperforms." Problem Relevance (25%) is carried by the benchmark findings. 

### **6.5 Where I was wrong on 15 July — stated, because unstated reads as unchecked** 

- **" t_max=15 is ~100× too short."** TASK-0110 measured **145,000×–3,950,000×** . I was wrong by three to four orders of magnitude, and their closed-form-plusOptuna cross-check is a much better instrument than my estimate was. My §2.2 finding stands on their measurement, not mine. 

- **"KRAS's Switch-II pocket likely does not exist in 4OBE."** TASK-0120 measured RMSD ratio 2.27 **and** CO(20) = 0.638 → LEARNABLE . **Refuted, by a direct measurement, correctly reported as contradicting the panel.** This is the single best piece of news in the repo and I got it backwards. 

- **"COMPETENCE_MAP's ceiling-below-floor is refuted by TASK-0093's own data."** Correct, and TASK-0118 confirmed it at larger magnitude than I estimated (0.326 swing). 

- **"The five-term potential is 88% V_R ≈ degree."** TASK-0121 measured 88.8% and ρ(V_R, degree) = +0.81. Correct. 

The team's measurements have beaten my estimates twice and confirmed them twice. **That is the correct ratio for a review to have, and it is why §2.1–2.5 should be measured rather than believed.** 

## **What this review did NOT verify** 

- I did not run your code. probe4.py reconstructs ceiling.py 's _PARAM_RANGES and a faithful-in-shape H_new ; the V-term surrogates are mine, not your potentials.py . If your per-draw AUC spread exceeds my 0.025–0.040, §2.1's null is **wider** , not narrower. 

- 12 null replicates → p-value resolution ~0.083. Enough to place all three margins in the null's bulk; not enough for a tight p on any one. That is P0-2's job. Numerics ran on 3MHT (N=327) and 1UBI (N=76), **not** your targets — RCSB is unreachable from this sandbox; these came from GitHub. The clock ratio, the closed-form equivalence, and the selection-bias argument are all structural, but the specific numbers are not yours. 

- I did not read analysis.py , protocol.py , select.py , report.py , labels.py , viz.py , the tests, the backend, or the frontend. 

- I did not verify the c-Myc resnums against 1NKP — I flagged the arithmetic, I did not check the structure. 

- I did not run GNM-TE. I assert it is the right baseline from its published description, not from reproducing it. No CIs on anything in this review, which is the same defect I am charging you with. 

**Attached:** probe4.py (clock ratio, closed form, ceiling null), probe.py / probe2.py / probe3.py (spectral dimension, proximity confound, slow-mode filtering, chirality, dephasing — from the 17 July steering memo). 

