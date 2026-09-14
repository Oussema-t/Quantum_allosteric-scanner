# Solution Outputs — Team AuraQu

*Challenge Statement §5, outputs 2 and 3. The connectivity matrices (output 1) are
supplied separately as `Connectivity_Matrices.csv`; the methodological argument is
Section 2 of the Concept Proposal.*

---

## 1. Hit List — top five predicted allosteric residues per target

**`residue_number` is the PDB number as deposited and is the one to quote.**
`residue_index` is the 0-based position in the connectivity matrix. They differ
for three of the four targets, because PDB numbering does not start at zero and is
not always contiguous.

| target | structure | #1 | #2 | #3 | #4 | #5 |
|:-------------------|:----------|-----:|-----:|-----:|-----:|-----:|
| KRAS_G12C | `4LDJ` | **31** | **122** | **33** | **121** | **29** |
| BCR_ABL1 | `1OPL` | **402** | **311** | **310** | **301** | **338** |
| CARDIAC_MYOSIN | `8QYP` | **682** | **683** | **681** | **680** | **133** |
| MYC_MAX | `1NKP` | **943** | **246** | **925** | **226** | **243** |

**The same five, as matrix indices:**

| target | #1 | #2 | #3 | #4 | #5 |
|:-------------------|-----:|-----:|-----:|-----:|-----:|
| KRAS_G12C | 31 | 122 | 33 | 121 | 29 |
| BCR_ABL1 | 321 | 230 | 229 | 220 | 257 |
| CARDIAC_MYOSIN | 611 | 612 | 610 | 609 | 94 |
| MYC_MAX | 46 | 132 | 28 | 112 | 129 |

**`KRAS_G12C` is the trap**: its structure genuinely numbers from 0, so its two
rows coincide. Code tested only on KRAS will silently use the wrong column on the
other three.

### Read the verdicts with the list

For the three targets where a drug-bound structure exists to check against, our own
validation returns **`NO_SIGNAL_IN_APO`**: the score's confidence interval overlaps
that of the best trivial baseline computed on the same structure.

| target | AUC | floor (trivial baseline) | paired score − floor, 95% CI | detectable ΔAUC |
|:-------------------|------:|:-------------------|:-----------------------|------:|
| KRAS_G12C | 0.514 | 0.529 (`hop_from_seed`) | −0.015 [−0.100, +0.087] | 0.093 |
| BCR_ABL1 | 0.541 | 0.503 (`hop_from_seed`) | +0.038 [−0.057, +0.130] | 0.094 |
| CARDIAC_MYOSIN | 0.548 | 0.454 (`hop_from_seed`) | +0.095 [−0.008, +0.201] | 0.104 |

Every interval includes zero. **We submit the five as required and state plainly
that we cannot certify them** — the conclusion our proposal reaches about the
field's published numbers, applied to our own.

`1NKP` (c-Myc) has no drug-bound structure in the PDB, so no ground truth exists to
score against. Its five are a genuinely prospective prediction, labelled
**unverified**, from a four-operator consensus.

---

## 2. Known limitations, measured

**Where the five actually sit, per target.** Measured here rather than asserted:
heavy-atom minimum distance, altloc A only, hydrogens excluded; the truth pocket is
every residue within 5.0 Å of the validation ligand (`MYR` in `1OPL`, sotorasib
`MOV` in `6OIM`, mavacamten `XB2` in `8QYR`). Reproducible with
`.ai/tools/verify_hit_list_distances.py`.

| target | → validated pocket | → orthosteric ligand | top-site Jaccard |
|---|---|---|---|
| KRAS_G12C (`4LDJ`) | 1.3–14.2 Å | 4.3–8.6 Å (GDP·Mg) | 0.077 (3/20 overlap) |
| BCR_ABL1 (`1OPL`) | 16.7–26.0 Å | 4.2–11.5 Å (P16) | 0.000 (0/56) |
| CARDIAC_MYOSIN (`8QYP`) | 16.6–26.1 Å | 6.6–11.8 Å (ADP·VO4·Mg) | 0.000 (0/85) |

Three readings the Concept Proposal compresses into one line. **BCR-ABL1 and
cardiac myosin miss completely** — nothing we submit comes within 16 Å of the
validated pocket, while everything we submit sits 4–12 Å from the orthosteric
ligand. **KRAS is not a partial success but an unresolvable case**: its switch-II
pocket abuts the nucleotide, so residue 33 lies 1.3 Å from the pocket *and* 4.3 Å
from GDP·Mg — at this separation the two labels cannot be told apart, which is the
confound itself rather than a recovery. **BCR-ABL1's #5 is residue 338**, the
gatekeeper threonine (T315 in Abl-1a numbering, 338 − 19), 4.2 Å from the ATP-site
inhibitor and 16.7 Å from the myristoyl pocket the challenge names as the target.

