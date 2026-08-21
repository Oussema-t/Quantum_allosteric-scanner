# TASK-0211 — ANM⊕rotamer QUBO: reachability ceiling before any further search effort

**Status:** HYPOTHESIS / spec. Contains one OBSERVED result on non-target structures.
**Date:** 2026-08-21. External session, no repo access, no rcsb egress.
**Supersedes the inference in:** whichever task concluded "single ANM-EvoEF2 iteration
insufficient" — that conclusion is under-determined, see §1.

---

## 1. The inference under review

Observed prior chain: druggability(holo) high → druggability(ANM-flexed apo + EvoEF2
repack) low → "single iteration insufficient" → more search → QUBO.

**The step from a low apo score to "search was insufficient" is not supported by the
experiment as run.** Three explanations are observationally identical:

| | explanation | does QUBO help? |
|---|---|---|
| (a) | search failure — right space, wrong point | yes |
| (b) | reachability failure — holo not in ANM⊕rotamer space | **no** — optimises a space lacking the answer |
| (c) | scorer brittleness — flat-then-cliff druggability objective | **no** — objective uninformative for any optimiser |

No claim about QUBO viability should be written until (a)/(b)/(c) are separated.

## 2. Literature status — the single iteration reproduces known art

- **Ref [15] Das/Gur/Cheng/Jo/Bahar/Roux 2014** exists because **single-shot ANM does not
  reach a second endpoint**; modes rotate along the path, requiring adaptive ANM with the
  Hessian rebuilt per step. The single-iteration failure is *predicted* by cited prior art.
- **Ref [1] Zheng 2023** samples many CG-NMA-guided conformations, not one.

**Therefore: the experiment confirms [15], it does not measure the model class.** Correct
the claim wording accordingly — "non-adaptive single-step ANM+repack insufficient,
consistent with [15]" — not "ANM+repack insufficient."

## 3. OBSERVED — the actuator/target scale mismatch

Cumulative overlap of a deformation with the top-k ANM modes (cutoff 15 Å, γ=1), real
CA structures, 40 surface sites per protein (ADK, 1R19, 3HSY, 3ENL — **not** challenge
targets).

| deformation | k=5 | k=10 | k=20 | k=50 |
|---|---|---|---|---|
| collective domain hinge (LID-like), ADK | 0.468 | 0.629 | 0.728 | 0.828 |
| smooth random field | 0.079 | 0.134 | 0.164 | 0.450 |
| **local 10 Å shell opening** (mean, 4 proteins × 40 sites) | **0.000** | **0.000–0.001** | **0.001–0.003** | **0.005–0.008** |
| single-residue kick | 0.011 | 0.069 | 0.076 | 0.239 |

Hinge control at 0.63 (k=10) matches classic ANM/apo-holo overlap literature → harness sound.

**OBSERVED: local pocket-opening deformation is essentially orthogonal to the low-mode
ANM subspace.**

**Diagnosis — scale gap, not search depth.** ANM low modes span *collective backbone*.
EvoEF2 repack spans *side chains*. **Local backbone rearrangement (loop/helix shift),
which is what most cryptic pockets are, is spanned by neither.** Iterating a two-layer
pipeline cannot close a gap neither layer spans, and neither can a QUBO over rotamers.

### 3.1 Caveat — load-bearing
The opening vector used is a uniform radial expansion of a 10 Å shell: **adversarially
local**. Real apo→holo displacements are more collective. **0.000 is a lower bound on true
overlap, not an estimate.** The number that settles this is §5.1 and must be computed
before this section is cited anywhere.

## 4. Reconciling the positive holo druggability score

**The holo positive is close to tautological.** The structure was crystallised with the
ligand in the pocket; the pocket is ligand-shaped by construction. It validates the
**scorer**. It does not establish that the conformation is populated in apo, nor that a
scoreable intermediate exists.

**Ref [18] Ostrem 2013** states the KRAS switch-II pocket is *induced* by the covalent
ligand. If correct, the pocket may not exist as an accessible apo state — no apo-side
search of any depth finds it. **CONTESTED:** MD-based cryptic-pocket work (Bowman lab,
PocketMiner training ensembles) does observe transient apo opening. Unsettled, decidable.

