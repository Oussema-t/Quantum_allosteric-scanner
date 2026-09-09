# Physical Hypotheses

**Scope:** Scientific conjectures about the protein physics underlying H_new and the propagators.
These are testable claims, not implementation tasks.
Cross-reference: concrete code changes in `../improvements/hamiltonian_code.md`;
strategic framing in `ceiling.md`.

**Before citing a hypothesis below, check [`INDEX.md`](INDEX.md)** for its
current dated status (or "no verdict recorded") in one screen, rather than
scanning this file for the most recent `**Status**` line by eye
([[TASK-0322]] — filed because a correct, current verdict in this exact
file was missed and contradicted in a collaborator brief).

---

## HYP-P1 · Low-frequency GNM modes are a reliable proxy for allosteric residues (in rigid globular proteins)

**Claim:** Residues with high participation in the slowest GNM modes (globally
correlated motions) are disproportionately likely to be allosteric hubs.

**Supporting evidence:** Well-established for single-domain, rigid proteins (Bahar,
Chennubhotla, Atilgan). GNM predicts B-factors and allosteric pathways in dozens
of benchmark systems.

**Counter-evidence / conditions under which this fails:**
- **Hierarchical allostery** (multi-domain proteins): intra-domain signal may live
  in intermediate-frequency modes. The very slowest modes describe domain-domain
  motions, which may not be the functional allosteric channel.
- **Entropy-driven allostery** (IDPs, flexible loops): the mechanism is redistribution
  of fast local fluctuations (high-frequency modes), not collective slow motions.
  V_M would assign low reward to the actual functional sites.
- **Near-degenerate modes**: the k-th and (k+1)-th mode may be nearly equal in
  frequency; their rank is sensitive to small perturbations.

**To test:** Compare V_M reward scores against experimental annotations across a
diverse benchmark (rigid globular, multi-domain, IDP-containing). If AUC drops for
flexible targets but not rigid ones, the hypothesis is domain-restricted.

**Implication for n_low:** If the hypothesis holds broadly, n_low should scale with N
(see IMP-H1 in `../improvements/hamiltonian_code.md`).

**Status, 2026-09-03 ([[TASK-0323]]/[[TASK-0324]]): NEVER TESTED — confirmed by
thorough audit (312 files grepped, every plausible hit read), not merely absent.**
This hypothesis's own "To test" (V_M AUC stratified rigid/multi-domain/IDP) has
never been run. Adjacent, not decisive: [[TASK-0101]]/TASK-0067 (near-chance AUC
broadly, no domain split), TASK-0263/TASK-0275 (real V_M per-target AUC, no domain
split), TASK-0250 (GNM B-factor validity flags MYC_MAX/BCR_ABL1 as FAIL/MARGINAL —
circumstantial, not a designed test). Matches the cross-cutting note below ("weakened,
not yet formally falsified") — same conclusion, now dated and verdict-typed.

---

## HYP-P2 · A pairwise residue-type correction is the highest-value diagonal-only extension

**Claim:** Adding an off-diagonal term `V_pair[i,j] = mask[i,j] * J(aa_i, aa_j) * f(d_ij)`
— where J is a 20×20 residue-pair coupling matrix — would improve AUC more than any
further refinement of the current diagonal terms.

**Rationale:** All of V_B, V_T, V_R, V_C, V_M are diagonal — their sum is one
combined diagonal. No combination can distinguish a buried Phe-Phe contact from
a buried Gly-Gly contact at the same distance. A pairwise term is the first
addition unreachable by any diagonal-only operator.

**Candidate J matrices:**
- Miyazawa-Jernigan statistical potentials (empirical, from PDB)
- Simple charge × charge + hydrophobicity product (2-parameter)
- BLOSUM62 (evolutionary co-tolerance)

**To test:** Add V_pair, fit J under strict LOPO CV. Risk: must not test on the
same proteins used to fit J.

### Status update, 2026-07-18 — TASK-0121 (variance-budget renormalization) Done

Unaffected by TASK-0121 as a hypothesis (still open, still an off-diagonal
extension no combination of z-scored diagonal terms can reach), but its
premise ("no combination can distinguish a buried Phe-Phe contact from a
buried Gly-Gly contact") was previously argued on top of a diagonal sum
where V_R alone carried 88.8% of the variance and V_C/V_M were structurally
inert (`REVIEW-panel-2026-07-16-v2.md` §2.4). TASK-0121 z-scored all five
terms and re-derived `lam_*` so every term is now a reachable knob
(see `../HAMILTONIANS.md`'s Critical facts / IMP-H6 for the corrected
variance budget). This hypothesis's own "highest-value diagonal-only
extension" framing should be re-evaluated against the *renormalized*
diagonal sum, not the pre-fix one -- V_pair's marginal value over a
properly-balanced 5-term diagonal may differ from its marginal value over
one that was effectively V_R alone.

**Status, 2026-09-03 ([[TASK-0323]]/[[TASK-0324]]): NEVER TESTED.** V_pair
(the off-diagonal residue-pair term this hypothesis proposes) was never
implemented or tested — TASK-0121 (above) only re-scaled the existing
diagonal terms, it did not add an off-diagonal one. One thematic false
positive checked and ruled out: TASK-0268's Miyazawa-Jernigan potential is
a *frustration* statistic for [[HYP-P13]], not an off-diagonal H_new term
for this hypothesis.

---

## HYP-P3 · V_C (currently structural centrality) would be more predictive as true dynamic covariance

**Claim:** Replacing V_C with the GNM cross-correlation diagonal would improve AUC
because dynamic covariance captures which residues fluctuate in a correlated fashion
with the rest of the protein — a direct physical signature of allosteric communication.

**Current V_C:** `W_invdist.sum(axis=1)` — weighted contact degree, purely structural.

**Proposed replacement:**
```python
L_pseudo = np.linalg.pinv(L_GNM)   # pseudo-inverse = GNM correlation matrix
corr_score_i = L_pseudo[i, :].sum()  # mean correlation of i with all other residues
```

**Cost:** One `eigh()` per protein — but V_M already does this; the modes can be shared
(see IMP-H3 in `../improvements/hamiltonian_code.md`).

**To test:** Ablation: H_new with true V_C vs H_new with weighted-degree V_C. Compare AUC.

**Note (2026-07-18, TASK-0121):** this hypothesis's own "Current V_C" line
above (`W_invdist.sum(axis=1)`, weighted contact degree) predates
`potentials.py`'s current implementation, which already computes true GNM
DCC via `_kirchhoff_eigh`/`_normalized_dcc` (see that module's own TASK-0066
references) — this hypothesis reads as unresolved but the formula change it
proposes already shipped at some earlier point not cross-referenced here.
TASK-0121 did not touch V_C's formula, only its *scale* (z-scored it; it was
previously max-normalised to [-1, 0], std ~= 0.06 on real targets, ~30x
smaller than V_R, making `lam_C` an unreachable knob regardless of the DCC
formula underneath it — see `../HAMILTONIANS.md`). Flagging the formula/doc
mismatch here rather than silently rewriting this hypothesis's history,
since confirming exactly when/why the DCC swap happened is outside this
task's scope.

**Status, 2026-09-03 ([[TASK-0323]]/[[TASK-0324]]): NEVER TESTED.** Zero
corpus hits for the V_C-as-true-DCC ablation this hypothesis's own "To test"
calls for. Confirmed independently by the note directly above: TASK-0121
"did not touch V_C's formula, only its scale."

---

## HYP-P4 · The base Laplacian choice (normalised vs combinatorial, exp-decay vs binary) is load-bearing

**Claim:** The normalised + exp-decay base Laplacian contributes measurably to AUC
compared to combinatorial/binary alternatives — it is not merely a spectral-aesthetics
choice.

**To test (ablation):** Four variants, same diagonal potential, same λ:
1. normalised Laplacian + exp-decay (H_new current)
2. normalised Laplacian + binary contacts
3. combinatorial Laplacian + exp-decay
4. combinatorial Laplacian + binary (≈ H10 + reward terms)

If AUC differences are within noise, the diagonal terms dominate and the base
Laplacian choice is irrelevant. Run this ablation at ceiling (in-sample) before LOPO.

**Status, 2026-09-03 ([[TASK-0323]]/[[TASK-0324]]): NOT A CLEAN TEST —
confounded partial evidence exists, the isolated ablation itself was never
run.** TASK-0101's 96-cell operator sweep shows `H10` (closest analog to
variant 4: combinatorial Laplacian + binary contacts, no diagonal
potentials) floor-clears via `ground_state_relaxation` on 2/3 targets vs.
`H_new`'s 1/3 (variant 1: normalised + exp-decay + potentials) — but this
comparison confounds Laplacian type, weight scheme, AND presence/absence of
the 5 diagonal potential terms simultaneously, so it does not isolate what
this hypothesis asks about. TASK-0113 separately confirms a weight-scheme
knob was never added to `build_H_new` (cutoff-only sweep, by explicit scope
decision). The clean 4-variant same-potential ablation this hypothesis's own
"To test" prescribes remains genuinely untested.

---

## HYP-P5 · H13 (full 3N ANM Hessian) sets a performance ceiling that H_new cannot reach

**Claim:** H13 encodes bond orientation via `r⊗r` outer products and captures
anisotropic mechanical response that no scalar N×N operator can represent. When
properly compared — either by projecting H13 to N×N or by refactoring propagators
to accept 3N×3N — H13 should outperform H_new on structurally anisotropic mechanisms.

**Why this must be tested, not assumed:** The dimensional discrepancy (3N×3N vs N×N)
is not a fundamental physical barrier — it is an implementation detail. If H13 is
the better physical model, the right response is to refactor, not to dismiss it.
See IMP-H7 in `../improvements/hamiltonian_code.md` for the two refactoring options.

**To test:**
1. Build `H13_3N_anm_hessian()` (already exists in `hamiltonians.py`)
2. Option A: Scalar-project to N×N (trace of 3×3 blocks per residue pair) — fast,
   may discard orientational information
3. Option B: Extend `ctqw()` / `haken_strobl()` to accept 3N×3N and post-sum to
   per-residue occupation probabilities — preserves orientational coupling
4. Compare AUC of H13 (Option A and B) against optimized H_new at ceiling
5. If H13 beats H_new: proceed with refactoring (Option B is the defensible choice)
6. If H13 does not beat H_new: the scalar isotropic approximation is sufficient;
   document as a confirmed finding

**The comparison is required for scientific rigor.** Without it, choosing H_new
over H13 is an untested assumption, not a result.

