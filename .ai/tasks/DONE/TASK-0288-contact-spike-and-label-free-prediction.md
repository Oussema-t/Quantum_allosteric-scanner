# TASK-0288 — Can the allosteric-site category be predicted without labels? And what is the near/far split made of?

- Status: Done — Finding F's provenance objection was raised, tested, and **rejected** ([[TASK-0289]])
- Assignee: Reviewer thread
- Priority: **High — benchmark-validity finding; corrects [[TASK-0284]] Finding A as published in the collaborator brief**
- Filed: 2026-08-28 by Reviewer thread (user-directed: "I am damn curious if we can crack the problem … categorise the proteins without looking at their labels")
- Related: [[TASK-0287]], [[TASK-0284]], [[TASK-0258]], [[TASK-0282]], [[TASK-0270]], [[TASK-0251]]

## Answer to the question asked

**Partly, and only trivially.** `min_A` is predictable out-of-sample in
absolute Å (LOO-CV rho = **+0.588**, p=0.0016) — but the entire signal is
*how much room the protein has*. Ask the non-trivial question, "given this
protein's size, will its pocket be relatively near or relatively far?",
and **nothing predicts it**: zero of 12 scale-free landscape descriptors
survive correction against scale-free position.

## Findings

**A. The near/far split is not simply protein size.** Silhouette survives
normalisation (0.722 raw → 0.752 on `min_A/Rg`). But the *non-normality*
does not (Shapiro p=0.0067 → 0.193), so the size-free evidence for two
groups is weaker than Finding A implied.

**B. The bimodality LRT is UNDERPOWERED here — inconclusive, not
negative.** Bootstrap LRT (1 vs 2 Gaussians) on log(min_A) gives LR=8.42,
**p=0.137**. Its own positive controls at the same n show it reliably
detects ≥2.0 SD separation (p=0.010–0.083) but not 1.5 SD (p=0.010–0.219);
the observed data sit at **1.88 SD**. **p=0.137 must not be reported as
evidence against two populations.**

**C. LABEL-FREE prediction of `min_A` works, and is geometric room.**

| feature set | LOO-CV rho | p |
|---|---|---|
| geometric room `[max_d, N]` | **+0.588** | 0.0016 |
| landscape spread | +0.568 | 0.0025 |
| druggability only | +0.100 | 0.63 |
| all label-free | +0.324 | 0.11 |

**Druggability carries no information about where the allosteric site
sits.** Adding features beyond geometric room makes prediction worse.

**D. Nothing predicts RELATIVE position.** `min_A ≤ max_d` holds for 28/28
by construction, so raw correlations carry a mechanical range ceiling.
Partialling on `max_d`: **no descriptor survives** (best p=0.041). Testing
scale-free shape against scale-free position `y_rel = min_A/max_d`:
**none of 12 survives** Bonferroni (best `median_d_rel`, p=0.071).

**E. Quaternary structure is a clean null.** The classic hypothesis —
oligomeric allostery puts the effector site at a subunit interface —
fails: monomeric mean `min_A` 5.39 Å vs oligomeric 5.80 Å, **MWU
p=0.50**; `n_chains` rho=+0.150, p=0.44. The far group mixes monomers
(HCV_NS5B, CARDIAC_MYOSIN, PTP1B) with oligomers (CASPASE7, PKR).

**F. What the distribution is actually made of — a POINT MASS at the
peptide bond, not a Gaussian component.** 9 of 28 structures (**32%**) lie
in a **0.076 Å window** at 1.287–1.363 Å. Under the fitted log-normal,
1.24 were expected; **binomial p = 2.0×10⁻⁶**.

1.32 Å is shorter than a C–C bond. It is the **peptide bond C–N
distance**. Checking the closest pocket residue against the closest
active-site residue, **all nine are sequence gap = 1** with Cα–Cα ≈ 3.8 Å:

| target | min_A | pocket → site | seq gap |
|---|---|---|---|
| DHPS_GC7 | 1.33 | A239 → A238 | **1** |
| PF_ATCASE | 1.36 | C112 → C111 | **1** |
| FBPASE_95S | 1.35 | C33 → C32 | **1** |
| TRP_SYNTHASE_F6F | 1.29 | B59 → B60 | **1** |
| MKK7_IBRUTINIB | 1.32 | A164 → A165 | **1** |
| TEM1_BLA_CBT | 1.33 | A237 → A236 | **1** |
| GLUK1_BPAM | 1.32 | A519 → A518 | **1** |
| FPPS_YF0282 | 1.33 | F253 → F254 | **1** |
| KRAS_G12C | 1.31 | A10 → A11 | **1** |