**Conclusion: the holo positive is consistent with (a), (b), and "ligand-stabilised only."
It does not single out (a) and must not be cited as if it does.**

## 5. Required experiments, in order

### 5.1 Mode-overlap on real challenge pairs — cheap, do first
Overlap of the true apo→holo displacement with the apo ANM subspace (after
superposition and rigid-body removal), k = 5/10/20/50, for 4OBE→6OIM, 1OPL→5MO4,
5TBY→6C1H. Bahar-style cumulative overlap.
- ≳0.5 → collective part reachable; concern reduces to the local residual (§3).
- ≲0.05 → model-class failure; retire the QUBO arm.

### 5.2 Reachability ceiling — decisive, oracle-supervised
Project the true apo→holo displacement onto the apo ANM subspace, take the best
achievable approximation, repack optimally (DEE/A* or Rosetta packer for a *global*
optimum, not a heuristic), score druggability.
- **This deliberately uses the answer. It is a CEILING, not a predictor.**
  File under `ceiling.md` with an explicit label-leakage header per repo convention.
- Ceiling high → failure is search → QUBO on the table, subject to §6.
- Ceiling low → model-class failure → retire the arm in the writeup rather than carry it.

### 5.3 Scorer-brittleness control — separates (c)
Interpolate apo→holo in 20 steps; score druggability at each. If the profile is
flat-then-cliff rather than monotone, **the druggability score is unusable as an
optimisation objective** regardless of the search method, and that is itself a reportable
finding about the field's tooling.

### 5.4 Adaptive ANM control — separates iteration count from model class
Re-run with adaptive ANM ([15]) rather than single-shot, holding everything else fixed.
Isolates "more iterations" from "wrong space."

## 6. If the ceiling passes: four defects in the current QUBO formulation

1. **Wrong optimisation type — most severe.** QUBO returns a minimum; cryptic pockets are
   *excited* states (ΔG_open > 0 is what makes them cryptic). Minimising energy over
   backbone⊕rotamers returns the apo structure.
   **Reformulation:** score = **minimum energy cost to open a druggable pocket at site j**,
   i.e. constrained minimisation with a pocket-volume penalty term. Still a QUBO; per-site,
   so it yields a ranking; informative even when the pocket stays closed; physically
   meaningful (pocket-opening free energy, cf. binding leverage and ref [1]). The current
   formulation asks a yes/no question that will nearly always answer no.
2. **Sequential ≠ joint.** ANM-then-repack greedily decomposes a coupled problem. Correct
   object: joint QUBO over (discretised mode amplitudes ⊗ rotamers). **Blocker to state
   explicitly:** EvoEF2 pair energies depend continuously on backbone, so this needs either
   m^k precomputed tables (exponential in modes retained) or linearisation exactly where
   steric repulsion is most nonlinear.
3. **Hardness is worst-case, not typical-case.** SCP is NP-hard, but DEE/A* and ILP
   (SCWRL4, OSPREY, Rosetta packer) solve real instances to global optimality routinely.
   Same failure shape as the ENM soft-mode result (pocket opening non-rare, p = 0.24–0.69).
   **A typical-case hardness demonstration is required before any quantum claim.** The
   joint backbone+rotamer problem is the better candidate but must be shown, not asserted.
4. **Missing variable class.** Per §3, add local backbone DOF (fragment/loop moves, or a
   local-mode subspace) or the QUBO searches a space that does not contain the target.

## 7. Verdict

**Not excluded. Not tested. Currently mis-typed.** The prior negative result measures
[15]'s known single-shot ANM limitation, not the model class. §5.1 and §5.2 are cheap and
decide the question either way; both outcomes are writeable under the program's
negative-result frame. Until they are run, the arm should appear in the submission as an
open proposal with §6.1's reformulation and §6.3's hardness gap named — **not** as a
validated quantum-plausible pathway, and **not** as excluded.
