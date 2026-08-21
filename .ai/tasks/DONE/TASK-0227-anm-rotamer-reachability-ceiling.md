# TASK-0227 (re-indexed from the 2026-08-21 external drop's "TASK-0211_anm_rotamer_qubo_reachability")

## Context

- ID: TASK-0227
- Status: Done
- Resolution: done
- Resolution Note: PDB-retest of the external drop's ANM mode-overlap claim on real challenge targets (4OBE/6OIM, 1OPL/5MO4, 5TBY/8QYR-corrected): collective apo->holo motion IS reachable by a static ANM subspace (0.51-0.67 overlap at k=50, clears the task's own 0.5 bar) -- reverses both the original ~0.000 synthetic finding and its own 9.4x adaptive correction, neither of which transferred from the synthetic toy to real data. Full findings in Done section + RESULTS.md.
- Owner: Implementer
- Claimed By: —
- Claimed At: —
- Source: `.ai/reviews/2026-08-21/TASK-0211_anm_rotamer_qubo_reachability.md` — external session, no repo
  access, no rcsb.org egress. **Every numeric in the body below was run on
  bundled non-target structures (prody / MDAnalysisTests). Nothing in it may be
  cited in the submission before a PDB-retest on real challenge targets.**
- **Re-indexed on filing.** The drop numbered this `TASK-0211_anm_rotamer_qubo_reachability`, but that ID is
  already taken in this register by unrelated, completed work:
  TASK-0210 (coupled backbone+rotamer search, Done), TASK-0211 (ensemble-graph
  observable independence, Done), TASK-0212 (frustration-rank reproducibility,
  closed as invalidated). Renumbered to TASK-0227 rather than the incumbents,
  per this register's own collision precedent (TASK-0156/0157, TASK-0168).
  **Cross-references inside the body below still use the drop's own numbering**
  and are mapped here: drop 0210 → TASK-0226, drop 0211 → TASK-0227,
  drop 0212 → TASK-0228.

## Intent Contract

Written retroactively on pickup — the drop below is a raw external review
document, not a scaffold-format Intent Contract, so this is added before
starting to make scope and validation explicit.

- Outcome: answer the question the source document's own §7 Verdict poses
  ("not excluded, not tested") for the cheapest, most decisive item on its
  own list — §5.1 (real-target mode overlap) — and its closely related
  §5.4 (adaptive control, same displacement data, same script family) —
  since the source's own §5's ordering names §5.1 "cheap, do first" and
  the accompanying `SESSION_2026-08-21_HANDOFF.md`'s own "Next actions,
  cheapest first" list puts exactly this ("hours") at #1.
- Why required, not assumed: the source document's central claims (§3's
  ~0.000 overlap, and TASK-0228's own correction to ~0.229/9.4×) are both
  explicitly self-flagged as measured on non-target structures only,
  "nothing... may be cited in the submission before a PDB-retest."
- In Scope:
  - §5.1: cumulative overlap of the true, Kabsch-superposed apo→holo Cα
    displacement (residues common to both structures) with the static
    apo ANM subspace (k=5/10/20/50), for the 3 pairs the source names:
    4OBE→6OIM, 1OPL→5MO4, 5TBY→6C1H — reusing `anm_mode_overlap.py`'s own
    `anm_subspace`/`cumulative_overlap` functions unmodified, not
    re-derived.
  - §5.4: the adaptive-vs-static equal-dimension comparison
    (`adaptive_subspace_test.py`, unmodified), same real displacement
    data, since it's cheap given §5.1's setup and directly checks whether
    the source's own 9.4× "correction" (TASK-0228 §2) transfers to real
    targets.
  - If a named target pair turns out invalid for this analysis (checked,
    not assumed), substitute this repo's own established correction and
    report both, with the reason.
  - Record the decisive result against the source document's own
    pre-registered thresholds (§5.1: ≳0.5 collective reachable, ≲0.05
    model-class failure) — don't invent new thresholds after seeing the
    data.