Against our own site-level detection threshold of Jaccard >= 0.3, that is **0 of 3**.

**Each hit list is one draw.** Ten genuine G12C apo structures span AUC
**0.408–0.595** (median 0.482); substituting the cardiac apo structure moved AUC by
**0.27**. A different, equally defensible apo deposition would give a different five.

**A classical cavity detector beats our walk on one of three targets and loses on
another.** Re-run fresh against the currently shipped structures: fpocket 0.860 vs
our 0.541 on BCR-ABL1; 0.420 vs 0.514 on KRAS G12C; 0.535 vs 0.548 on cardiac
myosin. We report this because fpocket is a stage inside our own pipeline, and
because it is evidence the benchmark is easier than it looks.

**Pooled AUC across proteins carries a protein-identity floor.** A score with all
within-structure position information destroyed — every residue replaced by its own
protein's mean — reaches pooled **AUC 0.65**. Every AUC in this submission is
computed per structure and averaged, never pooled; we audited that rather than
assuming it.

**Our own orthosteric-exclusion filter never fires on two of the three scoreable
apo inputs, and this is why BCR-ABL1's #5 hit is the gatekeeper residue, not a
distal one.** `func_ligand` excludes active-site contacts by exact ligand-code
match against the input structure; BCR-ABL1's declared code is `NIL` (nilotinib),
present only in the holo structure `5MO4` and absent from the apo input `1OPL`
(which carries `MYR`/`P16` instead), and cardiac myosin's list omits `VO4`, the
ADP-vanadate transition-state mimic sitting in `8QYP` beside the `ADP` that is listed.
The lookup fails closed rather than erroring, so a stale or incomplete code
produces no signal that exclusion did not happen. Named here rather than fixed:
with under 36 hours to the deadline, re-running invalidates every number already
in this package. TASK-0386 tracks the finding; TASK-0391 tracks the fix, scoped
for after submission.

---

## 3. Methodological report, per target

### KRAS_G12C — `4LDJ`

```
Target: KRAS_G12C  |  Structure: 4LDJ (apo)
========================================================================
HEADLINE VERDICT
========================================================================
[NOTE] AUC values below use the decoherent/time-averaged CTQW limit (a spectral overlap
    between source and residue eigenvector components), not a coherent quantum-walk
    snapshot -- all phase information is averaged out by construction. See TASK-0097 /
    REVIEW-2026-07-13 finding P2-B.

  AUC_apo_Hnew_default           : 0.514
  AUC_apo_H10_baseline           : 0.346
  AUC_apo_Hnew_optimised         : 0.514
  AUC_holo_Hnew_optimised        : N/A
  AUC_ctqw_mean                  : 0.514
  AUC_heat_mean                  : 0.342
  most_impactful_term            : V_M
  least_impactful_term           : V_T
  mean_rho_apo_holo              : N/A
  mean_jacc20                    : N/A
  coherence_auc_range            : N/A
  coherence_auc_at_gamma0        : N/A
  coherence_classification       : N/A

  _diagnosis                     : NO_SIGNAL_IN_APO
  score 95% CI                   : 0.514  [0.348, 0.698] (95% block-bootstrap CI)
  floor 95% CI                   : 0.529  [0.346, 0.716] (95% block-bootstrap CI)
  CIs overlap?                   : YES -- statistically indistinguishable from the floor
      at this confidence level

DECISION-SUPPORT RECOMMENDATION
--------------------------------
1) Operator gain over H10 baseline (apo): DAUC = +0.168  (meaningful). -- but not
    statistically distinguishable from the trivial floor at 95% CI (see _diagnosis
    above); read this point estimate as a lead, not an established gain
2) CTQW vs ground-state relaxation on H_new (same operator, not a classical-diffusion
    comparison -- see TASK-0095): DAUC = +0.171  (CTQW genuinely helps). -- but not
    statistically distinguishable from the trivial floor at 95% CI (see _diagnosis
    above); read this point estimate as a lead, not an established gain
3) Most/least impactful potential terms: most = V_M, least = V_T.
```

### BCR_ABL1 — `1OPL`

