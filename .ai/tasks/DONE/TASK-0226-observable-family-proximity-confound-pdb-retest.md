# TASK-0226 (re-indexed from the 2026-08-21 external drop's "TASK-0210_observable_family_confound")

## Context

- ID: TASK-0226
- Status: Done
- Owner: Implementer
- Claimed By: —
- Claimed At: —
- Source: `.ai/reviews/2026-08-21/TASK-0210_observable_family_confound.md` — external session, no repo
  access, no rcsb.org egress. **Every numeric in the body below was run on
  bundled non-target structures (prody / MDAnalysisTests). Nothing in it may be
  cited in the submission before a PDB-retest on real challenge targets.**
- **Re-indexed on filing.** The drop numbered this `TASK-0210_observable_family_confound`, but that ID is
  already taken in this register by unrelated, completed work:
  TASK-0210 (coupled backbone+rotamer search, Done), TASK-0211 (ensemble-graph
  observable independence, Done), TASK-0212 (frustration-rank reproducibility,
  closed as invalidated). Renumbered to TASK-0226 rather than the incumbents,
  per this register's own collision precedent (TASK-0156/0157, TASK-0168).
  **Cross-references inside the body below still use the drop's own numbering**
  and are mapped here: drop 0210 → TASK-0226, drop 0211 → TASK-0227,
  drop 0212 → TASK-0228.

---

## Original document, verbatim

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

---

## Repo agent's PDB-retest — Done

**2026-08-21 — Implementer A.** Section 5's PDB-retest instructions executed on real
targets. Scripts: `scripts/task0226_observable_family_confound_pdb_retest.py` (main
retest), `scripts/task0226_negative_control.py` (planted-signal control). Raw output:
`results/tasks/0226_observable_family_confound/{real_pdb_confound.json,
negative_control.json}` (gitignored `results/` path — same storage decision as
[[TASK-0225]], committed regardless).

