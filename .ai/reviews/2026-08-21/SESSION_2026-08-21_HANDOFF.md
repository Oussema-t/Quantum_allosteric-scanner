# SESSION_2026-08-21 — external session handoff

**Provenance:** external chat session, no repo access, no rcsb.org egress. All numerics run
on bundled non-target structures (prody / MDAnalysisTests test data). **No result here
touches a challenge target. Nothing may be cited in the submission before PDB-retest.**

**Files in this drop:**
| file | contents |
|---|---|
| `REFERENCE_HYPOTHESIS_REGISTER.md` | hypotheses extracted from challenge refs [1]–[25], tiered by threat/value, tested-status, open venues |
| `TASK-0210_observable_family_confound.md` | proximity confound across observable families, real PDB |
| `TASK-0211_anm_rotamer_qubo_reachability.md` | ANM⊕rotamer QUBO — inference review + reachability spec |
| `TASK-0212_conformer_graph_search.md` | conformer-graph search proposal; **contains a correction to TASK-0211 §3** |
| `real_pdb_confound.py`, `robust.py`, `obs_family_confound2.py`, `real_pdb_confound.json` | TASK-0210 harness + raw output |
| `anm_mode_overlap.py`, `adaptive_subspace_test.py` | TASK-0211/0212 harnesses, written to accept real apo→holo vectors |

---

## 1. New OBSERVED results (non-target structures)

1. **The proximity confound is not quantum and not ours.** 36 replicates, 9 real chains,
   partial Spearman controlling burial: classical heat kernel 0.861, GNM/DCC 0.899,
   ref [8] Markov commute 0.711, entropic coupling 0.773 — **CTQW 0.697, the least
   confounded of the seed-referencing family.** Only seed-blind observables escape:
   `dS_vib_global` 0.067, ref [16] slow-mode minima 0.292.
2. **Variance collapse reproduces independently.** 11-observable ENM zoo, mean effective
   rank **3.65 / 11** across 6 real chains. External confirmation of TASK-0199, different
   observable set, different proteins.
3. **Adaptive ENM subspaces beat static ones ~9.4×** at equal dimension (ADK, dim 110:
   0.229 vs 0.024) for local pocket-opening deformation.

## 2. Corrections issued this session

- **TASK-0211 §3 was over-read.** Its ~0.000 static-subspace overlap overstates the
  "scale gap" by roughly 9×. Superseded by TASK-0212 §2. Residual gap is real but smaller.
- **"Single ANM-EvoEF2 iteration insufficient" is under-determined.** It reproduces the
  known non-adaptive-ANM limitation documented in ref [15]; it is not evidence about the
  model class. Three explanations (search failure / reachability failure / scorer
  brittleness) are observationally identical in that experiment.
- **The positive holo druggability score is near-tautological** (crystallised with ligand;
  pocket is ligand-shaped). It validates the scorer only. It does not establish apo
  reachability, and ref [18] states the KRAS switch-II pocket is ligand-*induced*.
- **"Hardness lives at side-chain rotamer packing" needs qualifying.** SCP is NP-hard
  worst-case, but DEE/A* and ILP (SCWRL4, OSPREY) solve real instances to global optimality
  routinely. Same trap as the p = 0.24–0.69 soft-mode finding. Resolve before it becomes
  load-bearing.
- **Supervised path ≠ search difficulty.** RMSD-to-holo-guided iteration measures
  reachability and depth, never search cost. Any difficulty claim needs the unsupervised
  objective (TASK-0211 §6.1).

## 3. Reframings worth carrying into the submission

- **Proximity finding:** not "our observable is a distance detector" but "**every
  seed-referencing observable on a static contact graph is a distance detector, including
  the classical analogue the challenge itself cites in Section 5 — and the quantum walk is
  the least affected.**" Same evidence, discharges objective 4.2.
- **Ref [4] / ensemble allostery:** not a missed exit. The harmonic proxy lands in the same
  confounded room (0.773). The *nonlinear* EAM (binary folded/unfolded units) remains
  untested and is the type-correct quantum target (partition function estimation).
- **QUBO objective is mis-typed.** Cryptic pockets are *excited* states; a minimiser returns
  apo. Reformulate as **minimum energy cost to open a druggable pocket at site j**.
- **Move the walk from the residue graph to the conformer graph.** The proximity confound
  cannot exist there (no spatial embedding), it preserves the CTQW investment, and
  Montanaro quantum backtracking is a correct type-match. Quadratic only.

## 4. Highest-value untested items from the references

- **[1] Zheng** NMA-guided conformational sampling — reference number one, MD-free, the
  canonical method for the program's own reframing, **not implemented as a baseline.**
- **[1]+[2] stitched** — NMA sampling → persistent homology → pocket ranking. Zero MD, both
  halves from the organisers' bibliography. Strongest available forward proposal; revives
  the H₂ arm (TASK-0143's 0/7 used a bad proxy and did not kill the family).
- **[9] Gunasekaran** — attacks the negative class of every AUC in the repo. Mandatory in
  limitations regardless of testing.
- **[15] two-state ANM** — the principled instrument to *quantify* TASK-0209 rather than
  assert 2/7.
- **[6] effector-specificity** — audit ASD for additional annotated sites per target; the
  single-site answer key may be under-specified.
- **[11] Oh SVD dilation** — the missing hardware story for ENAQT.
- **[10] circuit cutting** — discharges the coarse-graining half of objective 4.2 on paper.

## 5. Next actions, cheapest first

1. `anm_mode_overlap.py` / `adaptive_subspace_test.py` with the true 4OBE→6OIM,
   1OPL→5MO4, 5TBY→6C1H displacements. Hours. Decides TASK-0211/0212 §2.
2. **Measure p** (progress probability per node, TASK-0212 §6.2). Cheapest decisive
   measurement; calibrated against the prior p = 0.24–0.69 finding. If p lands in that
   band, retire the quantum arm cleanly.
3. Re-run TASK-0210 on real targets with active-site seeds, SASA burial control, `prs_low`
   added, and the **corrected compact-label null** (the scattered null is anti-conservative
   ~4.8× at α=0.05, up to ~42× at α=0.001).
4. Ceiling experiments (TASK-0211 §5.2, TASK-0212 §5) → `ceiling.md` with leakage headers.

## 6. Add to the Cleveland Clinic question list

- **Section 5 mandates the elastic-network hypothesis via [8][15][16]; Section 2 cites [4]
  and [9], which hold that coupling does not decompose onto graph edges and that clean
  non-allosteric negatives may not exist. Which governs for scoring?**
- **Does constraint 3 ("no classical MD trajectories as inputs") exclude minimisation-based
  or Monte-Carlo conformational sampling?** No integrator, no time evolution — but a broad
  reading could be taken to exclude it.

## 7. Standing caveats

- Every number here is **confound structure or subspace geometry only**. No accuracy, AUC,
  or enrichment claim is licensed by any of it.
- **Unresolved and load-bearing:** `GNM_corr_low10` stayed confounded (0.870) here where
  the repo reports `prs_low` collapsing to ≈0.08. Different observables, so not a formal
  conflict — but settle it on the real targets before either number enters a document.
- The 2D ribbon toy (TASK-0212 §1) is a **gate test, not a result**. Sterics are trivial
  in 2D.
- TASK-0183 (PoC sprint plan) and TASK-0184 (submission document) remain P0 and overdue.
  Nothing in this drop changes that; §3's reframings are written to be usable directly in
  TASK-0184.
