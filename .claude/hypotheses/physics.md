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