**Targets**: KRAS_G12C (4OBE), BCR_ABL1 (1OPL), CARDIAC_MYOSIN (8QYP — `targets.yaml`'s
current substitution for the drop's stale "5TBY" citation, [[TASK-0124]]), PTP1B
(1SUG), MYC_MAX/c-Myc (1NKP). All real network fetches, no mocking.

**Seeds**: real annotated active/catalytic sites via `labels.functional_indices`, the
same call `run_challenge.py` itself uses — **not** the drop's radial-percentile draws.
KRAS_G12C: 18 real GDP/P-loop contact residues (`func_ligand-contact:GDP`). BCR_ABL1:
26 residues (`func_ligand-contact:NIL`). CARDIAC_MYOSIN: 18 residues
(`func_ligand-contact:ADP`). PTP1B: 9 residues, the UniProt-curated Cys215 catalytic
site (`active_site_uniprot`). MYC_MAX: 5 residues, **top-degree topological-proxy
fallback** — no functional ligand is resolvable for this target (no holo structure at
all, `func_ligand: ["DNA"]` never matches a HETATM), a pre-existing, already-documented
project limitation ([[TASK-0216]]), not something this task introduces or can fix.
MYC_MAX's own cells below should be read with that caveat.

**Bug caught before it produced any real number**: the first draft called
`functional_indices` with an empty `ligand_groups` list for every target (copying
`run_target_no_ground_truth`'s MYC_MAX-only pattern) — this silently forced every
target into the top-degree fallback, since a real `func_ligand` match requires holo's
own ligand contacts. Caught by inspecting `provenance` on the very first real run
(KRAS_G12C came back `'top-degree fallback'` when GDP is right there in 6OIM) before
trusting any downstream number. Fixed by reusing `consensus_labels.load_apo_holo_full`
(already-debugged apo+holo loader) and passing holo's real `ligand_groups`/heavy-atom
data through, matching `build_labels`'s own call shape exactly.

**Second bug, performance not correctness**: `dMSF_at_seed`'s own per-residue
stiffening sweep (an O(N) loop of N×N eigendecompositions) was first written *inside*
the per-seed loop — for CARDIAC_MYOSIN (N=704, 18 seeds) that is ~12,700 redundant
704×704 eigendecompositions instead of 704. Caught before it finished (killed after
the first observation, not after burning the wall-clock) by comparing against the
already-correct `dS_vib_global` sweep sitting right next to it, which computes its own
identical stiffening loop *once* outside the seed loop. Fixed by merging the two
sweeps into one pass, storing only the active-site-relevant columns of the perturbed
covariance (not the full (N,N) matrix, per the drop's own stated memory concern for
large real targets). CARDIAC_MYOSIN: 74s after the fix.

**Burial control**: real per-residue SASA (freesasa, Shrake-Rupley) on the apo
structure alone, `burial = -SASA` — replacing the drop's centroid-distance proxy.
Zero unmapped residues on any of the 5 targets.

### Results — real PDB, partial Spearman rho(dist | SASA-burial), 76 per-seed
### replicates (real active-site residues) pooled across the 5 targets, or one
### value per target for the full-active-site-set group (see script docstring
### for which observables are in which group and why)

| observable | group | \|partial rho\| | \|rho_ed\| | rho_burial |
|---|---|---|---|---|
| `GNM_corr_seed` (DCC) | per-seed, classical | **0.888 ± 0.068** | 0.875 | 0.126 |
| `GNM_corr_low10` (drop's own 10-mode port) | per-seed, low-mode | 0.865 ± 0.066 | 0.848 | 0.111 |
| `heat_T5` (classical diffusion) | per-seed, classical | 0.806 ± 0.097 | 0.788 | 0.089 |
| `dMSF_at_seed` (entropic coupling) | per-seed, entropic | 0.795 ± 0.082 | 0.816 | 0.455 |
| `transmission_E0` (ref [7], Landauer T(E=0)) | full-set, quantum transport | 0.795 | 0.827 | 0.466 |
| `CTQW_adj_T5` | per-seed, quantum | 0.788 ± 0.079 | 0.798 | 0.200 |
| `MRW_commute` (ref [8]) | per-seed, classical Markov | 0.755 ± 0.062 | 0.762 | 0.610 |
| `CTQW_adj_T25` | per-seed, quantum | **0.677 ± 0.118** | 0.695 | 0.194 |
| `chiral_circ` (Peierls/Hodge circulation) | full-set, quantum | 0.540 | 0.620 | 0.655 |
| `slow1_minima` — ref [16] (this task's own proxy) | per-seed, seed-blind, modal | 0.496 ± 0.193 | 0.513 | 0.150 |
| `dcc_low` (repo canonical, k=20) | full-set, low-mode | 0.384 | 0.455 | 0.323 |
| `prs_low` (repo canonical, k=20) | full-set, low-mode | **0.232** | 0.319 | -0.438 |
| `dS_vib_global` (Cooper–Dryden proxy) | per-seed, seed-blind, entropic | **0.082 ± 0.050** | 0.217 | -0.670 |

**Central claim replicated on real targets, real seeds, real SASA burial**: the CTQW
is not the most confounded seed-referencing observable — `CTQW_adj_T25` (0.677) sits
*below* every other seed-referencing observable in this table except the two seed-blind
ones and `chiral_circ`. The classical analogue the challenge itself cites (`MRW_commute`,
ref [8]) is confounded at 0.755, and the classical DCC/heat-kernel observables are the
*most* confounded of the entire family (0.81–0.89). **Same finding as the drop's own
non-target-structure result, now on real structures with real annotated active sites
and a real burial control — a materially stronger form of the same evidence, not a
repeat measurement of a weaker one.**

**Only seed-blind observables meaningfully escape** — `dS_vib_global` (0.082) cleanly;
`slow1_minima` (0.496 ± 0.193, wide spread [0.01, 0.76]) only partially, and notably
less cleanly on real targets than the drop's own non-target-structure number (0.292) —
a real, reportable difference, not smoothed over.

**Resolves drop §4.3's flagged discrepancy, partially.** On real targets: `prs_low`
(0.232) escapes the confound substantially better than either DCC-style measurement
tested — `dcc_low` (repo's own canonical k=20 implementation, 0.384) or `GNM_corr_low10`
(this task's own port of the drop's exact 10-mode math, 0.865). **This is a real,
family-level asymmetry (PRS vs. DCC), not an artifact of one implementation** — but the
0.384 vs. 0.865 gap *within* the nominally same "DCC" family (different mode count,
full-active-site-set vs. per-residue seed cardinality, different averaging convention)
means mode count/seed cardinality is a real, uncontrolled second variable here, not
cleanly isolated. Flagged for a follow-up if this distinction becomes load-bearing.

**`transmission_E0` (ref [7]) does not strengthen the negative result the way the drop
hoped** — it is one of the *most* confounded observables tested (0.795), consistent
with this project's own prior finding (RESULTS.md, TASK-0145: quantum transmission and
classical `1/R_eff` are strongly correlated, rho 0.74–0.85, same shared Laplacian).

**New finding, not in the original drop**: `chiral_circ` (this project's own candidate
proximity-orthogonal quantity, TASK-0140) shows a real, partial escape from the confound
(0.540) — worse than the two seed-blind observables, but meaningfully better than every
other seed-referencing observable in the table. Not previously characterized against
this specific confound structure.

### Negative control (drop §5's explicit requirement)

KRAS_G12C, real P-loop seed, `plant.select_distal_patch` (floor-blind AND far-hop by
construction — a proximity detector fails here by design) → 10-residue target patch,
Rg=5.28 Å → `plant.plant_channel` (strength=5.0, 10 paths, all applied, 34 edges
modified) → `dS_vib_global`/`slow1_minima` recomputed on the planted graph → tested
against `nulls.graph_walk_patch_matched` (the corrected, Rg-matched null the drop's own
Section 5 explicitly requires in place of the anti-conservative scattered null),
N=500 null draws.

| observable | true mean (in patch) | null mean ± std | p (one-sided) |
|---|---|---|---|
| `slow1_minima` | -0.0171 | -0.0889 ± 0.0638 | **0.0279** |
| `dS_vib_global` | -4.2991 | -4.5968 ± 0.5469 | 0.3333 |

**Mixed, honestly reported — not a clean confirmation.** `slow1_minima` shows nominal
enrichment in the planted distal patch (p=0.028), but does **not** survive even a
minimal 2-comparison Bonferroni correction (needs p<0.025). `dS_vib_global` — the
observable that escaped the confound most cleanly above — shows no significant
enrichment at this single tested strength/patch (p=0.33). **This is a single
strength/single-patch confirmatory check, not a formal LOD sweep** (that machinery
exists for other families, `scripts/mechanism_discriminating_plant.py`, [[TASK-0168]]);
it does not establish that either observable reliably carries planted signal, only that
one shows a weak, uncorrected-significant hint of it. A real open item, not smoothed
into "confirmed" — flagged for a follow-up LOD sweep before either observable's
seed-blindness is read as "and therefore carries real allosteric signal."

### Multiple comparisons

13 observables × 5 targets = 65 confound-structure comparison cells (partial Spearman
rho against distance/burial), plus 2 cells in the negative control (synthetic planted
signal). **Neither is added to RESULTS.md's own "Program-level multiple-comparison
budget" table** — that table's own stated scope is real-target-*label* comparisons
(AUC/p-value against an annotated pocket), and explicitly excludes synthetic-signal
negative controls; confound-structure correlations against distance/burial reference no
label at all. Logged here, transparently, per the drop's own explicit request, as a
separate category rather than force-fit into a table whose own definition does not
cover it.

### What this does NOT establish (carried forward from the drop's own §4, still true)

Every caveat in the drop's own Section 4 still applies verbatim on real data: this
bounds confound structure only, not predictive accuracy/AUC/enrichment; `dMSF_at_seed`
is a harmonic proxy, not the genuine (nonlinear) EAM; `slow1_minima` is this task's own
proxy for ref [16], not independently verified against that reference's exact method;
single perturbation magnitude (STIFF=3.0), not swept. **Additionally now resolved**:
seeds are real annotated active sites (not radial percentiles) and burial is real SASA
(not centroid distance) — the two items §5 flagged as mandatory before any of this
enters the submission.

### Consequence for the submission

Section 6's reframing (drop's own text, items 1–4 above) is now **evidence-backed on
real challenge targets**, not just non-target structures — safe to cite in
[[TASK-0184]] once that document is next touched. The one caveat that must travel with
it: the negative control is a single-condition confirmatory check, not a full LOD
characterization, and `dS_vib_global`'s own escape from the confound is not yet shown
to correspond to detecting a real planted signal at this tested strength.