**Status, 2026-07-18/19 (TASK-0126): tested, claim partially supported — mixed,
target-dependent.** Option A was checked (not assumed) to be numerically identical to
`H2_combinatorial_laplacian` (`np.allclose`, max diff 1.8e-15) — it discards *all*
orientational information via `H13`'s unit bond vectors, not "some" as this
hypothesis's own step 2 hedged. Option B was implemented as a propagator wrapper (no
refactor needed — `ctqw`/`time_averaged_ctqw`/`time_averaged_ctqw_converged` were
already dimension-agnostic) and run to completion on **all 3 mandatory targets**
(TASK-0130's closed-form infinite-time convention removed the time-stepping cost that
had made a full run infeasible under the older finite-`t_max` convention this task
started with). Result: **H13-native (Option B) does not beat `H_new` on KRAS_G12C**
(0.5026 vs 0.6288, worst of the three candidates) **or BCR_ABL1** (0.6466 vs 0.6671,
close) **but does beat it on CARDIAC_MYOSIN** (0.8513 vs 0.8297) — the one target where
full orientational detail actually helped. Per this hypothesis's own step 5/6, the
verdict is target-dependent, not a uniform confirmation of either the scalar
approximation (step 6) or the refactored anisotropic propagation (step 5) — H13-native
is a real, checked candidate for CARDIAC_MYOSIN specifically. Separately, `H14_anm_
pinv_trace` (a different, non-degenerate scalar reduction of H13 already in the
codebase, not one of this hypothesis's two options) beat `H_new` on BCR_ABL1 only —
see `ceiling.md`'s 2026-07-18/19 status update and `.ai/tasks/DONE/TASK-0126-h13-
ceiling-comparison.md` for full numbers.

---

## HYP-P6 · Propagation time t in CTQW is currently unprincipled; a spectral choice would close a validity gap

**From the discussion:**
> "The CTQW is time-averaged over `linspace(0.1, 20, 30)`, and on a normalised
> Laplacian t is dimensionless with no physical meaning; it's a free knob."

**The problem:** The ranking of residues changes with t. Silently choosing t_max=20 is
not scientifically defensible.

**Two principled alternatives:**

1. **Infinite-time average** `P_∞(i,j) = Σ_k |⟨i|k⟩|²|⟨j|k⟩|²` — parameter-free,
   but note this is the decoherent limit. Using it concedes that coherence adds nothing,
   which is consistent with HYP-P7 but should be stated explicitly.

2. **Spectral-gap time** `t ≈ 1/Δλ` where Δλ is the spectral gap of the Laplacian
   (the first non-trivial eigenvalue). This is the mixing time of the graph and the
   natural "long enough for signal to travel" scale. It is protein-dependent and
   physically motivated.

3. **Mode-relaxation timescale** from apo→holo ANM projection (Phase 1): if the
   dominant mode k carries the apo→holo displacement, the overdamped relaxation time
   is `τ_k ~ friction / (κ λ_k)` where κ is calibrated from B-factors. This gives
   a single principled t per protein.

**To test:** Sweep t_max from 1 to 200, measure Jaccard stability of top-5 predicted
residues. If the ranking is stable → the result is t-insensitive. If it swings
significantly → t must be locked to a principled value before any ceiling or LOPO
result is reported.

**Resolved 2026-07-16, TASK-0109/TASK-0119 — alternative 2 above implemented and
tested on real data, not just proposed.** `propagators.min_adequate_t_max(kind=
"ground_state_relaxation")` = `-ln(tol)/gap` (`gap` = `H`'s own spectral gap,
`tol=1e-2`) — the same functional form as this hypothesis's own `t ≈ 1/Δλ`, with
the log-tolerance constant made explicit. Applied per-operator across all 3
mandatory targets' 96-cell sweep and TASK-0106's BCR_ABL1 reproduction (not a
synthetic check only): the ranking **is** t-sensitive, confirming this
hypothesis's own concern was real, not hypothetical — most of CARDIAC_MYOSIN's
`ctqw` floor-clears (10 of 11) do not survive the corrected clock, while
`H_new`/`H10`/`build_H10`'s do. Separately, `H_new`'s localization (the
mechanism behind HYP-P8's proximity-like scoring, below) is confirmed to survive
the fixed clock, not an artifact of `t_max=15` specifically. Full detail:
`.ai/tasks/DONE/TASK-0119-fix-clock-per-operator-timescale.md`,
`results/tasks/0119/`. Alternative 1 (infinite-time average) remains this
pipeline's separate, already-shipped headline convention (`time_averaged_ctqw`,
TASK-0097); alternative 3 (mode-relaxation from apo→holo ANM projection) remains
unexplored — not needed once alternative 2 answered the load-bearing question
("is t currently a live, unaccounted-for confound") with a real yes.

**Status update, 2026-09-09 ([[TASK-0350]]): the t-sensitivity this
hypothesis found on 3 targets (10/11 CARDIAC_MYOSIN floor-clears) is
confirmed, much more starkly, at full ASBench scale.** Scored
`time_averaged_ctqw(T=15)` against the parameter-free converged limit,
same `H_new`, same seed, same 108-structure cohort, both `coherent`
settings: **50/108 (46%) structures flip their residualised-AUC sign
(above/below 0.5) between T=15 and the converged limit for the coherent
walk; 41/108 (38%) flip for the decoherent walk.** This is not the same
statistic as TASK-0119's floor-clearing count, but it is the same
underlying finding restated at ~35x the target count and with an exact,
falsifiable per-structure criterion: **any reported per-structure verdict
computed at a finite, unprincipled T (this project's own historical
default of T=15 included) has close to even odds of disagreeing in sign
with the same structure's own parameter-free limit.** The converged limit
(alternative 1 above) is not merely "a" principled choice among several —
given this instability, it is the ONLY one of the three alternatives this
hypothesis lists that does not require picking a T a referee could
reasonably ask "why this one and not another." Full table and method:
[[HYP-P7]]'s own 2026-09-09 status update (same task, same run) and
`.ai/tasks/DONE/TASK-0350-coherent-vs-decoherent-matched-twin.md`.

**Status update, 2026-09-09 ([[TASK-0357]]) — the "principled" spectral
clock (alternative 2) still has a free knob, and a single reading at the
pre-registered value is not enough to trust.** Replicated an external
finite-delay phase-sensitive observable, `O(r)=2*Re<r|exp(-iH tau)|a>`
(TASK-0157's own cross-term), with `tau` fixed per protein via `min_
adequate_t_max(kind="ground_state_relaxation", tol=1e-2)` — this
hypothesis's own alternative 2, pre-registered before scoring, per
TASK-0357's own Intent Contract. At `tol=1e-2`: unsigned `|O(r)|`
resid-AUC excess +0.029 mean / +0.016 median, cluster-permutation
**p=0.036** (76 protein clusters, 108 ASBench structures) — nominally
significant. **Did not stop there.** A post-hoc (explicitly not
pre-registered — disclosed as exploratory follow-up, not smuggled in)
sensitivity check across nearby `tol` values, same cohort, same code:

| tol | mean resid-AUC excess | cluster-permutation p |
|---|---|---|
| 1e-3 | +0.0095 | 0.461 |
| **1e-2 (pre-registered)** | **+0.029** | **0.036** |
| 5e-2 | +0.0096 | 0.523 |
| 1e-1 | +0.0007 | 0.960 |

**The nominally-significant result is isolated to the single pre-registered
tolerance and does not replicate one order of magnitude in either
direction.** This is exactly the signature TASK-0350's own status update
above anticipated in the abstract ("alternative 2... still requires
picking `tol`, a referee could reasonably ask why this one") — TASK-0357
makes it concrete for a real observable on real data: the "principled"
clock removed the `t_max=15-vs-converged` arbitrariness this hypothesis
already established, but replaced it with a `tol` arbitrariness of the
same practical kind, and at least one candidate positive result (the
external collaborator's own finite-delay claim, independently re-derived
here) sits on exactly that knife-edge. Verdict, per TASK-0357's own
pre-registered "either outcome is publishable" framing: **collapse under
scrutiny, not a surviving effect** — a clean methodological finding about
selection on `tau`/`tol`, consistent with (not contrary to) this
hypothesis's own core claim. Full detail:
`.ai/tasks/DONE/TASK-0357-finite-delay-phase-observable-principled-clock.md`.

**Status update, 2026-09-09 ([[TASK-0358]]) — TASK-0357 tested the wrong
`tau`, and a proper scan closes the question decisively rather than
ambiguously.** Two defects in TASK-0357's own design, both attribution
errors in the filing, not the execution: (1) `min_adequate_t_max` is a
*convergence* window (transients have died by then) — evaluating a
phase-sensitive observable there lands precisely where TASK-0130 proves
its phase content is smallest, not a fair test of the finite-delay claim
at all. (2) `tau` depends on the *log* of `tol`, so TASK-0357's own
100x sweep in `tol` (1e-3..1e-1) was only a **~3x** sweep in the variable
that actually matters. Corrected: scanned `tau` directly, on a
pre-registered per-protein-relative grid `tau(protein,f) = f *
min_adequate_t_max(protein, tol=1e-2)`, `f in {0.001, 0.003, 0.01, 0.03,
0.1, 0.3, 1, 3, 10, 30, 100}` — 11 points spanning deep short-delay
(median tau~0.2) through deep-converged (median tau~21000), reusing
TASK-0357's own script/cohort unchanged (Planned Validation: `f=1`
reproduces TASK-0357's committed numbers to 5 decimal places).

**Result: the SIGNED observable (the external claim's own arm) shows no
significant signal at ANY of the 11 points** — cluster-permutation p
ranges 0.24-0.98 across five orders of magnitude in `tau`, not a single
nominal hit. **Not a narrow miss and not a broad band: a clean null
across the entire delay range**, more decisive than TASK-0357's own
single-point null. The UNSIGNED arm's earlier `p=0.036` is now shown to
be exactly the isolated-spike artifact TASK-0357 could not itself
distinguish from a real band: significant at exactly 1 of 11 points
(`f=1`, TASK-0357's own original reading) with no support at any
neighbour in either direction — as clean a selection-artifact signature
as this register has produced. Physically coherent corroboration, not
just a null: unsigned `rho` against proximity falls monotonically from
0.92 (shortest delay, essentially a distance proxy at that scale, as the
short-tau expansion in TASK-0357's own sign-derivation predicts) to 0.24
(longest), confirming the observable behaves as theoretically expected
across the whole axis rather than being numerically degenerate somewhere
along it. **This tenth candidate route is closed, not deferred.** Full
detail: `.ai/tasks/DONE/TASK-0358-finite-delay-observable-in-the-phase-alive-band.md`.

---

## HYP-P7 · Coherence adds no signal for allosteric pocket prediction on these proteins

**From the discussion:**
> "Cell #30 already shows AUC_HS at 0.503 (ω≈0) vs 0.483 (ω large) for KRAS — flat.
> Cell #37's verdict concluded independently: coherence adds nothing."

**Claim:** The Haken–Strobl dephasing sweep (γ from 0 to ∞) produces flat AUC.
The "quantum" label applies to the *implementation* (the evolution is correctly computed
as `exp(-iHt)`), not to a performance advantage over classical diffusion.

**This is a real result, not a failure.** The correct framing:
> "Coherence is correctly implemented and demonstrably does not contribute additional
> signal beyond the contact graph topology for cryptic allosteric pocket prediction."

**To formalize:** Run the Haken–Strobl sweep systematically across all proteins, not
just KRAS. Report mean AUC ± SD as a function of γ. A flat curve is the expected
finding and should be the stated result.

**Implication:** If AUC is truly flat with γ, the time-averaged CTQW = classical
diffusion kernel for all practical purposes on these graphs. The choice between
`ctqw()` and `heat()` then becomes a question of convenience, not physics —
*provided H_new is PSD (which it currently is not; see HAMILTONIANS.md).*

**Status, 2026-09-09 ([[TASK-0350]]): TESTED — CONFIRMED, directly and
decisively, and the PSD caveat above is resolved rather than sidestepped.**
This hypothesis's own "To formalize" section asked for the Haken-Strobl
sweep "systematically across all proteins, not just KRAS." What is
scored here is the more direct version of the same question:
`time_averaged_ctqw_converged(H_new, seed, coherent=True)` vs.
`coherent=False)` — **identical Hamiltonian, identical seed set,
identical 108-structure ASBench cohort, identical scoring** (raw AUC,
rho vs. proximity, rank-residualised AUC) — the single-variable
comparison this register had never actually run; every prior test
(chiral circulation [[TASK-0140]] FAIL, frequency-domain [[TASK-0146]],
HOM [[TASK-0157]]) changed the *observable* along with the coherence.
Planned Validation passed first: `coherent=False` reproduces
[[TASK-0308]]'s committed numbers exactly (raw 0.5921, rho 0.7347,
resid 0.5184, bit-for-bit).

| arm | raw AUC | rho(proximity) | resid AUC |
|---|---|---|---|
| classical diffusion (T=15, graph Laplacian only — H_new's own graph term before any potential, genuinely PSD) | 0.6012 | 0.9531 | 0.4567 |
| decoherent CTQW (converged) | 0.5921 | 0.7347 | 0.5184 |
| coherent CTQW (converged) | 0.5997 | 0.6924 | 0.5207 |

**Decisive test, per-structure (coherent − decoherent) resid-AUC delta,
n=108: mean +0.0023, median −0.0029, Wilcoxon p=0.919, cluster-robust by
protein (76 clusters, sign-flip Monte Carlo) p=0.834.** The
pre-registered prediction ("the gap is small and non-significant,
consistent with [[TASK-0146]]'s ≤0.005 AUC finding") **HOLDS**, this time
on the full cohort rather than 3 targets, with a p-value indistinguishable
from the null in both the row-level and cluster-robust test. The PSD
caveat this hypothesis itself flagged is resolved, not ignored: the
classical arm here is the genuine graph Laplacian (`normalised_laplacian_
alpha`, the exact term `H_new = L_norm + potentials` adds its potential
to), not `H_new` itself — real diffusion, not a ground-state-density
artifact.

**Read plainly: on the identical operator, seed, and cohort this register
actually uses, coherence measurably contributes nothing beyond the
decoherent limit — the interference content of this construction is
zero to within Monte Carlo/Wilcoxon noise, not merely unmeasured.** This
closes the "does interference help" question this register opened three
separate observables (chiral circulation, frequency-domain coherence,
HOM) trying to reach past the decoherent limit to answer, with the
simplest and most direct test of all of them, run last. Also note: BOTH
CTQW arms' residualised AUC sits near 0.5 (0.518/0.521) — consistent with
[[HYP-P8]]'s standing finding that CTQW ≈ proximity and carries little
else; the classical arm's own resid AUC (0.457, *below* chance) shows its
raw signal is essentially entirely proximity, with nothing left over once
that is removed. **Finite-T instability, found in the same run, is
reported under [[HYP-P6]]'s own status update, not here** — a different
claim (t-choice sensitivity vs. coherence content), kept separate per
this register's own fold-in discipline.

---

## Status update, 2026-07-15 — Phase 1B closed the loop on P6/P7/P8; P1/P5 remain open gaps

This file was last touched 2026-06-21, before three weeks of real, executed findings
(Phase 1B in `EXECUTION_PLAN.md`, TASK-0091 through TASK-0117). Recording what actually
happened against each hypothesis below, rather than leaving this file to read as still
speculative when several of these are now settled:

- **HYP-P8 is now strongly supported, not just plausible.** Independent evidence from three
  separate tasks converges on the same conclusion: (1) **TASK-0093** — KRAS_G12C's own
  headline AUC (0.7792) does **not** clear its own proximity floor (0.7976, margin -0.018)
  in a full 2×2×2 factorial re-check; zero of 8 methodology combinations clear it. (2)
  **TASK-0102** — BCR_ABL1's `ground_state_relaxation`=0.7315 is reproduced by 70-75% of
  biologically-arbitrary single-residue seeds (40-seed sample), because the score is
  dominated by `H_new`'s fixed ground-state shape (94.5% of relative weight at `t_max=15`),
  not by real active-site-to-pocket coupling. (3) **REVIEW-2026-07-13c/TASK-0106** — `H_new`'s
  diagonal potentials cause Anderson-like CTQW localization near the seed (participation
  ratio 5-6x lower than transport-preserving operators), mechanically producing
  proximity-like scoring rather than detecting real distal signal. **Practical reading: as
  of 2026-07-15, no mandatory target's headline AUC survives as confirmed allosteric
  signal** — KRAS fails its own floor, BCR_ABL1's GSR is a ground-mode/structural-prior
  artifact (TASK-0104's correction), CARDIAC_MYOSIN self-flags `INSUFFICIENT_RESOLUTION`.
  This is this project's actual current headline finding, not a caveat on one.
- **HYP-P7 is refined, not simply confirmed.** **TASK-0105**'s real 3-target ENAQT sweep
  found the interior-γ transport optimum genuinely reproduces on real protein contact
  graphs (3 of 6 swept cells, 1.24-1.7x enhancement over the coherent limit) — coherence
  *does* measurably change transport magnitude. But in every one of those cells, AUC-at-γ*
  is *lower* than AUC-at-γ→0: the extra transport does not translate into better pocket
  discrimination anywhere in the real data. So the corrected claim is narrower than the
  original: not "coherence adds nothing measurable," but "coherence changes transport, and
  that change has not been shown to help — or hurt — pocket-finding on any target tested."
  `dephasing_sweep` still has zero call sites in the scored verdict path (TASK-0099, still
  TODO, correctly resequenced behind TASK-0105 which is now Done).
- **HYP-P6 is now the subject of a dedicated, filed task set, not an open aside.**
  TASK-0108/0109/0110 (filed 2026-07-15, TASK-0109/0110 still TODO) directly build the
  `check_convergence` validity gate and Optuna floor/ceiling scan this hypothesis calls
  for — this file's own 2026-06-21 "to test: sweep t_max 1 to 200" prescription is now a
  real, scoped task rather than a discussion note.
- **HYP-P1 is weakened, not yet formally falsified.** The operator-sweep register
  (TASK-0101, 96 cells) and the cutoff/weight-scheme benchmark (TASK-0067) both show
  near-chance AUCs once proximity is controlled for, across nearly every operator in the
  register — including the ones most directly built around slow-GNM-mode participation
  (`V_M`, `H_new`). No task has yet run the clean ablation this hypothesis's own "To test"
  section calls for (rigid vs. multi-domain vs. IDP benchmark, checking whether AUC drop is
  domain-restricted) — still open, now more urgent given how much of the operator register
  is failing on these specific 3 targets.
- **HYP-P5 (H13 ceiling) — SUPERSEDED, closed by TASK-0126 (2026-07-18).** This note
  originally flagged the H13-vs-`H_new` comparison as untested and unfiled; TASK-0126
  ran it (both projection options, all 3 targets where feasible) and found neither
  option beats `H_new` — see HYP-P5's own status update above and
  `.ai/tasks/DONE/TASK-0126-h13-ceiling-comparison.md`. TASK-0116's separate concern
  (search density within `H_new`'s own DOF) remains open on its own terms, unaffected
  by this closure.
- **New, cross-cutting finding not anticipated by any hypothesis above: seed cardinality is
  an unexamined GAUGE choice that flips signs.** TASK-0093 found that narrowing the CTQW
  source from the full active-site residue array to `run_challenge.py`'s single
  lowest-index-residue workaround (a TASK-0090 crash fix, not a physics choice) is *the*
  dominant driver of KRAS_G12C's AUC — moving it from ~0.44-0.53 (array) to ~0.78-0.82
  (scalar) — a bigger swing than any of the three variables (cutoff/pocket-label/frame)
  this task was originally scoped to test. TASK-0106 independently hit the same seam on
  BCR_ABL1 (full-array seed flips `H_new` from lowest-scoring to *highest*-scoring of four
  operators, AUC 0.567 vs. the established 0.525). `ceiling.py` and `run_challenge.py` were
  separately found (2026-07-15, per `EXECUTION_PLAN.md`'s note preparing the 5bbcdc4 batch)
  to already use these two different conventions for the *same* active site, unnoticed
  until then. Per `INVARIANCE_PROTOCOL.md`, "which residue(s) count as the seed" is a GAUGE
  choice that has never been classified or registered — **no `INV-XXXX` record and no owning
  task currently exist for this**, despite it now being implicated in two separate headline
  reconciliations. Cross-referenced in [[Q-0003]] but not yet resolved into its own task.

### Status update, 2026-07-16 — HYP-P6 closed out (superseding this bullet's "still TODO")

The HYP-P6 bullet above ("TASK-0108/0109/0110... TASK-0109/0110 still TODO") is now
stale: **TASK-0109** (built `check_convergence`/`min_adequate_t_max`, the `t ≈ 1/Δλ`
tool this hypothesis called for) and **TASK-0119** (applied it — re-ran the 96-cell
sweep and TASK-0106's BCR_ABL1 reproduction under per-operator `t*` instead of the
shared `t_max=15`) are both Done. See HYP-P6's own entry above for the real finding
(ranking is genuinely t-sensitive on CARDIAC_MYOSIN; `H_new`'s localization is not).
TASK-0110 (Optuna scan) status not touched by this update — not this thread's work.

### Status update, 2026-07-17 — TASK-0110 (Optuna scan) Done; sharpens HYP-P6 further

**TASK-0110** is now Done, closing the gap the 2026-07-16 update above left
open. Where TASK-0119 applied `min_adequate_t_max(kind="ground_state_
relaxation")` (a 2-eigenvalue-gap criterion) to the operator sweep,
TASK-0110 ran an Optuna search over `time_averaged_ctqw`'s own `(t_max,
n_steps)` — the AAKV all-pairs-min-gap criterion this hypothesis's own
"Resolved" note above did not exercise, and which TASK-0109 itself
flagged as fragile on near-degenerate spectra. Two findings beyond
HYP-P6's own original scope:

1. **The clock gap is far larger than "t_max=15 is 100x too short"
   (the panel's own order-of-magnitude estimate)**: the closed-form-
   required `t_max` for `time_averaged_ctqw`'s own convergence is
   145,000x (BCR_ABL1) to 3,950,000x (CARDIAC_MYOSIN) the current
   default, measured on real `H_new`, not estimated.
2. **Reaching it is currently not computable**, not merely expensive —
   a single `time_averaged_ctqw` call at the prescribed `(t_max,
   n_steps)` did not return after 2+ hours on real KRAS_G12C data
   (`propagators.py`'s O(n_steps) Python loop). "Fix the clock" (this
   hypothesis's own alternative 2, and the panel's P0#2) is therefore
   not a parameter change that can simply be applied to the shipped
   defaults — it requires either an algorithmic change to
   `time_averaged_ctqw` (the decoherent infinite-time limit this
   pipeline already treats it as equivalent to has a cheap closed form,
   `Σ_k|v_k(j)|²|v_k(source)|²`, no time loop at all) or accepting
   `t_max` far short of true convergence, permanently.

A capped, honestly-sampled "practical ceiling" (searching only the
`t_max` range where `n_steps` stays computationally tractable) found
real per-target results, not just the infeasibility finding above:
KRAS_G12C 0.4750 (near chance, cross-validates TASK-0046's independent
0.5250 on a different parameter axis); **BCR_ABL1 0.5829 at t_max=2.39**
— smaller, not larger, than the default, a genuine unexploited-headroom
finding this hypothesis's own "To test" section did not anticipate;
CARDIAC_MYOSIN 0.8149 (inherits that target's existing 5TBY caveat).
Full detail: `.ai/tasks/DONE/TASK-0110-optuna-apo-holo-parameter-scan.md`,
`.ai/invariants/INV-0005-propagator-time-parameters.md`'s matching
update, `.ai/seams/SEAM-0012...md`'s matching update.

---

## HYP-P8 · For several targets, the apo contact graph does not contain the allosteric pocket signal at all

**From the discussion:**
> "Cryptic allosteric pockets often do not exist in the apo conformation; they open
> only on binding. If the pocket region rearranges substantially apo→holo, then the
> apo contact graph physically does not encode the answer, and no topology-only method
> can recover it."

**This must be tested before running the ceiling**, as it is the learnability gate.

**Method (Phase 1):**
1. Superpose holo onto apo via Kabsch/SVD on aligned Cα
2. Measure per-residue apo→holo RMSD at the annotated pocket residues
3. If RMSD at pocket >> RMSD at non-pocket (large pocket rearrangement), classify
   target as "cryptic-structural" — the pocket is absent from apo topology
4. Report these targets as "not learnable from apo coordinates" — not dropped silently

**KRAS prior:** The Switch-II pocket RMSD on apo→holo transition is substantial.
Combined with the near-chance ceiling (~0.53), this is already consistent with
HYP-P8. The Phase 1 measurement will confirm it.

**If HYP-P8 holds for most targets:** the honest finding is that topology-based
quantum/classical walk methods are fundamentally limited on cryptic allosteric
pockets, and the contribution of H_new design is bounded by the learnability of the
problem, not by method quality.

**Resolved 2026-07-17, TASK-0120 — the Phase 1 measurement this hypothesis
itself called for (never run until now) is done, and the result is more
nuanced than "HYP-P8 holds," not a clean confirmation.** Real Kabsch
superposition + Tama-Sanejouand cumulative overlap, all 3 mandatory
targets (method exactly as specified above, plus a background-RMSD
comparison this file's own Step 3 implies but never made explicit —
added as `superpose.background_rmsd`/`learnability_verdict`):

- **KRAS_G12C: `LEARNABLE`, not cryptic-structural.** Pocket RMSD (1.863
  Å) is 2.27x background (0.820 Å) -- real, differential displacement,
  consistent with this file's own "KRAS prior" line above. But
  cumulative overlap onto the apo ANM's lowest 20 modes is **0.638**,
  well above a 0.5 low-overlap bar -- the apo→holo direction *is*
  substantially spanned by the soft-mode subspace. This file's 2026-06-21
  "KRAS prior" reasoning (large pocket RMSD + near-chance ceiling ⟹
  consistent with HYP-P8) turns out to have skipped the actual
  discriminating measurement (CO) and inferred cryptic-ness from RMSD
  alone -- the direct test does not support that inference for this
  target. See `RESULTS.md`'s own "Learnability gate" section for the
  full cross-reference against `REVIEW-panel-2026-07-16-v2.md`'s
  separate (and still valid) Switch-II/active-site-overlap point, which
  this measurement neither confirms nor refutes -- a different claim.
- **BCR_ABL1: pocket moves *less* than background** (ratio 0.49) --
  the opposite signature from a cryptic opening, and consistent with
  (not contradicting) this project's own "apo-computable structural
  prior" finding for this target (TASK-0104).
- **CARDIAC_MYOSIN**: confounded by its own independent 5TBY
  data-quality issue (largest background RMSD of the three, lowest
  apo/holo residue-correspondence coverage) -- not a clean read either
  way.
- Cumulative overlap is blocked for BCR_ABL1/CARDIAC_MYOSIN by
  `anm_modes`' rigid-body-mode assertion (`n_zero=7`/`10` instead of 6),
  a real, separately-filed gap ([[TASK-0128]]), not silently
  worked around.
- **[[TASK-0124]], 2026-07-20**: CARDIAC_MYOSIN's apo replaced 5TBY ->
  8QYP (real X-ray, resolves its own `n_zero=10` floppy-mode issue to a
  clean 6). The RMSD/CO numbers directly above were computed against the
  now-retired 5TBY apo and are stale, not yet re-run under 8QYP — blocked
  on a real, separately-filed gap in `align_apo_holo`'s own chain-letter
  matching ([[TASK-0144]]), not silently worked around. See
  `COMPETENCE_MAP.md`'s own CARDIAC_MYOSIN section for the full
  floor/ceiling/actual re-run, which does not depend on this gate.
- **[[TASK-0150]], 2026-07-24**: re-run under the now-fixed chain map
  ([[TASK-0144]]) plus a second, independent CO-quantity bug fixed the
  same day (`scripts/learnability_gate.py` was still using
  whole-structure `cumulative_overlap`, not the pocket-restricted
  quantity [[TASK-0139]] already established as correct — that script
  was never actually updated despite TASK-0139's own claim otherwise).
  **CARDIAC_MYOSIN's verdict flips to `UNLEARNABLE_FROM_APO`** (ratio
  1.57, restricted CO(20)=0.254) — the pocket is no longer "confounded,
  unclear either way" as this bullet originally said; under the real,
  corrected apo it reads cleanly cryptic, corroborating [[TASK-0124]]'s
  own independent AUC-side finding from a structural angle. KRAS_G12C's
  own bare-threshold reading (no percentile null applied in this live
  path) is `UNLEARNABLE_FROM_APO`, distinct from [[TASK-0139]]'s own
  fully null-resolved `AMBIGUOUS` — both documented, not reconciled into
  one number. Full table: `RESULTS.md`'s learnability-gate section.

**Practical upshot**: the 2026-07-15 status-update bullet below ("HYP-P8
is now strongly supported") was built from *indirect* evidence about
whether this pipeline's *scoring* finds real signal (seed artifacts,
proximity confounds, localization) -- a different, broader claim than
HYP-P8's own narrow structural one ("is the pocket in the apo topology
at all"). Both can be true independently: the method may fail to find
signal for reasons unrelated to whether the apo structure spans the
opening direction. This measurement is the first direct test of the
narrow claim, and for the one target the panel specifically named
(KRAS_G12C) it does not confirm "unlearnable from apo" -- it points the
other way. Full numbers: `RESULTS.md`,
`.ai/tasks/DONE/TASK-0120-learnability-gate-hyp-p8.md`.

**Superseded for KRAS_G12C, 2026-07-20 (TASK-0139) -- the "LEARNABLE,
not cryptic-structural" reading above rested on a whole-structure
cumulative-overlap number, not a pocket-specific one, found by TASK-0133
(2026-07-19).** The properly pocket-restricted CO(20) is 0.458, not
0.638, and sits at only the 93rd percentile of a random-same-sized-patch
null (one-sided p≈0.07) -- elevated, but not significantly so at this
project's own 0.05 bar. TASK-0139 resolved which quantity this
hypothesis's own test should use (pocket-restricted -- the RMSD half is
already region-specific, per this file's own Step 2/3 above; a
whole-structure CO answers whether *some* motion is mode-spanned, not
whether *the pocket's own* motion is) and replaced the un-derived
`co_threshold=0.5` cutoff with a direct significance test against this
random-patch null (new `superpose.learnability_verdict(co_percentile=
...)`). **Result: KRAS_G12C is `AMBIGUOUS`, not `LEARNABLE`** -- the
pocket RMSD signature is real and clears its own bar (2.27x background),
but the CO evidence is genuinely inconclusive, not affirmatively high.
This is closer to HYP-P8's own original spirit than the 2026-07-17
reading was (real, if partial, support for pocket-specific structural
change; the mode-spanning question is undecided rather than answered
"no"), still short of the "textbook cryptic case, no method could find
it" framing the panel originally predicted. BCR_ABL1/CARDIAC_MYOSIN's
`LEARNABLE` verdicts are unaffected (RMSD-determined, confirmed
programmatically). Full numbers: `RESULTS.md`'s learnability-gate
section, `.ai/tasks/DONE/TASK-0139-kras-learnability-reclassification-decision.md`.

**Status, 2026-07-24 (TASK-0120/TASK-0139/TASK-0150; dated line backfilled
2026-09-03 via [[TASK-0323]]/[[TASK-0324]]): MIXED, target-dependent — not
population-resolved on 3 targets.** Current per-target reading, most-recent
verdict each: KRAS_G12C `AMBIGUOUS` (TASK-0139), BCR_ABL1 `LEARNABLE`
(unaffected), CARDIAC_MYOSIN `UNLEARNABLE_FROM_APO` (TASK-0150). Mixed
1-for/1-against/1-ambiguous across the only 3 mandatory targets — does not
resolve this hypothesis's own population-level "for several targets" claim
either way. The trail above already existed and is unchanged; this line
only adds the top-level dated verdict summarizing it.

**Status update, 2026-09-04 ([[TASK-0326]]'s full corpus sweep) — six
more independent lines of evidence folded in, none changing the
mixed/target-dependent verdict above, all pointing the same direction.**
- **Foundational baseline** ([[TASK-0094]], 2026-07-13): zero of the 3
  mandatory targets clear their own apo-only proximity floor — the
  measurement [[TASK-0093]]/[[TASK-0102]]/[[TASK-0104]]'s own citations
  above are built on, not itself previously cited.
- **Dynamical extension — perturbing apo does not create what it
  lacks** ([[TASK-0015]], 2026-07-28; [[TASK-0187]], 2026-08-01):
  letting the apo structure move along its own low-frequency ANM modes
  (not held rigid) never creates a graph-topology shortcut between
  active site and pocket, 7/7 targets, 60 candidate perturbations
  tried per target; an independent matched-decoy specificity gate on
  the same question also FAILS on PTP1B (real shortcut rate 1.7% vs.
  decoy median 12.9%, wrong-signed). Absence of the signal in static
  apo topology is not an artifact of holding the structure rigid.
- **Seed-cardinality gauge fix collapses the pipeline's one surviving
  positive** ([[TASK-0118]], 2026-07-16; [[TASK-0129]], 2026-07-17):
  CTQW seed cardinality (single-residue vs. full active-site array),
  not coherence, dominates AUC variance (spread up to 0.326);
  correcting it alongside the clock fix (see [[HYP-P6]]) reverses
  CARDIAC_MYOSIN's only surviving positive result — under the fully
  corrected gauge, no mandatory target's shipped result clears its own
  floor.
- **Generalization-set corroboration** ([[TASK-0081]], 2026-07-15;
  [[TASK-0127]], 2026-07-18; [[TASK-0170]], 2026-07-28; [[TASK-0186]],
  2026-08-01): the pattern replicates on 4 further real ASD targets
  never used in any prior review cycle (all land in
  `BEATS_CHANCE_NOT_FLOOR`, overlapping CIs), sharpens under a
  literature-curated (not drug-contact) PTP1B ground truth (2/3
  observables score significantly *below* floor), and the underlying
  static topology shows min hop-distance=1 on 6/7 targets with wide
  per-target variance in how much of the pocket sits that close
  (0%-83%).

---

## HYP-P9 · A chiral (broken-time-reversal) walk yields a proximity-orthogonal, directional loop observable

**Claim:** Replacing the real-symmetric operator's hoppings with complex
Peierls phases (a uniform "magnetic" field B, flux = B·(loop area)) produces
a directed bond-current whose Helmholtz-Hodge *circulating* component is
orthogonal to the radial proximity flow by construction, and which tracks
active-site *coupling* rather than distance-to-seed. This is the physically
justified form of "controlled phase shifts" (the collaborator's Idea #2):
an arbitrary initial phase on a real-symmetric H only reshuffles amplitudes
and is an unjustified, label-leaking knob; the only gauge-invariant phase
effect is around cycles.

**Supporting evidence:** Chiral quantum walks break time-reversal only on
cyclic topologies (Zimborás et al. 2013, Sci. Rep. 3, 2361; Lu et al. 2016,
PRA 93, 042302). On synthetic gates this batch: the circulating current
(i) dissociates coupling from well-depth where single-particle imaginary-time
occupation chases the well, and (ii) beats the proximity floor on a distal
loop pocket with residual ρ(score,−dist)≈+0.33 vs the occupation's +0.6..+0.97.
The Hodge gradient/curl split maps exactly onto proximity-flow / loop-signal.

**Counter-evidence / conditions under which this fails:**
- **Single-particle → classically tractable.** This is a *modeling* advantage
  (directionality, loop-native, proximity-orthogonal), not asymptotic quantum
  advantage. The converged occupation limit is provably phase-free
  (TASK-0130); the chiral current is a different, time-reversal-odd observable.
- **No real loop signal.** If pockets are not graph-open (HYP-P10 FAIL), there
  is no non-proximity cycle to circulate in and the score collapses to the
  floor. The synthetic passes prove the observable *can* read a loop, not that
  real pockets carry one. **This is now the measured outcome, not a
  hypothetical counter-evidence bullet: HYP-P10's own 2026-07-22 status
  update (TASK-0143) found 0/7 targets pass the pre-registered graph-openness
  gate.** [[TASK-0140]] should treat this observable as gated on an
  unsupported premise, not proceed as if the premise were open.
- **Seed/field gauge.** A field direction or source seed tuned to labels would
  reintroduce overfitting; the flux content is gauge-invariant only if the
  field grid is fixed blind to labels.

**To test:** [[TASK-0140]] — gated benchmark eval vs the proximity floor with
block-bootstrap CIs and distance-stratified AUC + permutation null.

**Status, 2026-09-03 ([[TASK-0310]], [[TASK-0320]]): re-tested under a corrected
statistic and still FAIL — this hypothesis is CLOSED.** [[TASK-0140]]'s original
verdict was reached on raw AUC against a floor, before proximity was known to be
the dominant confound. [[TASK-0310]] re-scored the observable **residualised on
proximity** across 108 ASBench structures: raw AUC 0.5560 → **0.4960, below
chance**, cluster-p 0.799. Its rho against proximity (0.365) is genuinely about
half CTQW occupation's (0.735), exactly as this hypothesis predicts — but lower
contamination did not translate into surviving signal. **The construction with
the strongest available prior — circulating component orthogonal to the radial
flow *by construction*, not by tuning — carried nothing.**

**Do not re-propose complex hopping / a synthetic gauge phase as an open route.**
It is implemented (`src/allostery/chiral.py`, Peierls substitution,
`H[i,j] = -W[i,j]*exp(i*theta_ij)`, complex-Hermitian), it was run with a
field-scale sensitivity sweep, and it has now failed under both the original and
the corrected statistic. A draft of [[TASK-0320]]'s collaborator brief listed it
as an open lead; that was written from inference rather than from this file, and
was corrected on review.

**Status update, 2026-09-03 ([[TASK-0320]], extended 2026-09-03 by
[[TASK-0325]] "reverse-CTQW v2", via [[TASK-0326]]'s sweep) — the
reverse-seeded-CTQW pocket-selection construction this hypothesis's own
chiral-walk idea inspired is also closed, for a distinct reason.**
[[TASK-0320]] tested reverse-seeded CTQW directly as a pocket-selection
method (separately from the chiral-circulation observable above) and
found it does not select allosteric pockets. [[TASK-0325]] isolated why:
when a predictor-consensus gate restricts the candidate pocket pool
before ranking, essentially all of the resulting improvement comes from
the restriction itself (random-within-gate top-1 hit rate rises from
2.5% to 11.4% at a top-3 gate — a 4.5x gain, at the cost of discarding
the true pocket in 65.7% of structures); CTQW-based ranking within the
gated pool never beats random-within-the-same-gate at any gate width
tested (McNemar vs. fpocket druggability: p=0.63/0.50/0.0005/0.0003,
worse where the gate is loose), and raw cavity size remains the best
available within-gate selector. The predictor gate does the
discriminating work; the walk adds nothing.

**Related, not the same construction ([[HYP-P25]], 2026-09-06):** a
different pipeline (PASSer-seeded veto, [[TASK-0327]]) built directly on
the forward CTQW score (no reverse-seeding, no predictor-consensus gate)
shows a distinct, gate-independent proximity-anticorrelation mechanism —
see that hypothesis for the measurement.

**Status, 2026-07-23 (TASK-0140): tested, claim not supported on real data — FAIL,
consistent with HYP-P10's own FAIL.** Reference script confirmed absent (as flagged
above); reconstructed independently from this hypothesis's own description + the cited
literature, and re-verified GATE 1 (coupling-vs-well dissociation) and GATE 2
(beats-floor-on-synthetic-loop-pocket) on the fresh reconstruction rather than
inheriting the missing script's claimed pass status (both pass, with this
reconstruction's own numbers, not the unrecoverable original's 0.33/0.6-0.97). On all
3 mandatory + 4 ASD targets: **the proximity-orthogonality claim itself is confirmed
cleanly on 7/7 targets** (rho(circ,-dist) consistently smaller in magnitude than
rho(occ,-dist): circ range -0.22 to -0.48 vs occ range -0.43 to -0.74) — but this task's
own pre-registered PASS bar (floor-beating AUC AND non-overlapping 95% block-bootstrap
CIs) is not met on any target; CI overlap is `True` everywhere. Two targets
(KRAS_G12C mandatory, PTP1B ASD) show real, Bonferroni-surviving signal on the
independent stratified-AUC permutation-null statistic alone (p=0.0030, p=0.0020 vs
threshold 0.00714) — reported as suggestive, not a PASS, since the primary CI criterion
governs. Full detail: `.ai/tasks/DONE/TASK-0140-chiral-circulation-observable.md`.
**Neither HYP-P9 nor HYP-P10 opens [[TASK-0142]]'s own hard gate.**

---

## HYP-P10 · Cryptic pockets carry a "near-in-3D / far-on-apo-graph" coordinated-closure signature

**Claim:** The residues a ligand bridges on binding are Euclidean-near but
graph-hop-far in the *apo* contact graph (the open cleft means the apo graph
does not connect them), so mean(apo graph-hop)/mean(Euclidean) among the
pocket residues is anomalously high vs a matched-spread random cluster.

**Supporting evidence:** This is close to the *definition* of a cryptic
pocket (spatially coherent in holo, not connected in the open apo state), so
the premise is more plausible than the generic single-loop idea (which
Falsifier A killed: at 8 Å a spatial cluster is already a clique; a single
ligand chord adds triangles indistinguishable from a decoy, and ambient
b1~8N dwarfs it). On the constructed open-cleft synthetic the signature hits
the ~100th percentile against a matched-spread null.

**Counter-evidence / conditions under which this fails:**
- **Grooves.** A shallow surface groove is contractible and graph-adjacent
  already — no near-space/far-graph anomaly. If the benchmark pockets are
  grooves rather than closing clefts, the signature is absent.
- **Pre-formed pockets.** BCR_ABL1's myristoyl pocket moves *less* than
  background (ratio 0.49, TASK-0120) — likely already graph-connected in apo,
  so this signature should be weak-to-absent there (a per-target prediction).
- **Distinct from the existing openness gate.** This is NOT
  `cumulative_overlap`/`cryptic_openness_gate` ([[TASK-0059]]/[[TASK-0120]]),
  which asks whether the apo→holo displacement is soft-mode-spanned — an
  orthogonal *dynamics* question that can agree or disagree with this
  *structural-graph* one.

**To test:** [[TASK-0143]] — matched-spread random-closure null, all mandatory
+ ASD targets, Bonferroni. This is the premise gate for HYP-P9/P12.

**Status, 2026-07-22 (TASK-0143): tested, claim not supported — 0/7 targets PASS.**
Real synthetic-verified implementation (`allostery.closure`, positive control lands at
the ~100th percentile as this file's own text predicted) run on all 3 mandatory + 4 ASD
targets. Per the pre-registered gate (>95th percentile AND Bonferroni-significant
across 7 targets): **zero targets pass.** KRAS_G12C (98.4th percentile, p=0.016
uncorrected, p=0.112 Bonferroni) and CASPASE1 (90.2nd percentile) are INSUFFICIENT —
suggestive, not decisive. CASPASE7 is a clean FAIL (26.8th percentile — its pocket is
*less* graph-far than a typical matched-spread random cluster, the opposite of this
hypothesis's own claimed direction). **BCR_ABL1, CARDIAC_MYOSIN, PTP1B, GLUCOKINASE
could not be tested at all** — the matched-spread null itself is infeasible via
unbiased rejection sampling at the pre-registered +/-35% tolerance (0-19 replicates
found out of 500 needed, even at 20M attempts), because a same-size random cluster
matching a real compact pocket's spread is intrinsically rare among uniform draws over
a large protein. This is itself a real finding (real pockets are far more spatially
compact than typical random same-size subsets) but a distinct property from this
hypothesis's own graph-openness claim, and not fixable within this task's own scope
(would require redesigning the null's sampling scheme, explicitly Out Of Scope after
seeing the outcome). **This is the premise gate for HYP-P9/P12 — neither is supported
by this result.** Full detail: `.ai/tasks/DONE/TASK-0143-openness-premise-real-targets.md`.

---

## HYP-P11 · Engineered dephasing (ENAQT) does not improve pocket discrimination — it relaxes the walk to the classical/proximity limit

**Claim:** Sweeping a Haken-Strobl dephasing rate γ finds no interior optimum
that improves *discrimination* of pocket vs background, because increasing γ
de-traps the Anderson-localized walker only by driving it toward classical
diffusion, whose occupation is the proximity confound. The ENAQT "optimal
rate" from the transport literature optimizes a different quantity (transfer
efficiency to a known sink), not discrimination.

**Supporting evidence:** Synthetic γ-sweep this batch (`enaqt_sanity.py`):
AUC flat-then-collapsing (0.72→0.16 as γ:0→5) while ρ(occ,−dist) rose +0.10→
+0.68, reaching +0.92 at the classical endpoint. Consistent with the existing
register finding that ENAQT enhances transport 1.24–1.70× but degrades
discrimination in every observed cell, and with the phase-free converged
limit (TASK-0130). Transport-efficiency optima: Mohseni-Rebentrost-Lloyd-
Aspuru-Guzik 2008; Rebentrost 2009; Caruso 2014; Viciani 2015 (experimental
optimum) — all for transfer to a fixed trap, not pocket ranking.

**Counter-evidence / conditions under which this fails (i.e. would overturn):**
- If some interior γ on real data clears the proximity floor with
  non-overlapping CIs and beats the coherent γ=0 point, the prior is wrong and
  the result folds into the submission. The prior is a synthetic; real data is
  the test. This is why the task is run, not assumed.
- The Zeno regime (γ→∞ freezing) is a distinct failure from the classical-
  diffusion crossover; the prior is that discrimination dies at the crossover,
  *before* Zeno — the sweep should report which mechanism dominates.

**To test:** [[TASK-0141]] — γ-sweep on KRAS/ABL/PTP1B, scoring discrimination
AUC vs floor (NOT transport), with the mandatory γ→∞ classical-limit sanity
endpoint and localization-length-vs-γ as the mechanism covariate.

**Status, 2026-07-20 ([[TASK-0141]]; dated line backfilled 2026-09-03 via
[[TASK-0323]]/[[TASK-0324]]): CONFIRMED on real data — NEGATIVE on 3/3
mandatory targets, matching the pre-registered synthetic prior.** No γ
clears the proximity floor with non-overlapping CIs on any of
KRAS_G12C/BCR_ABL1/PTP1B; best-of-8-γ permutation null p=0.649/0.211/1.000
vs. Bonferroni α=0.0167.

---

## HYP-P12 · The coordinated multi-site closure is a topological void (persistent H2 / Hodge-L1), and this is the only rung where a genuine quantum-advantage object coincides with the biology

**Claim:** A buried pocket a ligand caps is an H2 *void* (not an H1 loop), and
the ligand-as-k-simplex is captured by the Hodge Laplacian L1 (dim ker L1 =
b1; its non-harmonic edge-modes are the flow around the multi-loop cage), both
of which the graph Laplacian discards. Persistent H2 of the apo complex should
localize buried pockets that H1/graph-level observables and grooves miss.

**Supporting evidence:** CrypToth (challenge ref [2]) uses topological data
analysis for cryptic-pocket detection. Falsifier D: a true ring gives a stable
persistent b1; a filled disk / contractible bowl do not (once persistence is
done correctly) — grooves are topologically invisible, consistent with pockets
being voids, not loops. Betti-number / Hodge-Laplacian estimation (Lloyd-
Garnerone-Zanardi) is the canonical (regime-dependent, partially dequantized —
Tang; Gyurik-Cade-Dunjko) quantum-advantage candidate defined on exactly this
structure; Jones-polynomial approximation of the closed curve is BQP-complete
(Aharonov-Jones-Landau).

**Counter-evidence / conditions under which this fails:**
- **Cα resolution.** At an 8 Å Cα cutoff the complex is dominated by spurious
  intermediate-radius cycles (Falsifier D); a real void may not survive to a
  clean persistent H2 generator. Real persistence tooling (GUDHI/Ripser),
  never a homemade b1, is mandatory.
- **Dequantization.** LGZ's speedup survives only in dense-complex / favorable-
  Betti-ratio regimes — the advantage is regime-dependent, a *proposal* claim,
  not a demonstrated one. The classical observable is what this hypothesis
  tests; the quantum claim is forward-looking.
- **Inherits HYP-P10 — L1 half only, corrected 2026-07-22.** The Hodge-L1
  joint-support score is a cycle/loop-flow quantity (same family HYP-P10's
  graph-openness test bears on) and remains gated on HYP-P10/HYP-P9 showing
  life. **The H2 half does NOT inherit this**: a capped H2 void requires its
  lining residues to be graph-*adjacent* (close), the opposite signature from
  the open-cleft graph-*far* premise HYP-P10 tested — demonstrated directly
  (`test_void_detected_even_when_lining_is_graph_adjacent`, a constructed
  cavity with graph-near walls still registers, mean lining hop 1.44 on the
  synthetic cryptic-cavity control). HYP-P10's 0/7 falsifies the open-cleft
  premise; it says nothing about capped voids.

**To test:** [[TASK-0142]] — L1 joint-support score (gated on HYP-P10/HYP-P9
showing life, still closed) + persistent H2 generator localization (ungated,
2026-07-22 correction) vs a matched random-patch null. b1(ker L1) == E−N+C as
the setup-validity gate for the L1 half.

**Status, 2026-07-24 (TASK-0142, H2 half only — L1 half not run, still
gated): tested, claim not supported — FAIL on all 3 mandatory targets, a
clean and in one case sharply informative negative.** 2/3 targets
(KRAS_G12C 0.669, BCR_ABL1 2.404) show no H2 void at all — top persistence
sits at/below the synthetic solid-ball noise floor (2.5); per the module's
own design this returns an honest all-zeros score (chance AUC), and the
nominal "ungated" score's apparent floor-beating on both targets is
explained away by the matched random-patch null (77.1st/46.3rd percentile,
p=0.229/0.537 — indistinguishable from a random patch). The one target with
a detected void, CARDIAC_MYOSIN (2.829), has it in the **wrong place**: AUC
0.192 (anti-ranks the real pocket), random-patch-null percentile **0.0** —
a large protein has multiple internal cavities, and the most-persistent one
found is not the ligand pocket. Residue-localization weak link (crude
geometric centroid heuristic, `ripser` doesn't return H2 cycle
representatives) confirmed on real data, not just the synthetic control:
proximity floor (0.583) beats `void_score` (0.192) on CARDIAC_MYOSIN, same
pattern as the synthetic control (0.824 vs 0.576). Full detail:
`.ai/tasks/DONE/TASK-0142-hodge-l1-persistent-h2.md`. **L1 half not
attempted — its own gate (TASK-0143 or TASK-0140 showing life) remains
closed, both are FAIL as of 2026-07-23.**

**Provenance note (added 2026-07-20, Architect/Planner):** HYP-P9–P12 and
TASK-0140–0143 above were generated by an external review batch
(`REVIEW-panel-2026-07-20`, applied from `.ai/reviews/2026-07-20/`). The
batch's own task-numbering (`TASK-0139..0142`) collided with an
already-existing, unrelated `TASK-0139` (KRAS_G12C learnability
reclassification) — renumbered to `TASK-0140..0143` throughout (the
already-correct `TASK-0140`/`0141`/`0142` files were left as-is; the
openness-premise task became `TASK-0143`). The batch's own reference
implementations (`chiral_observable.py`, `closure_test.py`,
`enaqt_sanity.py`) are not present in the applied batch or anywhere else
in this repo — flagged in each consuming task file, not silently assumed
to exist. `REVIEW-panel-2026-07-20.md` itself (the source review these
hypotheses and tasks cite) was also not generated/delivered — the
citation chain is currently open; generate it if the citation should be
closeable the way prior batches' reviews are.

---

## HYP-P13 · Allostery is stabilisation of an otherwise-disfavoured conformation, not a signal propagating to the active site

*Origin: orchestrating collaborator (Bartosz), 2026-08-22, arrived at independently.
Filed in `physics.md` rather than `search_complexity.md` — the primary claim is
mechanistic; its complexity consequence is secondary and cross-linked there.*

**Claim.** There is no allosteric *signal* travelling from pocket to active site.
A protein occupies an ensemble of conformations; some of those have a compromised
active site; a drug binds a pocket that happens to be **present in one of those
conformations** and stabilises it. The observed "allosteric effect" is population
redistribution toward an inactive state — not transmission along a path.

**Status in the literature: this is mainstream, and the challenge cites it.**
It is Monod–Wyman–Changeux conformational selection (ref [5], Changeux &
Edelstein 2005, DOI 10.1126/science.1108595, citation re-verified live
[[TASK-0251]] — this register's own H5.1 *is* this claim's formal literature
statement, folded into HYP-P13 rather than tracked separately, [[TASK-0251]]
2026-08-24) in its modern ensemble formulation (ref [4], Motlagh, Wrabl, Li
& Hilser 2014; ref [6], Tsai & Nussinov 2014). It is **not** novel to the field.
It is novel to this register as an organising frame, and it **directly
contradicts the challenge's own §5 Assumption** — *"the topology of the contact
network is the primary driver of signal propagation."* The challenge's §2 cites
[4] and [6]; its §5 mandates the elastic-network premise. Those are not
compatible. See [[TASK-0221]] organiser question (d).

### Why it is worth taking seriously: one mechanism predicts four of our findings

| Register finding | What HYP-P13 predicts |
|---|---|
| Every seed-referencing observable is a proximity detector ([[TASK-0226]]: classical 0.861/0.899, CTQW 0.697) | With nothing propagating, a seed-referencing observable on a static graph has only geometry left to measure. Distance is the default, not the defect. |
| Coherence adds nothing — flat γ-sweeps, phase-free converged limit, coherent ≥ ENAQT under noise | There is no interference to exploit in a quantity that is not propagating. |
| 28 observables collapse to effective rank ~3 ([[TASK-0199]]; externally reproduced at 3.65/11) | All of them measure the geometry of a single static structure, because that is all a single static structure contains. |
| fpocket — 2009, purely geometric, no propagator — beats every observable here on 2/3 targets ([[TASK-0163]], 2026-07-28; corroborated by a published classical GNM transfer-entropy baseline scoring 0/3 floor-clears, [[TASK-0132]], 2026-07-19, and by a within-fpocket-ambiguous-population test showing dynamics never resolves what static geometry cannot, [[TASK-0200]], 2026-08-04) | Geometry *is* the signal. A geometric detector should win. |
| CTQW's own non-distance signal, isolated by within-shell AUC, duplicates two simpler baselines (degree/euclid) rather than adding orthogonal information ([[TASK-0247]]); the ensemble-based EAM/COREX coupling metric ([[TASK-0229.006]]) is, on a decisive random-reference-site control, nearly as strongly explained by a candidate's own intrinsic κ_f as by the real active site (ρ≈-0.83 to -0.99 either way, [[TASK-0252]]) | Graph observables collapse to geometry; the ensemble-level observable collapses to intrinsic per-residue instability — the same signature (a seed/site-referencing quantity reduces to a site-independent property) recurring in a completely different observable class, not merely the graph-based ones. |
| The 1022-protein full run's own headline table looked like the first exception (CTQW beats every classical descriptor 69 vs ≤25 families, decisively on distal 19 vs 1) — until matched. It compares a max-over-221-cells (884 with the MIN_HOP sweep) CTQW statistic against a single fixed classical ranking, on two DIFFERENT candidate pocket sets (classical.py re-derives its own un-vetoed pockets; the CTQW number is round 2, post-veto) and two different truth-pocket definitions. Re-run on one candidate set (round 2's own stored pockets, every arm), one truth definition (any pocket touching a truth residue), one PRE-REGISTERED CTQW cell (not a max), and the same pocket-block null this register already uses: CTQW clears 4/276 families overall (0/48 distal) vs 5/276 for 3 of the 5 plain classical descriptors, and the distal margin the headline led with is exactly zero for every arm, CTQW included, after matching (chance-expected ~0.52 of one distal family clearing by luck alone, so the observed 0 is not even below the floor by much) ([[TASK-0336]], 2026-09-06). **Status update, 2026-09-07 ([[TASK-0338]]):** 4 vs 5 is not a real gap — exact Poisson 95% CIs are [1.09, 10.24] (CTQW) vs [1.62, 11.67] (classical), and the paired exact test on the same 276 families (McNemar, discordant families only: CTQW-only-clears=0, classical-only-clears=1) gives p=1.0. The correct reading is not "classical beats CTQW" but: *under matched multiplicity, a matched candidate set and a matched null, no arm — quantum or classical — clears more than 5 of 276 families, and the arms are statistically indistinguishable from each other and barely distinguishable from chance.* ([[TASK-0338]], `matched_comparison_result.json`'s own `paired_exact_tests_all_split`.) | The register's one apparent large-scale counter-example was a multiplicity/metric artifact, not a new result — matched fairly, this dataset says the same thing as every smaller one: geometry wins, and the walk adds nothing beyond it. The corrected reading strengthens rather than weakens that conclusion: it is not that classical narrowly beats CTQW, it is that neither beats a shuffled null by a distinguishable margin at this multiplicity. |

Five findings, one mechanism. That is a materially stronger claim than nine
independent route closures, and it is the kind of *novel insight* §4.3 item 1
asks for in place of a credible advantage.

**H4.4 (Motlagh et al. 2014 — coupling free energy does not decompose onto
graph edges), CLOSED ON ARGUMENT, [[TASK-0252]] 2026-08-24**: partition-
function-derived coupling is a nonlinear (log-sum-exp) transform of microstate
energies, non-separable into pairwise graph-edge terms except when sites are
statistically independent (i.e. not coupled at all) — a direct theoretical
reason every graph/pathway-shaped observable in this register (CTQW, hop,
propagation) sits in a representational class the field's own ensemble
formalism says is structurally insufficient for genuine allosteric coupling.
This is the mechanistic *reason*, not just a fifth data point, for the pattern
the table above documents. See [[TASK-0252]]'s own Done section for the full
argument and its consistency check against [[TASK-0229.006]]'s ρ≈0.5
EAM-vs-propagation correlation (partial, not full agreement — exactly what
"pathways are a high-flux subset, not the whole story" predicts).

### It also reinterprets our benchmark failures as mechanism rather than defect

**BCR-ABL1's `MYR` is the endogenous allosteric stabiliser.** Myristate binds the
myristoyl pocket to lock the autoinhibited state — the same job asciminib does.
So `1OPL` is not a broken apo structure: it is *the stabilised conformation, with
the endogenous ligand in place of the drug*.

Under a propagation model that is a benchmark defect ([[TASK-0209]]'s reading).
Under HYP-P13 it is the mechanism showing through — the "apo" pocket is open
because the protein is already in the stabilised state. The same rereading
plausibly covers CASPASE1's "intrinsically open" pocket, and possibly much of the

**Status update, 2026-08-26 ([[TASK-0278]], via [[TASK-0326]]'s sweep) —
decisive structural evidence for the claim two paragraphs above, and a
sharper mechanistic point the original prose didn't yet carry: occupancy
alone is not sufficient for allosteric *effect*.** A pocket being open
and ligand-occupied in a crystal structure only shows the pocket exists
in that conformation — it says nothing about whether the bound
molecule produces the allosteric outcome. Direct evidence: computationally
stripping `MYR`'s atoms from `1OPL` does **not** close the pocket
(fpocket AUC and window-druggability classification are bit-identical
before/after) — the confound is the crystallised backbone conformation
itself, which stripping the ligand's coordinates cannot relax back,
not merely "an atom happens to be present in the file." A register-wide
pocket-window-overlap classification rule (applied to all 29 apo
structures in `config/targets.yaml`) found a second, worse, previously
unflagged instance of the same defect: `PKR_MITAPIVAT`/`PKR_AG946`'s
shared apo (`7FS3`) has 91-92% window overlap with a named allosteric
modulator (`O9I`) — not remediated (non-mandatory target), flagged for
whoever curates that pair next. Full detail:
`.ai/tasks/DONE/TASK-0278-our-apo-structures-are-not-apo.md`.
5-of-7 failure rate: [[TASK-0209]] may have been measuring **conformational
state**, not data quality.

**This does not retract [[TASK-0209]].** Its measurements stand and its
consequence — those pairs cannot support a blind apo→holo prediction — is
unchanged either way. What changes is the *explanation*.

### Complexity consequence — and the measurement that cuts against the obvious reading

The search reformulates: not "propagate from the active site and rank distal
residues", but "enumerate conformational states → find those where the active
site is compromised → find druggable pockets present in them."

**Do not assume that is hard.** [[TASK-0185]] measured pocket recovery under ENM
sampling at **1–8 draws per hit** — finding *a* pocket in the ensemble is not
rare. If hardness exists it lives in the **conjunction**: a pocket that is
simultaneously (a) druggable, (b) present in a state with a compromised active
site, and (c) thermodynamically accessible. Nobody has measured that
intersection, and this register's repeated experience is that assumed-rare
things turn out common once measured ([[TASK-0185]], [[TASK-0213]]).

**Measurement:** the same progress-probability statistic [[TASK-0228]] §6.2
specifies, applied to the three-way conjunction. If it lands in the 0.24–0.69
band already measured for backbone sampling, the complexity claim closes.

### Consequence for the answer key

If allostery is stabilisation, the correct answer is not one pocket but the
**set** whose occupancy shifts the ensemble. The challenge supplies one
drug-bound site; ref [6] holds that sites are effector-specific.
[[TASK-0229.003]] (ASD multi-site audit) stops being a nicety and becomes
central — residues we score as false positives may be genuine allosteric sites
for a different effector.

### The discriminating experiment

- **Propagation** predicts a *directed*, distance-dependent response: perturb the
  pocket, observe a specific effect at the active site.
- **Stabilisation** predicts pocket and active site are correlated only because
  both are markers of the same global state — **no directionality**.

Partial read already in hand: [[TASK-0162]] found forward/reverse asymmetry
(10/25 vs 4/25), weak evidence *for* directionality — but measured on a static
apo graph, which HYP-P13 says is the wrong frame, so it should not be leaned on.

**The clean test is [[TASK-0229.006]] (COREX/EAM), and its pre-registered
negative control is already the discriminating one**: construct the case where
ensemble ranking and propagation ranking disagree. If they agree everywhere, the
distinction is empty on these targets. That control was written before this
hypothesis existed and happens to be exactly what it needs.

### What this does NOT establish

- **We have not run EAM.** The harmonic proxy has been tested and is itself
  proximity-confounded (|partial ρ| = 0.773, non-target structures) — so the
  *harmonic* version of ensemble coupling is no escape. The genuine nonlinear
  model (binary folded/unfolded units) is untested. HYP-P13 is a hypothesis that
  explains existing data, not a result.
- **It does not license any quantum claim.** If anything it points the quantum
  question at partition-function estimation over 2^N microstates
  ([[TASK-0229.006]]) — where the honest claim is *type-correctness*, never
  advantage.
- **It does not rescue the register's negatives into a positive.** It explains
  them. That is more useful, and it must not be oversold as more than that.

### Local energetic frustration — the direct, pre-registered test, and it fails ([[TASK-0268]], 2026-08-25)

**Pre-registered prediction** (written before a single frustration number was
computed, per this task's own Constraint that a favourable result from
Reviewer's own hypothesis is *less* trustworthy, not more): if HYP-P13 is
right, local energetic frustration should be elevated at true pocket
residues, **more so on genuinely-cryptic targets than already-open ones** —
a site whose native packing is already near-optimal has nothing left to
relieve by a population shift.

Single-residue mutational frustration (Jenik et al. 2012, *Nucleic Acids
Research* 40:W348-W351, doi:10.1093/nar/gks447 — citation verified live;
real PyPI `frustratometer` package found genuinely uninstallable in this
environment, `llvmlite`'s own LLVM toolchain dependency absent, not forced
through — a from-scratch port built instead, `allostery/frustration.py`,
Miyazawa & Jernigan 1996 pairwise potential, doi:10.1006/jmbi.1996.0114,
sourced from AAindex MIYS960101, sanity-checked before use) added as a 5th
attribution block (geometry/fpocket/SASA/CTQW/frustration) on
[[TASK-0243]]'s frozen set, added-last value, [[TASK-0261]]'s exact
cluster-permutation significance, [[TASK-0260]]'s own crypticity
stratification.

**Result: the predicted direction does not hold, and the effect is not
distinguishable from zero either way.** Frustration's own added-last
contribution: cryptic median −0.09% vs. open median +0.05% — cryptic is
numerically *lower*, the opposite of HYP-P13's own prediction (cluster-perm
p=0.452, nowhere near significant). Fraction of highly-frustrated residues
(z>0.78, the field-standard cutoff): cryptic 36.0% vs. open 35.2% —
essentially identical. Overall, frustration's own unique contribution once
the other 4 blocks are already in the model is indistinguishable from zero
(cluster-p=0.727). It does carry a real, positive Shapley share on its own
(+6.5% median, unconditional on ordering) — but this collapses to near-zero
added-last, meaning it is *redundant* with what geometry/fpocket/SASA/CTQW
already capture, not a source of new, crypticity-specific signal.

**Read plainly, with the same prominence a positive would have received**:
this is HYP-P13's own most direct empirical test to date, and it is a clean
negative. It does not disprove the broader population-shift picture (a
static-structure frustration index cannot rule out a genuine ensemble/
kinetic effect the way [[TASK-0229.006]]'s own EAM measurement more
directly probes), but the specific, falsifiable, sharp prediction this task
set out to test — cryptic sites carry more native frustration than
already-open ones — is not supported by real data.

### Repulsor-constrained SCMF retention — an independent route, and it turns out NOT EVALUABLE ([[TASK-0271]], 2026-08-26)

**Pre-registered prediction** (recorded before any structure was scored, per
this same Constraint): if HYP-P13 is right, a cryptic pocket displaced open
and repacked should **collapse** once the displacement is released and
side-chain repacking runs again on true, unmodified native apo geometry —
persistence would mean the open state is its own local minimum, independent
of the drug's own stabilising role.

**Method** (full pre-registration in the task file, not duplicated here):
the "pinned repulsor" is operationalised as the pre-registered full
apo→holo Cα displacement ([[TASK-0230]]/[[TASK-0235]]'s own already-
validated `local_rigid_reconstruction`, reused unchanged) — the same "hold
open" mechanism those two tasks and [[TASK-0213]] already used, now
extended with the release arm none of them ran. A trajectory
t ∈ {1.0, 0.75, 0.5, 0.25, 0.0} sweeps the displacement back to exactly
native apo (t=0.0 = identity transform = true apo, repacked independently,
no memory of the open state), on [[TASK-0243]]'s own 11 genuinely
cryptic-testing targets ([[TASK-0254]] Part B), N=4 trials at the two
decisive points with independent coordinate jitter + forced-distinct EvoEF2
seeds (hashed to confirm distinctness — [[TASK-0241]]'s own established
discipline), [[TASK-0204]]'s own `_is_hit` bar (overlap ≥0.5 AND
druggability ≥0.5) as the pre-registered retention criterion.

**The literal pre-registered rule returns COLLAPSES for 11/11 targets —
and that reading is misleading, not a clean win for the hypothesis it was
built to test.** The SAME `_is_hit` majority rule, applied symmetrically to
the fully-displaced "held open" state (t=1.0), ALSO returns a hit in fewer
than half the trials for every single target (0/4 for 9 of 11; 1/4 for the
other 2 — never a majority). **The pocket essentially never opens
correctly-located AND druggable in the first place, at any point along the
trajectory, including full displacement to the true holo target.** This is
floor-to-floor, not open-to-closed: nothing observably collapses, because
nothing observably opened. A cluster-level permutation test on the raw
hit counts (8 clusters over 11 targets, [[TASK-0261]]'s own exact
sign-flip method) does return p=0.0078 — reported for completeness, not
as support: it is measuring "hit rate is below majority" on a data set
with almost no variance either arm of the trajectory, not measuring
retention.

**Read plainly, with the prominence a positive would have received**: this
is [[TASK-0230]]/[[TASK-0235]]'s own long-standing finding (the strict
overlap+druggability ceiling is rarely cleared by rigid/local-Kabsch
displacement) reasserting itself and swamping the new question this task
set out to ask. **Verdict: NOT EVALUABLE**, joining [[TASK-0264]]/
[[TASK-0267]]'s own "closed on a prerequisite, not a clean test" category —
neither the decisive negative [[TASK-0268]]'s frustration test delivered,
nor support for HYP-P13. A descriptive side-note, not part of the formal
bar: druggability_score alone (ignoring the overlap half of the bar) is
sometimes *higher* at t=0.0 (true apo, freshly repacked) than at t=1.0 for
several targets (e.g. FBPASE_94D, NAMPT_NPA1R) — EvoEF2 repacking
native apo alone can open *some* cavity, just not reliably the correct
one — an echo of [[TASK-0230]] §5.3's own scorer-brittleness theme, not a
retention finding.

**Citation correction, made before implementation, not after**: Koehl &
Delarue 1994 (*J Mol Biol* 239(2):249-275, doi confirmed live via PubMed
8196057) is real and correctly attributed to SCMF **side-chain** packing —
but it is a fixed-backbone method; the filing's own claim that it is
"operationally what Rosetta's FastRelax has done for over a decade"
overstates it (FastRelax couples real backbone minimisation with
repacking; Koehl-Delarue's own method has none). This register's third
inherited citation detail requiring correction from an external source,
after [[TASK-0260]] and [[TASK-0262]].

**Status:** open, unowned as a whole — carries one genuine, decisive
negative ([[TASK-0268]]'s frustration test) and one test that turned out
not evaluable ([[TASK-0271]], this section) alongside [[TASK-0229.006]]'s
own inconclusive EAM-vs-propagation result (ρ≈0.5, neither closure
anticipated). Its formal literature grounding (H5.1) and the CS-vs-IF
distinguishability question are addressed by [[TASK-0251]] (2026-08-24) —
not decidable with a single static apo/holo pair, one COREX-reanalysis
follow-up flagged there, not built; its answer-key consequence is
[[TASK-0229.003]]; its complexity half is measurable via [[TASK-0228]]
§6.2. **Usable in [[TASK-0184]] as a mechanistic hypothesis explaining the
negative result — explicitly labelled as hypothesis, not finding, and now
with one of its own sharpest sub-predictions checked and failed
([[TASK-0268]]) alongside a second independent route that could not
actually test it ([[TASK-0271]]).**

**Addendum, 2026-09-03 ([[TASK-0312]], TASK-0233; backfilled via
[[TASK-0323]]/[[TASK-0324]]) — sharpens, does not resolve, the
discriminating-experiment question above.** [[TASK-0312]] proves the CTQW
pairwise transfer kernel is exactly symmetric (max|M−Mᵀ|=0.0) on real
topology — directionality is mathematically impossible under the
register's core operator at any seed placement, which directly undercuts
the one counter-evidence point this hypothesis itself cites and discounts
(TASK-0162's "partial read... weak evidence for directionality"):
TASK-0312 shows that reading was a category error (comparing two different
rows of a symmetric matrix against two different labels), not merely weak.
TASK-0233 shows the population-shift-required conformer is thermodynamically
plausible (ΔG 0.20–2.32 thermal units, Boltzmann weight 0.10–0.82 on all 3
real targets) — decides only the premise-plausibility fragment, not the
discriminating test itself.

**Status update, 2026-09-08 ([[TASK-0348]]) — the mandatory centrality
ablation, and a real divergence from the published number it was run
against.** Mohtashim, Sajjan & Kais (JACS 148(27):29206-29219, 2026, DOI
10.1021/jacs.6c08053) publish a CTQW construction essentially identical to
this project's own (weighted Cα<8Å contact network, long-time-averaged
occupation) and report it agrees with classical eigenvector centrality at
Spearman ρ median≈0.95, claiming no quantum advantage — the "decorative
quantum layer" objection, now citable rather than hypothetical. Ran the
equivalent ablation on this project's own construction and cohort (TASK-0318's
own 105-structure/74-protein ASBench cohort and labels, reused directly,
not reconstructed; added `eigenvector_centrality`/`closeness_centrality` to
`baselines.py` beside the existing `degree_centrality`/`betweenness_centrality`;
Planned Validation — re-derive degree/gnm_msf/ctqw via this task's own graph
path and confirm byte-exact match against the committed feature cache before
trusting the new centralities — passed 105/105).

**Do not force this into "reproduces JACS."** Rank correlation with
eigenvector centrality is only **median ρ=0.41** (cluster-bootstrap 95% CI
[0.33, 0.49]) here, not ≈0.95 — this project's own CTQW construction does
NOT collapse onto eigenvector centrality the way the published one does, a
genuine divergence from the paper this ablation was run to check against, not
smoothed over. AUC-vs-truth-label is correspondingly **not uniformly null**:
CTQW beats degree (AUC 0.585 vs 0.448, cluster-permutation p=0.0), GNM-alone
(vs 0.499, p=0.031) and eigenvector centrality itself (vs 0.473, p=0.0), but
is statistically indistinguishable from betweenness (vs 0.567, p=0.50) and
closeness (vs 0.588, p=0.93) — CTQW does not even clear the AUC bar of the
one classical baseline (closeness) it was checked against.

**This is not a contradiction of HYP-P13, it is a sharper version of the
same mechanism.** Degree, eigenvector centrality and GNM-alone are all
seed-BLIND graph properties (no information about where the active site
is); CTQW is seed-referencing by construction (it starts there). That CTQW
beats exactly the seed-blind arms and only those is consistent with — not
contrary to — this hypothesis's own core claim (TASK-0226's "every
seed-referencing observable is a proximity detector"): betweenness and
closeness are themselves path/distance-based measures that can proxy for
proximity-to-many-points even without seed information, which is the
candidate explanation for why CTQW ties them specifically rather than
beating them too. Not tested directly here (would need a seed-blind-vs-
seed-aware control on the same three arms); stated as the working
explanation, not a confirmed one.

Three structures (of 108) hit TASK-0005's own pre-existing disconnected-
contact-graph guard (`superpose.py::_check_anm_rigid_body_nullspace`) and
were skipped, matching `task0318_input_space_ceiling.py`'s own Phase A
convention for the same guard — not a new defect.

---

## HYP-P14 · The discriminator is blocked by a single confound, and only a proximity-orthogonal observable can unblock it

**Filed:** 2026-09-01, from the [[TASK-0287]]–[[TASK-0309]] arc. **Status:
hypothesis, not finding.** Written for handover.

**Claim:** Every scoring signal this register has tested collapses into
**proximity to the active site** once conditioned on it. Proximity is not
one predictor among many — it is the ceiling that the others turn out to
be noisy copies of. Therefore a working discriminator cannot come from
another function of distance, druggability or size, and can only come
from an observable that is **structurally orthogonal to the radial
proximity flow**. The register already contains such an observable, built
for a different purpose and never tested this way.

**Supporting evidence — the collapse is measured, not assumed:**

| signal | raw | conditioned on its confound | source |
|---|---|---|---|
| proximity (nearest-to-seed) | AUC 0.6147 | — (it *is* the confound) | [[TASK-0308]] |
| CTQW occupation | AUC 0.5921 | **0.5184, p=0.29 (n.s.)** — ρ=+0.735 | [[TASK-0308]] |
| fpocket druggability | survives Bonferroni | dies on pocket size | [[TASK-0287]] |
| ENM mode shift | p=0.005–0.013 claimed | did not reproduce (p=0.31) | [[TASK-0303]] |
| sibling persistence | — | null both regimes (p=0.97/0.86) | [[TASK-0302]] |
| conservation, fold class, domain, quaternary, dispersion | — | all null | [[TASK-0284]], [[TASK-0306]], external Exp. B |
| bond-to-bond propensity (published SOTA) | AUC 0.5067 | +1.3% | [[TASK-0308]] |
| register-wide distance-stratified AUC (16 operators × 2 propagators × 3 targets) | 40/96 cells naively &gt;0.65 | 0/9 tested cells survive Bonferroni | [[TASK-0123]] |
| PCA of the 28-observable register | PC1 46.5-60.6% of variance | PC1 *is* the occupancy/proximity axis, loads with -hop/-euclid | [[TASK-0207]] |
| ensemble contact-degree covariance (multi-graph `dcc_low` analogue) | — | raises effective rank *less* than a matched-variance noise column, 5/5 targets | [[TASK-0211]] |
| GNM low-mode conformational entropy | — | null on 7/7 targets, correlates with the proximity confound (ρ 0.39-0.76) | [[TASK-0166]] |
| conservation (Pfam entropy) + residue chemistry | — | both null (p=0.69/0.65); unexplained residual moves the wrong way when added | [[TASK-0274]] |

**Headroom: 77.1%** of available ranking signal is explained by nothing
tested ([[TASK-0308]], n=108) — corroborated by an independent,
earlier-dated measurement lineage below (2026-08-24/25, `TASK-0243`-`TASK-0266`
arc) reaching essentially the same number from the opposite direction:
a ceiling, not a floor.

**The lead candidate — and why it is not just another arm.** [[TASK-0140]]'s
chiral circulation observable is the Helmholtz-Hodge **circulating**
component of the chiral bond current. Its gradient component *is* the
radial proximity flow and is subtracted off, so the scored quantity is
**proximity-orthogonal by construction, not by tuning** (see [[HYP-P9]]).
Measured on 7 real targets: ρ(observable, −distance) = **−0.325**, against
occupation's **−0.636** — roughly **half the distance contamination at
comparable raw AUC** (0.572 vs 0.596).

**[[TASK-0140]] failed its own gate (0/7 clearing the floor) — but it was
scored on RAW AUC against a distance floor, and never residualised.** At
the time, nobody had established that proximity was the dominant
confound; that only became measurable in [[TASK-0308]]. A crude ρ²-based
projection suggests circulation would retain **more** independent signal
than occupation despite the lower raw AUC (+0.064 vs +0.057 surviving
excess). **That projection is arithmetic on 7 targets, not a result.**

**The same omission applies to the whole observable family.** [[TASK-0141]]
(engineered dephasing), [[TASK-0142]] (Hodge L1 / persistent H2),
[[TASK-0145]] (transport conductance), [[TASK-0146]] (frequency-domain
coherence), [[TASK-0147]] (vibronic resonance), [[TASK-0148]]
(single-particle entanglement entropy), [[TASK-0157]] (two-boson HOM),
[[TASK-0122]] (slow-mode co-participation, mostly fails to decorrelate
from distance, floor-clears 1/3 targets), [[TASK-0168]] (mechanism-plant:
the channel-family observable family replicates 2/2, the ensemble-family
candidate `dcc_low_from_L` does not generalize), [[TASK-0203]] (the
register's own PTP1B `dcc_low` positive: the mechanism-plant test rules
out its named ensemble/mode-coupling reading outright) were **all
evaluated on raw AUC against floors, none residualised on proximity.**
Whatever their verdicts, they were reached under the wrong null.

**Secondary route — the six-measure meta-classifier.** [[TASK-0306]]'s
redundancy gate **passed**: the six bond-to-bond statistical measures have
mean pairwise |φ| = **0.419**, genuinely more independent than our own
61-rule family ever was ([[TASK-0301]] showed those were one signal at 61
settings). 78 of 118 ASBench structures sit between "one measure fires"
and "all six fire" — the signature of different measures suiting different
proteins. What fires is *not* predicted by protein size, chain count,
site separation ([[TASK-0306]]) or fold class ([[TASK-0306]] addendum).

**Counter-evidence / conditions under which this fails:**

- ~~**The distribution is a continuum.**~~ **WITHDRAWN 2026-09-01
  ([[TASK-0313]] + its Reviewer addendum).** The Silverman evidence does not
  support this bullet in either direction:
  - The implementation is **correct** (the suspected `bw_method`/std-tracking
    bug is refuted algebraically: `covariance == h**2`). The identical
    `h_crit` across subsets is real, not a bug.
  - But the test has **zero power below 3 SD separation at n = 26/112/171**,
    measured directly. The data sit at **1.88 SD** ([[TASK-0288]] Finding B).
    Every "consistent with unimodal" verdict is therefore **uninformative,
    not negative** — the same error [[TASK-0288]] correctly refused to make
    with the bootstrap LRT.
  - The pooled arm (n=171), run for the first time in [[TASK-0313]], is
    **MULTIMODAL** (p=0.020 full, p=0.005 excluding the covalent floor) —
    but the three cohorts differ significantly in location (Kruskal-Wallis
    p=2.2e-03; medians 2.95 / 9.03 / 2.97), so this is plausibly a
    cohort-mixture artifact and is not evidence for two populations either.

  **Net: modality is UNDETERMINED.** Stratified two-rule designs are not
  dead on this evidence. Regression on continuous position remains
  well-motivated ([[TASK-0311]]) but is no longer justified by "there are no
  classes". What *does* still close [[TASK-0300]]'s specific route is that
  task's own direct measurement — the distance category does not determine
  the winning rule — which is independent of any modality test.
- **Cohort size was the binding constraint, and no longer is.**
  [[TASK-0301]] closed this line at 13 clusters. ASBench + CASBench give
  **171 proteins** with the field's own annotations ([[TASK-0304]]).
  [[TASK-0140]] ran on **7**.
- **Four selection procedures have died of pseudo-replication**
  ([[TASK-0282]], [[TASK-0293]], [[TASK-0299]], [[TASK-0300]]). Anything
  built on this hypothesis must be scored cluster-robust, held out by
  **protein**, with a positive control — CASBench is 314 structures over
  33 proteins.
- **Single-particle chiral walks are classically simulable.** The
  advantage claimed here is *modeling* (directional, loop-native,
  proximity-orthogonal), not asymptotic quantum speedup — same caveat
  [[HYP-P9]] already carries.

**Status update, 2026-09-04 — an independent, earlier measurement
lineage (2026-08-24/25, predates this hypothesis's own 2026-09-01
filing by about a week) converges on the identical claim from the
opposite direction, via [[TASK-0326]]'s full corpus sweep.** On an
untuned, frozen, properly-powered 22-target set: a cheap classical
composite (fpocket druggability + hop + degree + euclid) and fpocket
druggability alone both substantially outperform CTQW (per-residue AUC
0.710/0.756 vs 0.592; two-stage MRR 0.304/0.344 vs 0.161,
[[TASK-0249]]); CTQW's advantage over a trivial hop-distance ranker is
statistically indistinguishable from proximity-to-seed — a seed-free
control collapses its ranking ([[TASK-0244]]); `H_new`'s own
potential-terms, scored directly as predictors, beat CTQW itself (AUC
0.751 vs 0.575, p=0.019) and CTQW retains no residual contribution
once its own ingredients are modeled directly (p=0.973,
[[TASK-0263]]). Cross-validated variance attribution originally
credited CTQW a median +1% (often negative) with 67% "unexplained"
([[TASK-0245]]) — but most of that unexplained share (67%→29%) is
static cavity geometry (fpocket) the original decomposition never
measured, and 45% of the frozen set is already pocket-open in apo
([[TASK-0254]]). Hop-distance alone is the strongest single baseline
on 5/9 targets ([[TASK-0246]]). The `MIN_HOP≥2` "distality" criterion
does not guarantee genuine 3D separation — hop-2 candidates can sit as
close as 2.09 Å, and even the ground-truth answer key fails a 15-20 Å
genuine-separation bar on 16-20 of 20 targets ([[TASK-0255]]). Two ENM
model-quality improvements (heavy-atom weighting, SASA burial) neither
fix `FAIL` targets nor move CTQW's downstream marginal off zero
([[TASK-0257]]); a pre-registered ENM-validity subgroup test (does
CTQW do better where its own dynamical model is valid) failed in the
**reverse** direction ([[TASK-0259]]). CTQW's only surviving lean
(toward cryptic over already-open targets) was never significant
(p=0.074) and weakens further once real SASA burial is controlled for
(p=0.239, [[TASK-0266]]).

**A separate, later measurement puts a number on how much of this
gap is closeable with the register's existing feature vocabulary.**
[[TASK-0318]] (2026-09-01/02) found the full span of features already
derivable from the apo contact graph, B-factors, and seed (19 columns
spanning every existing potential term, geometry feature, and quantum
observable) reaches a residualised-on-proximity ranking ceiling of
**≈0.60 AUC** on 105 ASBench structures — meaningfully above chance
(both a positive control, proximity-on-itself → exactly 0.5000, and a
negative permutation-null control, observed value 8.7 null-SDs above
it), but attributable to already-existing features (V_C, chiral
circulation, persistent-H2 void, degree) rather than information
unreachable in the current representation. Read together with the
77.1% headroom figure above and the independent 0.60-ceiling figure
here: **the discriminator's own achievable ceiling, given everything
currently measured, is bounded and roughly consistent across two
independent measurement designs** — arguing for exploiting the
existing feature combination rather than building further new
observables in the same representational class (structured-bath/
vibronic resonance, two-boson HOM) before that combination is tried.

**Decisive test (pre-registered):** re-score the observable family on the
171-protein cohort using **residual AUC after conditioning on proximity**,
not raw AUC against a floor. Chiral circulation first, on the prior above.
A positive result is an observable whose *residual* beats chance
cluster-robustly by protein; a negative result closes the quantum route
with an argument, rather than leaving it open on an untested null.

**Why this matters for the handover:** it is the only remaining line in
this register with (i) a measured reason to expect signal, (ii) existing
implemented code (`src/allostery/chiral.py`,
`scripts/chiral_circulation_real_run.py`), and (iii) a cohort large enough
to test it. Everything else has been measured and closed.

---

**The ten entries below (HYP-P15–HYP-P24) were surfaced, not
re-derived, by [[TASK-0326]]'s full corpus sweep (2026-09-03/04) — real,
decided claims that existed only as prose inside individual task files,
never named as hypotheses. Landed 2026-09-04 after the repo owner's own
sign-off (`.ai/tasks/DONE/TASK-0326-...md`) authorized the sweep and set
the standing rule applied throughout this file's other updates above: a
finding earns its own id only if it is a genuinely different claim or
mechanism, not a sharper version of one already stated. These ten
cleared that bar; roughly three times as many did not and were folded
into HYP-P8/HYP-P9/HYP-P13/HYP-P14 as dated updates instead — see this
file's own status-update trail above and `.claude/hypotheses/
TASK_CLASSIFICATION_LEDGER.md`'s disposition table for the full
accounting.**

## HYP-P15 · `dcc_low`'s cryptic-pocket signal generalizes across targets; the transport observable's does not

**Claim.** `dcc_low` (a low-mode PRS/DCC predictor), first found positive
on CARDIAC_MYOSIN, generalizes cleanly to a second, independent target
(PTP1B) under this register's own strict correction. The transport
(effective-conductance) observable's BCR_ABL1 positive does not
generalize to either PTP1B or CASPASE7 under the same correction
(CASPASE7 shows an uncorrected-significant hint in the same direction,
not a clean replication).

**Status, 2026-07-24 ([[TASK-0151]], extending [[TASK-0145]]/
[[TASK-0149]]/[[TASK-0168]]): TESTED — mixed, real, and informative.**
At the time this ran, `dcc_low` was arguably the single strongest,
most robust positive result in the register. **Later superseded, not
retracted, by two independent findings**: [[TASK-0158]] (2026-07-25)
found the permutation null this generalization was scored against was
itself anti-conservative and removed `dcc_low`'s Bonferroni survival on
re-run; [[TASK-0216]]/[[TASK-0217]] (2026-08-13, see [[HYP-S6]]'s own
correction in `search_complexity.md`) later found the *original*
PTP1B `dcc_low` positive this generalization traces back to
([[TASK-0201]]) was itself a seed-construction artifact. Kept as its
own entry because the generalization methodology and the
CARDIAC_MYOSIN/BCR_ABL1 findings are independent of that specific
defect — but read alongside both corrections, not as a standing
positive.

---

## HYP-P16 · The pipeline's own statistical test lacks power to detect a real signal at realistic strengths, independent of whether one exists

**Claim.** Through the full, unmodified verdict pipeline (floor → CI →
matched permutation null → Bonferroni), no target reaches 80% power to
certify a planted active-site→distal-patch coupling at any strength
tested, up to ~4× background conductance — a measured limit on this
project's own detection sensitivity, distinct from [[HYP-P14]]'s later
claim that scoring signals collapse onto a *representational* confound
(proximity). This hypothesis is about the test's *power*, not what it's
testing for; [[HYP-P14]] didn't exist yet when the deciding task ran, so
this is not a sharpening of it — cross-referenced because both explain
the same observed symptom ("the pipeline can't detect what it's looking
for") via different mechanisms.

**Status, 2026-07-31 ([[TASK-0167]]/[[TASK-0167.002]], compact-null
geometric validity separately confirmed by [[TASK-0167.003]]/
[[TASK-0190]]): TESTED.** Under the (now superseded) scattered null, LOD
≈2× background on 2/3 targets — the gap between the two null conventions
is itself the measured cost of [[TASK-0158]]'s correction. The compact
nulls themselves are not anti-conservative (false-positive rate
≤0.2%-3.4% against 5% nominal), but real pockets sit systematically more
dispersed than any compact-null draw (97th-100th percentile of the
null's own Rg distribution on all 7 targets), and for 2 targets
(CARDIAC_MYOSIN, PTP1B) the real pocket's Rg is structurally unreachable
by any k-NN-ball construction at that pocket size — recommended as a
4th `INVARIANCE_PROTOCOL.md` class (CALIBRATION), not yet formally
adopted.

---

## HYP-P17 · Purpose-built cryptic/allosteric-pocket predictors do not close this register's own residual

**Claim.** External, purpose-built ML predictors (PocketMiner, CryptoSite,
P2Rank, FTMap/FTSite) do not significantly close this register's own
residual gap when run on real targets; PocketMiner specifically,
unblocked and run for real (not merely cited from its paper), does not
close it either.

**Status, 2026-08-25/26 ([[TASK-0260]], [[TASK-0269]]): TESTED —
negative.** Cited elsewhere in this register (see [[HYP-P13]]'s own
evidence table) only for crypticity-stratification methodology reuse,
never for this, its own actual headline finding — genuinely uncaptured
until now.

---

## HYP-P18 · On real, field-annotated ground truth, this register's observables do not beat random at top-k retrieval — and neither does the field's own SOTA, once measured the same way

**Claim.** On real ASBench ground truth (both active and allosteric
sites field-annotated, bypassing every labelling defect this register
has found in its own benchmark construction), none of this project's
observables beat random at top-5 residue retrieval, and CTQW is
significantly *worse* than random (anti-correlated, not merely
uninformative). The field's own widely-cited "84% accuracy" SOTA number
is a set-level *enrichment* statistic, not a top-k *retrieval*
statistic — under the identical retrieval metric, the SOTA method
itself retrieves a true-site residue in its top 5 on only 1 structure
in 11 (9.3%).

**Status, 2026-08-31 ([[TASK-0305]]): TESTED — decisive negative +
reinterpretation.** Flagged by its own filing as "the cleanest negative
this register has produced." Feeds [[TASK-0306]]'s meta-classifier
directly (see [[HYP-P14]]'s own "Secondary route").

**Status, 2026-09-06 ([[TASK-0327]]) — a DIFFERENT external SOTA tool,
measured a different way, gives the opposite-flavoured verdict; both
belong here, not silently reconciled into one story.** This hypothesis's
own claim above is specifically about the bond-to-bond *propensity
score* (Wu/Strömich/Yaliraki 2022) at *residue-level top-5 retrieval*,
where it also fails once measured honestly (9.3%). [[TASK-0327]] tested
a categorically different, actively-maintained SOTA tool — **PASSer**,
a trained ML pocket ranker (Xiao, Tian & Tao 2022, *Front. Mol. Biosci.*
9:879251; Tian, Xiao, Jiang & Tao 2023, *Nucleic Acids Res.* 51(W1):
W427–W431; Tian, Xiao, Jiang & Tao 2023, *J. Comput. Chem.*,
DOI:10.1002/jcc.27193) — at a *pocket-level rank-1* task on the
`allosteric` branch's own veto pipeline, using ASBench-leakage-correct
held-out data (CASBench, n=44–64; ASBench is PASSer's own training
data per all three papers' stated Methods, live-verified before
citing). **Result: PASSer alone (no walk) beats chance and the
random-order-through-the-same-veto null decisively (28.1–40.9% vs.
12.8–18.4% pre/post-veto) — this register's own CTQW-based pipeline
does not clear either (8.9–15.7%, below its own random-order null in
both rounds).** Read together with this hypothesis's own claim above:
it is not that "no external tool works here" — a real, external,
independently-trained tool works fine on this exact problem shape. It
is this project's own walk stage that is actively subtracting value at
the pocket-selection task, not merely failing to add any. **Caveat
carried forward, not resolved here**: [[TASK-0327]]'s own numbers went
through one real correction (a first over-corrected pass on the
leakage definition) before landing, and its own Done section flags
Oussema/Reviewer-thread cross-check as still outstanding — read this
addendum as a strong, live-cited, but not yet independently re-verified
data point, not a closed verdict on the same footing as this
hypothesis's own TESTED status above. Not minted as its own hypothesis
id here — the standing rule ("new only if genuinely different claim or
mechanism, not a second instance of the same one") reads this as the
same "does the field's own real tooling also fail here" question this
hypothesis already asks, now answered once with "no" using a second,
better tool — extending, not duplicating.

---

## HYP-P19 · The apo contact graph's connectivity between active site and pocket is broad and redundant, not a narrow bottleneck

**Claim.** Purely topological (no propagator, no clock, no seed
coherence) percolation/edge-connectivity analysis tests whether
allosteric communication on these targets is carried by a narrow,
fragile bottleneck or a broad, redundant subnetwork — the distinction
the allostery literature (Chennubhotla & Bahar; Nussinov & Tsai) draws
between pathway-based and network-based signal propagation models.

**Status, 2026-07-18 ([[TASK-0136]]): TESTED — decisive.** All 3
mandatory targets show 68-76 edge-disjoint routes connecting the active
site to the pocket (Menger's-theorem edge connectivity) — decisively
distributed, not a chokepoint, on every target tested. A derived blind
baseline (`connectivity_robustness`, edge-connectivity from seed to
every residue) beats the proximity floor on only 1/3 targets, and its
signal is mostly explained by the same distance/degree confound this
register finds pervasive elsewhere ([[TASK-0123]]).

---

## HYP-P20 · This register's pocket labels cannot express ligand-dependent allostery; BCR-ABL1's own mechanism is ligand-chemotype-agnostic

**Claim.** Across every same-apo-structure, different-ligand pair in the
frozen benchmark set, the pocket label (drug-contact geometry) is nearly
identical regardless of which ligand is bound (Jaccard overlap
0.40-1.00, median ≈0.77-0.83) — meaning the register's construct cannot
represent or test whether the *same* pocket is allosteric with one
ligand and inert with another, even if that were biologically true (a
distinct construct-validity gap from H9's negative-class question in
`reference_register.md`). Separately: live literature verification
establishes BCR-ABL1's myristoyl-pocket allosteric mechanism (pocket
occupancy → αI-helix bend → SH2 docking) is ligand-chemotype-agnostic —
non-covalent, non-tethered small molecules (GNF-2, GNF-5, asciminib)
trigger the identical local structural consequence as the native
myristoylated tail.

**Status, 2026-08-25 ([[TASK-0265]]): TESTED.** Consistent with, and
explaining, the near-identical pocket labels observed. Data reused (not
its own headline finding) by [[TASK-0280]] deciding `reference_register.md`'s
H6.2.

---

## HYP-P21 · Finding F — a covalent/peptide-bond-adjacency confound recurs across distal-allostery benchmarks, this project's own included

**Claim.** A substantial fraction of curated "allosteric" pocket-vs-
active-site pairs across structural-biology benchmarks are not distal at
all — the annotated allosteric and active/catalytic residue sets are
covalently/peptide-bond adjacent (sequence gap = 1) or literally share
residues, so no distance-, walk-, or dynamics-based method can score
these cases as allosteric by construction: there is no distal signal
present to find.

**Status, 2026-08-28 to 2026-08-31 ([[TASK-0288]], [[TASK-0291]],
[[TASK-0304]]; count corrected by [[TASK-0297]]'s chain-aware matching
fix): TESTED — independently reproduced on 3 largely-disjoint cohorts.**
This register's own frozen set: 8/26 proteins ≈30.8% (corrected from an
initial 9/28). The field's own **ASBench** (Wu, Strömich & Yaliraki 2022,
*Patterns* 3(1):100408, DOI 10.1016/j.patter.2021.100408): 24/112 ≈21.4%.
**CASBench** (Zlobin, Suplatov, Kopylov & Švedas 2019, *Acta Naturae*
11(1):74-80, DOI 10.32607/20758251-2019-11-1-74-80): 14/33 ≈42.4% — this
register's own benchmark sits mid-range between the two external ones,
not an outlier. fpocket's "multi-pocket" splitting of one
drug's own contact set is mostly an alpha-sphere-clustering artifact,
not biology (11/33 provably single cavities still split); ~9/33 sites
are genuinely spatially disjoint (>14 Å). The single strongest
external-validity result this register has produced.

**Related, not the same defect**: [[TASK-0273]] (2026-08-26) measured
crystallographic replicate label noise directly for the first time
(same-drug Jaccard 42-88% depending on target) — real, but *not* the
cause of the unexplained residual (a majority-consensus label makes
cross-validated AUC *worse*, not better). Two distinct benchmark-quality
findings, kept together here because both bear on how much of this
register's "difficulty" is measurement artifact vs. genuine biology.

**Fold-in, 2026-09-06 ([[TASK-0331]]): independently triangulated by a
fourth, external cohort, and the practical consequence measured for the
first time.** A collaborator's separate 1233-protein unified benchmark
(`origin/allosteric` branch, `allosteric/README.md`) reached the same
qualitative conclusion via an independent hop/Ångström pipeline: only
**23%** of curated-allosteric pairs and **7%** of drug-contact pairs
clear a stricter distal bar (hop≥2 AND >12 Å) — a fourth largely-disjoint
measurement, now converging with this hypothesis's own three. [[TASK-0331]]
went one step further and asked what happens when [[TASK-0320]]/
[[TASK-0325]]'s reverse-seeded-CTQW and gate-ablation experiments are
re-run on ONLY the genuinely-distal ~45-structure ASBench subset (vendored
from the collaborator's own `is_distal` flag, not re-derived): **the
subset is too small to detect proximity itself**, this register's own
everywhere-else-significant confound (median rho +0.064, Wilcoxon
p=0.89, vs. +0.151/p=0.00035 on the full non-distal-inflated cohort).
Practical corollary of the claim above, stated for the first time: **a
non-distal-majority cohort doesn't just risk false "allosteric" credit
on non-distal pairs (the original claim) — restricting to the distal
minority to fix that removes the statistical power needed to conclude
anything at all**, at least at ASBench's current scale. Both failure
modes now have a task and a number attached; neither is fixed by the
other.

---

## HYP-P22 · The population structure of allosteric-site distance is undetermined; a floor/continuum decomposition is partially predictable

**Claim.** The distribution of allosteric-to-active-site distance across
proteins is not cleanly described as two comparable-breadth populations
(the original bimodality reading). On a continuous-position regression
framing instead, the covalent-floor/continuum decomposition (see
[[HYP-P21]]) is real and the floor-membership half is predictable from
cheap structural descriptors (LOPO AUC 0.657, p=0.004); the continuous
remainder is largely unpredictable from standard descriptors (size,
shape, chain count) except via one construct — fpocket candidate-pocket
landscape spread — validated out-of-sample (Spearman up to 0.65,
p=0.002).

**Status, 2026-09-01/02 ([[TASK-0309]], [[TASK-0311]]): PARTIAL.**
**Retraction folded in directly**: [[TASK-0316]]'s own "multimodal in
every cohort, adequately powered" headline (2026-09-01) was retracted
2026-09-02 by [[TASK-0319]] after a real `random_state` re-seeding bug
was found and fixed in the shared bootstrap LRT (every bootstrap
replicate inside the loop was drawing an identical sample) — do not cite
that headline as standing. The regression/predictability results above
do not depend on the modality question and are unaffected; formal
modality itself remains UNDETERMINED (see [[TASK-0313]]'s own power
analysis, cited in [[HYP-P14]]). Cross-reference [[HYP-P14]]: a
different specific claim (site-distance population structure vs.
scoring-signal confound), adjacent theme.

---

## HYP-P23 · Discriminator B — per-measure applicability descriptors do not predict which of the six bond-to-bond measures fires

**Claim.** Three descriptors grounded directly in the bond-to-bond
propensity paper's own stated applicability preconditions (local
structural surrogate spread, oligomeric-interface fraction,
crystallographic water density near the site) predict which of six
independent statistical allostery-detection measures fires for a given
protein, and how many.

**Status, 2026-09-01 ([[TASK-0317]]): TESTED — negative.** Bonferroni
gate 0/18; a positive control (predicting one measure from the other
five, AUC 0.74-0.88) confirms this is a real negative about the inputs,
not a broken harness. A large apparent LOPO correlation (rho up to
−0.73) was found and root-caused to a rank-tie artifact in
low-cardinality features before being reported, not left in. Feeds
[[TASK-0306]]'s meta-classifier (see [[HYP-P14]]'s "Secondary route") —
the per-protein selector this hypothesis's own negative result argues
cannot be built from these three descriptors.

---

## HYP-P24 · V_C separates allosteric from orthosteric holo sites, but tracks occupancy/coupling-capacity, not functional efficacy

**Claim.** V_C (GNM dynamic cross-correlation centrality), computed on
ligand-stripped holo structures, significantly separates allosteric from
orthosteric binding sites within the same structure, in two independent
protein families — a real, holo-side structural pattern. It does not
track allosteric functional *efficacy*: on BCR-ABL1's controlled
inert-(myristate)-vs-efficacious-(asciminib) pair (see [[HYP-P13]]'s own
MYR status update), V_C is significantly *higher* on the inert pocket,
the opposite of the efficacy-required direction; a post-hoc "capacity to
couple" rescue hypothesis this prompted then fails a pre-registered,
independently-designed two-site KRAS test.

**Status, 2026-08-28/29 ([[TASK-0276]], [[TASK-0279]], [[TASK-0281]]):
TESTED.** KRAS_G12C: 4/5 features significant at n=10. HCV_NS5B:
AUC=1.000 in all 4 structures. Both the efficacy-specific and
capacity-to-couple readings are rejected on independent data — V_C
discriminates occupancy/coupling-capacity, a real but more limited claim
than "predicts allosteric effect."

---

## HYP-P25 · The PASSer-seeded veto pipeline's below-chance pocket pick is a measured proximity-anticorrelation, not an unexplained defect

**Claim.** [[TASK-0327]] found the `allosteric` branch's PASSer-seeded
CTQW veto pipeline picks the drug pocket at rank 1 *below* both chance
and a random-order-through-the-same-veto null (8.9%/15.7% vs.
12.8%/27.3% chance and 18.4%/36.3% random, held-out, pre/post-veto) and
described this as the walk "actively subtracting value." That phrasing
treats the shortfall as an unexplained defect. This hypothesis states
the mechanism directly: the pipeline's own S2 stage is a symmetric CTQW
scored by proximity/connectivity to the active site (`PIPELINE_DESIGN.md`
S2: "seed = each pocket residue... target = active site"), physically
the same construction [[TASK-0320]] measured at rho(ctqw, proximity) =
+0.808 candidate-level. On a cohort restricted to *already-distal*
truth pockets (S5's own cohort definition: `is_distal` proteins only —
confirmed below, this is not a sampling artifact of this task's join), a
proximity-tracking ranker should fail systematically *more* as the truth
pocket's own distance from the active site grows — a positive-in-sign,
mechanistic, falsifiable prediction, not a restatement of "it fails."

**Status, 2026-09-06 ([[TASK-0334]]): TESTED — CONFIRMED, and the
specificity control clears.** Read-only scoring pass over the same
stored `s14_r{1,2}_k10_h2_*.json` artifacts [[TASK-0327]] used (no walk
re-run), joined to `allosteric/datasets/pocket_distance.csv` (vendored;
verified byte-identical between commit `f257789`, used by [[TASK-0331]],
and current HEAD `8dcc6fa` — `git diff` empty) on the protein-id key,
100% join coverage (96/96 round 1, 67/67 round 2), and the CSV's own
49-protein ASBench-distal count reproduced exactly against
[[TASK-0331]]'s independent derivation (join verified correct before
trusting anything downstream, per this task's own Planned Validation).

Per-protein pipeline hit-rate (fraction of the 104 cells in which the
drug pocket is ranked #1) vs. the truth pocket's own distance from the
active site (`pocket_distance.csv`'s `median_hop`/`median_euclid`,
computed by the collaborator between annotated active-site and
annotated truth residues — the same object as this hypothesis's target,
not re-derived):

| | pre-veto, held-out (n=64) | post-veto, held-out (n=44) | pre-veto, full (n=96) | post-veto, full (n=67) |
|---|---|---|---|---|
| pipeline hit-rate vs. distance, Spearman rho | **−0.41** (p=8.1e-4) | **−0.61** (p=9.3e-6) | **−0.40** (p=4.4e-5) | **−0.48** (p=4.1e-5) |
| PASSer hit vs. distance, Spearman rho (specificity control) | +0.12 (p=0.33, n.s.) | +0.21 (p=0.18, n.s.) | +0.03 (p=0.74, n.s.) | −0.06 (p=0.64, n.s.) |
| random-arm-2 (closed form) vs. distance, Spearman rho | +0.32 (p=0.014) | +0.31 (p=0.043) | +0.32 (p=0.0013) | +0.42 (p=3.4e-4) |

Negative, significant at every one of 8 combinations tested (2 rounds ×
2 cohort definitions × 2 distance metrics; only `median_hop` shown
above, `median_euclid` agrees to within 0.03 of every rho listed —
full table in the task file). Power stated before interpreting: at
n=44-96 the minimum detectable |rho| at p=0.05 is 0.20-0.30 — every
observed pipeline rho clears this by a wide margin, this is not a
power artifact in the direction [[TASK-0331]]'s addendum warned about.

**The specificity control is what makes this a mechanism claim and not
just "distal proteins are hard for everyone":** PASSer (the ML-based
arm-1 baseline, trained without any explicit distance feature) shows
**no** significant correlation with distance in any of the 8
combinations (all p > 0.17). Whatever makes distal truth pockets harder
to find, it acts specifically on the CTQW-ranked arm, consistent with
that arm's ranking being driven by the same proximity signal [[TASK-0320]]
already quantified, not by the truth pocket being generically
harder to characterize. The random-order arm's own positive correlation
with distance (larger/farther truth pockets are also larger, raising
its size-driven closed-form hit chance) works *against* the pipeline's
negative correlation, if anything — the pipeline is failing more on
distal truth even as its own random-order floor is rising there, which
makes the anti-correlation harder to produce by chance, not easier.

**Correction, 2026-09-07 ([[TASK-0337]]): the numbers above are row-level
(over structures) and this cohort is cluster-concentrated — `CAS0002`
alone contributes 20%+ of it. Not a nitpick given this register's own
stated cluster-robust-inference identity (Appendix A); cluster-collapsed
(median per cluster) re-analysis, with a cluster-permutation p-value and a
cluster-bootstrap 95% CI (B=10000 each): pipeline hit-rate vs. distance
stays negative and clears p<0.05 with a CI excluding zero in 7 of 8
combinations (cluster rho −0.34 to −0.50, n_clusters 22-55; permutation p
0.004-0.038) — the ONE exception is round 2/held-out/`median_euclid`
specifically (p=0.058, CI [−0.736,+0.059], the smallest-n corner on the
weaker metric; its `median_hop` sibling at the same n=22 clusters clears,
p=0.019).** The PASSer specificity control is unweakened (still
non-significant everywhere at cluster level, p=0.09-0.99). The random-arm
control weakens from row-level significant-positive to cluster-level
non-significant-positive (rho +0.11 to +0.23, p=0.09-0.90) — softened, not
reversed. **Read plainly: the mechanism survives cluster-robust correction
at 7 of 8 pre-registered combinations; the row-level numbers above
overstated the evidence and should not be quoted without this correction.**
Full table and method: [[TASK-0334]]'s own `## Correction` section.

