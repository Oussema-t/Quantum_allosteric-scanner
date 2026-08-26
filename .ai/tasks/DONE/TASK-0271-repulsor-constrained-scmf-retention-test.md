# TASK-0271 — Repulsor-constrained self-consistent repack, then release: does the pocket stay open?

- Status: TODO
- Assignee: unassigned (suggest Implementer B or D — TASK-0235's machinery is the base)
- Priority: **High — it is a direct [[HYP-P13]] test by an independent route, and it fills a gap three prior tasks left open**
- Filed: 2026-08-26 by Reviewer
- Related: [[TASK-0230]], [[TASK-0235]], [[TASK-0241]], [[TASK-0213]], [[TASK-0268]], [[HYP-P13]], [[TASK-0204]]

## The gap

Three tasks have displaced a backbone and repacked side chains — [[TASK-0230]]
(ceiling), [[TASK-0235]] (local-Kabsch + EvoEF2), [[TASK-0213]] (coupled
search). **None of them ever released the constraint and asked whether the
opened pocket stays open.** That is the metastability question, and it has
never been run here.

The construction comes from an external exchange, and its two halves fix each
other's defect:

- Our own displacement approach has **no coupling** — frozen backbone, frozen
  repack, applied in sequence.
- A self-consistent mean-field loop (alternating repack/minimise) supplies the
  coupling, but it is **downhill**, so it converges back to the apo basin —
  the same excited-state error this register has hit three times.
- **A pinned repulsor holds the pocket open while the loop converges.** Then
  remove it and re-converge, measuring retention.

**Naming discipline, load-bearing**: the loop is **self-consistent mean-field
side-chain packing** and is operationally what Rosetta's FastRelax has done
for over a decade. It is **not** novel and must not be presented as such. The
external exchange attributed it to Koehl & Delarue 1994 — **verify that
citation live before writing it down**; this register has inherited three
wrong citation details from external sources already ([[TASK-0260]],
[[TASK-0262]]).

## Why this is a HYP-P13 test, not a quantum one

[[HYP-P13]] states allostery is *stabilisation of an otherwise-disfavoured
conformation*. That predicts, directly: **the pocket should collapse once the
repulsor is removed.** Persistence would mean the open state is its own
minimum and the ligand is not doing the stabilising.

[[TASK-0268]] just failed HYP-P13's frustration prediction (cryptic residues
showed *lower* frustration, cluster-p=0.727). This attacks the same hypothesis
by a completely independent route. **Two independent tests are worth having
whichever way this lands** — and if it also fails, HYP-P13 should be retired
rather than left standing on the strength of the four findings it was
originally written to explain.

Scope this as a HYP-P13 / metastability test. **It needs no quantum claim to
be worth running, and should not carry one.**

## Scope

- [x] Reuse [[TASK-0235]]'s `local_rigid_reconstruction` + `_run_evoef2`
      machinery rather than introducing Rosetta — a new toolchain turns a
      two-day task into a two-week one, and EvoEF2 is already vendored and
      validated here.
- [x] Implement the alternating loop: repack → local backbone relax → repack,
      to convergence, **with a pinned repulsor** occupying the target pocket.
      Operationalised as the pre-registered full apo→holo displacement, not
      a literal atom — see Done and the Pre-registration section below for
      why (no backbone minimiser/torsion machinery exists here to do the
      literal version without risking fabricated clash artifacts).
- [x] **Pre-register the retention criterion before running.** See
      "Pre-registration" section below, written and committed to before any
      structure was scored.
- [x] Release the repulsor, re-converge the same loop, and measure retention.
- [x] Report per target on [[TASK-0243]]'s frozen set, prioritising the **11
      cryptic-testing targets** ([[TASK-0254]] part B) — the already-open ones
      cannot test collapse because there is nothing to collapse.
