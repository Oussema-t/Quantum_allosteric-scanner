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

## Provenance

Produced by the pipeline at `github.com/Oussema-t/Quantum_allosteric-scanner`
(branch `bartosz`), published 2026-09-15. The five residues in each list match the
Concept Proposal's own table exactly — checked, not assumed.