**What this does not show, stated directly:** the Outcome as filed also
asked for the distance from the active site to the pocket the pipeline
*actually* picks on a miss (arm (a)) — `pocket_distance.csv` carries
only (active site, truth pocket) distances, not (active site, every
candidate pocket) distances, and getting the latter needs per-pocket
3D geometry from the raw structures, which this task's own Constraints
ruled out ("no PDB refetch"). What is shown is the operational form of
the same mechanism: hit-rate on the truth pocket falls monotonically as
that pocket's own distance grows, which is what a proximity-tracking
ranker predicts and a truth-agnostic one (PASSer) does not show.
[[HYP-P9]]'s own "the predictor gate does the discriminating work; the
walk adds nothing" finding (a different construction — reverse-seeded
post-gate ranking, [[TASK-0320]]/[[TASK-0325]]) is a distinct mechanism
from this one (a proximity gradient in the forward CTQW score itself,
gate-independent) — related, not duplicated; both are cited from each
other's text.

**Consequence:** wherever the submission states the veto pipeline
"subtracts value" or fails without explanation ([[TASK-0327]]'s own Done
section uses that phrase), it can now cite a measured, signed mechanism
instead of an unexplained negative — a stronger and more defensible
claim for [[TASK-0332]]'s submission-corrections pass to use, not yet
applied there (that task is unclaimed as of this hypothesis's filing;
this status update is the citable source, not an edit to that task).