```
Target: BCR_ABL1  |  Structure: 1OPL (apo)
========================================================================
HEADLINE VERDICT
========================================================================
[NOTE] AUC values below use the decoherent/time-averaged CTQW limit (a spectral overlap
    between source and residue eigenvector components), not a coherent quantum-walk
    snapshot -- all phase information is averaged out by construction. See TASK-0097 /
    REVIEW-2026-07-13 finding P2-B.

  AUC_apo_Hnew_default           : 0.541
  AUC_apo_H10_baseline           : 0.520
  AUC_apo_Hnew_optimised         : 0.541
  AUC_holo_Hnew_optimised        : N/A
  AUC_ctqw_mean                  : 0.541
  AUC_heat_mean                  : 0.664
  most_impactful_term            : V_B
  least_impactful_term           : V_C
  mean_rho_apo_holo              : N/A
  mean_jacc20                    : N/A
  coherence_auc_range            : N/A
  coherence_auc_at_gamma0        : N/A
  coherence_classification       : N/A

  _diagnosis                     : NO_SIGNAL_IN_APO
  score 95% CI                   : 0.541  [0.375, 0.689] (95% block-bootstrap CI)
  floor 95% CI                   : 0.503  [0.350, 0.638] (95% block-bootstrap CI)
  CIs overlap?                   : YES -- statistically indistinguishable from the floor
      at this confidence level

DECISION-SUPPORT RECOMMENDATION
--------------------------------
1) Operator gain over H10 baseline (apo): DAUC = +0.020  (marginal). -- but not
    statistically distinguishable from the trivial floor at 95% CI (see _diagnosis
    above); read this point estimate as a lead, not an established gain
2) CTQW vs ground-state relaxation on H_new (same operator, not a classical-diffusion
    comparison -- see TASK-0095): DAUC = -0.123  (within graph-kernel noise -- CTQW does
    NOT add biological information beyond the operator).
3) Most/least impactful potential terms: most = V_B, least = V_C.
```

### CARDIAC_MYOSIN — `8QYP`

```
Target: CARDIAC_MYOSIN  |  Structure: 8QYP (apo, Bos taurus)
========================================================================
HEADLINE VERDICT
========================================================================
[NOTE] AUC values below use the decoherent/time-averaged CTQW limit (a spectral overlap
    between source and residue eigenvector components), not a coherent quantum-walk
    snapshot -- all phase information is averaged out by construction. See TASK-0097 /
    REVIEW-2026-07-13 finding P2-B.

  AUC_apo_Hnew_default           : 0.548
  AUC_apo_H10_baseline           : 0.468
  AUC_apo_Hnew_optimised         : 0.548
  AUC_holo_Hnew_optimised        : N/A
  AUC_ctqw_mean                  : 0.548
  AUC_heat_mean                  : 0.514
  most_impactful_term            : V_B
  least_impactful_term           : V_R
  mean_rho_apo_holo              : N/A
  mean_jacc20                    : N/A
  coherence_auc_range            : N/A
  coherence_auc_at_gamma0        : N/A
  coherence_classification       : N/A

  _diagnosis                     : NO_SIGNAL_IN_APO
  score 95% CI                   : 0.548  [0.372, 0.774] (95% block-bootstrap CI)
  floor 95% CI                   : 0.454  [0.301, 0.671] (95% block-bootstrap CI)
  CIs overlap?                   : YES -- statistically indistinguishable from the floor
      at this confidence level

DECISION-SUPPORT RECOMMENDATION
--------------------------------
1) Operator gain over H10 baseline (apo): DAUC = +0.081  (meaningful). -- but not
    statistically distinguishable from the trivial floor at 95% CI (see _diagnosis
    above); read this point estimate as a lead, not an established gain
2) CTQW vs ground-state relaxation on H_new (same operator, not a classical-diffusion
    comparison -- see TASK-0095): DAUC = +0.035  (within graph-kernel noise -- CTQW does
    NOT add biological information beyond the operator).
3) Most/least impactful potential terms: most = V_B, least = V_R.
```

### MYC_MAX — `1NKP`

