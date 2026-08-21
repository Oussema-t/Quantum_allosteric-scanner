# TASK-0210 — Observable-family proximity confound: quantum vs classical vs entropic

**Status:** OBSERVED (non-target structures) / **REQUIRES PDB-RETEST**
**Date:** 2026-08-21
**Provenance:** external chat session, no repo access, no rcsb.org egress.
Scripts in this drop: `real_pdb_confound.py`, `obs_family_confound2.py`, `robust.py`.

---

## 1. Claim under test

> The proximity confound is a property of **seed-referencing scoring on a static contact
> graph** — not of the CTQW propagator, not of quantumness, and not of the
> correlation-versus-entropy distinction.

If true, this reframes the program's central negative result: the confound is not an
implementation defect in the quantum arm but a property of the observable class the
challenge mandates in Section 5.

## 2. Method

Real CA coordinates, 9 single chains bundled with `prody` / `MDAnalysisTests`
(N = 76–436). Contact graph at 8.5 Å plus enforced chain connectivity. Four buried-ish
seeds per chain drawn from the 35th–80th radial percentile, so that seed proximity is
**not** collinear with burial. 36 (chain, seed) replicates.

Scoring: Spearman ρ of each observable against Euclidean distance to seed, reported as a
**partial** rank correlation controlling for burial (distance from centroid). Controlling
burial matters — without it, a centrally placed seed makes "far from seed" and "surface"
the same variable and every number is inflated.

## 3. Results — real PDB, 36 replicates

| observable | family | \|partial ρ(dist \| burial)\| | ρ(burial) |
|---|---|---|---|
| `heat_T5` (classical diffusion) | seed-ref, classical | **0.861 ± 0.119** | 0.160 |
| `GNM_corr_seed` (DCC) | seed-ref, equilibrium | **0.899 ± 0.065** | 0.166 |
| `GNM_corr_low10` (dcc_low analogue) | seed-ref, low-mode | **0.870 ± 0.068** | 0.096 |
| `CTQW_adj_T5` | seed-ref, quantum | 0.788 ± 0.133 | 0.220 |
| `CTQW_adj_T25` | seed-ref, quantum | **0.697 ± 0.194** | 0.145 |
| `MRW_commute` — **ref [8]** | seed-ref, classical Markov | 0.711 ± 0.125 | 0.561 |
| `dMSF_at_seed` (entropic coupling) | seed-ref, entropic | 0.773 ± 0.162 | 0.505 |
| `dS_vib_global` (Cooper–Dryden) | **seed-blind**, entropic | **0.067 ± 0.057** | −0.370 |
| `slow1` minima — **ref [16]** | **seed-blind**, modal | **0.292 ± 0.218** | — |

Synthetic replication (24 replicates, compact lattice globule, ⟨k⟩ = 8.1, diameter 11)
reproduces the same ordering — see `robust.py`.

### 3.1 Findings

- **OBSERVED — the confound is not quantum.** The classical heat kernel (0.861) and GNM
  correlation (0.899) are **more** distance-locked than the CTQW (0.697–0.788). The CTQW
  is the *least* confounded member of the seed-referencing family tested.
- **OBSERVED — the mandated classical baseline is confounded too.** Ref [8]'s Markov
  commute time sits at 0.711 and carries an additional burial load of 0.561.
- **OBSERVED — the entropic route offers no escape while it stays seed-referencing.**
  `dMSF_at_seed` — the closest static-structure proxy for an ensemble-coupling quantity —
  is confounded at 0.773. **This is the direct answer to the concern that ref [4] was a
  missed exit: on a static structure, the harmonic ensemble route lands in the same room.**
- **OBSERVED — only seed-blind observables escape.** `dS_vib_global` (0.067) and ref [16]
  slow-mode minima (0.292). Both are proximity-orthogonal and both are **unable to answer
  "connectivity to the active site"** as objective 4.1 phrases it. They address it only
  under that objective's own "in most cases" qualifier.
- **OBSERVED — variance collapse reproduces independently.** An 11-observable ENM zoo
  (CTQW, heat, MRW, DCC, DCC-low, GNM MSF, slow1, slow1-3, degree, burial, distance) has
  **mean effective rank 3.65 / 11** across 6 real chains (range 3.22–4.02, entropy-based).
  This is an **external confirmation of TASK-0199's rank-~3 finding** using a different
  observable set on different proteins — it is not a repeat measurement.