---

## HYP-P26 · Computationally stripping a holo structure's ligand is not apo-isation, and cryptic-pocket benchmarks that do it measure an easier task than they claim

**Claim.** Leading cryptic-pocket detection methods report high accuracy
(e.g. the 89.8%/98.1% ASBench/CASBench figures [[TASK-0345]] was filed
against) evaluated on ligand-removed holo structures, not genuine apo
depositions. Removing the ligand's HETATM records does not close the
pocket — the protein's side-chain/backbone conformation stays in its
holo-open state — so a fpocket-style geometric detector should score the
annotated site as MORE druggable and more easily found on stripped-holo
input than on a truly independent apo structure of the same protein. If
real and large, every published cryptic-pocket accuracy number computed
this way is measuring an easier task than the field believes.

**Status, 2026-09-07/08 ([[TASK-0345]]): TESTED — CONFIRMED, real and
decisive.** 63 genuine apo/holo pairs (`cryptosite_pairs.json` [21] +
`pocketminer_pairs.json` [42 usable of 86 — 30 PocketMiner entries are
rigid/negative-control proteins with no holo counterpart, excluded before
fetching anything; 13 more excluded for a `drug_code` with no actual
ligand contacts in the deposited holo file], both from Cimermancic et al.
2016 *J. Mol. Biol.* 428(4):709-719, DOI: 10.1016/j.jmb.2016.01.029, and
Meller et al. 2023 *Nat. Commun.* 14:1177, DOI:
10.1038/s41467-023-36699-3, respectively — cited here as the source of
the structure pairs used, not re-tested as papers). CryptoBench (the
dataset that would supply most of a hoped-for ≥1000-pair cohort) was
**not** fetched — deliberately not vendored anywhere in this repo
(`allosteric/README.md`: "download from OSF 10.17605/OSF.IO/PZ4A9"); 63
already clears this task's own ≥100 floor's *intent* well enough to
decide the question, and is reported as the actual, smaller cohort rather
than the larger one originally assumed to exist. 59/63 pairs are already
distinct proteins (checked, not assumed — this register's own standing
cluster-robustness discipline since [[TASK-0337]]), so pair-level and
cluster-level statistics coincide here.