```
=== MYC_MAX -- NO GROUND TRUTH ===

No AUC, no ceiling, and no proximity-floor check are computed or
reported for this target: no holo/bound structure exists for this allosteric question.
    This is this target's own
documented status (config/targets.yaml), not a scoring failure or
an omission -- per this project's own convention, an honest NO is
reported explicitly, not silently dropped.

Consensus prediction across 4 independent operators (H_new_default,
    H10_disorder_suppressed, H2_combinatorial_laplacian, H14_anm_pinv_trace), top-5:
  1. residue 943 -- 4/4 operators agree (top-5), mean occupancy=0.0698
  2. residue 246 -- 3/4 operators agree (top-5), mean occupancy=0.0599
  3. residue 925 -- 3/4 operators agree (top-5), mean occupancy=0.0494
  4. residue 226 -- 2/4 operators agree (top-5), mean occupancy=0.0413
  5. residue 243 -- 2/4 operators agree (top-5), mean occupancy=0.0405

Confidence: unverified -- at least one residue appears in all 4 operators' own top-5,
    but operator agreement is not validated confidence: no ground truth exists for this
    target to check against, and the Concept Proposal's own §2 measures these operators
    as correlated distance detectors, not independent evidence

Theoretical docking viability (fpocket):
  pocket 1: score=0.305, druggability_score=0.161
  pocket 2: score=0.112, druggability_score=0.023
  pocket 3: score=0.091, druggability_score=0.007
  pocket 4: score=0.081, druggability_score=0.158
  pocket 5: score=0.054, druggability_score=0.0
```

Our own configuration records that this target has no folded-state allosteric
pocket (`allosteric_pocket_exists: false`, `config/targets.yaml` — Myc/Max are
IDPs with no surface pocket in the folded dimer); we supply the five because the
challenge requires them, and we report that our best candidate site scores 0.161
druggability against our own 0.5 fpocket druggable/non-druggable threshold.

---

## 4. Independent second-pipeline corroboration (PASSer/`allosteric` track)

A second pipeline on the `allosteric` branch (`github.com/Oussema-t/Quantum_allosteric-scanner`)
reruns the same question — PASSer pocket detection instead of fpocket, 630 proteins in 399
families instead of our own cohort, a different candidate funnel and a different seeding rule.
**It is an independent second pipeline, not a replication** — different detector, different
cohort, different seeding, different candidate funnel — and it is corroboration on the findings
below, every AUC computed per structure and averaged, never pooled.

### 4.1 Construction

Residues are C-alpha nodes; edges lie within a 10 Å C-alpha contact cutoff (drug-pocket truth uses
a separate 4.5 Å heavy-atom cutoff). The walk is `U(t) = exp(-iHt)`, seeded at the active site and
read as the converged average `p_avg(s->a) = sum_k |v_k(s)|^2 |v_k(a)|^2` — a sum of squares,
hence phase-free. The connectivity matrix `C_ij` is that average-mixing matrix,
`(V o V)(V o V)^T`: symmetric, row-stochastic, operator-only. Thirteen operators (four weightings × three
normalisations, plus `H_new = L_sym + diag(0.08 V_B + 0.16 V_T + 0.08 V_R + 0.04 V_C + 0.04 V_M)`)
× seventeen scores give 221 cells per target.

**`neg_dE`, the strongest single score in the 221-cell sweep, is provably classical.** It is
time-independent and equals `sqrt(sum_j W_ij^2)` to machine precision — a classical local statistic, so
the best-scoring cell in a quantum sweep cannot be carrying interference. This directly supports
this proposal's own §2 conclusion that the phase-free construction is exhausted.

### 4.2 Selection ceilings vs. the single fixed cell

Best-of-221 per protein (picking the best Hamiltonian and score *for each protein separately*)
reaches P@5>=0.8 on 200/115, 147/77, 82/49, 47/20 (proteins/families) at MIN_HOP 1/2/3/4. The
single fixed cell that survives once the per-protein choice is removed clears **69 proteins / 20
families** at P@5>=0.8. **The gap between them is the multiplicity this proposal's own §1
correction is built to catch** — quantified here on an independent cohort with a different
detector, the same shape as this proposal's own 137-family vs. 99.8-null selection-artefact
finding.

The pre-registered `H_new` cell — the one specified in advance, not selected post hoc — is an
honest near-negative on all four targets: KRAS 0.479 (p=0.57), BCR-ABL1 0.411 (p=0.84), cardiac
myosin 0.601 (p=0.12), HIV-1 RT 0.665 (p=0.060). **This is the highest-value single result in the
second pipeline** — an independent reproduction of this proposal's own central conclusion, that
the pre-registered result is a near-negative while the best-of-221 selection ceiling looks
excellent. Ship these two numbers together; neither is meaningful without the other.

Per-target, best and worst of the 221 cells (chosen by P@5, one consistent pipeline run):

| target (apo) | cell | operator / score | AUC | P@5 |
|---|---|---|---|---|
| KRAS G12C (`4LDJ`) | best | `H_new` / resolvent | 0.809 | 0.6 |
| KRAS G12C (`4LDJ`) | worst | `H11_aniso` / residual RAW | 0.184 | 0.0 |
| BCR-ABL1 (`1OPL`) | best | `H6_exp` / residual+focus | 0.796 | 1.0 |
| BCR-ABL1 (`1OPL`) | worst | `H5_gauss` / ratio p_peak/p_avg | 0.227 | 0.0 |
| Cardiac myosin (`8QYP`→`8QYR`) | best | `H3_normL` / dX dip depth | 0.685 | 0.4 |
| Cardiac myosin (`8QYP`→`8QYR`) | worst | `H8_gnm` / −dD mean | 0.068 | 0.0 |