- [x] **Trial independence**: [[TASK-0241]] found TASK-0235's "4 trials" were
      one computation repeated four times, byte-identical inputs, because
      `_run_evoef2` takes no seed. Vary the seed or perturb the input, hash
      the trial inputs to prove they differ, and report the jitter band before
      treating any spread as sampling. 88/88 trial hashes distinct across
      both decisive points (44 at t=1.0, 44 at t=0.0).
- [x] Cluster-robust significance ([[TASK-0261]]'s exact cluster-level
      permutation) — this task's own 11 targets are 8 clusters (not 20/13,
      that was [[TASK-0261]]'s own set; this is a different 22-target
      config's 11-member subset, re-clustered directly against
      `candidate_targets_task0243.yaml`, not assumed).

## Acceptance

- [x] Verified citation for the SCMF loop, or an explicit "attribution not
      established". Real citation, real attribution to SCMF side-chain
      packing — but the filing's own "= Rosetta FastRelax" equivalence
      overstates it (FastRelax has real backbone minimisation; Koehl-Delarue
      does not). Corrected, see Done.
- [x] Pre-registered retention criterion, recorded before the first number.
- [x] Per-target retention on the cryptic subset, with a jitter band and
      hashed trial inputs.
- [x] An explicit HYP-P13 verdict, and an update to
      `.claude/hypotheses/physics.md` either way. Verdict: **NOT EVALUABLE**
      (not a clean support for HYP-P13 despite the literal pre-registered
      rule's own 11/11 COLLAPSES readout — see Done).
- [x] `RESULTS.md`.

## Constraint

[[HYP-P13]] is this register's own hypothesis, written up by the Reviewer.
That makes a favourable result **less** trustworthy, not more — the same
caution [[TASK-0268]] carried. Pre-register, and if the pocket persists after
release, report that as evidence *against* HYP-P13 with the prominence the
hypothesis currently enjoys.

## Citation check (done before implementation)

Koehl & Delarue 1994, *J Mol Biol* 239(2):249-275, "Application of a
self-consistent mean field theory to predict protein side-chains
conformation and estimate their conformational entropy" — **real, correctly
attributed to SCMF side-chain packing**, verified live (PubMed 8196057;
ScienceDirect S0022283684713660). But it is specifically a **fixed-backbone**
method (side-chain rotamer probabilities given main-chain coordinates) — the
filing's own claim that this is "operationally what Rosetta's FastRelax has
done for over a decade" **overstates it**: FastRelax couples real backbone
torsion minimisation with repacking; Koehl-Delarue's own method has no
backbone degree of freedom at all. **Corrected, not silently written down.**
A further disclosed gap: EvoEF2's `SideChainRepack` is a simulated-annealing
point-estimate optimizer, not a literal probabilistic mean-field solver —
an approximation to true SCMF, same as every other EvoEF2 use in this
register.

## Pre-registration (2026-08-26, before any structure was scored)

**This project has no backbone minimiser and no torsion-space (NeRF)
machinery** ([[TASK-0235]]'s own module docstring). A literal alternating
"repack / minimise-with-memory" SCMF loop cannot be built without either:
(a) transplanting EvoEF2-chosen side-chain atoms across differing backbone
frames with no internal-coordinate representation to do it correctly — risks
fabricating clash artifacts that would masquerade as a real hysteresis
signal — or (b) inventing a backbone force field this register does not
have. Neither is attempted. **The loop actually run**:

- **"Repulsor held"**: the pinned repulsor is operationalised as the
  pre-registered **full, unprojected apo→holo Cα displacement**
  ([[TASK-0230]]/[[TASK-0235]]'s own `_common_set_and_projection`/
  `local_rigid_reconstruction`, reused unchanged) — the same physically-
  grounded "hold the pocket open" mechanism [[TASK-0230]], [[TASK-0235]] and
  [[TASK-0213]] already used for their own "open" arm, extended here with
  the release arm they never ran. Disclosed explicitly: this is **not** a
  literal inserted steric atom.
- **Release trajectory**: t sweeps `[1.0, 0.75, 0.5, 0.25, 0.0]` (t=1.0 =
  held fully open, t=0.0 = backbone at exact native apo). At each t, the
  backbone target is the **absolute** transform (native apo → apo + t·Δ),
  never compounded step-to-step — avoids drift/artifact from repeatedly
  applying a Cα-derived rigid transform to already-transformed atoms. At
  t=0.0 the transform is the identity: this step is EvoEF2 `SideChainRepack`
  run on **true, unmodified native apo geometry**, independently optimising
  its own rotamers with no memory of the open state — the honest "did we
  actually release everything" reference point.
- **Trial independence**: N=4 trials/target (this register's own established
  multi-trial convention, [[TASK-0230]]/[[TASK-0235]]), each with independent
  Gaussian coordinate perturbation (σ=0.15 Å, [[TASK-0241]]'s own established
  nuisance-perturbation magnitude and per-trial-seeded `_perturb_disp`,
  reused verbatim) plus a forced-distinct EvoEF2 RNG seed
  (`time.sleep(1.05)`, [[TASK-0241]]'s own confirmed mechanism). Full
  replication (N=4) at the two **decisive** points (t=1.0, t=0.0); a single
  representative trial at the three intermediate points, which are
  **descriptive shape only** (gradual vs. cliff-edge collapse), not part of
  the formal bar — stated here before any number exists, so this asymmetry
  cannot be read as bar-shopping after the fact.
- **Retention criterion, fixed now**: `_is_hit` ([[TASK-0204]]'s own
  established rule — fpocket overlap_frac ≥ 0.5 AND druggability_score ≥
  0.5) evaluated **at t=0.0**.
  - **PERSISTS** (evidence *against* HYP-P13): majority (≥3/4) of the t=0.0
    trials clear `_is_hit`. Side-chain repacking alone, at true native
    backbone geometry, supports a druggable open pocket with no lingering
    displacement.
  - **COLLAPSES** (evidence *for* HYP-P13, its own predicted direction):
    majority of t=0.0 trials fail `_is_hit`.
- **Register-level verdict**: per-target PERSISTS/COLLAPSES counts, corrected
  for the pseudo-replication [[TASK-0261]] already found in this same
  22-target config (the 11 cryptic-testing targets cluster into 8 distinct
  apo structures — KSHV_PROTEASE_24Q/25G share 2PBK, HCV_NS5B_POO/CMF share
  2HAI, FBPASE_94D/95S share 5LDZ) — [[TASK-0261]]'s own exact cluster-level
  sign-flip test against a null of 50/50 PERSISTS/COLLAPSES.

## Done

**2026-08-26, Implementer B.** Ran exactly the pre-registered method above,
unchanged, on all 11 targets. Full numbers in `RESULTS.md`'s own
"Does a released, repulsor-held-open pocket stay open?" section and
`.claude/hypotheses/physics.md`'s HYP-P13 section (both updated, not
duplicated verbatim here) — summary:

**A real bug found and fixed before the real run**: the first attempt
crashed on NAMPT_NPA1R (`t0242.prep` returns `pocket=None`, TypeError). Not
a new defect — it is exactly the altloc issue `task0249_composite_dumb_
baseline.py`'s own docstring already documents for this same target
("NAMPT_NPA1R's own real defect"); this script had not yet inherited that
fix. Added `prody.parsePDB` `altloc="all"` monkeypatch, verbatim from
TASK-0249, before running for real. A second, smaller bug in the script's
own first draft: EvoEF2's own internal filename parsing splits on the
FIRST `.`, not the last — a trial tag containing a literal decimal point
(`_t1.0_`) silently truncated EvoEF2's own output filename, making
`_run_evoef2` report a false "exited 0, no output" error for every trial.
Fixed by using a dot-free tag (`100pct`/`075pct`/etc.) before any real
number was computed.

**Citation check** (done first, before any code): Koehl & Delarue 1994,
*J Mol Biol* 239(2):249-275 — real, correctly the origin of SCMF
side-chain packing, verified live (PubMed 8196057, ScienceDirect
S0022283684713660). The filing's own "operationally what Rosetta's
FastRelax has done for over a decade" **overstates it**: Koehl-Delarue is
fixed-backbone; FastRelax couples real backbone torsion minimisation with
repacking. Corrected in `.claude/hypotheses/physics.md`, not silently
written down as given — this register's third inherited citation detail
needing a fix, after [[TASK-0260]] and [[TASK-0262]].

**Result**: the literal pre-registered rule returns **COLLAPSES for
11/11 targets** at t=0.0 (0/4 or 1/4 hits — never a majority). Taken alone
this reads as a clean win for HYP-P13. **It is not one**, and reporting it
as such would violate this task's own Constraint. The same `_is_hit`
majority rule, applied symmetrically to t=1.0 (the fully displaced,
supposedly "held open" reference point), *also* fails a majority for
every single target: 0/4 for 9 of 11 targets, 1/4 for the remaining two
(KSHV_PROTEASE_24Q, KSHV_PROTEASE_25G). **The pocket essentially never
opens correctly-located and druggable at once, anywhere along the
trajectory** — including full displacement to the true holo target. This
is floor-to-floor, not open-to-closed: nothing demonstrably collapses
because nothing demonstrably opened. `results/tasks/
0271_repulsor_scmf_retention/results.json` has every trial's
`overlap_frac`/`druggability_score`, not just the binary hit.

The cluster-permutation test on the raw t=0.0 hit counts (8 clusters,
[[TASK-0261]]'s own exact sign-flip method, `t0261.CM` overridden to this
task's own cluster map, algorithm unchanged) returns p=0.0078 — reported
for completeness per the pre-registration, but it is measuring "hit rate
below majority" on a near-zero-variance series across the whole
trajectory, not measuring retention, and does not change the verdict below.

**Verdict: NOT EVALUABLE.** Neither a decisive negative (like
[[TASK-0268]]'s frustration test) nor support for HYP-P13 — the
displace-and-repack machinery this register has validated
([[TASK-0230]]/[[TASK-0235]]) essentially never clears its own strict
overlap+druggability bar on this 11-target cryptic subset, at any point
along the release trajectory, so the retention question this task set out
to answer has no data to answer it with. Joins [[TASK-0264]]/[[TASK-0267]]'s
own "closed on a prerequisite, not a clean test" category. Descriptive,
not part of the formal bar: druggability_score alone (ignoring overlap) is
sometimes *higher* at t=0.0 than t=1.0 for several targets (FBPASE_94D up
to 0.75 vs ≤0.46 at t=1.0; NAMPT_NPA1R up to 0.93 vs ≤0.10) — independent
EvoEF2 repacking of true native apo can open *some* druggable cavity, just
not reliably the correct one, echoing [[TASK-0230]] §5.3's own
scorer-brittleness theme rather than telling us anything about retention.

**Trial independence, verified not assumed**: 88/88 trial hashes distinct
across the two decisive points (44 at t=1.0, 44 at t=0.0) — the exact
byte-identical-input defect [[TASK-0241]] found in TASK-0235's own "4
trials" does not recur here.

**`.claude/hypotheses/physics.md` updated** under HYP-P13's own section,
same prominence [[TASK-0268]]'s decisive negative received, including the
floor-problem caveat and the citation correction.

**Artifacts**: `scripts/task0271_repulsor_scmf_retention.py`; `results/
tasks/0271_repulsor_scmf_retention/results.json` (every trial, both
binary hit and continuous overlap/druggability); `RESULTS.md`; this file.

**Not attempted, explicitly out of scope**: a literal inserted steric
repulsor atom (no backbone force field/gradient access exists to model it
without fabricating artifacts, disclosed in the Pre-registration section
above); iterative rotamer-memory transplant across differing backbone
frames (same reason); re-running the already-open targets from
[[TASK-0254]] Part B (nothing to test collapse against, per this task's
own Scope).
