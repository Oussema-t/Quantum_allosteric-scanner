# Physical Hypotheses

**Scope:** Scientific conjectures about the protein physics underlying H_new and the propagators.
These are testable claims, not implementation tasks.
Cross-reference: concrete code changes in `../improvements/hamiltonian_code.md`;
strategic framing in `ceiling.md`.

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
`results_task0119/`. Alternative 1 (infinite-time average) remains this
pipeline's separate, already-shipped headline convention (`time_averaged_ctqw`,
TASK-0097); alternative 3 (mode-relaxation from apo→holo ANM projection) remains
unexplored — not needed once alternative 2 answered the load-bearing question
("is t currently a live, unaccounted-for confound") with a real yes.

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
  real pockets carry one.
- **Seed/field gauge.** A field direction or source seed tuned to labels would
  reintroduce overfitting; the flux content is gauge-invariant only if the
  field grid is fixed blind to labels.

**To test:** [[TASK-0140]] — gated benchmark eval vs the proximity floor with
block-bootstrap CIs and distance-stratified AUC + permutation null.

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
- **Inherits HYP-P10.** If pockets aren't graph-open/void-like, this fails with
  the rest of the family.

**To test:** [[TASK-0142]] — L1 joint-support score + persistent H2 generator
localization vs a matched random-patch null, gated on HYP-P10/HYP-P9 showing
life. b1(ker L1) == E−N+C as the setup-validity gate.

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