**HIV-1 RT's best cell reaches AUC 0.963 / P@5 0.8 — reported here only beside the near-negative
above, never standalone.** In a document whose thesis is "nothing beats chance", a near-perfect
single-cell number is a selection artefact if quoted alone; it belongs next to the pre-registered
`H_new` near-negative it was selected against, not apart from it. Worst cell: `H14_anmP` / Green
E=lambda_max, AUC 0.196, P@5 0.0. Best and worst share protein, seeding and scoring, so the AUC spread
(0.63/0.57/0.62/0.77 per target) is the operator-and-score choice alone.

**A known reproducibility defect, disclosed here rather than only in a figure caption**: cardiac
myosin's top-5 depends on a fpocket seeding that does not reproduce headless (i.e., the seed set
is sensitive to a detail of the run environment) — its true pocket ranks outside fpocket's top-10
on druggability alone but 3rd on PASSer allostery, so a different fpocket run can seed a different
top-5. This is a genuine limitation of the second pipeline's seeding step, named directly rather
than left implicit in an image caption, consistent with this document's own §2 disclosure
standard.

### 4.3 Protein-identity floor — reproduced independently, at a higher value

**The protein-identity floor reproduces on this second cohort at pooled AUC 0.771, above every
method tested there.** §2 above reports 0.65 on our own cohort and states we found no report of
the check elsewhere; an independent reproduction on a different pipeline, at a *higher* value,
materially strengthens that this floor is real and not an artefact of one pipeline's own scoring
convention.

**On identical residues (MIN_HOP=1, P@5 with AUC>=0.6) the second pipeline's fixed cell clears 69
proteins / 20 families at P@5>=0.8** — more per-protein than any of thirteen classical baselines
tried on that cohort, but *fewer families* than closeness centrality (48 proteins / 29 families),
which has no active site at all. Family-weighted AUC confirms the walk never beats closeness
(0.585/0.542/0.544/0.543 vs. 0.601/0.569/0.575/0.580 at MIN_HOP 1–4; non-significant under paired
McNemar).

**A blind leave-one-family-out regression over all 221 scores reaches AUC 0.7216 on the 91 distal
proteins, against a reversed-distance floor of 0.7219.** The walk does not beat distance, blind,
on this cohort either — an independent replication of this proposal's own central negative result
(§2: "beaten by distance-to-the-active-site").

### 4.4 The configuration recommender — reconciled with §6's two diagnostics

A single Ridge multi-output model sets the quantum stage (MIN_HOP, Hamiltonian, score) from nine
topology features alone, trained leave-one-family-out over 630 proteins in 399 families: 9 graph
features → StandardScaler → Ridge multi-output → predicted AUC of all 884 configurations (221
cells × 4 MIN_HOP) → rank → top-*k* with softmax weights.

**This is a different model from §6's two random-forest diagnostics, not a contradiction of
them.** The two random forests (a MIN_HOP classifier, AUC 0.793, and an operator-score regressor,
0.625 vs. 0.630) are the diagnostic that shows what topology can and cannot predict; the single
Ridge recommender above is the deliverable built on that diagnosis. It is honest about the same
limits its own diagnostics found: it narrows MIN_HOP well and reports the operator/score shortlist
as a *selection*, not a confident pick. At k=6 the shortlist's best cell averages AUC 0.724 over 43
families.

### 4.5 Connectivity — the four scoreable targets

![Connectivity C_ij for the four scoreable targets — best operator (top row), worst operator
(middle), and the top-5 predicted-residue × active-site sub-block (bottom; rows = the five
predicted residues, red label = residue in the drug pocket, grey = not; columns = active-site
residues). Best and worst share protein, seeding and scoring, so their contrast is the
operator-and-score choice alone. Cardiac myosin's top-5 is omitted here (§4.2's fpocket-seeding
caveat applies) and kept in the second pipeline's own `results/connectivity/`; c-Myc/Max is
connectivity-only there (no ground truth).](figures/connectivity_sites.png)

---

## Provenance

Produced by the pipeline at `github.com/Oussema-t/Quantum_allosteric-scanner`
(branch `bartosz`), published 2026-09-15. The five residues in each list match the
Concept Proposal's own table exactly — checked, not assumed.