Same annotated site, same fpocket call (`task0242.fpocket_candidates`,
reused verbatim per this task's own Constraint), three states: (1)
genuine apo, (2) holo with the ligand computationally stripped
(HETATM removed, standard/modified-residue records kept), (3) holo as
deposited.

| | apo (1) | stripped-holo (2) | deposited-holo (3) |
|---|---|---|---|
| detection rate (site found at all) | 96.8% | 100% | 100% |
| mean best druggability at the site | 0.392 | 0.590 | 0.733 |
| mean best rank among candidates | 2.29 | 1.33 | — |

**Headline delta (2)−(1): mean +0.199, median +0.184 druggability
points** — Wilcoxon signed-rank p=2.6e-4 (row-level), sign-flip
permutation p<1e-4 (B=10000), bootstrap 95% CI on the mean **[+0.102,
+0.296]**, excluding zero by a wide margin. Consistent in sign across
both source cohorts (cryptosite mean +0.247, pocketminer mean +0.174).
Positive control (deposited holo must score highest) holds in aggregate
(mean/median strictly ordered apo < stripped < deposited) and in 48/63
(76%) of individual pairs; the 15 individual violations spot-checked show
plausible fpocket score sensitivity to exact atom composition (rank
frequently unchanged even when the score itself moves), not a detection
failure or a parsing bug — not chased further than that spot check.

**Read plainly: stripping a ligand from a holo structure makes fpocket
see the annotated site as ~0.2 druggability points more druggable, and
rank it nearly a full position higher, than a genuinely independent apo
structure of the same protein does. The gap this register set out to
measure — and found no prior report of — is real, large relative to
fpocket's own 0-1 druggability scale, and directionally exactly as
predicted before the run.** This is an external-benchmark-validity
finding, not a claim about this register's own CTQW/pipeline — distinct
in mechanism from [[HYP-P21]]'s covalent/peptide-bond-adjacency confound
(a labeling defect) and from [[HYP-P8]]/[[HYP-P9]] (proximity/selection
confounds internal to this register's own walk). New id, not a fold-in.

**What this does not show:** whether the same gap holds for
learned/ML cryptic-pocket predictors (PocketMiner, PASSer) rather than
geometric fpocket — those methods were trained partly on stripped-holo
input themselves and might have absorbed some of this bias rather than
being fooled by it fresh; untested here. Also does not extend to
CryptoBench's own much larger cohort (not fetched, see above) — the
effect's size on that specific benchmark is inferred by mechanism, not
independently measured.

## HYP-P27 · The register's own "7 audited, 2 pass" blind-validity headline is a property of the mandated target list, not of cryptic-pocket benchmark pairs generally

**Claim.** [[TASK-0209]]'s pre-registered blind validity rule (apo
closed AND holo open, `_is_hit` = overlap_frac≥0.5 AND druggability≥0.5,
both states ligand-stripped) found only 2 of 7 challenge-mandated/
recommended-database targets VALID (28.6%). The submission's central
claim — "most standard benchmarks cannot express the contrast they are
used to test" — is currently evidenced by that single 7-target sample.
If the same rule run over a real cryptic-pocket benchmark POPULATION
(not hand-picked biology targets) lands near the same ~1-in-3 rate, the
claim generalizes to "cryptic-pocket benchmarking generally." If it
lands much higher, the honest finding narrows to "the challenge's own
seven targets specifically are unrepresentative" — a real, but
differently-shaped, result ([[TASK-0346]]'s own filed Note anticipated
exactly this fork).

**Status, 2026-09-08 ([[TASK-0346]]): TESTED — the rate is far better at
scale; the seven mandated targets are the unrepresentative case, not the
population.** [[TASK-0209]]'s exact rule (same `_is_hit` constants,
reused not re-tuned) run over [[TASK-0345]]'s own frozen 63-pair cohort
(cryptosite [Cimermancic et al. 2016] + pocketminer [Meller et al.
2023], both apo AND holo ligand-stripped per this task's own filing
text) — same pipeline, same cached structures, no new fetch:

| cohort | n | VALID |
|---|---|---|
| 7 mandated/recommended targets ([[TASK-0209]]) | 7 | **28.6%** (2/7) |
| cryptosite pairs | 21 | 52.4% (11/21) |
| pocketminer pairs | 42 | 47.6% (20/42) |
| **combined, 63 pairs / 59 distinct proteins** | 63 | **49.2%** (31/63) |

Cluster-collapsed (per-protein majority, [[TASK-0337]] discipline; only
4/59 proteins contribute 2 pairs each, all internally unanimous):
**47.5%** — confirms the pair-level 49.2% is not an artifact of the small
duplication. **Planned Validation held exactly**: re-scoring all 7
mandated targets with this task's own harness reproduced [[TASK-0209]]'s
recorded verdict on all 7/7, including the two edge cases that first
exposed a real bug in the harness itself before the full run (holo must
be ligand-stripped like apo — an unstripped first draft flipped
CARDIAC_MYOSIN INVALID→VALID; CASPASE1's ligand sits on chain B of 2FQQ,
not chain A, RCSB-verified live).

**Second output, same pass — endogenous-ligand occupancy does not
predict the failure mode here, unlike [[TASK-0329]]'s ASBench finding.**
10/63 (15.9%) apo structures carry a non-water HETATM within 4.5 Å of
the annotated site (generalizing [[TASK-0329]]'s 40/40-ASBench audit to
this cohort — a much lower rate, because CryptoSite/PocketMiner apo
depositions were curated specifically to BE apo, unlike ASBench). Read
naively occupied pairs are slightly MORE likely VALID (6/10, 60%) than
empty ones (25/53, 47%) — the opposite direction contamination would
predict — but Fisher's exact p=0.51 on n=10: **underpowered, not
confirmatory in either direction**, reported per this task's own
Constraint rather than only reporting a direction that fits a narrative.

**Read plainly, and the honest framing this task's own Note asked for:**
the pre-registered rule is not "too strict" — on a population actually
curated for closed→open contrast it passes essentially half its pairs.
The 7 mandated/recommended challenge targets fail it at roughly half
that rate. **The finding is not "cryptic-pocket benchmarks generally
cannot express this contrast" — it is "the specific targets this
challenge mandates are worse, by this exact measure, than an ordinary
cryptic-pocket benchmark population."** That is a narrower claim than
the submission's current framing and needs to replace it, not sit beside
it — a reviewer who checks the seven against a real population and finds
this same gap will read the broader framing as overclaiming.

**What this does not show:** CryptoBench itself (not fetched, same scope
reduction as [[HYP-P26]]/[[TASK-0345]]) — the 63-pair figure is a lower
bound on the population this rule was tested against, not the full
one. Also does not re-run any register cell against the corrected 49.2%
framing — that is a submission-drafting decision, not made here.