For comparison the far group has gaps of 5, 29, 35, 73, 136, and one
cross-chain.

**For roughly a third of this benchmark, the annotated "allosteric"
pocket is covalently bonded to the active site.** That is not a distal
site; it is the same site. No distance-, walk-, or dynamics-based method
can score it as allosteric, because there is no distal signal present.

> **Provenance objection — raised, tested, REJECTED (2026-08-29).**
> While writing this up, `prep()` was found to be **non-deterministic**:
> `HCV_NS5B_POO` returns a 32-residue active site on the first call in a
> process and a 3-residue one on later calls, swinging its `min_A`
> between **1.33 Å and 17.94 Å** — a 16 Å swing on a flagship "distal"
> exemplar. Cause: `backend.active_site.detect_active_site`
> (`backend/active_site.py:174-187`) runs a **silent exception fallback
> chain** `_from_uniprot -> _from_ligands -> _from_site_records -> empty`.
> A transient network failure silently changes which tier answers, and
> `prep()` discards the returned `source` provenance.
>
> This threatened Finding F directly: a broad UniProt annotation makes any
> nearby pocket abut the active site (`min_A ≈ 1.3`) while a narrow
> 3-residue ligand-derived site does not, so heterogeneous provenance
> could in principle manufacture the whole spike.
>
> **[[TASK-0289]]'s sweep tested it and it does not hold.** With fresh,
> provenance-recorded seed sizes: `n_seed` vs `min_A` **rho=−0.148,
> p=0.45**; spike mean `n_seed` 15.9 vs rest 12.6, **MWU p=0.44**; 7 of
> the 9 spike targets are `uniprot`-sourced, the same tier as most of the
> far group. The counterexamples are structural and not defeasible:
> **TRP_SYNTHASE has a 2-residue active site and sits in the spike
> (1.29 Å); PKR has 26 and sits in the far group (11.69 Å)** — the
> opposite of the artifact's prediction.
>
> **The `n_seed/N` control quoted above (p=0.072) was itself contaminated**
> — it used `n_seed` from the committed rows, recorded under whichever
> tier answered that run. On fresh values the effect vanishes entirely.
>
> **Residual caveat:** `min_A` is still the committed taxonomy value. A
> fully clean answer needs `min_A` recomputed under deterministic seeds,
> still owed by [[TASK-0289]]'s Scope.

**Control — is the spike our own artefact?** Partly, but not mainly. A
broad active-site annotation does push `min_A` down (`n_seed/N` vs
`min_A` rho=−0.385, p=0.043; spike group 0.054 vs 0.030, MWU p=0.072).
But the spike group contains targets with **4- and 6-residue** seeds,
which cannot be over-broad. **Contributing factor, not the explanation.**

## Consequences

1. **[[TASK-0284]] Finding A's bimodality evidence is inconclusive at this
   n** (Finding B above).
2. The spike is a **benchmark-validity finding**, not an artifact of our
   own detection — same class as the KRAS genotype defect ([[TASK-0270]])
   and the myosin ligand defect. It is the sharpest available answer to
   why every method in this register floors on a large subset: **~32% of
   the benchmark is not an allostery problem.** Report it with the
   deterministic-recompute caveat until [[TASK-0289]] closes.
3. The negative result in D is the strongest evidence yet that pocket
   *location* is not encoded at any structural scale we can measure — and
   it is **unaffected** by the provenance defect, because it tests
   scale-free landscape shape against scale-free position within each
   protein's own geometry.

## Next

- **[[TASK-0289]]'s deterministic `min_A` recompute** before Finding F
  goes to the collaborator as a headline. The provenance objection is
  already rejected; what remains is confirming the numbers move nowhere.
- Restate Finding A in `CTQW_CONTRIBUTION_BRIEF.html` and
  [[TASK-0184]]. **Not done here — the brief is under collaborator review.**
- Then: consider reporting `min_A` stratified by seq-gap >= 2 as the
  honest allosteric subset.