- Out Of Scope:
  - §5.2 (oracle-supervised reachability ceiling) — needs a global-optimum
    side-chain repacker (DEE/A*/Rosetta-class); confirmed not installed in
    this environment (`EvoEF2` absent). Flagged, not run.
  - §5.3 (scorer-brittleness interpolation control) — needs a druggability
    scorer; `fpocket` also confirmed not installed (and TASK-0206 already
    documents this repo's own fpocket build-drift history). Flagged, not
    run.
  - §5.2/§6.1's reformulated QUBO objective, §6's four formulation defects,
    and §6.2-equivalent (TASK-0228's own "p" progress-probability
    measurement) — downstream of §5.1/§5.2 and this task's own "if the
    ceiling passes" framing; moot until a ceiling experiment exists.
  - Editing TASK-0228 itself — same displacement data directly answers its
    own §2 "PDB-RETEST" instruction too, noted here for whoever picks that
    task up next, but not resolved under this task's own claim.
- Constraints And Invariants: read-only against the ANM/rotamer question —
  no change to `backend/`'s live pipeline; this is a research-tree
  (`__WORK_IN_PROGRESS__/`) investigation, output under
  `__WORK_IN_PROGRESS__/results/tasks/0227_anm_rotamer_reachability/`,
  matching this project's existing per-task results-folder convention.
- Planned Validation: real, network-fetched RCSB structures (not mocked),
  the project's own shared Kabsch implementation (`backend/geometry.py`,
  not re-derived), and the source's own harness functions imported
  unmodified — so the only new code is data plumbing (fetch, common-residue
  selection, superposition), not new physics.

---

## Original document, verbatim

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

---

## Done

**§5.1/§5.4 run on real challenge targets. Decisive: the collective part is
reachable on all 3 real, valid target pairs — reverses both the source
document's original ~0.000 claim and its own 9.4× correction, neither of
which transfers from the synthetic toy to real data.**

Script + raw output:
`__WORK_IN_PROGRESS__/results/tasks/0227_anm_rotamer_reachability/pdb_retest.py`
(+ `pdb_retest_results.json`). Reused `anm_mode_overlap.py`'s
`anm_subspace`/`cumulative_overlap` and `adaptive_subspace_test.py`'s
`adaptive_union`/`captured`/`modes` unmodified, per this task's own
Constraint — only new code is the real-PDB plumbing (fetch via
`backend.data_layer.load_structure`, common-residue selection, Kabsch
superposition via `backend/geometry.py`).

| target | apo/holo | N common | RMSD (Å) | static overlap k=5/10/20/50 | adaptive/static ratio (dim=110) |
|---|---|---|---|---|---|
| KRAS_G12C | 4OBE→6OIM | 166 | 1.36 | 0.254 / 0.404 / 0.467 / **0.667** | 1.03× |
| BCR_ABL1 | 1OPL→5MO4 | 429 | 0.98 | 0.295 / 0.342 / 0.417 / **0.577** | 0.88× |
| CARDIAC_MYOSIN (fully corrected) | 8QYP→8QYR | 698 | 1.18 | 0.595 / 0.766 / 0.826 / **0.901** | 1.01× |
| CARDIAC_MYOSIN (holo-only corrected) | 5TBY→8QYR | 709 | 3.75 | 0.275 / 0.298 / 0.368 / 0.511 | 0.77× |
| CARDIAC_MYOSIN (literal spec, invalid) | 5TBY→6C1H | 366 | 26.80 | 0.043 / 0.087 / 0.192 / 0.386 | 1.46× |