## 4. What this does NOT establish

Read these before citing any number above.

1. **No answer key.** These are bundled test structures, not challenge targets, and none
   has an annotated allosteric site here. This bounds **confound structure only**. It says
   nothing about predictive accuracy, AUC, or enrichment.
2. **The harmonic proxy is not EAM.** `dMSF_at_seed` uses harmonic spring stiffening.
   Ref [4]'s ensemble model uses **binary folded/unfolded** units — nonlinear and
   non-Gaussian. **The genuine EAM remains untested.** Do not write "we tested the
   ensemble model." Write "we tested its harmonic linear-response proxy."
3. **Low-mode discrepancy — unresolved and load-bearing.** Here `GNM_corr_low10` stayed
   confounded (0.870), whereas the repo reports `prs_low` collapsing to ρ ≈ 0.08. These
   are different observables (DCC vs PRS) on different systems, so the two results are not
   formally in conflict — **but the discrepancy must be resolved on the actual targets
   before either number appears in a document.** If PRS-low genuinely decorrelates where
   DCC-low does not, that is a real and reportable asymmetry. If it does not replicate,
   an existing repo claim needs correcting.
4. **Burial control is a proxy.** Distance-from-centroid is a crude burial measure.
   Re-run with relative SASA on the real targets.
5. **Single perturbation magnitude.** STIFF = 3.0, first-shell only. Not swept.
6. **Seed selection is radial-percentile, not the true active site.** On the real targets
   the seed must be the annotated catalytic/active site.

## 5. PDB-RETEST instructions for repo agents

**Mandatory before any of this enters the submission.**

- **Targets:** KRAS_G12C (4OBE), BCR-ABL1 (1OPL), Cardiac Myosin (5TBY), PTP1B apo,
  c-Myc/Max (1NKP). Apo only — the input structures.
- **Seeds:** annotated active/catalytic site residues, not radial percentiles.
- **Burial control:** relative SASA (DSSP/FreeSASA), replacing centroid distance.
- **Add:** `prs_low` alongside `GNM_corr_low10` in the same harness, to settle §4.3.
- **Add:** the chiral / Peierls-phase Hodge observable, which is the program's own
  candidate proximity-orthogonal quantity — it belongs in this table.
- **Add:** ref [7] ENM impulse-response energy transport (closed-form, MD-free). Predicted
  distance-dominated; if so, the confound survives a change of physical framework, which
  strengthens the negative result.
- **Null:** use the corrected **compact-label** permutation null. The scattered
  permutation null is anti-conservative by ~4.8× at α = 0.05 and up to ~42× at α = 0.001
  for compact labels. Do not reuse it here.
- **Multiple comparisons:** this harness adds ~9 observables × 5 targets = ~45 cells to
  the program-level budget. Log them.
- **Negative control (required by repo convention):** construct a case where the true
  allosteric signal and the distance confound make **different** predictions, and confirm
  that `dS_vib_global` and slow-mode minima track the former. Without that control, their
  low ρ shows only that they ignore the seed — which is trivially true by construction and
  is **not** evidence that they carry allosteric signal.

## 6. Consequences for the submission

1. **Reframe the proximity finding.** Not "our quantum observable turned out to be a
   distance detector" but "**every seed-referencing observable on a static contact graph
   is a distance detector, including the classical analogue the challenge itself cites in
   Section 5 — and the quantum walk is the least affected of them.**" Same evidence,
   accurate, and materially stronger.
2. **It discharges objective 4.2.** "Comparison to classical analogs, where relevant,
   should be analyzed" — this is that analysis, with a quantified head-to-head.
3. **It closes off the ref [4] rescue honestly.** The ensemble angle does not recover a
   positive result on static structures. Say so, and say what remains open (nonlinear EAM,
   §4.2) rather than leaving the reader to wonder whether it was overlooked.
4. **The escape route is seed-blindness or conformational search, not a better operator.**
   Both surviving proximity-orthogonal observables are seed-blind. That is consistent with
   the program's existing conclusion that the problem is conformational search, not
   residue scoring — and it is now supported by a measurement rather than an argument.