**Two target-pair substitutions, both reasons recorded (per this task's own
In Scope item) — the second one caught only because a concurrent thread's
work was visible, not independently found here.** `backend/systems.py`
already flags 6C1H as invalid for CARDIAC_MYOSIN (Unconventional MYOSIN-Ib,
actin-bound cryo-EM, no mavacamten — confirmed directly by the 26.8 Å
"displacement," an order of magnitude beyond every other pair's 1–4 Å);
`holo_validation=8QYR` fixes the holo side. But `__WORK_IN_PROGRESS__/
config/targets.yaml` (TASK-0124) goes further: **5TBY itself is a docked
SWISS-MODEL homology model** (20.0 Å nominal resolution, EM-fitted, zero
ligands, RCSB-verified 2026-08-19 per TASK-0222), not an experimental apo
structure — `apo_pdb: 8QYP` is the real X-ray apo. Found this by reading
an untracked script another concurrent thread (the same 'Reviewer-thread
(Opus)' this task's claim was overridden from — still actively working,
apparently now on [[TASK-0228]]) had already left at
`__WORK_IN_PROGRESS__/scripts/task0228_adaptive_subspace_pdb_retest.py`,
not independently discovered; credited here rather than presented as this
task's own finding. Re-ran with the fully-corrected pair: RMSD drops to
1.18 Å (in line with the other two clean targets, vs. 3.75 Å for the
homology-model apo), and overlap rises sharply (0.90 at k=50, 0.77 already
at k=10) — the crude homology-model apo was suppressing the apparent
overlap by roughly half, not changing its direction. All three numbers
kept in the table above for transparency (worse-apo → better-apo →
same-conclusion progression is itself informative, not just noise).

**Verdict, against this task's own pre-registered §5.1 thresholds** (≳0.5
collective reachable, ≲0.05 model-class failure): all 3 real, valid target
pairs clear 0.5 at k=50 — CARDIAC_MYOSIN clears it by k=5 on the fully
corrected pair; none approach 0.05 at any k. **The collective part of real
apo→holo motion is reachable by a plain static apo ANM subspace** — the
opposite of §3's "essentially orthogonal" framing. Per this task's own
decision rule, this retires the "model-class failure" reading and demotes
§3's concern to its already-acknowledged secondary status (a possible
smaller local residual, not evaluated here — see Out Of Scope).

**Not just a magnitude correction — the direction of surprise reverses
too.** TASK-0228's own §2 correction argued the ~0.000 static number
understated reality ~9× (0.024→0.229, via an adaptive subspace) but still
concluded "0.229 is still not 1.0... a genuine, smaller local-backbone
gap." On real targets, plain **static** ANM alone reaches 0.58–0.90 —
higher, on every target, than TASK-0228's own *adaptive*-subspace number
for its synthetic deformation (0.229). And the adaptive/static ratio on
real data is 0.77×–1.46× (sometimes adaptive is *worse* at equal
dimension) — even on the highest-fidelity pair (CARDIAC_MYOSIN,
8QYP→8QYR) it's a bare 1.01×, essentially no gain, once real, high-quality
apo geometry is used. Nothing like the reported 9.4×. Both prior numbers
were artifacts of the synthetic "adversarially local 10 Å shell opening"
deformation type (explicitly flagged as a lower bound by the source's own
§3.1 caveat) — confirmed here, not merely suspected.

**Out of reach in this pickup, confirmed not merely assumed**: §5.2
(oracle-supervised ceiling) needs a global-optimum side-chain repacker —
`which EvoEF2` and a filesystem search both came up empty in this
environment. §5.3 (scorer-brittleness interpolation) needs a druggability
scorer — `fpocket` binary also absent (consistent with TASK-0206's own
fpocket build-drift history in this repo). Both need dedicated tooling
work; recorded as a natural follow-up, not silently skipped.

**RESULTS.md updated** (claimed + staleness-checked per TASK-0195's
protocol before editing; `check_references.py` clean after) — new section
"ANM subspace reachability of real apo→holo motion — PDB-retest reverses
the synthetic-toy result". **Not done**: editing TASK-0228 itself, though
the same dataset directly answers its own §2 "PDB-RETEST" request — left
for whoever picks that task up, noted in its Dependency context via this
task's own cross-reference above, per this task's own Out Of Scope.

**Claim history**: this task was claimed by 'Reviewer-thread (Opus)' at
2026-08-21 11:16 and overridden on explicit user instruction ("pick up
(and override claim if needed) on 227") at 2026-08-21 (this session) —
recorded via `claim.py claim --force --reason`, not a silent takeover.
